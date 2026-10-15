"""Read-only coverage audit: names are candidates, not approved spatial identity.

Run after exporting actual composed Atlas city scope/coordinates. No runtime
data or poetry profiles are edited. Source geometry remains in the upload.
"""
import argparse, hashlib, json, re
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('upload',type=Path)
p.add_argument('scope',type=Path)
p.add_argument('coordinates',type=Path)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
raw=a.upload.read_bytes();d=json.loads(raw)
scope=json.loads(a.scope.read_text());coords=json.loads(a.coordinates.read_text())
features=[f for f in d['features'] if f['properties']['ISO3']=='NGA']
normal=lambda s:re.sub('[^a-z0-9]','',s.casefold())
lookup={}
for f in features:lookup.setdefault(normal(f['properties']['agglosName']),[]).append(f)

def in_ring(point,ring):
    result=False
    for i,v in enumerate(ring):
        last=ring[i-1]
        if (v[1]>point[1])!=(last[1]>point[1]) and point[0]<(last[0]-v[0])*(point[1]-v[1])/(last[1]-v[1])+v[0]:result=not result
    return result

def contains(f,point):
    for poly in f['geometry']['coordinates']:
        ring=poly[0];xs=[v[0] for v in ring];ys=[v[1] for v in ring]
        if min(xs)<=point[0]<=max(xs) and min(ys)<=point[1]<=max(ys) and in_ring(point,ring) and not any(in_ring(point,r) for r in poly[1:]):return True
    return False

def brief(f):
    ps=[p for poly in f['geometry']['coordinates'] for ring in poly for p in ring]
    return {'sourceID':f['id'],'sourceName':f['properties']['agglosName'],
            'bbox':[min(p[0] for p in ps),min(p[1] for p in ps),max(p[0] for p in ps),max(p[1] for p in ps)],
            'positions':len(ps),'rings':sum(len(poly) for poly in f['geometry']['coordinates'])}

rows=[]
for city,state in sorted(scope['cities'].items()):
    named=lookup.get(normal(city),[])
    point=[coords[city]['lon'],coords[city]['lat']] if city in coords else None
    spatial=[f for f in features if contains(f,point)] if point else []
    if len(named)==1:
        status='name-match-spatial-confirmed' if point and named[0] in spatial else 'name-match-location-review-needed'
    elif len(named)>1:status='ambiguous-name'
    elif spatial:status='different-name-containing-area-review-needed'
    else:status='no-qualifying-match-in-this-pass'
    rows.append({'city':city,'atlasState':state,'status':status,'nameCandidates':[brief(f) for f in named],
                 'containingCandidates':[brief(f) for f in spatial],
                 'existingCentre':coords.get(city),'implemented':city in ('Kaduna','Zaria'),
                 'next':'State geometry + spatial/alias review before import; preserve source name and vintage2020'})

noncity=[v for v in scope['locationValues'] if v not in scope['cities']]
result={'scope':'39 explicit mapped cities in current composed Atlas cityStates; all location labels separately inventoried',
        'sourceCommit':'5dddd6a73fca1f89895ed42e29c5dd3c4c0f95e0','sitesVersion':57,
        'uploadSha256':hashlib.sha256(raw).hexdigest(),'uploadFeatureCount':len(d['features']),
        'nigeriaFeatureCount':len(features),'rows':rows,'otherLocationLabels':noncity,
        'limits':'No new identities/imports; point containment is evidence of footprint overlap, not proof of same city/legal boundary. Name-only matches need geographic check. Noncity labels not forcibly geocoded.'}
out=root/'research/geography/atlas-city-urban-coverage.json';out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
lines=['# Atlas city / urban-extent coverage audit','',
       'Scope: current GitHub main5dddd6a / Sites57; 39 mapped cities. No app/data import.','',
       '| Atlas city | Atlas state | Name match | Containing area at existing centre | Status |',
       '|---|---|---|---|---|']
for r in rows:lines.append('| '+ ' | '.join([r['city'],r['atlasState'],', '.join(f['sourceName']+' ('+f['sourceID']+')' for f in r['nameCandidates']) or '—',', '.join(f['sourceName']+' ('+f['sourceID']+')' for f in r['containingCandidates']) or 'Not established',r['status']])+' |')
lines+=['','Other location labels (not automatically treated as cities): '+', '.join(noncity)+'.','',result['limits'],'',
        'Yola’s point lies inside the feature named Jimeta. Keep that as a containing-area candidate, not a Yola rename. Ile-Ife/Ife1, Lafia/Lafia1 and spelling variants Ilesa/Ilesha and Ogbomoso/Ogbomosho have spatial support, but still require state/alias review. Owerri, Awka, Ikot Ekpene and Karu have neither a normalized exact name nor an existing source coordinate qualifying a footprint in this pass. This is not absence of settlements or poetry.','',
        '## State geometry access checkpoint','',
        'Official geoBoundaries API https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM1/ directly read15Oct2026: boundaryID NGA-ADM1-27671186,37units, GRID3, represented2022,CCBY4, build12Dec2023. API advertises simplified download https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson . Connected GitHub reads of repository file and advertised raw URL returned Git LFS pointer only: expected827817bytes, SHA256 edd28050c7f1ae40471424605f74e4d2df83502e4f301089761ae18f8ae2fbbf. No state geometries retrieved; do not claim alignment/rollout from metadata. No network restriction bypass attempted. User browser download/upload is needed with current capabilities.','',
        'No keyword web query this pass. Exact local operations: normalize each city name to lowercase alphanumerics and compare only ISO3=NGA agglosName; for each existing sourced city point, bounding-box prefilter and point-in-MultiPolygon excluding holes; record every positive and negative row. No fuzzy candidate imported.']
(root/'research/geography/atlas-city-urban-coverage.md').write_text('\n'.join(lines)+'\n')
from collections import Counter
print(json.dumps({'cities':len(rows),'statusCounts':Counter(r['status'] for r in rows),'otherLocationLabels':len(noncity)}))
