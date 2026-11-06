"""Offline catalog extraction, safety, drift, and publication regressions."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('catalog_builder',ROOT/'scripts/build_pages.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

class CatalogTests(unittest.TestCase):
    def test_generated_catalog_is_deterministic_and_complete(self):
        first=builder.build_catalog()
        self.assertEqual(builder.serialize(first),builder.serialize(builder.build_catalog()))
        generated=ROOT/'docs/resources.json'
        if generated.exists():
            self.assertEqual(json.loads(generated.read_text(encoding='utf-8')),first)
        self.assertEqual(len(first['resources']),sum(source['count'] for source in first['sources']))
        self.assertEqual(len(first['sources']),5)

    def test_source_markdown_change_changes_generated_payload_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for source,_ in builder.SOURCES.values():
                target=root/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,target)
            before=builder.build_catalog(root)
            path=root/'کتاب‌ها/README.md'
            path.write_text(path.read_text(encoding='utf-8').replace('آموزش گیت به زبان فارسی','عنوان آزمون ساختگی'),encoding='utf-8')
            after=builder.build_catalog(root)
            self.assertNotEqual(before['sourceDigest'],after['sourceDigest'])
            self.assertEqual(after['resources'][0]['title'],'عنوان آزمون ساختگی')
            self.assertEqual(len(before['resources']),len(after['resources']))

    def test_balanced_urls_and_channel_prefixes_and_related_links(self):
        text='## موضوع\n1. **مدرس ساختگی** — Python و Git. [مشاهده کانال](https://example.org/@channel)\n'
        row=builder.parse_source(text,'کانال‌های یوتیوب/README.md','کانال‌های یوتیوب','کانال')[0]
        self.assertEqual(row['title'],'مدرس ساختگی');self.assertIn('Python',row['description'])
        row=builder.parse_source('## موضوع\n- [عنوان](https://example.org/(python)) — توضیح؛ [مرجع](https://example.org/docs).\n','کتاب‌ها/README.md','کتاب‌ها','کتاب و متن')[0]
        self.assertEqual(row['url'],'https://example.org/(python)')
        self.assertEqual(row['relatedLinks'],[{'title':'مرجع','url':'https://example.org/docs'}])
        self.assertEqual(row['sourceLine'],2)

    def test_malformed_unsafe_empty_and_duplicate_entries_fail_closed(self):
        for text in ['# خالی\n','## تست\n- [عنوان](https://example.org/unfinished', '## تست\n- [عنوان](javascript:alert(1))', '## تست\n- [عنوان](https://example.org/?token=synthetic)', '## تست\n- [عنوان](https://example.org)\n- [دوباره](https://example.org)']:
            with self.subTest(text=text):
                self.assertRaises(ValueError,builder.parse_source,text,'کتاب‌ها/README.md','کتاب‌ها','کتاب و متن')

    def test_access_claims_come_from_explicit_notes_not_title(self):
        source='## تست\n- [دوره رایگان](https://example.org/a)\n- [دوره](https://example.org/b) — صفحه ناشر در ۲۲ اکتبر ۲۰۲۶ دوره را رایگان اعلام می‌کند.\n'
        rows=builder.parse_source(source,'دوره‌ها/README.md','دوره‌ها','دوره')
        self.assertIn('نیازمند بررسی',rows[0]['access'])
        self.assertIn('ناشر رایگان اعلام',rows[1]['access'])
        self.assertIn('۲۰۲۶',rows[1]['description'])

    def test_supplementary_types_follow_explicit_youtube_structure(self):
        rows=builder.parse_source('## کانال‌های فارسی بیشتر\n1. [کانال](https://www.youtube.com/@fictional)\n## دوره‌ها\n1. [ویدیو](https://www.youtube.com/playlist?list=fixture)\n','منابع-تکمیلی/README.md','منابع تکمیلی','منبع تکمیلی')
        self.assertEqual([r['kind'] for r in rows],['کانال','ویدیو'])

    def test_pages_runs_on_all_master_and_pull_request_changes(self):
        workflow=(ROOT/'.github/workflows/pages.yml').read_text(encoding='utf-8')
        self.assertNotIn('paths:',workflow)
        self.assertIn('needs: verify',workflow)
        self.assertIn('python scripts/build_pages.py --check',workflow)
        self.assertIn('name: github-pages-${{ github.run_attempt }}',workflow)
        self.assertIn('artifact_name: github-pages-${{ github.run_attempt }}',workflow)
        self.assertIn('contents: read',workflow)
