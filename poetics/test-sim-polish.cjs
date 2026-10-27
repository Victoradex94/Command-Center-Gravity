const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function harness(){
 const listeners=new Map(),timeouts=new Map();let next=0,reduced=false;
 const button={textContent:'',setAttribute(k,v){this[k]=v}},window={document:{querySelector:()=>button},matchMedia:()=>({matches:reduced}),addEventListener(k,f){if(!listeners.has(k))listeners.set(k,new Set());listeners.get(k).add(f)},removeEventListener(k,f){listeners.get(k)?.delete(f)}};
 const context=vm.createContext({window,console,setTimeout(f,ms){const id=++next;timeouts.set(id,{f,ms});return id},clearTimeout(id){timeouts.delete(id)}});
 vm.runInContext(fs.readFileSync('dist/atlas-input.js','utf8'),context,{filename:'atlas-input.js'});
 vm.runInContext(fs.readFileSync('dist/living-sim.js','utf8'),context);
 return {S:window.PoeticsLivingSim,window,button,timeouts,setReduced:v=>reduced=v,route(){for(const f of [...(listeners.get('hashchange')||[])])f()},finish(){for(const [id,t] of [...timeouts]){timeouts.delete(id);t.f()}}};
}
async function run(){
 const app=fs.readFileSync('dist/app.js','utf8');assert(!/\u00c3\u00a2|\u00c3\u201a|\u00c3\u00b0|\u00c3\u0192/.test(app),'in-game copy contains corrupted UTF-8');assert(app.includes('₦450'));assert(app.includes('Vic’Adex concept'));assert(app.includes('Loading Atlas data from Supabase…'));
 const h=harness(),S=h.S,baseline=JSON.stringify([S.cityLayouts,S.venueArchivalData,S.simulatedPoets,S.conveningCalendar]);
 const ids=['freedom-park','sifax','lautech-gate','under-g','muson','merit-house','alliance-jos'];
 const svgIds=new Set();
 for(const id of ids){
  const day=S.renderVenueVignette(id,0),night=S.renderVenueVignette(id,2);
  assert(day.includes('data-sim-phase="day"'));assert(night.includes('data-sim-phase="night"'));
  assert(day.includes('scene-'+id+'-brick-pattern'));assert(day.includes('prefers-reduced-motion'));
  assert(day.includes(S.venueArchivalData[id].name));assert.equal(day,S.renderVenueVignette(id,0));
  for(const match of day.matchAll(/\bid="([^"]+)"/g)){assert(!svgIds.has(match[1]),'cross-venue SVG ID collision');svgIds.add(match[1])}
 }
 assert(S.renderVenueVignette('sifax',1).includes('data-sim-phase="dusk"'));
 const coords={Lagos:{lat:6.5244,lon:3.3792},Ibadan:{lat:7.3775,lon:3.9470},Abuja:{lat:9.0765,lon:7.3986}};
 const bus=S.getTransitAnimation('Lagos','Ibadan',coords),plane=S.getTransitAnimation('Lagos','Abuja',coords);
 assert.equal(bus.isPlane,false);assert.equal(bus.vehicle,'🚌');assert(bus.distanceKm>100&&bus.distanceKm<150);assert.equal(plane.isPlane,true);
 assert.equal(S.getTransitAnimation('Unknown','Abuja',coords).fromCoords,null);
 assert.equal(S.getTransitAnimation('Lagos','Abuja',{...coords,Lagos:{lat:Infinity,lon:3}}).distanceKm,null);
 assert(plane.transitHtml.includes('Fictional travel encounter'));assert(plane.transitHtml.includes('not navigation directions'));
 const map=S.renderCityMiniMap('Lagos',null,plane);
 assert(map.includes('sim-transit-route'));
 assert(map.includes('class="sim-transit-vehicle"'));
 assert(map.includes('city-centre distance is not a road route'));
 assert(!map.includes('sim-venue-node'),'transit rendering does not place unverified venue coordinates');
 const nodes={'#sim-mini-map-view':{innerHTML:''},'#sim-transit-banner':{innerHTML:''}},root={querySelector:s=>nodes[s]||null};
 let resolved=false;const transit=S.animateTravel(root,'Lagos','Abuja',coords).then(()=>resolved=true);
 assert(nodes['#sim-mini-map-view'].innerHTML.includes('sim-transit-vehicle'));await Promise.resolve();assert(!resolved);assert.equal([...h.timeouts.values()][0].ms,3000);
 h.route();await transit;assert(resolved);assert.equal(h.timeouts.size,0);
 h.setReduced(true);const reduced=S.animateTravel(root,'Lagos','Abuja',coords);assert.equal([...h.timeouts.values()][0].ms,0);h.finish();await reduced;
 assert.equal(JSON.stringify([S.cityLayouts,S.venueArchivalData,S.simulatedPoets,S.conveningCalendar]),baseline,'decorative features changed archival data');
 let created=0,closed=0,stopped=0,audible=0,resume;
 class Context{
  constructor(){created++;this.currentTime=0;this.destination={}}
  createGain(){return {gain:{setValueAtTime(){},setTargetAtTime(v){assert(v<=.01);audible++}},connect(){}}}
  createOscillator(){return {frequency:{setValueAtTime(){}},connect(){},start(){},stop(){stopped++},disconnect(){}}}
  resume(){return new Promise(r=>resume=r)}close(){closed++;return Promise.resolve()}
 }
 h.window.AudioContext=Context;assert.equal(created,0,'audio starts without gesture');
 const pending=S.toggleAudio(h.button);assert.equal(created,1);assert.equal(audible,0);
 await S.toggleAudio(h.button);assert.equal(closed,1);assert.equal(stopped,2);resume();await pending;assert.equal(audible,0,'stale resume unmuted audio');
 const active=S.toggleAudio(h.button);resume();await active;assert.equal(audible,1);h.route();assert.equal(closed,2);assert.equal(h.button['aria-pressed'],'false');S.stopAudio();assert.equal(closed,2);
 h.window.AudioContext=class extends Context{resume(){return Promise.reject(new Error('denied'))}};await S.toggleAudio(h.button);assert.equal(closed,3);assert.equal(h.button.textContent,'Ambient sound unavailable');
 delete h.window.AudioContext;await S.toggleAudio(h.button);assert.equal(created,3);
 console.log('PASS sim polish: seven deterministic culturally preserved facades, unique IDs, day/dusk/night, city-centre travel card, cancellation/reduced motion, immutable archive, opt-in audio and resume/route/failure races.');
}
run().catch(e=>{console.error(e);process.exitCode=1});
