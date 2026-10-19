"""Derive the Atlas's display input without changing the full research snapshot."""
from pathlib import Path
import json,re

dist=Path(__file__).resolve().parents[1]/'dist'
source=(dist/'canonical-research.js').read_text(encoding='utf-8')
match=re.fullmatch(r'window\.PoeticsResearch\s*=\s*([\s\S]*?);?\s*',source)
if not match:
    raise ValueError('Unexpected canonical research source')
data=json.loads(match[1].removesuffix(';'))
# directory.js consumes only this table. The complete source stays unchanged in
# canonical-research.js; dates, sources, profiles and deep research are retained.
data['tables']={'People & Platforms':data['tables']['People & Platforms']}
(dist/'canonical-research-runtime.js').write_text('window.PoeticsResearch='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8',newline='\n')
print('Prepared browser research input; full canonical-research.js retained')
