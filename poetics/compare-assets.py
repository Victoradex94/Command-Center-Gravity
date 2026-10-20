import re, os

work = r'C:\Users\Victor Adetimilehin\Documents\Codex\2026-10-19\update-the-private-github-repository-victoradex94\work\poetics-staging-connector\poetics'
os.chdir(work)

with open('dist/atlas-preview-75.html', 'r', encoding='utf-8') as f:
    preview = f.read()
with open('dist/index.html', 'r', encoding='utf-8') as f:
    idx = f.read()

prev_assets = re.findall(r'(?:src|href)="([^"#]+\.(?:js|css))"', preview)
idx_assets = re.findall(r'(?:src|href)="([^"#]+\.(?:js|css))"', idx)

print(f'Preview assets: {len(prev_assets)}')
for a in prev_assets:
    base = re.sub(r'\.[a-f0-9]{12}\.', '.', a)
    print(f'  prev: {a} -> {base}')

print(f'\nIndex assets: {len(idx_assets)}')
for a in idx_assets:
    base = re.sub(r'\.[a-f0-9]{12}\.', '.', a)
    print(f'  idx: {a} -> {base}')
