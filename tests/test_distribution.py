"""Standalone packaging and immutable original-logo checks."""
import hashlib
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_NAME="openapi-compat-audit"
LOGO_SHA={'area-zero-logo-full.svg': '89b459e6a4e61748d2d56d54da2cd17ff2b55deafbbc90e45e43d4c319462d16', 'area-zero-logo-icon.svg': 'f566816db1f90656499b5e8377b04cc96584c45b2a62c8113895f3f24eeb0c68'}

class DistributionTests(unittest.TestCase):
    def test_skill_frontmatter_and_name(self):
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\n'))
        self.assertIn('name: '+EXPECTED_NAME, text)
        self.assertIn('description:', text)
    def test_links_and_documentation(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        for url in re.findall(r'\]\(([^)]+)\)',text) + re.findall(r'(?:src|href)="([^"]+)"',text):
            if url.startswith(('http://','https://','#','mailto:')): continue
            dest=ROOT / url.partition('#')[0]
            self.assertTrue(dest.exists(), f'Broken link: {url}')
        for name in ('CONTRIBUTING.md','SECURITY.md','BRAND.md','CHANGELOG.md','LICENSE'):
            self.assertTrue((ROOT/name).is_file())
    def test_official_logo_not_modified(self):
        for name,expected in LOGO_SHA.items():
            self.assertEqual(hashlib.sha256((ROOT/'assets'/name).read_bytes()).hexdigest(), expected)
    def test_visual_assets_well_formed(self):
        for name in ('hero.svg',*LOGO_SHA.keys()):
            ET.parse(ROOT/'assets'/name)
    def test_required_fixtures(self):
        for path in (('openapi-before.json', 'openapi-after.json', 'openapi-demo-report.md')):
            self.assertTrue((ROOT/'examples'/path).is_file())
