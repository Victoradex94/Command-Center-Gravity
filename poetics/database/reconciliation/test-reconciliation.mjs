import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
const r=JSON.parse(fs.readFileSync(new URL('./reconciliation-report.json',import.meta.url)));
assert.equal(r.base.rows,449);assert.equal(r.current.rows,453);assert.equal(r.base.edges,664);assert.equal(r.current.edges,667);
assert.equal(r.changedExistingNodeIds.length,0);assert.equal(r.removedNodeIds.length,0);assert.equal(r.missingExistingEdges.length,0);assert(r.aliasesExact);
assert.equal(r.movedExistingEdges.length,235);assert.equal(r.addedEdges.length,3);assert(r.addedEdges.every(e=>e.subject==='yopafest-2021'));assert.equal(r.addedSourceUrls.length,1);
const sql=fs.readFileSync(new URL('./007_apply_verified_graph_delta.sql',import.meta.url),'utf8').replace(/--[^\n]*/g,'');
assert(!/\b(UPDATE|DELETE|ALTER|GRANT|REVOKE)\b/i.test(sql));assert(sql.includes('EXCEPT ALL'));assert(sql.includes('BEGIN;')&&sql.includes('COMMIT;'));assert(sql.includes('RAISE EXCEPTION'));assert(sql.includes(r.provenance.capture.sha256));
// Content-multiset subtraction distinguishes insertion/reordering from changes.
function delta(a,b){const key=x=>JSON.stringify(x),m=new Map();for(const e of a)m.set(key(e),(m.get(key(e))||0)+1);const add=[];for(const e of b){const k=key(e),n=m.get(k)||0;if(n)m.set(k,n-1);else add.push(e);}return{add,missing:[...m].filter(([k,n])=>n>0)};}
assert.deepEqual(delta([{id:'a'},{id:'b'}],[{id:'new'},{id:'b'},{id:'a'}]),{add:[{id:'new'}],missing:[]});assert.equal(delta([{id:'a'},{id:'a'}],[{id:'a'}]).missing[0][1],1);
if(process.argv[2]){const bytes=fs.readFileSync(process.argv[2]);assert.equal(bytes.length,r.provenance.capture.bytes);assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),r.provenance.capture.sha256);const p=JSON.parse(bytes);assert.equal(p.sourceCommit,r.provenance.currentCommit);assert.equal(p.rows.length,453);assert.equal(p.edges.length,667);}
console.log('PASS source counts, unchanged identities, content-multiset matching, ordinal-shift detection, capture integrity and no destructive/permission SQL. SQL execution remains untested.');
