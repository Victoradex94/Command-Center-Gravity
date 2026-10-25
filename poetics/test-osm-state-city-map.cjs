const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),assert=require('assert/strict');
const raw=fs.readFileSync('research/geography/kaduna-zaria-osm-export.geojson');
const canonical=raw.toString('utf8').replace(/\r\n/g,'\n');
assert.equal(crypto.createHash('sha256').update(canonical).digest('hex'),'b99ab84a9e53e11bd94ce47854423664364aade90104afaf444edf69c3faa151');
const exportData=JSON.parse(raw),window={};for(const f of ['nigeria-states','nigeria-states-map','osm-state-locators','state-city-map'])vm.runInNewContext(fs.readFileSync('dist/'+f+'.js','utf8'),{window});
const m=window.PoeticsStateCityMap,d=m.data;assert.equal(d.stateObject,'relation/3709353');assert.equal(d.stateSourceDate,'2013');assert.equal(d.exportTimestamp,'2026-10-14T20:35:21Z');assert.equal(d.cities.length,2);
assert.equal(JSON.stringify(d.geometry),JSON.stringify(exportData.features.find(f=>f.id===d.stateObject).geometry));
assert(d.excluded.some(e=>e.object==='relation/3709376'));assert(d.excluded.some(e=>e.object==='node/2163706705'));
const ring=d.geometry.coordinates[0];assert.deepEqual(ring[0],ring.at(-1));assert.equal(ring.length,1930);
for(const p of ring){assert(p.every(Number.isFinite));assert(Math.abs(p[0])<=180&&Math.abs(p[1])<=90);const [x,y]=m.project(p);assert(x>=0&&x<=744&&y>=0&&y<=600);}
function inside(p,ring){let yes=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const a=ring[i],b=ring[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])yes=!yes;}return yes;}
for(const c of d.cities){assert(inside(c.coordinates,ring));assert(d.geometry.coordinates.slice(1).every(h=>!inside(c.coordinates,h)));}
const kad=m.project(d.cities.find(c=>c.name==='Kaduna').coordinates),zar=m.project(d.cities.find(c=>c.name==='Zaria').coordinates);assert(zar[0]>kad[0]&&zar[1]<kad[1],'Zaria must be northeast of Kaduna under the common projection');
const html=m.render('Kaduna',{Kaduna:6,Zaria:2},{People:1,Places:4,Platforms:2,Prizes:1,Publications:0},'Zaria',15);assert(html.includes('data-map-city="Kaduna"'));assert(html.includes('data-map-city="Zaria"'));assert(html.includes('Zaria city centre: 2 matching entries'));assert(html.includes('data-category-state="Kaduna"'));assert(!html.includes('3709376'));assert(!html.includes('<iframe'));assert(!/NaN|Infinity/.test(html));assert.equal(m.render('Lagos',{},{}),'');
console.log('PASS raw provenance hash, exact state geometry, administrative/state-label exclusions, closed finite rings, point containment, shared projection/orientation, accessible city locators, preserved category controls, qualified urban-extent description and attribution.');
