const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const index=fs.readFileSync('dist/index.html','utf8');
const previous=fs.readFileSync('dist/atlas-preview-59.html','utf8');
const names=h=>[...h.matchAll(/<script src="([^"]+)"([^>]*)>/g)];
const plain=s=>s.replace(/\.[a-f0-9]{12}(?=\.js$)/,'');
assert.deepEqual(names(index).map(m=>plain(m[1])),names(previous).map(m=>plain(m[1])));
for(const m of names(index)){assert(m[2].includes('defer'));assert(!m[2].includes('async'));}
let checked=0;
for(const m of names(index)){
 const original=fs.readFileSync('dist/'+plain(m[1]),'utf8');
 if(!/^window\.\w+\s*=/.test(original))continue;
 const a={window:{}},b={window:{}};
 try{vm.runInNewContext(original,a);vm.runInNewContext(fs.readFileSync('dist/'+m[1],'utf8'),b)}catch{continue}
 assert.equal(JSON.stringify(a.window),JSON.stringify(b.window));checked++;
}
assert(checked>=4);
const bytes=h=>[...h.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g)].reduce((n,m)=>n+fs.statSync('dist/'+m[1]).size,0);
assert(bytes(index)<bytes(previous));
console.log(JSON.stringify({status:'PASS',dataAssignmentsEqual:checked,previousBytes:bytes(previous),currentBytes:bytes(index),savedBytes:bytes(previous)-bytes(index),scope:'Uncompressed local asset bytes; not network timing or rendered QA'}));
