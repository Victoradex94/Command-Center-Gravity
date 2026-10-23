const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const noop=()=>{};
function harness(){
 let storageReads=0,atlasRenders=0,gameRenders=0;const scripts=[],controls={};
 const main={innerHTML:'',classList:{remove:noop},focus:noop},toast={style:{}};
 const document={hidden:false,activeElement:null,querySelector:s=>s==='#main'?main:s==='#toast'?toast:(s==='#retry-games'||s==='#retry-atlas')?(controls.retry||(controls.retry={})):null,querySelectorAll:()=>[],addEventListener:noop,createElement:()=>({remove:noop}),head:{append:s=>scripts.push(s)}};
 const window={Poetics3D:{position:()=>({x:0,z:0})}, PoeticsSupabaseAtlas:{async read(){return {rows:[],edges:[]}}},PoeticsDirectoryData:{replaceSnapshot:noop},renderDirectory:()=>atlasRenders++,renderPoeticsAbout:noop,renderContribute:noop,addEventListener:noop,scrollTo:noop,matchMedia:()=>({matches:false})},location={hash:'#/atlas'};
 const context=vm.createContext({window,document,location,localStorage:{getItem:()=>{storageReads++;return null},setItem:noop},clearInterval,clearTimeout,setTimeout,setInterval,URLSearchParams});
 const run=f=>vm.runInContext(fs.readFileSync('dist/'+f,'utf8'),context);
 run('game-assets.js');run('game-loader.js');run('app.js');context.countGame=()=>gameRenders++;vm.runInContext('games=()=>countGame();',context);
 return {window,location,context,scripts,main,controls,run,counts:()=>({storageReads,atlasRenders,gameRenders}),route:hash=>{location.hash=hash;return vm.runInContext('route()',context)},finish:s=>{run(s.src);s.onload()}};
}
async function run(){
 const h=harness();await h.route("#/atlas");assert.equal(h.scripts.length,0);assert.deepEqual(h.counts(),{storageReads:0,atlasRenders:1,gameRenders:0});
 const pending=h.route('#/games');assert.equal(h.scripts.length,5);assert(h.main.innerHTML.includes('Loading your poetry world'));
 h.route('#/atlas');for(const s of h.scripts)h.finish(s);await pending;assert.equal(h.counts().gameRenders,0);assert.equal(h.counts().storageReads,0);
 await h.route('#/games');assert.equal(h.counts().gameRenders,1);assert.equal(h.counts().storageReads,1);assert.equal(h.scripts.length,5);
 await h.route('#/atlas');await h.route('#/games');assert.equal(h.scripts.length,5);assert.equal(h.counts().storageReads,1);
 const fail=harness(),attempt=fail.route('#/games');fail.scripts[0].onerror();for(const s of fail.scripts.slice(1))fail.finish(s);await attempt;assert(fail.main.innerHTML.includes('The Games could not load'));assert.equal(fail.counts().storageReads,0);
 const retry=fail.controls.retry.onclick();assert.equal(fail.scripts.length,6);assert.equal(fail.scripts[5].src,fail.scripts[0].src);fail.finish(fail.scripts[5]);await retry;assert.equal(fail.counts().gameRenders,1);assert.equal(fail.counts().storageReads,1);
 console.log('PASS real lazy-loader/app route in VM: zero Games requests/save reads on Atlas, parallel ordered assets, pending navigation cancellation, one-time save restoration, warm return, load error and narrow retry. Not a browser test.');
}
run().catch(e=>{console.error(e);process.exitCode=1});
