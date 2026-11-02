const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const noop=()=>{};
function harness(){
 let storageReads=0,atlasRenders=0,gameRenders=0;const scripts=[],controls={},snapshots=[],fallbackAtlas={records:[{id:'venue',name:'Sample Venue',type:'Venue',city:'Ibadan',year:2020,description:'A source-listed venue.',source:'archive'},{id:'platform',name:'Sample Platform',type:'Platform',city:'Lagos',year:2021,description:'A source-listed platform.',source:'archive'}],edges:[['venue','platform','listed by','archive',2021]],sources:{archive:{title:'Archive record',url:'https://example.test/archive',scope:'A bundled source; claim review remains pending.'}}};
 const main={innerHTML:'',classList:{remove:noop},focus:noop},toast={style:{}};
 const document={hidden:false,activeElement:null,querySelector:s=>s==='#main'?main:s==='#toast'?toast:(s==='#retry-games'||s==='#retry-atlas')?(controls.retry||(controls.retry={})):null,querySelectorAll:()=>[],addEventListener:noop,createElement:()=>({remove:noop}),head:{append:s=>scripts.push(s),appendChild:s=>{if(s.src)scripts.push(s)}}};
 const window={PoeticsSupabaseAtlas:{async read(){return {rows:[{id:'live',verification:'source',links:[],media:[],years:[]}],edges:[]}}},PoeticsAtlas:fallbackAtlas,PoeticsDirectoryData:{replaceSnapshot(snapshot){assert(snapshot.rows.every(r=>r.verification&&Array.isArray(r.links)&&Array.isArray(r.media)&&Array.isArray(r.years)));assert(snapshot.edges.every(e=>/^https:\/\//.test(e.url)));snapshots.push(snapshot);}},renderDirectory:()=>atlasRenders++,renderPoeticsAbout:noop,renderContribute:noop,addEventListener:noop,scrollTo:noop,matchMedia:()=>({matches:false})},location={hash:'#/atlas'};
 const context=vm.createContext({window,document,location,localStorage:{getItem:()=>{storageReads++;return null},setItem:noop},clearInterval,clearTimeout,setTimeout,setInterval,URLSearchParams});
 const run=f=>vm.runInContext(fs.readFileSync('dist/'+f,'utf8'),context);
 run('atlas-input.js');window.PoeticsAtlas=fallbackAtlas;run('game-assets.js');run('game-loader.js');run('app.js');context.countGame=()=>gameRenders++;vm.runInContext('games=()=>countGame();showLoginPortal=()=>countGame();renderGamesHub=()=>countGame();',context);
 return {window,location,context,scripts,main,controls,snapshots,run,counts:()=>({storageReads,atlasRenders,gameRenders}),route:hash=>{location.hash=hash;return vm.runInContext('route()',context)},finish:s=>{run(s.src);s.onload()}};
}
async function run(){
 const h=harness();await h.route('#/atlas');assert.equal(h.scripts.length,0);assert.equal(h.snapshots[0].rows[0].id,'live');assert.deepEqual(h.counts(),{storageReads:0,atlasRenders:1,gameRenders:0});
 const unavailable=harness();unavailable.window.PoeticsSupabaseAtlas.read=async()=>{throw Error('Offline')};await unavailable.route('#/atlas');assert.equal(unavailable.scripts.length,0);assert.equal(unavailable.snapshots.length,0);assert(unavailable.main.innerHTML.includes('The Atlas could not load'));
 const empty=harness();empty.window.PoeticsSupabaseAtlas.read=async()=>({rows:[],edges:[]});await empty.route('#/atlas');assert.equal(empty.snapshots.length,0);assert.equal(empty.scripts.length,0);assert(empty.main.innerHTML.includes('The Atlas could not load')); assert.equal(h.window.PoeticsGameAssets.length,7);assert(h.window.PoeticsGameAssets.some(x=>x.startsWith('living-sim.')));assert(h.window.PoeticsGameAssets.some(x=>x.startsWith('rhyme-game.')));
 const pending=h.route('#/games');assert.equal(h.scripts.length,7);assert(h.main.innerHTML.includes('Loading your poetry world'));
 h.route('#/atlas');for(const s of h.scripts)h.finish(s);await pending;assert.equal(h.counts().gameRenders,0);assert.equal(h.counts().storageReads,0);
 await h.route('#/games');assert.equal(h.counts().gameRenders,1);assert.equal(h.counts().storageReads,1);assert.equal(h.scripts.length,7);assert(!h.scripts.some(s=>s.src===h.window.PoeticsLazyAssets['rhyme-lexicon']));
 const lexiconPending=h.window.PoeticsLoadAsset('rhyme-lexicon');assert.equal(h.scripts.length,8);assert.equal(h.scripts.at(-1).src,h.window.PoeticsLazyAssets['rhyme-lexicon']);h.finish(h.scripts.at(-1));await lexiconPending;
 await h.route('#/atlas');await h.route('#/games');assert.equal(h.scripts.length,8);assert.equal(h.counts().storageReads,1);
 const fail=harness(),attempt=fail.route('#/games');fail.scripts[0].onerror();for(const s of fail.scripts.slice(1))fail.finish(s);await attempt;assert(fail.main.innerHTML.includes('The Games could not load'));assert.equal(fail.counts().storageReads,0);
 const beforeRetry=fail.scripts.length,retry=fail.controls.retry.onclick();assert.equal(fail.scripts.length,beforeRetry+1);assert.equal(fail.scripts.at(-1).src,fail.scripts[0].src);fail.finish(fail.scripts.at(-1));await retry;assert.equal(fail.counts().gameRenders,1);assert.equal(fail.counts().storageReads,1);
 const submit=harness(),contribute=submit.window.PoeticsLazyAssets.contribute;assert(contribute);const submitPending=submit.route('#/submit');assert.equal(submit.scripts.length,1);assert.equal(submit.scripts[0].src,contribute);submit.finish(submit.scripts[0]);submit.window.renderContribute=()=>{submit.main.innerHTML='SUBMIT READY';};await submitPending;assert.equal(submit.main.innerHTML,'SUBMIT READY');
 for(const hash of ['#/about','#/archive','#/research']){
  const fresh=harness();delete fresh.window.renderPoeticsAbout;
  const loading=fresh.route(hash);assert.equal(fresh.scripts.length,1);assert.equal(fresh.scripts[0].src,fresh.window.PoeticsLazyAssets.contribute);
  assert(fresh.main.innerHTML.includes('Loading project information'));
  fresh.finish(fresh.scripts[0]);fresh.window.renderPoeticsAbout=()=>{fresh.main.innerHTML='ABOUT READY';};await loading;
  assert.equal(fresh.main.innerHTML,'ABOUT READY');assert.equal(fresh.counts().storageReads,0);
 }
 const stale=harness(),waiting=stale.route('#/about');await stale.route('#/atlas');stale.finish(stale.scripts[0]);stale.window.renderPoeticsAbout=()=>{throw Error('stale route rendered');};await waiting;
 console.log('PASS lazy routes including fresh About/Archive/Research, dependency loading and cancellation.');
}
run().catch(e=>{console.error(e);process.exitCode=1});
