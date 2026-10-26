"""Give every entrypoint asset a content-addressed URL, not a cache query."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
root=Path(__file__).resolve().parents[1]
dist=root/'dist';index=dist/'index.html';html=index.read_text(encoding='utf-8');mapping={}
# Compact executable delivery copies, retaining readable canonical sources.
# Formatting and local identifier shortening only; no compression transforms,
# property mangling, public API renaming or data mutation.
compact_names=['game-loader.js','entry-status.js','near-me-radar.js','directory.js','ecosystem-switcher.js','state-city-map.js','app.js','state-urban-map.js','nigeria-states-map.js','atlas-navigation.js','supabase-atlas.js']
compact_input={name:(dist/name).read_text(encoding='utf-8') for name in compact_names}
compact=json.loads(subprocess.check_output(['node',str(root/'scripts/minify-delivery.cjs')],input=json.dumps(compact_input),text=True,encoding='utf-8'))
# Rebuild the display-only derivative on every release; never edit the snapshot.
subprocess.run([sys.executable, str(root/'scripts/prepare-browser-data.py')], check=True)
# Build the pronunciation index from the pinned, credited source before it is fingerprinted.
subprocess.run([sys.executable, str(root/'scripts/build-rhyme-lexicon.py')], check=True)
# Also resolves a prior fingerprint so the helper can run after source edits.
def asset(match):
    attr,old=match.groups();name=old.split('?')[0]
    name=re.sub(r'\.[a-f0-9]{12}(?=\.(?:js|css)$)','',name)
    source=dist/name
    if not source.exists():raise RuntimeError('Missing asset '+name)
    payload=compact.get(name,source.read_text(encoding='utf-8')).encode('utf-8')
    if source.suffix=='.css':
        # Remove ordinary comments only; retain quoted text and /*! notices.
        payload=re.sub(r'''("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|/\*(?!\!)[\s\S]*?\*/''',lambda m:m[1] if m[1] is not None else ' ',payload.decode('utf-8')).encode('utf-8')
    # Compact pure JSON assignments for delivery; retain readable canonical sources.
    if source.suffix=='.js':
        data=re.fullmatch(r'(window\.\w+\s*=)\s*([\s\S]*?);?\s*',source.read_text(encoding='utf-8'))
        if data:
            try:
                value=json.loads(data[2].removesuffix(';'))
                payload=(data[1]+json.dumps(value,ensure_ascii=False,separators=(',',':'))+';\n').encode('utf-8')
            except json.JSONDecodeError:
                pass
    digest=hashlib.sha256(payload).hexdigest()
    stem=source.stem+'.'+digest[:12]+source.suffix
    (dist/stem).write_bytes(payload)
    mapping[name]=dict(file=stem,sha256=digest)
    return attr+'="'+stem+'"'
# Games are requested only when their route opens, but retain content-addressed
# delivery and the original dependency order.
game_names=['engine.js','opportunities.js','living-sim.js','rhyme-game.js','gamemap.js','city3d.js','world.js']
for name in game_names:
    asset(re.match(r'(src)="([^"]+)"','src="'+name+'"'))
lazy_assets={'near-me':asset(re.match(r'(src)="([^"]+)"','src="near-me-radar.js"')).split('\"')[1],'contribute':asset(re.match(r'(src)="([^"]+)"','src="contribute.js"')).split('\"')[1],'atlas-fallback':asset(re.match(r'(src)="([^"]+)"','src="atlas-fallback.js"')).split('\"')[1],'connection-mindmap':asset(re.match(r'(href)="([^"]+)"','href="connection-mindmap.css"')).split('\"')[1],'rhyme-lexicon':asset(re.match(r'(src)="([^"]+)"','src="rhyme-lexicon.js"')).split('\"')[1]}
(dist/'game-assets.js').write_text('window.PoeticsGameAssets='+json.dumps([mapping[n]['file'] for n in game_names],separators=(',',':'))+';window.PoeticsLazyAssets='+json.dumps(lazy_assets,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
# Bundle only immutable data. Executable modules retain their dependency order.
import runpy
data_names=runpy.run_path(str(root/'scripts/prepare-atlas-input.py'))['prepare'](dist)
def remove_data(match):
    name=re.sub(r'\.[a-f0-9]{12}(?=\.js$)','',match[1])
    return '' if name in data_names or name=='atlas-input.js' else match[0]
html=re.sub(r'<script src="([^"]+)"[^>]*></script>',remove_data,html)
html=html.replace('<script ', '<script src="atlas-input.js" defer></script><script ',1)
html=re.sub(r'(src|href)="([^"#]+\.(?:js|css)(?:\?[^"#]*)?)"',asset,html)
index.write_text(html,encoding='utf-8',newline='\n')
(root/'research/release-assets.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Fingerprinted',len(mapping),'entrypoint assets')
