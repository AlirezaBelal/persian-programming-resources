"""Offline checks for repository structure, local links, and obvious unsafe content."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = (
    "کتاب‌ها", "دوره‌ها", "دوره‌های آموزشی در یوتیوب",
    "کانال‌های یوتیوب", "منابع-تکمیلی",
)
REQUIRED = {"README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "LICENSE",
            ".github/ISSUE_TEMPLATE/resource.yml", ".github/workflows/content-integrity.yml",
            "tests/content_contract.py"} | {f"{name}/README.md" for name in CATEGORIES}
LINK = re.compile(r"\[[^\]\n]+\]\(((?:[^()\s]|\([^()\n]*\))+)\)")
SECRETS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
)
BLOCKED_HOSTS = {"t.me", "telegram.me", "mega.nz", "mediafire.com"}


def anchors(text):
    """GitHub-style IDs for the plain ATX headings used by this directory."""
    used = set()
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        heading = re.sub(r"<[^>]+>", "", heading).lower()
        base = "".join(c for c in heading if c.isalnum() or c in " _-\u200c").replace(" ", "-")
        slug, number = base, 0
        while slug in used:
            number += 1
            slug = f"{base}-{number}"
        used.add(slug)
    return used


def check(root):
    root = root.resolve()
    errors, texts = [], {}
    for required in sorted(REQUIRED):
        if not (root / required).is_file():
            errors.append(f"{required}: required file missing")
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in {".git", ".idea", "__pycache__"} for part in rel.parts) or not path.is_file():
            continue
        allowed = (path.suffix == ".md" or str(rel) in {"LICENSE", ".gitignore"}
                   or (rel.parts[0] == "tests" and path.suffix == ".py")
                   or (rel.parts[0] == ".github" and path.suffix in {".yml", ".yaml"}))
        if not allowed:
            errors.append(f"{rel}: unexpected file type; keep third-party material outside the repository")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            errors.append(f"{rel}: cannot read valid UTF-8 text")
            continue
        texts[path] = text
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in SECRETS):
                errors.append(f"{rel}:{number}: credential/private-key pattern found")
        if path.suffix != ".md":
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line and not (line.endswith("  ") and not line.endswith("   ")):
                errors.append(f"{rel}:{number}: unintended trailing whitespace")
            remainder = LINK.sub("", line)
            if re.search(r"\[[^\]\n]+\]\(", remainder):
                errors.append(f"{rel}:{number}: malformed Markdown link")
            for match in LINK.finditer(line):
                try:
                    url = urlsplit(match[1])
                    host = (url.hostname or "").lower()
                except ValueError:
                    errors.append(f"{rel}:{number}: malformed link URL")
                    continue
                if any(host == h or host.endswith("." + h) for h in BLOCKED_HOSTS):
                    errors.append(f"{rel}:{number}: unverified mirror/messaging host")
                if url.scheme in {"http", "https"}:
                    if not host or url.username is not None or url.password is not None:
                        errors.append(f"{rel}:{number}: invalid or credential-bearing external URL")
                    continue
                if url.scheme or url.netloc:
                    errors.append(f"{rel}:{number}: unsupported link scheme")
                    continue
                target = (path.parent / unquote(url.path)).resolve() if url.path else path
                if not target.is_relative_to(root) or not target.is_file():
                    errors.append(f"{rel}:{number}: local link target missing or outside repository")
                elif url.fragment and target.suffix == ".md":
                    try:
                        if unquote(url.fragment) not in anchors(target.read_text(encoding="utf-8")):
                            errors.append(f"{rel}:{number}: local heading anchor missing")
                    except (UnicodeError, OSError):
                        errors.append(f"{rel}:{number}: local link target unreadable")
    for name in ["README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"] + [f"{c}/README.md" for c in CATEGORIES]:
        text = texts.get(root / name)
        if text is not None and (not re.search(r"^#\s+.*[آ-ی]", text, re.MULTILINE)
                                 or '<div dir="rtl">' not in text
                                 or text.count("<div") != text.count("</div>")):
            errors.append(f"{name}: expected a Persian H1 and balanced RTL container")
    if "MIT License" not in texts.get(root / "LICENSE", ""):
        errors.append("LICENSE: expected MIT license text")
    return errors


if __name__ == "__main__":
    errors = check(ROOT)
    if errors:
        print("Content contract failed:\n" + "\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("Content contract passed (offline files, UTF-8, local links, anchors, and safety patterns).")
