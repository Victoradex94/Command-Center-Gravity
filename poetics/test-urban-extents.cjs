const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const window={};for(const f of ['atlas','nigeria-states','nigeria-states-map','osm-state-locators','urban-extents','geography-registry','state-city-map'])vm.runInNewContext(fs.readFileSync('dist/'+f+'.js','utf8'),{window});
const u=window.PoeticsUrbanExtents,g=window.PoeticsGeography,m=window.PoeticsStateCityMap;
assert.equal(u.sourceFeatureCount,1714);assert.equal(u.countryCounts.NGA,1465);assert.equal(u.vintage,2020);assert.equal(u.features.length,2);
assert(g.hasUrbanExtent('Kaduna'));assert(!g.hasUrbanExtent('Lagos'));
const raw=JSON.parse(fs.readFileSync('research/geography/africapolis-kaduna-zaria-2020-source.geojson'));
function inside(p,ring){let yes=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const a=ring[i],b=ring[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])yes=!yes;}return yes;}
let vertices=0,holes=0;
for(const f of u.features){const source=raw.features.find(x=>x.id===f.id);assert.equal(source.properties.ISO3,'NGA');assert.equal(f.city,source.properties.agglosName);assert.equal(f.geometry.type,'MultiPolygon');const layer=g.get(f.id);assert.equal(layer.role,'urban-extent');assert.equal(layer.sourceVintage,2020);assert.equal(layer.license,'CC BY 4.0');
 assert.equal(f.geometry.coordinates.length,source.geometry.coordinates.length);
 for(let p=0;p<f.geometry.coordinates.length;p++){const poly=f.geometry.coordinates[p];holes+=poly.length-1;assert.equal(poly.length,source.geometry.coordinates[p].length);for(let r=0;r<poly.length;r++){const ring=poly[r],original=source.geometry.coordinates[p][r];assert.equal(ring.length,original.length);assert.deepEqual(ring[0],ring.at(-1));for(let i=0;i<ring.length;i++){vertices++;for(let k=0;k<2;k++)assert(Math.abs(ring[i][k]-original[i][k])<=0.000000501);const [x,y]=m.project(ring[i]);assert(Number.isFinite(x)&&Number.isFinite(y));assert(x>=0&&x<=744&&y>=0&&y<=600);}}}
 const centre=window.PoeticsOSMStateLocators.cities.find(x=>x.name===f.city).coordinates;assert(f.geometry.coordinates.some(poly=>inside(centre,poly[0])&&poly.slice(1).every(r=>!inside(centre,r))),'Source city centre must align with footprint');
}
assert.equal(vertices,26474);assert.equal(holes,48);
const html=m.render('Kaduna',{Kaduna:4,Zaria:4},{People:1,Places:4,Platforms:2,Prizes:1,Publications:0},'Zaria',64);
assert.equal((html.match(/class="urban-extent /g)||[]).length,2);assert(html.includes('clip-path="url(#kaduna-urban-clip)"'));assert(html.includes('fill-rule="evenodd"'));assert(!html.includes('<iframe'));assert(!/NaN|Infinity/.test(html));
const download=JSON.parse(fs.readFileSync('dist/urban-extents-kaduna-2020.geojson'));assert.equal(download.features.length,2);assert.equal(download.metadata.uploadSha256,u.uploadSha256);
console.log('PASS two source-ID matched NGA footprints; all26474 vertices/48holes retained; <=0.0000005deg rounding; city-centre containment, common projection, qualified registry/attribution, state clipping and downloadable GeoJSON. No topology/current-boundary audit claimed.');
