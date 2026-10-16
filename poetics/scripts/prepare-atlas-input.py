"""Create a lossless browser-only data bundle; retain readable research sources."""
from pathlib import Path
from collections import Counter
import json, re

DATA_NAMES = ['atlas.js', 'canonical-research-runtime.js', 'national-directory.js',
              'directory-expansion.js', 'nigeria-boundary.js', 'nigeria-states.js',
              'osm-state-locators.js', 'state-urban-manifest.js', 'atlas-audit.js',
              'game-assets.js']

def prepare(dist):
    data = {}
    for name in DATA_NAMES:
        match = re.fullmatch(r'window\.(\w+)\s*=\s*([\s\S]*?);?\s*', (dist/name).read_text())
        if not match:
            raise ValueError('Expected a pure data assignment: '+name)
        data[match[1]] = json.loads(match[2].removesuffix(';'))
    counts = Counter()
    def collect(value):
        if isinstance(value, str): counts[value] += 1
        elif isinstance(value, list):
            for item in value: collect(item)
        elif isinstance(value, dict):
            for item in value.values(): collect(item)
    collect(data)
    strings = [s for s,n in counts.items() if len(s)>24 and n>1 and len(s)*(n-1)>n*9+len(s)+4]
    string_ids = {s:i for i,s in enumerate(strings)}
    schemas, schema_ids = [], {}
    def pack(value):
        if isinstance(value, str) and value in string_ids: return ['s', string_ids[value]]
        if isinstance(value, list): return ['a', *[pack(v) for v in value]]
        if isinstance(value, dict):
            keys = tuple(value)
            if keys not in schema_ids:
                schema_ids[keys] = len(schemas); schemas.append(keys)
            return ['o', schema_ids[keys], *[pack(v) for v in value.values()]]
        return value
    packed = pack(data)
    payload = json.dumps([strings,schemas,packed], ensure_ascii=False, separators=(',',':'))
    decoder = "(function(p){'use strict';function u(v){if(!Array.isArray(v))return v;if(v[0]==='s')return p[0][v[1]];if(v[0]==='a')return v.slice(1).map(u);return Object.fromEntries(p[1][v[1]].map((k,i)=>[k,u(v[i+2])]));}Object.assign(window,u(p[2]));})("+payload+");\n"
    (dist/'atlas-input.js').write_text(decoder)
    return DATA_NAMES

if __name__ == '__main__':
    prepare(Path(__file__).resolve().parents[1]/'dist')
