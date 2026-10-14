import fs from 'node:fs';import vm from 'node:vm';import crypto from 'node:crypto';
const [dir,commit,out]=process.argv.slice(2);if(!dir||!/^[a-f0-9]{40}$/.test(commit||'')||!out)throw Error('Use source directory, exact commit, output path');
const window={};for(const f of ['atlas','canonical-research','national-directory','directory-expansion','atlas-audit','entry-status','nigeria-states','nigeria-states-map','atlas-icons','entry-schema','directory'])vm.runInNewContext(fs.readFileSync(dir+'/'+f+'.js','utf8'),{window});
const payload={sourceCommit:commit,rows:window.PoeticsDirectoryData.rows,edges:window.PoeticsDirectoryData.edges};
const bytes=Buffer.from(JSON.stringify(payload)+'\n');fs.writeFileSync(out,bytes);console.log(JSON.stringify({file:out,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex'),rows:payload.rows.length,edges:payload.edges.length}));
