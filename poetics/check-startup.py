import re, os

work = r'C:\Users\Victor Adetimilehin\Documents\Codex\2026-10-19\update-the-private-github-repository-victoradex94\work\poetics-staging-connector\poetics'
os.chdir(work)

with open('dist/index.html', 'r', encoding='utf-8') as f:
    current = f.read()
with open('dist/atlas-preview-75.html', 'r', encoding='utf-8') as f:
    baseline = f.read()

def get_assets(html):
    matches = re.findall(r'(?:src|href)="([^"#]+\.(?:js|css))"', html)
    total = 0
    for m in matches:
        p = os.path.join('dist', m)
        if not os.path.exists(p) and m == 'contribute.676d669df152.js':
            p = os.path.join('test-fixtures', m)
        sz = os.path.getsize(p)
        print(f'  {m}: {sz}')
        total += sz
    return total, len(matches)

print('--- BASELINE ---')
tot_a, len_a = get_assets(baseline)
print(f'Baseline total: {tot_a}, 80% threshold: {tot_a * 0.8}')

print('--- CURRENT ---')
tot_b, len_b = get_assets(current)
print(f'Current total: {tot_b}, Len B: {len_b}, Target diff: {tot_b - (tot_a * 0.8)}')
