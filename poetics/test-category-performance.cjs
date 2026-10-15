const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),{performance}=require('perf_hooks');
const index=fs.readFileSync('dist/index.html','utf8'),previous=fs.readFileSync('dist/atlas-preview-62.html','utf8');
function compose(html){const window={};for(const m of html.matchAll(/<script src="([^"]+)"/g)){if(/^(app|atlas-ui-guard)\./.test(m[1]))continue;vm.runInNewContext(fs.readFileSync('dist/'+m[1],'utf8'),{window,URLSearchParams});}return window;}
const now=compose(index),before=compose(previous);
assert.equal(JSON.stringify(now.PoeticsDirectoryData),JSON.stringify(before.PoeticsDirectoryData));
assert.equal(now.PoeticsDirectoryData.rows.length,453);assert.equal(now.PoeticsDirectoryData.edges.length,667);
const full={window:{}};vm.runInNewContext(fs.readFileSync('dist/canonical-research.js','utf8'),full);
const expected=JSON.parse(JSON.stringify(full.window.PoeticsResearch));expected.tables={'People & Platforms':expected.tables['People & Platforms']};
assert.equal(JSON.stringify(now.PoeticsResearch),JSON.stringify(expected));
assert(Object.keys(full.window.PoeticsResearch.tables).length>1);
for(const c of now.PoeticsStateMap.categories){const icon=now.PoeticsIcon(c);assert(icon.includes(`data-category-icon="${c}"`));assert(icon.includes('aria-hidden="true"'));}
let html='',nodes={};const noop=()=>{},root={classList:{add:noop},set innerHTML(s){html=s;nodes={}},querySelector(s){if(s.startsWith('#')&&!html.includes('id="'+s.slice(1)+'"'))return null;return nodes[s]||(nodes[s]={focus:noop,setSelectionRange:noop,setAttribute:noop,scrollIntoView:noop})},querySelectorAll(){return []}};
now.renderDirectory(root);
for(const c of now.PoeticsStateMap.categories){assert(html.includes(`data-category="${c}"`));assert((html.match(new RegExp(`data-category-icon="${c}"`,'g'))||[]).length>=2);}
const manifest=now.PoeticsStateUrbanManifest,oldAPI=before.PoeticsStateUrbanMap,newAPI=now.PoeticsStateUrbanMap;
const paths=s=>[...s.matchAll(/\sd="([^"]+)"/g)].map(m=>m[1]);
let calls=0;const instrumentedMath=Object.create(Math);instrumentedMath.log=x=>{calls++;return Math.log(x)};
const w={PoeticsStateUrbanManifest:manifest,PoeticsStateMap:now.PoeticsStateMap,PoeticsIcon:now.PoeticsIcon};vm.runInNewContext(fs.readFileSync('dist/state-urban-map.js','utf8'),{window:w,Math:instrumentedMath});
const api=w.PoeticsStateUrbanMap,data=JSON.parse(fs.readFileSync('dist/'+manifest.states.Kaduna.url));api.prime('Kaduna',data);
let first=api.render('Kaduna',{Kaduna:4,Zaria:4},{People:1,Places:4,Platforms:2,Prizes:1},'All places',64);assert(calls>0);
calls=0;let changed=api.render('Kaduna',{Kaduna:0,Zaria:2},{People:2},'All places',2);assert.equal(calls,0);assert(changed.includes('data-count="2"'));assert(!changed.includes('data-map-city="Kaduna"'));assert(changed.includes('data-map-city="Zaria"'));
api.render('Kaduna',{Zaria:2},{People:2},'Zaria',2);assert(calls>0);calls=0;api.render('Kaduna',{Zaria:1},{People:1},'Zaria',1);assert.equal(calls,0);
api.prime('Kaduna',data);api.render('Kaduna',{Zaria:1},{People:1},'Zaria',1);assert(calls>0);
const values={People:3,Places:2,Platforms:4,Prizes:1,Publications:1};
const timings=[];
for(const state of ['Kaduna','Lagos','Niger','Borno']){
 const d=JSON.parse(fs.readFileSync('dist/'+manifest.states[state].url)),counts=Object.fromEntries(d.cities.map(c=>[c.city,3]));oldAPI.prime(state,d);newAPI.prime(state,d);
 for(const selected of ['All places',...d.cities.map(c=>c.city)]){const old=oldAPI.render(state,counts,values,selected,64),fresh=newAPI.render(state,counts,values,selected,64);
  // Category icons differ; geographic paths must remain exactly the same.
  const geo=s=>paths(s.slice(s.indexOf('<svg data-map-level')));assert.deepEqual(geo(fresh),geo(old));
  for(const c of Object.keys(values))assert(fresh.includes(`data-category-icon="${c}"`));
 }
 const n=20;let t=performance.now();for(let i=0;i<n;i++)oldAPI.render(state,counts,values,'All places',64);const oldMs=performance.now()-t;
 t=performance.now();for(let i=0;i<n;i++)newAPI.render(state,counts,values,'All places',64);timings.push({state,redraws:n,beforeMs:+oldMs.toFixed(2),afterMs:+(performance.now()-t).toFixed(2)});
}
const bytes=h=>[...h.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g)].reduce((n,m)=>n+fs.statSync('dist/'+m[1]).size,0);
assert(bytes(index)<bytes(previous)*.85);
console.log(JSON.stringify({status:'PASS',entries:453,connections:667,fullComposedDataUnchanged:true,iconsInFiltersLegendStateCounts:true,beforeInitialBytes:bytes(previous),afterInitialBytes:bytes(index),geometryCPU:timings,scope:'Node/VM asset and geometry preparation checks; not browser loading or visual QA'},null,2));
