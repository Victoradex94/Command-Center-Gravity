from pathlib import Path
import re,json,math
p=Path(__file__).resolve().parents[1]/'dist'/'nigeria-states.json';d=json.loads(p.read_text())
def rings(path):
 tokens=re.findall(r'[mz]|-?\d+(?:\.\d+)?',path);x=y=sx=sy=0;i=0;ring=[];result=[]
 while i<len(tokens):
  if tokens[i]=='z':
   if len(ring)>2:result.append(ring)
   ring=[];x,y=sx,sy;i+=1;continue
  if tokens[i]=='m':
   if len(ring)>2:result.append(ring)
   ring=[];i+=1;new=True
  else:new=False
  x+=float(tokens[i]);y+=float(tokens[i+1]);i+=2
  if new:sx,sy=x,y
  ring.append([x,y])
 if len(ring)>2:result.append(ring)
 return result
for s in d['locations']:
 polys=rings(s['path']);best=None
 for ring in polys:
  ymin=min(v[1] for v in ring);ymax=max(v[1] for v in ring)
  # Pick the middle of the widest interior scanline interval, never a bounding-box-only point.
  for step in range(1,40):
   y=ymin+(ymax-ymin)*step/40;intersections=[]
   for a,b in zip(ring,ring[1:]+ring[:1]):
    if (a[1]>y)!=(b[1]>y):intersections.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
   intersections.sort()
   for a,b in zip(intersections[::2],intersections[1::2]):
    score=(b-a)*math.sin(math.pi*step/40)
    if best is None or score>best[0]:best=(score,[(a+b)/2,y])
  if not best:raise ValueError(s['name'])
 s['labelPoint']=best[1]
d['metadata']['changes']+=' Added interior label points from original state paths.'
p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n');p.with_suffix('.js').write_text('window.PoeticsStates='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
