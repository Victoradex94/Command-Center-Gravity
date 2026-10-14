const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),window={};
for(const f of ['atlas','canonical-research','national-directory','directory-expansion','atlas-audit','entry-status','nigeria-states','nigeria-states-map','atlas-icons','entry-schema','directory'])vm.runInNewContext(fs.readFileSync('dist/'+f+'.js','utf8'),{window});
const {rows,edges}=window.PoeticsDirectoryData,by=id=>rows.find(r=>r.id===id);
assert(rows.length>=341);assert(edges.length>=534);
assert.equal(new Set(rows.map(r=>r.id)).size,rows.length);
for(const r of rows){for(const field of ['name','category','type','description','location','dates','dateMeaning','verification','activity'])assert(r.standardEntry[field],r.id+': '+field);assert(Array.isArray(r.standardEntry.sources));}
for(const e of edges){assert(by(e.a));assert(by(e.b));assert(e.url&&e.status);}
for(const id of ['cross-event-5','ccpc-benin-2023','ccpc-ph-2023','ccpc-ikot-2023','ccpc-yenagoa-2023','ccpc-issele-2023']){
 const r=by(id);assert.equal(r.eventEvidence,'Announced; occurrence unverified');assert.equal(r.dateFact.label,'Scheduled');assert(!r.historical);assert.notEqual(r.activityStatus.label,'Active');
 for(const e of edges.filter(e=>e.a===id&&!e.association))assert(/announc/i.test(e.label+e.status));
}
const proposal=by('ccpc-orerokpe-proposal');assert(proposal.dateFact.value.includes('inferred'));assert(!proposal.historical&&!proposal.upcoming);assert.notEqual(proposal.activityStatus.label,'Active');
assert(by('salome-ikokoyo')&&by('salomi-ikoyoko'));assert(!edges.some(e=>[e.a,e.b].includes('salome-ikokoyo')&&[e.a,e.b].includes('salomi-ikoyoko')));
const gombe=by('ccpc-gsu-speech');assert.equal(gombe.dateFact.label,'Speech publication');assert(gombe.dateBasis.includes('Event day, room and edition year are unresolved'));
assert(!edges.some(e=>e.a==='abdulbaki-speech'&&e.b==='cross-event-0'));assert(!edges.some(e=>e.a==='ccpc-gsu-speech'&&e.b==='cross-venue-0'));
assert(!edges.some(e=>e.a==='bots-contest-2025'&&/winner/i.test(e.label)));assert(by('bots-2025').sourceVariants.venue.includes('Edo Innovation Hub'));
for(const id of ['izuma','ash-flakes','oil-lamp'])assert.equal(by(id).category,'Publications');assert(by('izuma').dateBasis.includes('not the publication year'));assert.equal(by('oil-lamp').dateFact.value,'2005');assert.equal(by('ash-flakes').dateFact.value,'December 2008');assert(by('oil-lamp').gaps.includes('82'));assert(by('ash-flakes').gaps.includes('unverified')); 
assert(!edges.some(e=>e.a==='ogaga-ifowodo'&&e.b==='dlf-world-poetry-2024'&&/attend|perform|reader/.test(e.label)));
assert(by('dlf-world-poetry-2024').eventEvidence.includes('insider'));
for(const state of ['Bayelsa','Delta','Edo','Rivers','Akwa Ibom','Cross River'])assert(rows.some(r=>window.PoeticsStateMap.statesForRecord(r).includes(state)));
assert(window.PoeticsStateMap.statesForRecord(proposal).includes('Delta'));
const m=JSON.parse(fs.readFileSync('research/south-south-search-matrix.json'));
assert.equal(m.groups.length,13);assert.equal(m.groups.flatMap(x=>x.queries).length,52);for(const g of m.groups)assert(g.negativeYield);
console.log('PASS retained South South baseline identities and sourced links, standard fields, all South South states, announcement/held separation, uncertain dates and aliases, anthology metadata and 52-query yield ledger.');
