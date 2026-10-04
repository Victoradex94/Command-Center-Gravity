"""Local-only Git object/ref integration fixture. Run outside executable-blocked suite."""
from pathlib import Path
import subprocess
import os

class LocalBareGitTransport:
    """Synthetic local bare remote only; Git SHA and CAS, no shell/network.

    Files are materialized as Git objects in the fixture bare repository before
    update-ref. Objects are local preparation; only refs constitute publication.
    This is deliberately not a live-host push adapter.
    """
    def __init__(self, repository, ref='refs/heads/ledger-fixture'):
        self.repository = Path(repository).resolve()
        if not self.repository.is_dir() or not (self.repository / 'HEAD').is_file():
            raise ValueError('existing local bare Git fixture required')
        self.ref = ref
        self._git('check-ref-format', ref)
        if self._git('rev-parse', '--is-bare-repository').strip() != b'true':
            raise ValueError('bare fixture required')

    def _git(self, *args, data=None):
        env = dict(os.environ, GIT_AUTHOR_NAME='Synthetic fixture',
                   GIT_AUTHOR_EMAIL='fixture@example.invalid',
                   GIT_COMMITTER_NAME='Synthetic fixture',
                   GIT_COMMITTER_EMAIL='fixture@example.invalid',
                   GIT_AUTHOR_DATE='2000-01-01T00:00:00+00:00',
                   GIT_COMMITTER_DATE='2000-01-01T00:00:00+00:00')
        return subprocess.run(['git', '--git-dir=' + str(self.repository), *args],
                              input=data, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=True, env=env).stdout

    def head(self):
        try:
            return self._git('rev-parse', '--verify', self.ref).decode().strip()
        except subprocess.CalledProcessError:
            return None

    def parent(self, sha):
        values = self._git('rev-list', '--parents', '-n', '1', sha).decode().split()
        if len(values) > 2:
            raise ValueError('merge commit forbidden')
        return values[1] if len(values) == 2 else None

    def read(self, sha):
        names = self._git('ls-tree', '-r', '--name-only', '-z', sha).split(b'\0')
        return {n.decode(): self._git('show', sha + ':' + n.decode()) for n in names if n}

    def construct(self, parent, files):
        tree = {}
        for path, content in sorted(files.items()):
            node = tree
            parts = path.split('/')
            if any(p in ('', '.', '..') for p in parts):
                raise ValueError('unsafe path')
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = self._git('hash-object', '-w', '--stdin', data=content).decode().strip()
        def build(node):
            entries = []
            for name, value in sorted(node.items()):
                mode, kind, oid = ('040000', 'tree', build(value)) if isinstance(value, dict) else ('100644', 'blob', value)
                entries.append(f'{mode} {kind} {oid}\t{name}\0'.encode())
            return self._git('mktree', '-z', data=b''.join(entries)).decode().strip()
        args = ['commit-tree', build(tree)]
        if parent:
            args += ['-p', parent]
        return self._git(*args, data=b'AJ-0015 synthetic ledger transaction\n').decode().strip()

    def publish(self, expected, sha):
        try:
            self._git('update-ref', self.ref, sha, expected or '0' * 40)
            return 'SUCCESS'
        except subprocess.CalledProcessError:
            return 'CONFLICT'
