import { Pool } from 'jsr:@db/postgres@^0';
import { createHandler } from './handler.mjs';
import { queries } from './queries.mjs';

// No fallback to an administrator connection or service-role API key.
const dbUrl=Deno.env.get('POETICS_READ_DB_URL');
const pool=dbUrl?new Pool(dbUrl,1,true):null;
const handler=createHandler({tokenHash:Deno.env.get('POETICS_ACTION_TOKEN_SHA256'),read:async(resource:string,p:Record<string,unknown>)=>{
  if(!pool)throw new Error('No reader connection');
  const spec=queries[resource as keyof typeof queries],connection=await pool.connect();
  let started=false;
  try {
    await connection.queryArray('BEGIN READ ONLY');started=true;
    await connection.queryArray("SET LOCAL statement_timeout='3000ms'");
    const result=await connection.queryObject(spec.text,spec.args(p));
    await connection.queryArray('COMMIT');started=false;
    return result.rows;
  } finally {
    if(started)try{await connection.queryArray('ROLLBACK');}catch{/* Do not expose driver errors. */}
    connection.release();
  }
}});
Deno.serve(handler);
