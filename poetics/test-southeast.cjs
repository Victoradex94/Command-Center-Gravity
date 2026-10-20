const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),window={};
for(const f of ['atlas','canonical-research','national-directory','directory-expansion','atlas-audit','entry-status','nigeria-states','nigeria-states-map','atlas-icons','entry-schema','directory'])vm.runInNewContext(fs.readFileSync('dist/'+f+'.js','utf8'),{window});
const {rows,edges}=window.PoeticsDirectoryData,by=id=>rows.find(r=>r.id===id);
assert(rows.length>=400);assert(edges.length>=596);
for(const [state,n] of Object.entries({Abia:25,Ebonyi:19,Imo:18,Delta:16,Gombe:11,Edo:13}))assert.equal(rows.filter(r=>window.PoeticsStateMap.statesForRecord(r).includes(state)).length,n);
for(const id of ['ana-abia-april-2026','abakaliki-love-2018','ebonyi-literary-evening-2026','ana-imo-igbo-poetry-2025']){assert.equal(by(id).eventEvidence,'Announced; occurrence unverified');assert(!by(id).historical);assert.notEqual(by(id).activityStatus.label,'Active');}
assert(!window.PoeticsStateMap.statesForRecord(by('ebonyi-literary-evening-2026')).length);
assert(by('ebonyi-laureates-book-club').dateBasis.includes('physical/online'));
assert.equal(rows.filter(r=>window.PoeticsStateMap.statesForRecord(r).includes('Ebonyi')&&r.historical).length,1);assert(by('grains-unveiling-2022').historical);
assert(by('chukwubuike-launch-2022').dateBasis.includes('exact event date not normalized'));
assert(!by('tranquillity-turbulence').years.length);
for(const id of ['jangolova','wriggling-freedom'])assert(by(id).dateBasis.includes('original publication year'));
assert(edges.some(e=>e.a==='aba-story-2018'&&by(e.b).name==='Dike Chukwumerije'));
assert(!edges.some(e=>e.a==='aba-festival-2019'&&e.b==='aba-museum'));
assert(!edges.some(e=>e.a==='ana-imo-poetry-2024'&&/winner/i.test(e.label)));
const m=JSON.parse(fs.readFileSync('research/southeast-search-matrix.json'));assert.equal(m.groups.length,11);assert.equal(m.groups.flatMap(g=>g.queries).length,44);for(const g of m.groups){assert(g.negativeYield);for(const q of g.queries)assert(q.q&&q.yieldNote&&q.status);}
console.log('PASS southeast counts, role-specific connections, announcement/held separation, online geography, unknown metadata and 44-query ledger.');

assert(by('fr-njoku-poetry-2020').historical);assert(edges.some(e=>e.a==='nnenna-ihebom'&&e.b==='fr-njoku-poetry-2020'&&e.label==='winner reported'));assert(!by('ccpc-abakaliki-2023').historical);assert(!by('abakaliki-spoken-festival-2025').historical);

assert(by('ana-abia-okara-2019').historical);assert.equal(by('ana-abia-yusuf-2019').dateFact.value,'5 July 2019');assert(!rows.some(r=>r.name==='ANA Abia Anthology'));

assert(by('grains-journal').dateBasis.includes('chronology unresolved'));assert.equal(by('grains-unveiling-2022').dateFact.value,'14 July 2022');assert(!by('ae-funai').eventEvidence);
