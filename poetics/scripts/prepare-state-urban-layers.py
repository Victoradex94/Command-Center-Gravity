"""Build lazy geographic state views from verified uploads, not poetry data.

The exact uploads remain in Library. Rendering derivatives retain every ring;
RDP max deviation .0001deg (~11m), preserving winding and area within1% or
falling back to original ring. No legal/topological accuracy claim.
"""
import argparse, collections, hashlib, json, math, re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('states',type=Path);p.add_argument('urban',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=root/'dist/geography';out.mkdir(exist_ok=True)
sb=a.states.read_bytes();ub=a.urban.read_bytes();states=json.loads(sb)['features'];urban=json.loads(ub)
assert hashlib.sha256(sb).hexdigest()=='edd28050c7f1ae40471424605f74e4d2df83502e4f301089761ae18f8ae2fbbf'
assert len(states)==37 and len({f['properties']['shapeName'] for f in states})==37
scope=json.loads((root/'research/geography/atlas-city-scope-v57.json').read_text())
coordinates=json.loads((root/'research/geography/atlas-city-coordinates-v57.json').read_text())
audit=json.loads((root/'research/geography/atlas-city-urban-coverage.json').read_text())
features={f['id']:f for f in urban['features'] if f['properties']['ISO3']=='NGA'}
stateName=lambda f:'Federal Capital Territory' if f['properties']['shapeName']=='Abuja Federal Capital Territory' else f['properties']['shapeName']
stateMap={stateName(f):f for f in states}

def in_ring(p,r):
    yes=False
    for i,v in enumerate(r):
        b=r[i-1]
        if (v[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-v[0])*(p[1]-v[1])/(b[1]-v[1])+v[0]:yes=not yes
    return yes
def polys(g):return g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
def contains(g,p):return any(in_ring(p,x[0]) and not any(in_ring(p,r) for r in x[1:]) for x in polys(g))
def area(r):return sum(p[0]*r[i-1][1]-r[i-1][0]*p[1] for i,p in enumerate(r))/2
def rdp(points,tol):
    if len(points)<=2:return points
    x,y=points[0];dx=points[-1][0]-x;dy=points[-1][1]-y;den=dx*dx+dy*dy
    best=-1;index=0
    for i,p in enumerate(points[1:-1],1):
        t=max(0,min(1,((p[0]-x)*dx+(p[1]-y)*dy)/den)) if den else 0
        dist=(p[0]-x-t*dx)**2+(p[1]-y-t*dy)**2
        if dist>best:best,index=dist,i
    if best>tol*tol:return rdp(points[:index+1],tol)[:-1]+rdp(points[index:],tol)
    return [points[0],points[-1]]
def simplify_ring(r):
    assert len(r)>=4 and r[0]==r[-1]
    pivot=max(range(1,len(r)-1),key=lambda i:(r[i][0]-r[0][0])**2+(r[i][1]-r[0][1])**2)
    s=rdp(r[:pivot+1],.0001)[:-1]+rdp(r[pivot:],.0001)
    original=area(r);reduced=area(s)
    if len(s)<4 or original*reduced<=0 or abs(reduced-original)>abs(original)*.01:s=r
    return [[round(x,6),round(y,6)] for x,y in s]
def simplified(g):return {'type':'MultiPolygon','coordinates':[[simplify_ring(r) for r in poly] for poly in polys(g)]}

metadata={'source':'https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM1/','boundaryID':'NGA-ADM1-27671186','stateVintage':2022,'stateAttribution':'GRID3 via geoBoundaries','license':'CC BY 4.0','stateUploadSha256':hashlib.sha256(sb).hexdigest(),'stateUploadBytes':len(sb),'urbanSource':'https://docs.digitalearthafrica.org/en/latest/data_specs/Africapolis_urban_specs.html','urbanAttribution':'OECD/SWAC and e-Geopolis','urbanVintage':2020,'urbanUploadSha256':hashlib.sha256(ub).hexdigest(),'urbanExtractedAt':urban['timeStamp'],'precision':'Rendering derivative: RDP .0001degree, every ring retained; ring winding/area guard1%, six decimal rounding. Not current/legal city limits.'}
grouped=collections.defaultdict(list);review=[]
for row in audit['rows']:
    candidates=row['nameCandidates'] or row['containingCandidates']
    if len(candidates)!=1:review.append({'city':row['city'],'state':row['atlasState'],'status':'unresolved','reason':'No unique name or source-point containing footprint'});continue
    f=features[candidates[0]['sourceID']];city=row['city'];state=row['atlasState'];pr=f['properties'];centre=[pr['Longitude'],pr['Latitude']]
    existing=coordinates.get(city);point=[existing['lon'],existing['lat']] if existing else None
    centroidInState=contains(stateMap[state]['geometry'],centre)
    centreInState=bool(point and contains(stateMap[state]['geometry'],point))
    if not centroidInState and not (centreInState and contains(f['geometry'],point)):raise ValueError('Unqualified state match '+city)
    g=simplified(f['geometry'])
    if point and contains(f['geometry'],point)!=contains(g,point):g=f['geometry']
    note='Containing urban area named '+pr['agglosName']+'; not a city rename' if city=='Yola' else ('Source name: '+pr['agglosName'] if city!=pr['agglosName'] else '')
    grouped[state].append({'city':city,'sourceName':pr['agglosName'],'sourceID':f['id'],'geometry':g,'labelPoint':point or centre,'note':note,'stateAssociation':'existing centre and footprint' if not centroidInState else 'source centroid in expected state','crossState':not centroidInState})
    review.append({'city':city,'state':state,'status':'selectable-containing-area' if city=='Yola' else 'selectable-urban-extent','sourceName':pr['agglosName'],'sourceID':f['id'],'sourceCentroidInState':centroidInState,'existingCentreInState':centreInState,'note':note,'crossState':not centroidInState})

manifest={'metadata':metadata,'states':{}};totalBytes=0
for name,f in stateMap.items():
    slug=re.sub('[^a-z0-9]+','-',name.lower()).strip('-');unmatched=[x['city'] for x in review if x['state']==name and x['status']=='unresolved']
    centres=[{'city':c,'coordinates':[v['lon'],v['lat']]} for c,v in coordinates.items() if scope['cities'].get(c)==name]
    payload={'state':name,'geometry':f['geometry'],'cities':grouped[name],'centres':centres,'unmatched':unmatched,'metadata':metadata}
    b=(json.dumps(payload,separators=(',',':'))+'\n').encode();sha=hashlib.sha256(b).hexdigest();filename=slug+'.'+sha[:12]+'.json';(out/filename).write_bytes(b);totalBytes+=len(b)
    manifest['states'][name]={'url':'geography/'+filename,'sha256':sha,'bytes':len(b),'cities':[x['city'] for x in grouped[name]],'unmatched':unmatched}
(root/'dist/state-urban-manifest.js').write_text('window.PoeticsStateUrbanManifest='+json.dumps(manifest,separators=(',',':'))+';\n')
(root/'research/geography/state-urban-rollout.json').write_text(json.dumps({'metadata':metadata,'cities':review,'states':manifest['states'],'totalBytes':totalBytes},indent=2)+'\n')
print(json.dumps({'states':len(states),'selectable':sum(len(v) for v in grouped.values()),'unresolved':[r['city'] for r in review if r['status']=='unresolved'],'payloadBytes':totalBytes,'largestBytes':max(x['bytes'] for x in manifest['states'].values())}))
