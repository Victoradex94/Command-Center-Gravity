const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const path=require('node:path');const dist=path.join(__dirname,'dist');
const files=['atlas','canonical-research','national-directory','directory-expansion','nigeria-boundary','nigeria-map','nigeria-states','nigeria-states-map','atlas-icons','atlas-audit','entry-status','entry-schema','directory'];
const sources=files.map(f=>fs.readFileSync(path.join(dist,f+'.js'),'utf8'));
function harness(){
 const w={location:{hash:'#/atlas'}},ctx={window:w};for(const s of sources)vm.runInNewContext(s,ctx);
 let html='',controls={};const noop=()=>{};const root={classList:{add:noop},set innerHTML(s){html=s;controls={};},get innerHTML(){return html;},querySelector(s){return controls[s]||(controls[s]={focus:noop,setSelectionRange:noop,scrollIntoView:noop,setAttribute:noop});},querySelectorAll(){return[];}};
 const record=w.PoeticsDirectoryData.rows.find(r=>r.id==='graciano');assert(record,'known profile must exist');
 w.PoeticsAtlasNavigation={read:()=>({mode:'Directory',query:'',selected:record.id,enabled:['People','Places','Platforms','Prizes','Publications'],state:'All states',zone:'All zones',geo:'All places',year:'All years',activity:'All formats',browsing:true}),commit:noop};
 return {w,root,record,controls:()=>controls,html:()=>html};
}
const unsafe=['javascript:alert(1)','JaVaScRiPt:alert(1)',' \u0000\tjavascript:alert(1)','java\tscript:alert(1)','java\nscript:alert(1)','java\rscript:alert(1)','data:text/html,<script>alert(1)</script>','vbscript:msgbox(1)','unknown:payload'];
const safe=['https://example.com/a b?q=a:b&x=2','http://example.com','mailto:poet@example.com','tel:+23412345','//example.com/path','./page.json','/page?q=a:b','./folder/a:b','#section:one',''];
const decode=s=>s.replace(/&(?:amp|lt|gt|quot|#39);/g,x=>({'&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&#39;':"'"}[x]));
let failures=[];
for(const input of [...unsafe,...safe]){
 const t=harness();t.record.media=[{url:input,sourceURL:input,caption:'security case',credit:'review'}];t.w.renderDirectory(t.root);
 const m=t.html().match(/<a class="profile-photo [^"]*" href="([^"]*)"[^>]*><img src="([^"]*)"/);assert(m,'selected media sink rendered');
 const expected=unsafe.includes(input)?'#':input;
 for(const raw of m.slice(1)){
  const value=decode(raw);if(value!==expected)failures.push({input,expected,actual:value});
  assert(['http:','https:','mailto:','tel:'].includes(new URL(value,'https://review.example/').protocol),'browser-normalised protocol must be safe');
 }
}
for(const payload of ['"><script>alert(1)</script>','" autofocus onfocus="alert(1)','<img src=x onerror=alert(1)>']){
 const t=harness();t.w.renderDirectory(t.root);t.controls()['#directory-query'].oninput({target:{value:payload,selectionStart:payload.length}});
 assert(t.html().includes('id="directory-query" value=""'));assert.equal(t.controls()['#directory-query'].value,payload);
}
console.log(JSON.stringify({cases:unsafe.length+safe.length,queryCases:3,failures},null,2));assert.equal(failures.length,0,'all safe values must survive unchanged');
console.log('PASS independent fresh-harness security matrix and URL protocol parsing');
