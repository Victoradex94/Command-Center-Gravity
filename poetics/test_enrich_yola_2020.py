"""Exercise Yola 2020 enrichment script."""
from pathlib import Path
import json, shutil, subprocess, sys, tempfile, unittest

class TestEnrichYola2020(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='poetics-yola-test-')
        self.base = Path(self.temp.name)
        self.scripts = self.base / 'scripts'
        self.dist = self.base / 'dist'
        self.scripts.mkdir()
        self.dist.mkdir()

        self.script_src = Path(__file__).parent / 'scripts/enrich-yola-2020.py'
        self.script_dst = self.scripts / 'enrich-yola-2020.py'
        shutil.copy(self.script_src, self.script_dst)

        self.audit_json = self.dist / 'atlas-audit.json'
        self.audit_js = self.dist / 'atlas-audit.js'
        self.audit_json.write_text('{"profiles": [], "relationships": []}')

    def tearDown(self):
        try:
            self.temp.cleanup()
        except OSError:
            pass

    def run_script(self):
        subprocess.run([sys.executable, str(self.script_dst)], check=True)

    def test_adds_profiles_and_relationships(self):
        self.run_script()
        data = json.loads(self.audit_json.read_text())

        profiles = {p['id']: p for p in data.get('profiles', [])}
        self.assertEqual(len(profiles), 5)
        self.assertIn('adamawa-arts-festival-2020', profiles)
        self.assertEqual(profiles['adamawa-arts-festival-2020']['city'], 'Yola')
        self.assertTrue(profiles['adamawa-arts-festival-2020'].get('historical'))

        rels = data.get('relationships', [])
        self.assertEqual(len(rels), 4)

        js_content = self.audit_js.read_text()
        self.assertTrue(js_content.startswith('window.PoeticsAudit='))
        self.assertTrue(js_content.endswith(';\n'))

    def test_idempotent(self):
        self.run_script()
        self.run_script()

        data = json.loads(self.audit_json.read_text())
        self.assertEqual(len(data.get('profiles', [])), 5)
        self.assertEqual(len(data.get('relationships', [])), 4)

if __name__ == '__main__':
    unittest.main()
