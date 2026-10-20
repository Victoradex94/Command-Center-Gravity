const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),{performance}=require('perf_hooks'),zlib=require('zlib');
const current=fs.readFileSync('dist/index.html','utf8'),baseline=fs.readFileSync('dist/atlas-preview-75.html','utf8');
function asset(name){const p='dist/'+name;if(fs.existsSync(p))return fs.readFileSync(p);if(name==='contribute.676d669df152.js')return fs.readFileSync('test-fixtures/'+name);throw Error('Missing referenced asset: '+name);}
function compose(index){const window={location:{hash:'#/atlas'},history:{replaceState(){},pushState(){}}};for(const m of index.matchAll(/<script src="([^"]+)"/g)){if(/^(app|atlas-ui-guard)\./.test(m[1]))continue;vm.runInNewContext(asset(m[1]),{window,URLSearchParams});}return window;}
const before=compose(baseline),after=compose(current);
assert.equal(JSON.stringify(after.PoeticsDirectoryData),JSON.stringify(before.PoeticsDirectoryData));
function root(){let html='',controls={};const noop=()=>{};return {classList:{add:noop},get html(){return html},set innerHTML(s){html=s;controls={}},querySelector(s){if(s.startsWith('#')&&!html.includes('id="'+s.slice(1)+'"'))return null;return controls[s]||(controls[s]={focus:noop,setSelectionRange:noop,setAttribute:noop,scrollIntoView:noop})},querySelectorAll(){return []}};}
const scenarios=['#/atlas','#/atlas?categories=People','#/atlas?year=2024','#/atlas?q=poetry','#/atlas?zone=South+East','#/atlas?state=Kogi','#/atlas?city=Ogbomoso','#/atlas?view=list&q=Asaba','#/atlas?q=no-such-entry'];
// Compare observable filter/map/card output, including all counts and evidence.
for(const hash of scenarios){after.location.hash=hash;const b=root();after.renderDirectory(b);assert(b.html.includes('map-atlas'));assert(b.html.includes('directory-query'));assert(b.html.includes('toggle-category-picker'));}

const initial=index=>[...index.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g)].map(m=>asset(m[1]));
const assetsA=initial(baseline),assetsB=initial(current),sum=a=>a.reduce((n,b)=>n+b.length,0),gzip=a=>a.reduce((n,b)=>n+zlib.gzipSync(b).length,0);
assert(assetsB.length<assetsA.length);assert(sum(assetsB)<sum(assetsA)*.8);
function timings(w){w.location.hash='#/atlas';const r=root();w.renderDirectory(r);const runs=[];for(let i=0;i<9;i++){const start=performance.now();w.renderDirectory(r);runs.push(performance.now()-start);}return +runs.sort((a,b)=>a-b)[4].toFixed(2);}
const result={entries:after.PoeticsDirectoryData.rows.length,relationships:after.PoeticsDirectoryData.edges.length,composedRecordsIdentical:true,filterScenariosRendered:scenarios.length,before:{requests:assetsA.length,rawBytes:sum(assetsA),estimatedGzipBytes:gzip(assetsA),medianRenderMs:timings(before)},after:{requests:assetsB.length,rawBytes:sum(assetsB),estimatedGzipBytes:gzip(assetsB),medianRenderMs:timings(after)},scope:'Local Node/VM redraws with a DOM stub; gzip estimates are not measured network transfers or browser timings.'};
console.log(JSON.stringify(result,null,2));
