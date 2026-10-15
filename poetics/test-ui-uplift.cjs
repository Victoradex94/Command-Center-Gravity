const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const noop=()=>{};let html='',controls={},nodes=[],parents=[],chips=[],categoryButtons=[],fetches=0;
const window={location:{hash:'#/atlas',href:'https://example.test/#/atlas'},history:{pushState(_,__,h){window.location.hash=h},replaceState(_,__,h){window.location.hash=h}},fetch:async url=>{fetches++;return {ok:true,json:async()=>JSON.parse(fs.readFileSync('dist/'+url))}}};
for(const m of fs.readFileSync('dist/index.html','utf8').matchAll(/<script src="([^"]+)"/g)){if(/^(app|atlas-ui-guard)\./.test(m[1]))continue;vm.runInNewContext(fs.readFileSync('dist/'+m[1],'utf8'),{window,URLSearchParams});}
const parse=(s,attr,key)=>[...s.matchAll(new RegExp('<button[^>]*'+attr+'="([^"]+)"[^>]*>','g'))].map(m=>({tagName:'button',dataset:{[key]:m[1]}}));
const root={classList:{add:noop},set innerHTML(s){html=s;controls={};nodes=parse(s,'data-node','node');parents=parse(s,'data-geography-parent','geographyParent');chips=parse(s,'data-clear-filter','clearFilter');categoryButtons=[...s.matchAll(/<button data-category-state="([^"]+)" data-category-count="([^"]+)" data-count="([^"]+)"/g)].map(m=>({dataset:{categoryState:m[1],categoryCount:m[2],count:+m[3]}}));},querySelector(s){if(s.startsWith('#')&&!html.includes('id="'+s.slice(1)+'"'))return null;return controls[s]||(controls[s]={focus:noop,setSelectionRange:noop,setAttribute:noop,scrollIntoView:noop,select:noop})},querySelectorAll(s){return s==='[data-node]'?nodes:s==='[data-clear-filter]'?chips:s==='[data-geography-parent]'?parents:s==='[data-category-state]'?categoryButtons:[]}};
const change=(id,value)=>controls[id].onchange({target:{value}}),state=()=>window.PoeticsAtlasNavigation.read(window.location.hash);
async function run(){
 window.renderDirectory(root);assert.equal(fetches,0);
 for(const id of ['directory-state','directory-zone','directory-geo','directory-year','directory-activity','map-category-filter'])assert.equal((html.match(new RegExp('id="'+id+'"','g'))||[]).length,1);
 assert(html.includes('filters-expanded'));controls['#toggle-map-filters'].onclick();assert(html.includes('filters-collapsed'));controls['#toggle-map-filters'].onclick();
 change('#directory-state','Kaduna');await new Promise(r=>setTimeout(r,0));assert(html.includes('class="state-category-counts"'));assert.equal(categoryButtons.reduce((n,b)=>n+b.dataset.count,0),8);
 change('#directory-geo','Zaria');assert.equal(categoryButtons.reduce((n,b)=>n+b.dataset.count,0),4);
 const chosenCity=state().geo;controls['#close-results'].onclick();assert.equal(state().geo,chosenCity);assert.equal(state().state,'Kaduna');assert.equal(state().browsing,false);assert(!html.includes('<aside class="map-results"'));
 const closed=window.location.hash;window.renderDirectory(root);assert.equal(window.location.hash,closed);assert(!html.includes('<aside class="map-results"'));
 controls['#browse-records'].onclick();assert(html.includes('<aside class="map-results"'));assert.equal(state().geo,'Zaria');
 parents.find(p=>p.dataset.geographyParent==='state').onclick();assert.equal(state().geo,'All places');assert.equal(state().state,'Kaduna');
 parents.find(p=>p.dataset.geographyParent==='zone').onclick();assert.equal(state().state,'All states');assert.equal(state().zone,'North West');
 parents.find(p=>p.dataset.geographyParent==='country').onclick();assert.equal(state().zone,'All zones');
 change('#directory-state','Delta');await new Promise(r=>setTimeout(r,0));controls['#directory-query'].oninput({target:{value:'Orerokpe',selectionStart:8}});assert(html.includes('Proposal; not completed'));
 const first=nodes.find(n=>window.PoeticsDirectoryData.rows.some(r=>r.id===n.dataset.node));assert(first);first.onclick();assert.equal(state().query,'Orerokpe');assert(html.includes('class="atlas-profile"'));controls['#back-results'].onclick();assert.equal(state().query,'Orerokpe');
 chips.find(c=>c.dataset.clearFilter==='search').onclick();assert.equal(state().query,'');assert.equal(state().state,'Delta');
 change('#directory-year','2024');chips.find(c=>c.dataset.clearFilter==='year').onclick();assert.equal(state().year,'All years');assert.equal(state().state,'Delta');
 chips.find(c=>c.dataset.clearFilter==='state').onclick();assert.equal(state().state,'All states');assert.equal(state().zone,'South South');
 controls['#directory-reset'].onclick();assert.equal(state().zone,'All zones');assert.equal(state().enabled.length,5);assert.equal(state().browsing,false);
 assert.equal(window.PoeticsDirectoryData.rows.length,453);assert.equal(window.PoeticsDirectoryData.edges.length,667);
 console.log('PASS packaged-module UI behavior: one filter card, collapse, parent path, individual clearing, preserved panel/map/search state across reload, city category totals, announced Delta evidence,453/667. VM/DOM-stub only.');
}
run().catch(e=>{console.error(e);process.exitCode=1});
