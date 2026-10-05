"""AJ16 actual Git only in disposable local bare fixture; no hosted transport."""
from pathlib import Path
import subprocess
import tempfile
from dispatcher.git_ledger import GitLedger, digest
from dispatcher.isolation import LocalAuthorityProvider, IsolationCoordinator, import_snapshot
from tests.git_bare_fixture import LocalBareGitTransport
from tests.test_isolation import fixture_manifest


def main():
    with tempfile.TemporaryDirectory(prefix='aj0016-local-bare-') as directory:
        root = Path(directory); bare = root / 'synthetic.git'
        subprocess.run(['git', 'init', '--bare', str(bare)], check=True, capture_output=True)
        class LostResponse(LocalBareGitTransport):
            def __init__(self, path):
                super().__init__(path); self.calls = 0
            def publish(self, expected, intended):
                self.calls += 1
                assert super().publish(expected, intended) == 'SUCCESS'
                raise RuntimeError('synthetic lost response')
        t = LostResponse(bare); l = GitLedger(root/'ledger.json', t); token=l.acquire('synthetic')
        m=fixture_manifest(); accepted=digest(m)
        c=IsolationCoordinator(LocalAuthorityProvider(root/'authority.json'), l, m, accepted)
        c.initialize(); c.transition('LEGACY','HELD'); c.transition('HELD','PREPARING')
        h=import_snapshot(l,token,m,accepted)
        assert len(h)==40 and t.calls==7
        assert import_snapshot(GitLedger(root/'ledger.json',t),token,m,accepted)==h and t.calls==7
        assert len(l._remote()[2]['events'])==7
        c.activate(h)
        restarted=IsolationCoordinator(LocalAuthorityProvider(root/'authority.json'),l,m,accepted)
        assert restarted.dispatch('AJ-8001',surface='new',epoch=1,head=h)['synthetic']
        restarted.rollback_hold()
        assert restarted.provider.read()['selected'] is None
        print('PASS: AJ16 local bare Git; seven exact import commits; seven lost-response publications; restart zero replay; activation/restart selection; rollback HOLD; no network')


if __name__ == '__main__': main()
