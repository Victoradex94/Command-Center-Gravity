"""Rebuild/test main in isolation; publish only validated app files, entrypoint last."""
from pathlib import Path, PurePosixPath
import argparse, contextlib, datetime, json, os, re, shutil, subprocess, sys, tempfile

EXTENSIONS = {'.js', '.css', '.html', '.json', '.geojson', '.png', '.jpg', '.jpeg', '.svg', '.webp', '.woff', '.woff2'}
TEXT = {'.js', '.css', '.html', '.json', '.geojson', '.svg'}
SECRET = re.compile(rb'sb_secret_[A-Za-z0-9_-]+|(?:ghp_|github_pat_)[A-Za-z0-9_]+|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')
CHECKS = ['atlas-navigation', 'state-urban-integration', 'directory', 'map-first', 'security', 'near-me', 'near-me-integration', 'delivery', 'engine', 'rhyme', 'contribute', 'nigeria-gis', 'category-performance', 'fast-startup', 'game-lazy-route', 'game-travel', 'sim-polish', 'rhyme-polish', 'supabase-snapshot', 'osm-state-city-map', 'state-urban-rollout']

def command(args, cwd, capture=False):
    result = subprocess.run([str(a) for a in args], cwd=cwd, check=True, text=True, encoding='utf-8', stdout=subprocess.PIPE if capture else sys.stdout, stderr=sys.stderr)
    return result.stdout.rstrip() if capture else ''

def allowed(name):
    p = PurePosixPath(name)
    return (not p.is_absolute() and '\\' not in name and ':' not in name and name == p.as_posix()
            and all(part not in ('', '.', '..') and not part.startswith('.') for part in p.parts)
            and p.suffix.lower() in EXTENSIONS
            and (len(p.parts) == 1 or p.parts[0] in ('media', 'geography')))

def contained(root, name):
    p = root / name
    for item in (p, *p.parents):
        if item == root.parent: break
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise ValueError('Links/junctions are forbidden: ' + name)
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes app folder: ' + name)
    return p

def checked_file(root, name):
    if not allowed(name): raise ValueError('Disallowed app path: ' + name)
    p = contained(root, name)
    if not p.is_file(): raise ValueError('Missing app file: ' + name)
    if p.suffix.lower() in TEXT and SECRET.search(p.read_bytes()):
        raise ValueError('Potential secret in app file: ' + name)
    return p

def assets(dist):
    names = []
    for p in sorted(dist.rglob('*')):
        if p.is_file() or p.is_symlink():
            name = p.relative_to(dist).as_posix()
            checked_file(dist, name)
            names.append(name)
    for ref in re.findall(r'(?:src|href)="([^"#]+\.(?:js|css|html))"', (dist / 'index.html').read_text(encoding='utf-8')):
        if not re.match(r'https?://', ref): checked_file(dist, ref)
    for css in dist.glob('*.css'):
        for ref in re.findall(r'url\([\s\'"]*([^\s\)\'"#]+)', css.read_text(encoding='utf-8')):
            if ref.startswith('media/'): checked_file(dist, ref)
    return names

def verify(app, node):
    command([sys.executable, '-X', 'utf8', 'scripts/fingerprint-assets.py'], app)
    for name in CHECKS: command([node, 'test-' + name + '.cjs'], app)
    assets(app / 'dist')

@contextlib.contextmanager
def checkout(repo, ref):
    with tempfile.TemporaryDirectory(prefix='poetics-sync-') as scratch:
        target = Path(scratch) / 'checkout'
        command(['git', 'worktree', 'add', '--detach', str(target), ref], repo)
        try: yield target
        finally: command(['git', 'worktree', 'remove', '--force', str(target)], repo)

