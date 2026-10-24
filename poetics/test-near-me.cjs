const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('dist/near-me-radar.js','utf8'),boundary=fs.readFileSync('dist/nigeria-boundary.js','utf8');
const unescape=s=>s.replace(/&(?:amp|lt|gt|quot|#39);/g,x=>({'&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&#39;':"'"}[x]));
function harness(supported=true){
 const ids=new Map(),keys=new Set(),requests=[];let focused=null,writesAfterRemove=0;
 class Element{
  constructor(tag='div'){this.tagName=tag;this.nodes=new Map();this.dataset={};this.connected=true;this.html='';}
  set innerHTML(s){if(!this.connected)writesAfterRemove++;this.html=s;this.nodes.clear();}
  get innerHTML(){return this.html;}
  appendChild(e){if(e.id)ids.set(e.id,e);e.connected=true;}
  remove(){this.connected=false;if(this.id)ids.delete(this.id);}
  focus(){focused=this;}
  querySelector(s){if(!this.nodes.has(s))this.nodes.set(s,new Element());return this.nodes.get(s);}
  querySelectorAll(s){
   if(Array.isArray(this.nodes.get(s)))return this.nodes.get(s);
   const cls=s.slice(1),out=[];
   for(const m of this.html.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g)){
    if(!(m[1].match(/class="([^"]*)"/)?.[1].split(' ').includes(cls)))continue;
    const b=new Element('button');b.innerHTML=m[2];for(const d of m[1].matchAll(/data-([\w-]+)="([^"]*)"/g))b.dataset[d[1]]=unescape(d[2]);out.push(b);
   }
   if(out.length){this.nodes.set(s,out);return out;}
   for(const child of this.nodes.values())if(child instanceof Element)out.push(...child.querySelectorAll(s));
   return out;
  }
 }
 const trigger=new Element('button');ids.set('near-me-btn',trigger);
 const doc={getElementById:id=>ids.get(id)||null,createElement:tag=>new Element(tag),head:new Element(),body:new Element(),addEventListener:(type,f)=>{if(type==='keydown')keys.add(f);},removeEventListener:(type,f)=>{if(type==='keydown')keys.delete(f);}};
 const w={PoeticsAtlas:{placeCoordinates:{Lagos:{lat:6.454066,lon:3.394673,precision:'City-centre locator'},Abuja:{lat:9.05785,lon:7.49508,precision:'City-centre locator'}}}};
 w.PoeticsDirectoryData={rows:[...rows,{id:'poet-link',name:'Visiting Poet',category:'People'}],edges:[{a:'close',b:'poet-link',label:'advertised performance at',url:'https://example.test/evidence'}]};
 const nav=supported?{geolocation:{getCurrentPosition:(success,error,options)=>requests.push({success,error,options})}}:{};
 const context={window:w,document:doc,navigator:nav};vm.runInNewContext(boundary,context);vm.runInNewContext(code,context);
 return {w,doc,ids,keys,requests,trigger,focused:()=>focused,writes:()=>writesAfterRemove,container:()=>ids.get('nm-container')};
}
const point=(latitude=6.454066,longitude=3.394673)=>({coords:{latitude,longitude}});
const rows=[
 {id:'event',name:'Spoken event',category:'Prizes',format:'Spoken-word competition',city:'Lagos'},
 {id:'far',name:'Far venue',category:'Places',latitude:6.8,longitude:3.4,coordinatePrecision:'Venue address'},
 {id:'close',name:'<img src=x onerror=alert(1)>',category:'Platforms',latitude:6.46,longitude:3.4,coordinatePrecision:'Exact venue'},
 {id:'city',name:'City estimate',category:'Places',city:'Lagos'},
 {id:'unknown',name:'Unlocated',category:'Platforms',city:'Unknown'},
 {id:'person',name:'Person',category:'People',city:'Lagos'},
 {id:'locator',name:'City locator',category:'Places',placeType:'City',city:'Lagos'}
];
{
 const h=harness();assert.equal(h.requests.length,0,'module load must not request location');assert.equal(h.ids.has('nm-styles'),false);
 assert.equal(h.w.PoeticsNearMe.haversine(0,0,0,0),0);assert(Math.abs(h.w.PoeticsNearMe.haversine(0,0,0,1)-111.1949)<.01);
 assert.equal(h.w.PoeticsNearMe.haversine(4,5,7,8),h.w.PoeticsNearMe.haversine(7,8,4,5));
}
for(const outcome of ['success','error']){
 const h=harness();h.w.PoeticsNearMe.init(()=>{},()=>rows);const old=h.requests[0];h.container().querySelector('.nm-close-btn').onclick();
 assert.equal(h.keys.size,0);assert.equal(h.focused(),h.trigger);
 if(outcome==='success')old.success(point());else old.error({code:1});
 assert.equal(h.writes(),0,'cancelled callback must not write detached DOM');assert.equal(h.keys.size,0);
 h.w.PoeticsNearMe.init(()=>{},()=>rows);old.success(point());assert(h.container().innerHTML.includes('Locating...'),'old request must not overwrite reopened panel');
 h.requests[1].success(point());h.container().querySelector('.nm-close').onclick();assert.equal(h.keys.size,0);
}
for(const errorCode of [1,2,3]){
 const h=harness();h.w.PoeticsNearMe.init(()=>{},()=>rows);h.requests[0].error({code:errorCode});
 assert(h.container().innerHTML.includes(['','Permission denied.','Location unavailable.','Timed out.'][errorCode]));
 assert.equal(h.keys.size,1);const cities=h.container().querySelectorAll('.nm-city-btn');assert.equal(cities.length,2,'only recorded fallback hubs');
 cities.find(b=>b.dataset.city==='Lagos').onclick();assert(h.container().querySelector('.nm-results').innerHTML.includes('City estimate'));
}
{
 const h=harness(false);h.w.PoeticsNearMe.init(()=>{},()=>rows);assert(h.container().innerHTML.includes('Geolocation unsupported'));assert.equal(h.keys.size,1);
 [...h.keys][0]({key:'Escape'});assert.equal(h.keys.size,0);assert.equal(h.container(),undefined);
}
for(const location of [point(7,2),point(40,-70),point(NaN,3)]){
 const h=harness();h.w.PoeticsNearMe.init(()=>{},()=>rows);h.requests[0].success(location);assert(h.container().innerHTML.includes('Select a city'),'outside mapped Nigeria must use fallback');
}
{
 const h=harness();let chosen=null,eligible=rows,reads=0;const getRows=()=>{reads++;return eligible;};h.w.PoeticsNearMe.init(id=>chosen=id,getRows);h.requests[0].success(point());
 const result=h.container().querySelector('.nm-results');assert(result.innerHTML.includes('&lt;img src=x onerror=alert(1)&gt;'));assert(!result.innerHTML.includes('<img'));
 assert(result.innerHTML.includes('City estimate'));assert(result.innerHTML.includes('Lagos'));assert(result.innerHTML.includes('Recorded connections: Visiting Poet'));assert(result.innerHTML.includes('Spoken event'));assert(h.container().innerHTML.includes('Historical records do not confirm an upcoming event'));assert(result.innerHTML.includes('(approx)'));assert(!result.innerHTML.includes('Unlocated'));assert(!result.innerHTML.includes('Person'));assert(!result.innerHTML.includes('City locator'));assert(!result.innerHTML.includes('Far venue'));
 const radius=h.container().querySelector('.nm-dist-btn');radius.onclick({target:radius});assert(result.innerHTML.includes('Far venue'),'50km radius includes surrounding venue');
 assert(result.innerHTML.indexOf('City estimate')<result.innerHTML.indexOf('Far venue'),'nearest ordering');
 const buttons=result.querySelectorAll('.nm-item');buttons.find(b=>b.dataset.node==='close').onclick();assert.equal(chosen,'close');assert.equal(h.keys.size,0);
 eligible=[rows.find(r=>r.id==='far')];h.w.PoeticsNearMe.init(()=>{},getRows);h.requests[1].success(point());assert.equal(reads,2,'fresh eligible rows on every opening');assert(h.container().querySelector('.nm-results').innerHTML.includes('No events'));
}
console.log('PASS deferred radar, Haversine, recorded coordinates, approximate city fallback, Nigerian boundary, denial/error/timeout/unsupported, cancellation and reopen races, radius/sort, escaped content, fresh filters and map-focus callback');
