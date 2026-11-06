"""Deterministic, offline catalog generation from five tracked Markdown sources."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
import argparse
import hashlib
import json
import os
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'کتاب و متن': ('کتاب‌ها/README.md', 'کتاب‌ها'),
    'دوره': ('دوره‌ها/README.md', 'دوره‌ها'),
    'ویدیو': ('دوره‌های آموزشی در یوتیوب/README.md', 'دوره‌های آموزشی در یوتیوب'),
    'کانال': ('کانال‌های یوتیوب/README.md', 'کانال‌های یوتیوب'),
    'منبع تکمیلی': ('منابع-تکمیلی/README.md', 'منابع تکمیلی'),
}
LINK = re.compile(r'\[(?P<title>[^\]\n]+)\]\((?P<url>(?:[^()\s]|\([^()\n]*\))+)\)')
SENSITIVE = {'api_key','apikey','access_token','token','auth','authorization','password','secret','client_secret','signature'}
BLOCKED = {'t.me','telegram.me','mega.nz','mediafire.com'}

class Plain(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

def clean(value):
    value = LINK.sub(lambda m: m['title'], value)
    parser = Plain(); parser.feed(value)
    return ' '.join(''.join(parser.parts).replace('**','').split()).strip(' -*—–:؛')

def safe_url(value):
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or '').lower()
        return (parsed.scheme in {'http','https'} and bool(host) and not parsed.username
                and parsed.password is None and not any(c.isspace() or ord(c)<32 for c in value)
                and not any(host == h or host.endswith('.'+h) for h in BLOCKED)
                and not any(k.lower() in SENSITIVE for k,_ in parse_qsl(parsed.query,keep_blank_values=True)))
    except ValueError:
        return False

def parse_source(text, source, category, default_kind):
    resources = []; heading = ''; seen = set()
    for number, line in enumerate(text.splitlines(),1):
        if re.match(r'^#{2,3} ',line):
            heading=line.lstrip('# ').strip()
        if not re.match(r'^\s*(?:[-*]|\d+\.)\s+',line):
            continue
        matches=list(LINK.finditer(line))
        external=[m for m in matches if urlsplit(m['url']).scheme in {'http','https'}]
        if not external:
            if re.search(r'\]\((?:https?:|javascript:|data:)',line):
                raise ValueError(f'{source}:{number}: malformed or unsafe resource link')
            continue
        first=external[0]
        if any(not safe_url(m['url']) for m in external):
            raise ValueError(f'{source}:{number}: unsafe resource URL')
        if any(name in first['url'] for name in ('github.com/AlirezaBelal/masir-yadgiri', 'github.com/AlirezaBelal/persian-programming-resources')):
            continue
        prefix=line[:first.start()]
        channel=re.match(r'^\s*\d+\.\s+\*\*(.+?)\*\*\s*[—–:-]\s*(.*)',prefix)
        title=clean(channel[1] if channel else first['title'])
        description=clean(channel[2] if channel else line[first.end():]).replace('[مجوز ترجمه نیازمند بررسی]', '').strip()
        if not title or not heading:
            raise ValueError(f'{source}:{number}: resource title or topic missing')
        key=(first['url'],heading)
        if key in seen:
            raise ValueError(f'{source}:{number}: duplicate entry in the same topic')
        seen.add(key)
        kind=default_kind
        host=(urlsplit(first['url']).hostname or '').lower()
        if default_kind=='منبع تکمیلی' and host in {'youtube.com','www.youtube.com','youtu.be'}:
            kind='کانال' if 'کانال' in heading else 'ویدیو'
        flags=[]
        if 'مجوز ترجمه نیازمند بررسی' in line: flags.append('مجوز ترجمه نیازمند بررسی')
        if 'قدیمی' in line: flags.append('منبع قدیمی')
        if 'نشانی نیازمند بررسی' in line: flags.append('نشانی نیازمند بررسی')
        if first['url'].startswith('http:'): flags.append('پیوند بدون HTTPS')
        access='ناشر رایگان اعلام کرده؛ یادداشت تاریخ‌دار منبع را بخوانید' if re.search(r'ناشر.*رایگان اعلام',line) else 'دسترسی و هزینه نیازمند بررسی'
        resources.append({'title':title,'url':first['url'],'description':description,'category':category,
                          'topic':heading,'kind':kind,'flags':flags,'access':access,'publisher':host,
                          'source':source,'sourceLine':number,
                          'relatedLinks':[{'title':clean(m['title']),'url':m['url']} for m in external[1:]]})
    if not resources:
        raise ValueError(f'{source}: no resource entries found')
    return resources

def build_catalog(root=ROOT):
    resources=[]; sources=[]
    for kind,(source,category) in SOURCES.items():
        text=(root/source).read_text(encoding='utf-8')
        entries=parse_source(text,source,category,kind)
        sources.append({'path':source,'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),'count':len(entries)})
        resources.extend(entries)
    payload={'schemaVersion':1,'sources':sources,'resources':resources}
    payload['sourceDigest']=hashlib.sha256(json.dumps(sources,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    return payload

def serialize(catalog):
    return json.dumps(catalog,ensure_ascii=False,indent=2)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Fail if generated resources.json differs from tracked sources')
    args=parser.parse_args()
    expected=serialize(build_catalog()); output=ROOT/'docs/resources.json'
    if args.check:
        if not output.is_file() or output.read_text(encoding='utf-8')!=expected:
            raise SystemExit('Generated catalog is stale; run python scripts/build_pages.py')
        print('Catalog matches all five tracked sources.'); return
    output.parent.mkdir(exist_ok=True)
    fd, temporary=tempfile.mkstemp(prefix='.catalog-',suffix='.tmp',dir=output.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as stream:
            stream.write(expected)
        os.replace(temporary,output)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    print(f'Generated {len(json.loads(expected)["resources"])} resources from {len(SOURCES)} tracked catalogs.')

if __name__=='__main__':
    main()
