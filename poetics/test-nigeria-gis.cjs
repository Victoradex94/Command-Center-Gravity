const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const window={};const context={window};
for(const f of ['atlas.js','canonical-research.js','national-directory.js','directory-expansion.js','nigeria-boundary.js','nigeria-map.js','nigeria-states.js','nigeria-states-map.js','atlas-icons.js','atlas-audit.js','entry-status.js','entry-schema.js','directory.js'])vm.runInNewContext(fs.readFileSync('dist/'+f,'utf8'),context);
const geo=JSON.parse(fs.readFileSync('dist/nigeria-boundary.geojson','utf8'));
assert.equal(geo.features.length,1);assert.equal(geo.features[0].properties.iso3,'NGA');assert.equal(geo.metadata.license,'Public domain');assert.deepEqual(JSON.parse(JSON.stringify(window.PoeticsNigeria)),geo);
const ring=geo.features[0].geometry.coordinates[0];assert.deepEqual(ring[0],ring.at(-1));assert(ring.length>50);for(const [lon,lat] of ring){assert(lon>2&&lon<15);assert(lat>4&&lat<15);const [x,y]=window.PoeticsNigeriaMap.project(lon,lat);assert(x>=0&&x<=1000&&y>=0&&y<=850);}
const svg=window.PoeticsNigeriaMap.render(window.PoeticsAtlas.placeCoordinates,{Lagos:1,Abuja:3},'Abuja');assert(!svg.includes('<iframe'));assert(!svg.includes('tileLayer'));assert(svg.includes('Abuja: 3 entries'));assert(!svg.includes('Lafia:'));assert(svg.includes('nigeria-city selected'));assert(!svg.includes('NaN'));
const {rows,edges}=window.PoeticsDirectoryData;
for(const r of rows){assert(r.name&&r.details&&r.yearLabel&&r.status);assert(Array.isArray(r.links)&&r.links.length);assert(Array.isArray(r.media)&&Array.isArray(r.years));for(const y of r.years){assert(y.year>=1900&&y.year<=2026);assert(y.label&&/^https:\/\//.test(y.url));}for(const m of r.media)assert(m.credit&&m.sourceURL&&m.rights);}
for(const name of ['Word Tour (WordTour)','Eko Poetry Slam','Words Rhymes & Rhythm (WRR)','Artmosphere','Freedom Spoke Words','Figures of Speech Movement (FOS)'])assert.equal(rows.filter(r=>r.name===name).length,1);
const fos=rows.find(r=>r.id==='fos'),graciano=rows.find(r=>r.name==='Graciano Enwerem');assert(edges.some(e=>e.a===graciano.id&&e.b===fos.id));assert.equal(fos.years[0].year,2015);assert(fos.gaps.includes('Founding year'));
const reciprocal=(id,target)=>edges.filter(e=>e.a===id||e.b===id).some(e=>(e.a===id?e.b:e.a)===target);
for(const e of edges){assert(reciprocal(e.a,e.b));assert(reciprocal(e.b,e.a));}
assert(edges.some(e=>e.a==='kemi-bakare'&&e.b==='eko-slam'&&e.date===2014));assert(!edges.some(e=>e.a==='kemistry'&&e.b==='eko-slam'));
assert(!edges.some(e=>e.a==='freedom-spoke'&&e.b==='freedomhall'));assert(rows.find(r=>r.id==='wordtour').gaps.includes('Tour dates'));
console.log(`PASS Nigeria-only GIS geometry, projection, map markers and standard profiles: ${rows.length} entries, ${edges.length} source-linked relationships.`);
