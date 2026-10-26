"""Exercise entrypoint asset fingerprinting and minification."""
import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

class FingerprintAssets(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='poetics-fingerprint-test-')
        self.base = Path(self.temp.name)
        self.dist = self.base / 'dist'
        self.scripts = self.base / 'scripts'
        self.research = self.base / 'research'
        self.lexical = self.research / 'lexical'
        self.dist.mkdir()
        self.scripts.mkdir()
        self.research.mkdir()
        self.lexical.mkdir()

        # Copy the target script
        target_script_path = Path(__file__).parent / 'scripts/fingerprint-assets.py'
        target_script = target_script_path.read_text(encoding='utf-8')
        (self.scripts / 'fingerprint-assets.py').write_text(target_script, encoding='utf-8')
        shutil.copy2(target_script_path.with_name('minify-delivery.cjs'), self.scripts / 'minify-delivery.cjs')
        shutil.copy2(target_script_path.with_name('build-rhyme-lexicon.py'), self.scripts / 'build-rhyme-lexicon.py')
        shutil.copytree(target_script_path.parent / 'vendor', self.scripts / 'vendor')

        # Mock dependencies
        (self.scripts / 'prepare-browser-data.py').write_text("pass", encoding='utf-8')
        (self.scripts / 'prepare-atlas-input.py').write_text("def prepare(d): return ['atlas-data.js', 'other-data.js']\n", encoding='utf-8')
        (self.lexical / 'cmudict.dict').write_text('NIGHT N AY1 T\nLIGHT L AY1 T\n', encoding='utf-8')
        (self.lexical / 'local-pronunciations.json').write_text('{"schema":1,"entries":{}}\n', encoding='utf-8')

        # Setup base HTML and game assets required by the script
        self.html = '<script src="app.js"></script><script src="engine.js"></script><script src="opportunities.js"></script><script src="gamemap.js"></script><script src="city3d.js"></script><script src="world.js"></script>'
        (self.dist / 'index.html').write_text(self.html, encoding='utf-8')

        # Create dummy assets
        self.dummy_assets = ['app.js', 'engine.js', 'opportunities.js', 'living-sim.js', 'rhyme-game.js', 'gamemap.js', 'city3d.js', 'world.js', 'atlas-input.js', 'directory.js', 'ecosystem-switcher.js', 'state-city-map.js', 'state-urban-map.js', 'nigeria-states-map.js', 'atlas-navigation.js', 'supabase-atlas.js', 'game-loader.js', 'entry-status.js', 'near-me-radar.js', 'contribute.js', 'atlas-fallback.js', 'connection-mindmap.css', 'rhyme-lexicon.js']
        for asset in self.dummy_assets:
            (self.dist / asset).write_text(f'// {asset} content\n', encoding='utf-8')
        (self.dist / 'app.js').write_text('window.fixtureApp=1;\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def run_fingerprint(self):
        return subprocess.run([sys.executable, 'scripts/fingerprint-assets.py'], cwd=self.base, capture_output=True, text=True, check=True)

    def test_missing_asset_raises_error(self):
        (self.dist / 'missing.js').unlink(missing_ok=True)
        (self.dist / 'index.html').write_text('<script src="missing.js"></script>', encoding='utf-8')
        result = subprocess.run([sys.executable, 'scripts/fingerprint-assets.py'], cwd=self.base, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing asset missing.js', result.stderr)

    def test_fingerprints_html_and_writes_manifest(self):
        self.run_fingerprint()
        html = (self.dist / 'index.html').read_text(encoding='utf-8')

        self.assertNotIn('src="app.js"', html)
        self.assertRegex(html, r'src="app\.[a-f0-9]{12}\.js"')

        manifest = json.loads((self.research / 'release-assets.json').read_text(encoding='utf-8'))
        self.assertIn('app.js', manifest)
        self.assertIn('file', manifest['app.js'])
        self.assertIn('sha256', manifest['app.js'])

        fingerprinted_file = self.dist / manifest['app.js']['file']
        self.assertTrue(fingerprinted_file.exists())
        self.assertEqual(fingerprinted_file.read_text(encoding='utf-8'), 'window.fixtureApp=1;\n')

    def test_compacts_json_assignment(self):
        (self.dist / 'data.js').write_text('window.my_data = {\n  "key": "value",\n  "arr": [\n    1,\n    2\n  ]\n}; \n', encoding='utf-8')
        (self.dist / 'index.html').write_text(self.html + '<script src="data.js"></script>', encoding='utf-8')

        self.run_fingerprint()

        manifest = json.loads((self.research / 'release-assets.json').read_text(encoding='utf-8'))
        fingerprinted_file = self.dist / manifest['data.js']['file']
        compacted = fingerprinted_file.read_text(encoding='utf-8')

        self.assertEqual(compacted, 'window.my_data ={"key":"value","arr":[1,2]};\n')

    def test_removes_data_scripts_from_html(self):
        (self.dist / 'atlas-data.js').write_text('window.atlas = {};', encoding='utf-8')
        (self.dist / 'other-data.js').write_text('window.other = {};', encoding='utf-8')
        (self.dist / 'index.html').write_text('<script src="atlas-data.js"></script><script src="other-data.js"></script><script src="app.js"></script>', encoding='utf-8')

        self.run_fingerprint()

        html = (self.dist / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('atlas-data', html)
        self.assertNotIn('other-data', html)
        self.assertRegex(html, r'src="app\.[a-f0-9]{12}\.js"')
        self.assertRegex(html, r'src="atlas-input\.[a-f0-9]{12}\.js" defer></script>')

    def test_generates_game_assets_file(self):
        self.run_fingerprint()
        game_assets_path = self.dist / 'game-assets.js'
        self.assertTrue(game_assets_path.exists())
        content = game_assets_path.read_text(encoding='utf-8')

        self.assertTrue(content.startswith('window.PoeticsGameAssets=['))
        self.assertTrue(content.endswith(';\n'))

        manifest = json.loads((self.research / 'release-assets.json').read_text(encoding='utf-8'))
        expected_names = [manifest[n]['file'] for n in ['engine.js','opportunities.js','living-sim.js','rhyme-game.js','gamemap.js','city3d.js','world.js']]
        game_part, lazy_part = content.rstrip().rstrip(';').split(';window.PoeticsLazyAssets=')
        parsed_array = json.loads(game_part.removeprefix('window.PoeticsGameAssets='))
        lazy_assets = json.loads(lazy_part)
        self.assertEqual(lazy_assets, {key: manifest[name]['file'] for key, name in [('contribute', 'contribute.js'), ('near-me', 'near-me-radar.js'), ('atlas-fallback', 'atlas-fallback.js'), ('connection-mindmap', 'connection-mindmap.css'), ('rhyme-lexicon', 'rhyme-lexicon.js')]})
        self.assertEqual(parsed_array, expected_names)

    def test_builds_pronunciation_asset_with_reviewed_local_entries(self):
        (self.lexical / 'local-pronunciations.json').write_text(
            '{"schema":1,"entries":{"poise":{"source":"Reviewed local pronunciation note","pronunciations":["P OY1 Z"]}}}\n',
            encoding='utf-8',
        )
        self.run_fingerprint()
        manifest = json.loads((self.research / 'release-assets.json').read_text(encoding='utf-8'))
        payload = (self.dist / manifest['rhyme-lexicon.js']['file']).read_text(encoding='utf-8')
        encoded = payload.split('root.PoeticsRhymeLexicon=', 1)[1].split(';})(typeof window', 1)[0]
        lexicon = json.loads(encoded)
        self.assertEqual(lexicon['wordRimes']['night'], ['AY T'])
        self.assertEqual(lexicon['wordRimes']['light'], ['AY T'])
        self.assertEqual(lexicon['wordRimes']['poise'], ['OY Z'])

    def test_strips_existing_fingerprints_during_resolution(self):
        self.run_fingerprint()
        html1 = (self.dist / 'index.html').read_text(encoding='utf-8')

        (self.dist / 'app.js').write_text('window.fixtureApp=2;\n', encoding='utf-8')

        self.run_fingerprint()

        html2 = (self.dist / 'index.html').read_text(encoding='utf-8')
        self.assertNotEqual(html1, html2)

        manifest = json.loads((self.research / 'release-assets.json').read_text(encoding='utf-8'))
        fingerprinted_file = self.dist / manifest['app.js']['file']
        self.assertEqual(fingerprinted_file.read_text(encoding='utf-8'), 'window.fixtureApp=2;\n')

        app_matches = [m for m in html2.split('<script') if 'app.' in m]
        self.assertEqual(len(app_matches), 1)

if __name__ == '__main__':
    unittest.main()
