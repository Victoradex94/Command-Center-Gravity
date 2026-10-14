"""Give every entrypoint asset a content-addressed URL, not a cache query."""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[1]
dist=root/'dist';index=dist/'index.html';html=index.read_text();mapping={}
# Also resolves a prior fingerprint so the helper can run after source edits.
def asset(match):
    attr,old=match.groups();name=old.split('?')[0]
    name=re.sub(r'\.[a-f0-9]{12}(?=\.(?:js|css)$)','',name)
    source=dist/name
    if not source.exists():raise RuntimeError('Missing asset '+name)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    stem=source.stem+'.'+digest[:12]+source.suffix
    (dist/stem).write_bytes(source.read_bytes())
    mapping[name]=dict(file=stem,sha256=digest)
    return attr+'="'+stem+'"'
html=re.sub(r'(src|href)="([^"#]+\.(?:js|css)(?:\?[^"#]*)?)"',asset,html)
index.write_text(html)
(root/'research/release-assets.json').write_text(json.dumps(mapping,indent=2)+'\n')
print('Fingerprinted',len(mapping),'entrypoint assets')
