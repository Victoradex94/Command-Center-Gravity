"""Build the Kaduna state/centre layer from the retained OSM export.

Administrative level 6 and state-label nodes are intentionally excluded.
This creates city-centre locators, never city-area polygons.
"""
import json, hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'research/geography/kaduna-zaria-osm-export.geojson'
raw = source.read_bytes()
export = json.loads(raw)
state = next(f for f in export['features'] if f['properties'].get('ISO3166-2') == 'NG-KD')
assert state['properties']['admin_level'] == '4'
assert state['geometry']['type'] == 'Polygon'
cities = [f for f in export['features'] if f['geometry']['type'] == 'Point' and f['properties'].get('place') == 'city']
assert {f['properties']['name'] for f in cities} == {'Kaduna', 'Zaria'}
data = {
    'state': 'Kaduna', 'exportTimestamp': export['timestamp'],
    'exportSha256': hashlib.sha256(raw).hexdigest(),
    'license': 'ODbL 1.0', 'attribution': '© OpenStreetMap contributors',
    'stateSourceDate': state['properties'].get('source:date'),
    'stateObject': state['id'], 'geometry': state['geometry'],
    'cities': [{'name': f['properties']['name'], 'object': f['id'], 'coordinates': f['geometry']['coordinates']} for f in cities],
    'excluded': [{'object': f['id'], 'reason': 'Administrative level 6 area; city extent not established' if f['geometry']['type'] == 'Polygon' else 'State label, not city centre'} for f in export['features'] if f is not state and f not in cities],
}
(root / 'dist/osm-state-locators.js').write_text('window.PoeticsOSMStateLocators=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('Prepared Kaduna state polygon and two city-centre locators; excluded two other features.')
