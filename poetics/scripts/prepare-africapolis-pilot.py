"""Prepare a source-qualified Kaduna/Zaria pilot, never inferred city limits.

Input is the user-downloaded WFS response. Retain full input hash and exact
selected source features; runtime geometry rounds to six decimal places only.
"""
import argparse, collections, hashlib, json, math
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
raw = a.input.read_bytes()
d = json.loads(raw)
assert d['type'] == 'FeatureCollection'
assert d['numberReturned'] == d['numberMatched'] == len(d['features'])
assert d['crs']['properties']['name'].endswith('EPSG::4326')
selected = [f for f in d['features'] if f['properties']['ISO3'] == 'NGA' and f['properties']['agglosName'] in ('Kaduna', 'Zaria')]
assert len(selected) == 2
source = {'type': 'FeatureCollection', 'features': selected}
out = root / 'research/geography'
out.mkdir(exist_ok=True)
(out / 'africapolis-kaduna-zaria-2020-source.geojson').write_text(json.dumps(source, separators=(',', ':')) + '\n')

def round_positions(value):
    if isinstance(value[0], (int, float)):
        assert len(value) == 2 and all(math.isfinite(x) for x in value)
        assert -180 <= value[0] <= 180 and -90 <= value[1] <= 90
        return [round(x, 6) for x in value]
    return [round_positions(v) for v in value]

features = []
for f in selected:
    assert f['geometry']['type'] == 'MultiPolygon'
    for poly in f['geometry']['coordinates']:
        for ring in poly:
            assert len(ring) >= 4 and ring[0] == ring[-1]
    features.append({'id': f['id'], 'city': f['properties']['agglosName'], 'state': 'Kaduna',
                     'geometry': {'type': 'MultiPolygon', 'coordinates': round_positions(f['geometry']['coordinates'])}})
metadata = {
    'dataset': 'Africapolis', 'layer': 'africapolis:Africapolis_2020', 'vintage': 2020,
    'crs': 'EPSG:4326', 'license': 'CC BY 4.0', 'attribution': 'OECD/SWAC and e-Geopolis',
    'source': 'https://docs.digitalearthafrica.org/en/latest/data_specs/Africapolis_urban_specs.html',
    'extractedAt': d['timeStamp'], 'uploadedFile': a.input.name,
    'uploadSha256': hashlib.sha256(raw).hexdigest(), 'uploadBytes': len(raw),
    'sourceFeatureCount': len(d['features']), 'countryCounts': dict(collections.Counter(f['properties']['ISO3'] for f in d['features'])),
    'selection': 'Exact NGA + Kaduna/Zaria name match; checked against uploaded Kaduna state geometry',
    'precision': 'Six decimal degree rounding; no simplification; all rings/holes retained',
    'scope': '2020 urban settlement extents, not legal city limits or current 2026 boundaries; other states not integrated',
    'features': features,
}
(root / 'dist/urban-extents.js').write_text('window.PoeticsUrbanExtents=' + json.dumps(metadata, separators=(',', ':')) + ';\n')
(out / 'africapolis-pilot-manifest.json').write_text(json.dumps({k:v for k,v in metadata.items() if k != 'features'}, indent=2) + '\n')
print('Prepared two urban extents; preserved all rings and excluded non-NGA features.')