def publish(app, destination, backup_root):
    names = assets(app / 'dist')  # Validate everything before writing anything.
    destination = destination.absolute()
    if not destination.is_dir() or destination.name.lower() != 'poetics':
        raise ValueError('Destination must be an existing poetics directory.')
    if destination.resolve() == (app / 'dist').resolve(): raise ValueError('Source equals destination.')
    for name in names: contained(destination, name)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = backup_root / stamp
    changed = [n for n in names if not (destination / n).is_file() or (destination / n).read_bytes() != (app / 'dist' / n).read_bytes()]
    for name in changed:
        current = destination / name
        if current.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current, saved)
    for name in sorted(changed, key=lambda n: n == 'index.html'):
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix='poetics-sync-', dir=p.parent)
        try:
            with os.fdopen(handle, 'wb') as stream: stream.write((app / 'dist' / name).read_bytes())
            os.replace(temporary, p)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    for name in names:
        if (destination / name).read_bytes() != (app / 'dist' / name).read_bytes(): raise ValueError('Readback differs: ' + name)
    return {'filesVerified': len(names), 'filesChanged': len(changed), 'backup': str(backup) if backup.exists() else None}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for flag in ('--from-github', '--to-github', '--verify-only'): modes.add_argument(flag, action='store_true')
    parser.add_argument('--repo-path', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--localwp-path', type=Path)
    parser.add_argument('--import-files', nargs='+')
    parser.add_argument('--node', default='node')
    parser.add_argument('--log-file', type=Path)
    args = parser.parse_args()
    if args.log_file:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        stream = args.log_file.open('w', encoding='utf-8', buffering=1)
        sys.stdout = sys.stderr = stream
    if not shutil.which('git') and os.name == 'nt':
        git_dir = Path(os.environ['USERPROFILE']) / '.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd'
        os.environ['PATH'] = str(git_dir) + os.pathsep + os.environ.get('PATH', '')
    app = args.repo_path.resolve()
    repo = Path(command(['git', 'rev-parse', '--show-toplevel'], app, True))
    if args.verify_only:
        verify(app, args.node)
        return
    if args.localwp_path is None: raise ValueError('An explicit LocalWP destination is required.')
    if args.from_github:
        remote = command(['git', 'remote', 'get-url', 'origin'], repo, True)
        if remote.removesuffix('.git') not in ('https://github.com/Victoradex94/Command-Center-Gravity', 'git@github.com:Victoradex94/Command-Center-Gravity'):
            raise ValueError('Origin is not the approved repository.')
        command(['git', 'fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main'], repo)
        commit = command(['git', 'rev-parse', 'origin/main'], repo, True)
        with checkout(repo, commit) as clean:
            built = clean / 'poetics'
            verify(built, args.node)
            command(['git', 'diff', '--exit-code'], clean)
            if command(['git', 'ls-files', '--others', '--exclude-standard'], clean, True):
                raise ValueError('Build drift: main produced untracked delivery files.')
            result = publish(built, args.localwp_path, repo.parent / 'poetics-sync-backups')
        record = {'commit': commit, 'completedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), **result}
        (repo.parent / 'poetics-sync-status.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
        print(json.dumps(record))
    else:
        branch = command(['git', 'branch', '--show-current'], repo, True)
        if not branch or branch == 'main': raise ValueError('Import into a named review branch, never main.')
        if command(['git', 'status', '--porcelain', '--untracked-files=all'], repo, True): raise ValueError('Import requires a clean review branch.')
        if not args.import_files: raise ValueError('Name readable sources with --import-files; blanket imports are disabled.')
        for name in args.import_files:
            if re.search(r'\.[a-f0-9]{12}\.(js|css)$', name) or name in ('atlas-input.js', 'canonical-research-runtime.js', 'game-assets.js'):
                raise ValueError('Import readable source, not generated assets: ' + name)
            checked_file(args.localwp_path, name)
        with checkout(repo, 'HEAD') as clean:
            for name in args.import_files:
                target = clean / 'poetics/dist' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(args.localwp_path / name, target)
            verify(clean / 'poetics', args.node)
            changed = command(['git', 'status', '--porcelain', '--untracked-files=all'], clean, True)
            if command(['git', 'status', '--porcelain', '--untracked-files=all'], repo, True): raise ValueError('Review branch changed during import.')
            for line in changed.splitlines():
                name = line[3:].strip('"')
                if not (name.startswith('poetics/dist/') or name == 'poetics/research/release-assets.json') or line[:2] not in (' M', '??'):
                    raise ValueError('Unexpected import change: ' + name)
            for line in changed.splitlines():
                name = line[3:].strip('"')
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(clean / name, target)
        print('Named source import checked. Review the diff; nothing committed or pushed.')

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('SYNC FAILED: ' + str(error), file=sys.stderr)
        sys.exit(1)
