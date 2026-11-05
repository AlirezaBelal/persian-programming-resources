from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "کتاب و متن": (ROOT / "کتاب‌ها" / "README.md", "کتاب‌ها"),
    "دوره": (ROOT / "دوره‌ها" / "README.md", "دوره‌ها"),
    "ویدیو": (ROOT / "دوره‌های آموزشی در یوتیوب" / "README.md", "دوره‌های آموزشی در یوتیوب"),
    "کانال": (ROOT / "کانال‌های یوتیوب" / "README.md", "کانال‌های یوتیوب"),
    "منبع تکمیلی": (ROOT / "منابع-تکمیلی" / "README.md", "منابع تکمیلی"),
}
LINK = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)\s]+)\)(?P<tail>[^\n]*)")

class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)

def clean(value):
    p = Plain(); p.feed(value); return " ".join("".join(p.parts).split()).strip(" -*—:؛")

resources = []
for kind, (path, category) in SOURCES.items():
    heading = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### ") or line.startswith("## "):
            heading = line.lstrip("# ").strip()
        if not re.match(r"^\s*(?:[-*]|\d+\.)\s+", line): continue
        match = LINK.search(line)
        if not match: continue
        title, url, tail = match.group("title", "url", "tail")
        if "github.com/AlirezaBelal/persian-programming-resources" in url: continue
        description = clean(tail.split("**")[0].strip(" —–-"))
        flags = []
        if "مجوز ترجمه نیازمند بررسی" in tail: flags.append("مجوز ترجمه نیازمند بررسی")
        if "قدیمی" in tail: flags.append("منبع قدیمی")
        resources.append({"title": clean(title), "url": url, "description": description, "category": category, "topic": heading, "kind": kind, "flags": flags, "source": path.relative_to(ROOT).as_posix()})

if not resources: raise SystemExit("No curated resource entries were found.")
out = ROOT / "docs" / "resources.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"resources": resources}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Generated {len(resources)} resources from {len(SOURCES)} tracked catalogs.")
