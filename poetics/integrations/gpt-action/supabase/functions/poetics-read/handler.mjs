const categories = new Set(['People','Places','Platforms','Prizes','Publications']);
const headers = {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const json = (body,status=200) => new Response(JSON.stringify(body),{status,headers});
async function authorized(request,expected) {
  if (!/^[a-f0-9]{64}$/.test(expected||'')) return false;
  const auth=request.headers.get('authorization')||'';
  if (!auth.startsWith('Bearer ')||auth.length<39||auth.length>520) return false;
  const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(auth.slice(7))));
  let mismatch=0;for(let i=0;i<32;i++)mismatch|=digest[i]^parseInt(expected.slice(i*2,i*2+2),16);
  return mismatch===0;
}
export function createHandler({tokenHash,read}) {
  return async request => {
    if (!/^[a-f0-9]{64}$/.test(tokenHash||'')) return json({error:'Reader not configured'},503);
    if (!await authorized(request,tokenHash)) return json({error:'Unauthorized'},401);
    if (request.method!=='GET') return new Response(JSON.stringify({error:'Read-only endpoint'}),{status:405,headers:{...headers,Allow:'GET'}});
    const url=new URL(request.url),match=url.pathname.match(/^(?:\/functions\/v1)?\/poetics-read\/(nodes|connections|sources|ledger)\/?$/);
    if(!match)return json({error:'Not found'},404);
    const resource=match[1],allowed=new Set(['q','limit','offset',...(resource==='nodes'?['id','category']:resource==='connections'?['nodeId']:resource==='ledger'?['artifactId']:[])]);
    for(const key of url.searchParams.keys())if(!allowed.has(key)||url.searchParams.getAll(key).length!==1)return json({error:'Unsupported or repeated parameter'},400);
    const p=Object.fromEntries(url.searchParams);for(const key of ['q','id','nodeId','artifactId'])if((p[key]||'').length>200)return json({error:'Parameter too long'},400);
    const limit=p.limit===undefined?10:Number(p.limit),offset=p.offset===undefined?0:Number(p.offset);
    if(!Number.isInteger(limit)||limit<1||limit>20||!Number.isInteger(offset)||offset<0||offset>10000)return json({error:'Invalid pagination'},400);
    if(p.category&&!categories.has(p.category))return json({error:'Invalid category'},400);
    if(resource==='connections'&&!p.nodeId?.trim())return json({error:'nodeId is required'},400);
    if(resource==='ledger'&&!p.artifactId?.trim())return json({error:'artifactId is required; no implicit latest ledger'},400);
    try {
      const rows=await read(resource,{q:p.q||'',id:p.id||'',category:p.category||'',nodeId:p.nodeId||'',artifactId:p.artifactId||'',limit,offset});
      const body={resource,rows,limit,offset,returned:rows.length,hasMore:rows.length===limit,
        authority:'Private staging snapshot. Drive remains the current research ledger; do not assume this snapshot matches the published Atlas.'};
      if(new TextEncoder().encode(JSON.stringify(body)).length>64000)return json({error:'Result too large; reduce limit or narrow query'},413);
      return json(body);
    } catch {return json({error:'Staging read unavailable'},503);}
  };
}
