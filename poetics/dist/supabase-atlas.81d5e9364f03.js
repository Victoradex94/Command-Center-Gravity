'use strict';
(function(){
const config={url:'https://tknahlnirtnanzqqvufb.supabase.co',key:'sb_publishable_UPiYBIuJMZlcIP3z3asP7Q_oZ2gWUb-'};
async function rpc(name,body){const response=await fetch(config.url+'/rest/v1/rpc/'+name,{method:'POST',headers:{apikey:config.key,Authorization:'Bearer '+config.key,'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(body||{})});if(!response.ok)throw Error('Supabase request failed ('+response.status+').');return response.json();}
let readPromise;
window.PoeticsSupabaseAtlas={read(){if(!readPromise)readPromise=rpc('read_poetics_atlas_snapshot').then(snapshot=>{if(!snapshot||!Array.isArray(snapshot.rows)||!Array.isArray(snapshot.edges))throw Error('Unexpected Atlas response.');return snapshot;}).catch(error=>{readPromise=null;throw error;});return readPromise;},submit(payload){return rpc('submit_poetics_atlas_record',{p_submission:payload});}};
})();
