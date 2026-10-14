const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),window={};
for(const f of ['atlas','canonical-research','national-directory','directory-expansion','atlas-audit','entry-status','nigeria-states','nigeria-states-map','atlas-icons','entry-schema','directory'])vm.runInNewContext(fs.readFileSync('dist/'+f+'.js','utf8'),{window});
const {rows,edges}=window.PoeticsDirectoryData,by=id=>rows.find(r=>r.id===id);
assert(rows.length>=409);assert(edges.length>=606);
assert.equal(rows.filter(r=>window.PoeticsStateMap.statesForRecord(r).includes('Kogi')).length,3);
assert.equal(by('ccpc-lokoja-2024').dateFact.value,'26 October 2024');assert(by('ccpc-lokoja-2024').eventEvidence.includes('single report family'));
assert(!edges.some(e=>[e.a,e.b].includes('ccpc-lokoja-2024')&&/2023/.test(String(e.date))));
assert(!edges.some(e=>e.a==='ccpc-lokoja-2024'&&/host/.test(e.label)));
assert.equal(by('ansa').city,'Nigeria');assert.equal(by('penkup-international').city,'Nigeria');assert(!by('dont-love-yourself').years.length);
assert.equal(rows.filter(r=>r.id==='ccpc-awka-2023').length,1);assert.equal(by('ccpc-awka-2023').dateFact.value,'October 2023');
assert(by('uche-nnyagu').verification.sourceURL.endsWith('/NAU4594'));
assert(edges.some(e=>e.a==='vincent-eze-awka'&&e.b==='ccpc-awka-2023'&&e.status.includes('not verified')));
assert.equal(by('ccpc-abakaliki-2023').eventEvidence,'Announced; occurrence unverified');
assert(!edges.some(e=>e.a==='ccpc-gsu-speech'&&e.b==='cross-event-0'));
const m=JSON.parse(fs.readFileSync('research/kogi-awka-search-matrix.json'));assert.equal(m.groups.flatMap(g=>g.queries).length,12);for(const g of m.groups){assert(g.negativeYield);for(const q of g.queries)assert(q.q&&q.yieldNote);}
console.log('PASS Kogi mapped counts and single-family provenance, no 2023 merge/host inference, corrected Awka access, planned host role and publication date uncertainty.');
