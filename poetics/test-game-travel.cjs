const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const noop=()=>{},elements=new Map(),timeouts=new Map();let next=0,renders=0,saves=0,travels=0;
function element(id){if(elements.has(id))return elements.get(id);const classes=new Set(),el={id,innerHTML:'',value:'',textContent:'',style:{setProperty:noop},dataset:{},classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x),toggle:noop},setAttribute:noop,removeAttribute:noop,focus:noop,appendChild:noop,insertBefore:noop,querySelector:()=>null,querySelectorAll:()=>[],click(){return this.onclick?.()},scrollIntoView:noop};el.parentElement=el;elements.set(id,el);return el}
const main=element('#main'),travel=element('travel'),circuit=element('circuit'),panel=element('#tab-circuit');travel.dataset.action='travel';circuit.dataset.tab='tab-circuit';
let mainHTML='';Object.defineProperty(main,'innerHTML',{get:()=>mainHTML,set(v){mainHTML=v;renders++;panel.classList.remove('active-panel')}});
main.querySelector=s=>s==='[data-tab="tab-circuit"]'?circuit:s==='#audio-toggle'?null:s==='#world-toggle'?null:elements.get(s)||null;
main.querySelectorAll=s=>s==='[data-action]'?[travel]:s==='.in-game-tab'?[circuit]:s==='.in-game-panel'?[panel]:[];
const document={hidden:false,head:{appendChild:noop},querySelector:s=>s==='#in-game-ui-styles'?{}:s==='.community'||s==='.player-avatar'?null:element(s),querySelectorAll:()=>[],addEventListener:noop,createElement:()=>element('created')};
const listeners=new Map(),window={addEventListener(k,f){if(!listeners.has(k))listeners.set(k,new Set());listeners.get(k).add(f)},removeEventListener(k,f){listeners.get(k)?.delete(f)},matchMedia:()=>({matches:false}),scrollTo:noop,PoeticsLoadGames:()=>new Promise(()=>{}),Poetics3D:{mount:noop,go:noop},PoeticsWorld:()=>'',PoeticsSupabaseAtlas:{async read(){return {rows:[{}],edges:[]}}},PoeticsDirectoryData:{replaceSnapshot:noop},renderDirectory:()=>{main.innerHTML='ATLAS'}};
const location={hash:'#/games'},context=vm.createContext({window,document,location,console,structuredClone,URLSearchParams,localStorage:{getItem:()=>null,setItem(){saves++}},setInterval:()=>1,clearInterval:noop,setTimeout(f,ms){const id=++next;timeouts.set(id,{f,ms});return id},clearTimeout:id=>timeouts.delete(id)});
const run=name=>vm.runInContext(fs.readFileSync('dist/'+name,'utf8'),context);run('atlas-input.js');run('engine.js');run('opportunities.js');run('living-sim.js');run('app.js');
const original=window.PoeticsEngine.act;window.PoeticsEngine.act=(g,t,a)=>{if(t==='travel')travels++;return original(g,t,a)};
vm.runInContext("initializeGame();game.city='Lagos';game.money=0;game.energy=100;games();",context);
element('#destination').value='Abuja';element('#poem').value='Test verse';element('#penname').value='Test poet';
async function test(){
 const beforeRender=renders;await travel.onclick();assert.equal(travels,1);assert.equal(saves,0);assert.equal(renders,beforeRender);assert.equal(element('#sim-transit-banner').innerHTML,'','failed travel rendered transit');
 vm.runInContext('game.money=5000;game.energy=100;',context);
 const origin=vm.runInContext('({money:game.money,energy:game.energy,day:game.day})',context),pending=travel.onclick();
 assert.equal(travels,2);assert.equal(saves,1);assert.equal(renders,beforeRender,'transit immediately redrew destination');assert(element('#sim-transit-banner').innerHTML.includes('Lagos → Abuja'));assert(element('#sim-mini-map-view').innerHTML.includes('sim-transit-vehicle'));
 await travel.onclick();assert.equal(travels,2,'repeat click charged twice');assert.equal(saves,1);
 for(const [id,t] of [...timeouts])if(t.ms===3000){timeouts.delete(id);t.f()}await pending;
 assert.equal(renders,beforeRender+1);assert(panel.classList.contains('active-panel'),'circuit was not restored after arrival');assert.equal(vm.runInContext('game.money',context),origin.money-600);assert.equal(vm.runInContext('game.city',context),'Abuja');
 element('#destination').value='Lagos';const cancelled=travel.onclick();location.hash='#/atlas';for(const f of [...listeners.get('hashchange')])f();await cancelled;await Promise.resolve();assert.equal(mainHTML,'ATLAS','late travel redrew games after route exit');assert.equal(vm.runInContext('gameBusy',context),false);
 console.log('PASS actual app travel lifecycle: rejected trip has no transit, successful trip charged/saved once, visible awaiting transit, repeated-click guard, circuit restoration and route-exit cancellation. DOM-stub integration, not browser rendering.');
}
test().catch(e=>{console.error(e);process.exitCode=1});
