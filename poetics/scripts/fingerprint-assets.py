"""Give every entrypoint asset a content-addressed URL, not a cache query."""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[1]
dist=root/'dist';index=dist/'index.html';html=index.read_text();mapping={}
# Rebuild the display-only derivative on every release; never edit the snapshot.
exec((root/'scripts/prepare-browser-data.py').read_text(),{'__file__':str(root/'scripts/prepare-browser-data.py')})
# Also resolves a prior fingerprint so the helper can run after source edits.
def asset(match):
    attr,old=match.groups();name=old.split('?')[0]
    name=re.sub(r'\.[a-f0-9]{12}(?=\.(?:js|css)$)','',name)
    source=dist/name
    if not source.exists():raise RuntimeError('Missing asset '+name)
    payload=source.read_bytes()
    # Compact pure JSON assignments for delivery; retain readable canonical sources.
    if source.suffix=='.js':
        data=re.fullmatch(r'(window\.\w+\s*=)\s*([\s\S]*?);?\s*',source.read_text())
        if data:
            try:
                value=json.loads(data[2].removesuffix(';'))
                payload=(data[1]+json.dumps(value,ensure_ascii=False,separators=(',',':'))+';\n').encode()
            except json.JSONDecodeError:
                pass
    digest=hashlib.sha256(payload).hexdigest()
    stem=source.stem+'.'+digest[:12]+source.suffix
    (dist/stem).write_bytes(payload)
    mapping[name]=dict(file=stem,sha256=digest)
    return attr+'="'+stem+'"'
# Games are requested only when their route opens, but retain content-addressed
# delivery and the original dependency order.
game_names=['engine.js','opportunities.js','gamemap.js','city3d.js','world.js']
for name in game_names:
    asset(re.match(r'(src)="([^"]+)"','src="'+name+'"'))
(dist/'game-assets.js').write_text('window.PoeticsGameAssets='+json.dumps([mapping[n]['file'] for n in game_names],separators=(',',':'))+';\n')
html=re.sub(r'(src|href)="([^"#]+\.(?:js|css)(?:\?[^"#]*)?)"',asset,html)
index.write_text(html)
(root/'research/release-assets.json').write_text(json.dumps(mapping,indent=2)+'\n')
print('Fingerprinted',len(mapping),'entrypoint assets')
