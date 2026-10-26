"""Exercise copying and failure safeguards against disposable staging folders."""
from pathlib import Path
import subprocess, sys, tempfile, unittest
from importlib.util import module_from_spec, spec_from_file_location
sys.dont_write_bytecode = True
spec = spec_from_file_location('sync', Path(__file__).parent / 'scripts/sync-localwp.py')
sync = module_from_spec(spec)
spec.loader.exec_module(sync)

class SyncSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='poetics-sync-test-')
        self.base = Path(self.temp.name)
        self.app = self.base / 'app'
        self.dist = self.app / 'dist'
        self.stage = self.base / 'poetics'
        self.dist.mkdir(parents=True)
        self.stage.mkdir()
        (self.dist / 'index.html').write_text('<script src="app.js"></script>')
        (self.dist / 'app.js').write_text('window.version=103;')
        (self.stage / 'index.html').write_text('previous entrypoint')
        (self.stage / '.env.local').write_text('TEST_ONLY_SECRET=do-not-touch')
    def tearDown(self):
        self.temp.cleanup()
    def publish(self):
        return sync.publish(self.app, self.stage, self.base / 'backups')
    def test_publish_preserves_environment_and_recovers_previous_files(self):
        result = self.publish()
        self.assertEqual(result['filesChanged'], 2)
        self.assertEqual((self.stage / '.env.local').read_text(), 'TEST_ONLY_SECRET=do-not-touch')
        self.assertEqual((Path(result['backup']) / 'index.html').read_text(), 'previous entrypoint')
        self.assertEqual(self.publish()['filesChanged'], 0)
    def test_nested_secret_file_stops_before_any_write(self):
        p = self.dist / 'media'; p.mkdir()
        (p / '.env.local').write_text('TEST_ONLY_SECRET=private')
        with self.assertRaises(ValueError): self.publish()
        self.assertEqual((self.stage / 'index.html').read_text(), 'previous entrypoint')
        self.assertFalse((self.stage / 'app.js').exists())
    def test_secret_content_in_allowed_file_stops_before_writes(self):
        (self.dist / 'app.js').write_text('sb_secret_test_fixture_only')
        with self.assertRaises(ValueError): self.publish()
        self.assertEqual((self.stage / 'index.html').read_text(), 'previous entrypoint')
    def test_missing_delivery_asset_leaves_entrypoint_unchanged(self):
        (self.dist / 'app.js').unlink()
        with self.assertRaises(ValueError): self.publish()
        self.assertEqual((self.stage / 'index.html').read_text(), 'previous entrypoint')
    def test_escape_and_unrelated_file_names_rejected(self):
        for name in ('../wp-config.php','/app.js','media/../../secret.json','media/backup.sql','media/key.pem','supabase/migrations.sql','media/.git/config','C:\\app.js'):
            self.assertFalse(sync.allowed(name), name)
    def test_destination_symlink_cannot_write_outside_staging(self):
        outside = self.base / 'outside.js'; outside.write_text('preserve')
        try: (self.stage / 'app.js').symlink_to(outside)
        except OSError: self.skipTest('Symlinks unavailable on this Windows account')
        with self.assertRaises(ValueError): self.publish()
        self.assertEqual(outside.read_text(), 'preserve')
    def test_native_check_failure_is_propagated(self):
        with self.assertRaises(subprocess.CalledProcessError):
            sync.command([sys.executable, '-c', 'raise SystemExit(17)'], self.base)
    def test_drift_gate_detects_modified_and_untracked_outputs(self):
        subprocess.run(['git','init','-q'], cwd=self.base, check=True)
        subprocess.run(['git','add','app'], cwd=self.base, check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'], cwd=self.base, check=True)
        (self.dist / 'app.js').write_text('changed output')
        self.assertNotEqual(subprocess.run(['git','diff','--exit-code'],cwd=self.base,stdout=subprocess.DEVNULL).returncode,0)
        (self.dist / 'new.123456789abc.js').write_text('generated')
        self.assertIn('new.123456789abc.js',sync.command(['git','ls-files','--others','--exclude-standard'], self.base, True))
    def test_review_sync_requires_exact_non_main_branch_and_scoped_changes(self):
        subprocess.run(['git','init','-q'], cwd=self.base, check=True)
        tracked = self.base / 'poetics/dist/gamemap.js'; tracked.parent.mkdir(parents=True)
        tracked.write_text('baseline')
        subprocess.run(['git','add','app','poetics'], cwd=self.base, check=True)
        subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'], cwd=self.base, check=True)
        subprocess.run(['git','branch','-m','codex/review'], cwd=self.base, check=True)
        tracked.write_text('reviewed map change')
        self.assertEqual(sync.validate_review_branch(self.base,'codex/review'),'codex/review')
        with self.assertRaises(ValueError): sync.validate_review_branch(self.base,'codex/other')
        stray = self.base / 'README.md'; stray.write_text('out of scope')
        with self.assertRaises(ValueError): sync.validate_review_branch(self.base,'codex/review')
        stray.unlink()
        subprocess.run(['git','branch','-m','main'], cwd=self.base, check=True)
        with self.assertRaises(ValueError): sync.validate_review_branch(self.base,'main')

if __name__ == '__main__': unittest.main()
