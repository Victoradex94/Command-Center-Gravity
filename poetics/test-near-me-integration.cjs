const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const index=fs.readFileSync('dist/index.html','utf8');
const delivered=name=>{const match=index.match(new RegExp('(src|href)="('+name+'\\.[a-f0-9]{12}\\.js)"'));assert(match,'delivered '+name);return fs.readFileSync('dist/'+match[2],'utf8');};
async function test(){
 const scripts=[],noop=()=>{};let html='',controls={},opened=null,openCount=0;
 const window={location:{hash:'#/atlas'},PoeticsNearMe:{init:(focus,getRows)=>{opened={focus,getRows};openCount++;}}};
 const document={createElement:()=>({remove:noop}),head:{append:s=>scripts.push(s)}};
 const context={window,document,console};
 for(const file of ['atlas','canonical-research','national-directory','directory-expansion','nigeria-boundary','nigeria-map','nigeria-states','nigeria-states-map','atlas-icons','atlas-audit','entry-status','entry-schema','directory'])vm.runInNewContext(fs.readFileSync('dist/'+file+'.js','utf8'),context);
 const before=JSON.stringify(window.PoeticsDirectoryData.rows.map(r=>window.PoeticsEntryStatus.classify(r,new Date('2026-10-24T00:00:00Z'))));
 vm.runInNewContext(delivered('entry-status'),context);
 assert.equal(JSON.stringify(window.PoeticsDirectoryData.rows.map(r=>window.PoeticsEntryStatus.classify(r,new Date('2026-10-24T00:00:00Z')))),before,'formatting-only delivery preserves every fixture status');
 vm.runInNewContext(delivered('game-assets'),context);vm.runInNewContext(delivered('game-loader'),context);
 const radarFile=window.PoeticsLazyAssets['near-me'];assert(/^near-me-radar\.[a-f0-9]{12}\.js$/.test(radarFile));
 assert(radarFile.includes(crypto.createHash('sha256').update(fs.readFileSync('dist/'+radarFile)).digest('hex').slice(0,12)),'radar hash matches actual delivery bytes');
 const root={classList:{add:noop},set innerHTML(v){html=v;controls={};},querySelector(s){return controls[s]||(controls[s]={focus:noop,setSelectionRange:noop,scrollIntoView:noop,setAttribute:noop});},querySelectorAll:()=>[]};
 window.renderDirectory(root);assert(html.includes('id="near-me-btn"'));assert.equal(scripts.length,0,'initial render must not fetch radar');
 controls['#directory-query'].oninput({target:{value:'Mic',selectionStart:3}});
 const button=controls['#near-me-btn'];button.onclick();assert.equal(button.disabled,true);assert.equal(scripts.length,1);assert.equal(scripts[0].src,radarFile);
 const same=window.PoeticsLoadAsset('near-me');assert.equal(window.PoeticsLoadAsset('near-me'),same,'pending fetch is deduplicated');
 scripts[0].onload();await same;await Promise.resolve();assert.equal(button.disabled,false);assert(opened);
 const expected=opened.getRows().map(r=>r.id).sort();assert(expected.length>0);
 controls['#directory-geo'].onchange({target:{value:'Lagos'}});
 controls['#near-me-btn'].onclick();await Promise.resolve();await Promise.resolve();assert.equal(scripts.length,1,'warm radar uses cached asset');
 assert.equal(opened.getRows().map(r=>r.id).sort().join(','),expected.join(','),'nearby getter preserves search while ignoring previous geographic scope');
 const outside=opened.getRows().find(r=>String(r.city).includes('Ogbomoso'));assert(outside,'surrounding/other-city record is not trapped by old city filter');
 opened.focus(outside.id);assert(html.includes('class="atlas-profile"'));assert(html.includes(outside.name),'focus opens the actual selected profile');
 const load=window.PoeticsLoadAsset;window.PoeticsLoadAsset=()=>Promise.reject(Error('network unavailable'));
 const retry=controls['#near-me-btn'];retry.onclick();await Promise.resolve();await Promise.resolve();await Promise.resolve();assert.equal(retry.disabled,false);assert.equal(retry.textContent,'Retry Near Me');
 window.PoeticsLoadAsset=load;retry.onclick();await Promise.resolve();await Promise.resolve();assert(openCount>=3,'retry opens radar successfully');
 // Exercise the actual shared loader failure eviction, rather than replacing its internals.
 window.PoeticsLazyAssets['review-retry']='review-retry.js';const failed=load('review-retry');scripts[1].onerror();await assert.rejects(failed);
 const recovered=load('review-retry');assert.equal(scripts.length,3);scripts[2].onload();await recovered;
 console.log('PASS actual directory Near Me button, cold/warm deduplicated hashed loader, network retry, non-geographic filter retention, fresh row getter, selected Atlas profile focus and minified status equivalence');
}
test().catch(error=>{console.error(error);process.exitCode=1;});
