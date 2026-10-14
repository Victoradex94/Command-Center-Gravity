const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),window={};for(const f of ['atlas','canonical-research','national-directory','directory-expansion','atlas-audit','entry-status','nigeria-states','nigeria-states-map','atlas-icons','entry-schema','directory'])vm.runInNewContext(fs.readFileSync('dist/'+f+'.js','utf8'),{window});
const {rows,edges}=window.PoeticsDirectoryData,by=id=>rows.find(r=>r.id===id);assert(rows.length>=421);assert(edges.length>=627);
assert(by('ccpc-abeokuta-2024').historical);assert(!by('ccpc-abeokuta-2024').dateFact);assert(by('ccpc-abeokuta-2024').dateBasis.includes('exact event day not stated'));
assert.equal(by('ccpc-ojokoro-2024').eventEvidence,'Announced; occurrence unverified');assert(!by('ccpc-ojokoro-2024').historical);assert.notEqual(by('ccpc-ojokoro-2024').activityStatus.label,'Active');
assert.equal(rows.filter(r=>r.id==='nwuguru-chidiebere').length,1);assert(by('nwuguru-chidiebere').nameVariants.includes('Chidiebere Nwuguru'));assert.equal(by('ccpc-abakaliki-2023').eventEvidence,'Announced; occurrence unverified');
assert(edges.some(e=>e.a==='nwuguru-chidiebere'&&e.b==='uncanny-58'&&e.status==='Publisher table of contents'));assert.equal(by('rhapsodies-corper').dateFact.value,'1998');
assert(!edges.some(e=>e.a==='ana-abia-yusuf-2019'&&e.b==='abia-hotels-aba'));assert(by('ana-abia-yusuf-2019').dateBasis.includes('Intellectual Giant'));assert(!by('ana-abia-yusuf-2019').dateBasis.includes('₦'));assert(by('ana-abia-yusuf-2019').verification.sourceURL.endsWith('#page=25'));
assert(by('ana-abia-august-2024').eventEvidence.includes('single newspaper'));
console.log('PASS held/announced separation, exact-day uncertainty, identity and publisher links, withdrawn Abia metadata and access-limited lead exclusion.');
