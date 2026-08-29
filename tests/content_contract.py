from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = sorted(ROOT.rglob("*.md"))

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
]
DISALLOWED_MIRROR_PATTERNS = [
    "t.me/",
    "telegram.me/",
    "mega.nz/",
    "mediafire.com/",
]

errors = []

if not MARKDOWN_FILES:
    errors.append("No Markdown content found.")

for path in MARKDOWN_FILES:
    rel = path.relative_to(ROOT)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{rel}: not valid UTF-8")
        continue

    for match in EMAIL_RE.finditer(text):
        errors.append(f"{rel}: personal email address found: {match.group(0)}")

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: credential/private-key pattern found")

    lowered = text.lower()
    for pattern in DISALLOWED_MIRROR_PATTERNS:
        if pattern in lowered:
            errors.append(f"{rel}: unverified mirror domain found: {pattern}")

    if re.search(r"\]\([^\n)]*\(https?://", text, re.IGNORECASE):
        errors.append(f"{rel}: malformed nested URL in Markdown link")

root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
required_phrases = [
    "# منابع رایگان برنامه‌نویسی فارسی",
    "دوره رایگان پایتون فارسی",
    "کتاب برنامه‌نویسی فارسی",
    "سوالات متداول",
    "does not mirror, upload, or redistribute",
    "Curation principles",
    "Linked third-party resources are **not relicensed",
]
for phrase in required_phrases:
    if phrase not in root_readme:
        errors.append(f"README.md: missing content/SEO boundary: {phrase}")

category_expectations = {
    "کتاب‌ها/README.md": "# کتاب‌های رایگان برنامه‌نویسی فارسی",
    "دوره‌ها/README.md": "# دوره‌های رایگان برنامه‌نویسی فارسی",
    "دوره‌های آموزشی در یوتیوب/README.md": "# دوره‌های رایگان برنامه‌نویسی فارسی در یوتیوب",
    "کانال‌های یوتیوب/README.md": "# کانال‌های یوتیوب فارسی برای آموزش برنامه‌نویسی",
}
for rel_path, heading in category_expectations.items():
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    if heading not in text:
        errors.append(f"{rel_path}: missing discoverable H1: {heading}")

books = (ROOT / "کتاب‌ها/README.md").read_text(encoding="utf-8")
if "و ساده برای فهم بهتر الگوریتم‌ها" in books:
    errors.append("کتاب‌ها/README.md: orphaned algorithm description returned")

courses = (ROOT / "دوره‌ها/README.md").read_text(encoding="utf-8")
c_section = courses.split("### سی\n", 1)[1].split("### سی شارپ", 1)[0]
if "جاواپرو" in c_section:
    errors.append("دوره‌ها/README.md: Java course is miscategorized under C")

license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
if "MIT License" not in license_text:
    errors.append("LICENSE: expected MIT license text")

if errors:
    print("Content contract failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print(f"Content contract passed for {len(MARKDOWN_FILES)} Markdown files.")
