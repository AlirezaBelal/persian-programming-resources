"""Small fixtures for editorial freedom and real content-contract failures."""

from pathlib import Path
import tempfile
import unittest

from content_contract import REQUIRED, check


class ContentContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in REQUIRED:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('<div dir="rtl">\n\n# عنوان دلخواه فارسی\n\n</div>\n'
                            if path.suffix == '.md' else 'MIT License\n', encoding='utf-8')

    def write_readme(self, text):
        (self.root / 'README.md').write_text(
            '<div dir="rtl">\n\n# متن آموزشی تازه\n\n' + text + '\n</div>\n', encoding='utf-8')

    def test_ordinary_edits_encoded_paths_and_duplicate_anchors_are_valid(self):
        self.write_readme('[متن](کتاب‌ها/README.md#عنوان-دلخواه-فارسی)\n'
                          '## تست‌نویسی\n## تست‌نویسی\n[بخش دوم](#تستنویسی-1)\n'
                          '[دوره](https://example.org/course/(python))\n'
                          'تغییر عبارت‌ها و توضیح سیاست درباره t.me/ مجاز است.  \n')
        self.assertEqual(check(self.root), [])
        self.write_readme('[دوره](دوره‌های%20آموزشی%20در%20یوتیوب/README.md)')
        self.assertEqual(check(self.root), [])

    def test_missing_files_and_invalid_utf8_are_reported_without_crashing(self):
        (self.root / 'README.md').unlink()
        (self.root / 'SECURITY.md').write_bytes(b'\xff')
        errors = check(self.root)
        self.assertTrue(any('README.md: required file missing' in e for e in errors))
        self.assertTrue(any('SECURITY.md: cannot read valid UTF-8' in e for e in errors))

    def test_missing_target_anchor_and_outside_path_are_rejected(self):
        for destination in ('missing.md', 'کتاب‌ها/README.md#ناموجود', '../outside.md'):
            with self.subTest(destination=destination):
                self.write_readme(f'[متن]({destination})')
                self.assertTrue(any('README.md:' in error for error in check(self.root)))

    def test_unsafe_urls_and_secret_patterns_do_not_echo_values(self):
        for destination in ('https://t.me/unverified', 'javascript:alert(1)',
                            'https://user:synthetic-password@example.org/'):
            with self.subTest(destination=destination):
                self.write_readme(f'[منبع]({destination})')
                errors = check(self.root)
                self.assertTrue(errors)
                self.assertNotIn(destination, '\n'.join(errors))
        synthetic = 'ghp_' + 'x' * 30
        self.write_readme(synthetic)
        self.assertTrue(any('credential' in e for e in check(self.root)))
        self.assertNotIn(synthetic, '\n'.join(check(self.root)))

    def test_unexpected_download_and_malformed_link_are_rejected(self):
        (self.root / 'book.pdf').write_bytes(b'synthetic fixture')
        self.write_readme('[متن](https://example.org/unfinished')
        errors = check(self.root)
        self.assertTrue(any('book.pdf: unexpected file type' in e for e in errors))
        self.assertTrue(any('malformed Markdown link' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
