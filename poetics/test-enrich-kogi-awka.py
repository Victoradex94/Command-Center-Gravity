import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

class TestEnrichKogiAwka(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.scripts = self.root / 'scripts'
        self.research = self.root / 'research'
        self.dist = self.root / 'dist'

        self.scripts.mkdir()
        self.research.mkdir()
        self.dist.mkdir()

        # Setup initial state for the script
        self.p_audit = self.dist / 'atlas-audit.json'
        self.p_audit.write_text(json.dumps({
            "profiles": [
                {"id": "ccpc-awka-2023", "gaps": "old", "verification": {"reviewedAt": "old"}, "links": []},
                {"id": "uche-nnyagu", "gaps": "old", "verification": {"reviewedAt": "old"}, "links": []},
                {"id": "awka-window", "gaps": "old", "verification": {"reviewedAt": "old"}, "links": []},
                {"id": "ansa", "gaps": "old", "verification": {"reviewedAt": "old"}, "links": []},
                {"id": "maymunah-kadiri", "gaps": "old", "verification": {"reviewedAt": "old"}, "links": []}
            ],
            "relationships": []
        }))

        self.p_sources = self.research / 'south-south-sources.json'
        self.p_sources.write_text(json.dumps([
            {"url": "https://profile.unizik.edu.ng/nau4594", "other": "data"},
            {"url": "https://other.com", "nested": {"url": "https://profile.unizik.edu.ng/nau4594"}}
        ]))

        # Copy script
        original_script = Path(__file__).parent / 'scripts' / 'enrich-kogi-awka.py'
        self.script_path = self.scripts / 'enrich-kogi-awka.py'
        shutil.copy(original_script, self.script_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_enrichment_script(self):
        # Run the script
        import sys
        result = subprocess.run([sys.executable, str(self.script_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Script failed with output: {result.stderr}")

        # Verify changes in atlas-audit.json
        audit_data = json.loads(self.p_audit.read_text())
        profiles = {p['id']: p for p in audit_data['profiles']}

        # Check updates to existing profiles
        self.assertEqual(profiles['ccpc-awka-2023']['gaps'], 'Official profile opened directly 13 October 2026. Exact event day and additional participants remain unverified.')
        self.assertEqual(profiles['ccpc-awka-2023']['verification']['reviewedAt'], '2026-10-13')

        # New profile added
        self.assertIn('vincent-eze-awka', profiles)
        self.assertEqual(profiles['vincent-eze-awka']['name'], 'Vincent Eze (Awka itinerary)')
        self.assertEqual(profiles['vincent-eze-awka']['city'], 'Awka')

        # New relationship added
        rels = audit_data['relationships']
        self.assertTrue(any(r['a'] == 'vincent-eze-awka' and r['b'] == 'ccpc-awka-2023' for r in rels))

        # Verify sources corrected (replace & correct functions)
        sources_data = json.loads(self.p_sources.read_text())
        self.assertEqual(sources_data[0]['url'], 'https://profile.unizik.edu.ng/NAU4594')
        self.assertEqual(sources_data[1]['nested']['url'], 'https://profile.unizik.edu.ng/NAU4594')

        # Verify claims written
        claims_file = self.research / 'kogi-awka-claims.json'
        self.assertTrue(claims_file.exists())
        claims_data = json.loads(claims_file.read_text())
        self.assertEqual(claims_data['reviewedAt'], '2026-10-13')
        self.assertTrue(len(claims_data['claims']) > 0)

        # Verify JS export written
        audit_js = self.dist / 'atlas-audit.js'
        self.assertTrue(audit_js.exists())
        self.assertTrue(audit_js.read_text().startswith('window.PoeticsAudit='))

if __name__ == '__main__':
    unittest.main()
