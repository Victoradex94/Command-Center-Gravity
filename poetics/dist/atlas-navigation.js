'use strict';
(function(){
const categories=['People','Places','Platforms','Prizes','Publications'];
function read(hash){const p=new URLSearchParams(String(hash||'').split('?')[1]||'');return {mode:({list:'Directory',connections:'Mind map'})[p.get('view')]||'Map',query:(p.get('q')||'').slice(0,300),selected:p.get('record')||null,state:p.get('state')||'All states',zone:p.get('zone')||'All zones',geo:p.get('city')||'All places',year:p.get('year')||'All years',activity:p.get('format')||'All formats',enabled:p.has('categories')?p.get('categories').split(',').filter(c=>categories.includes(c)):categories.slice(),browsing:p.get('panel')==='1',stateMapMode:'outline'};}
function hash(s){const p=new URLSearchParams();const set=(k,v,def)=>{if(v&&v!==def)p.set(k,v);};set('view',({'Directory':'list','Mind map':'connections'})[s.mode]);set('state',s.state,'All states');set('zone',s.zone,'All zones');set('city',s.geo,'All places');set('year',s.year,'All years');set('format',s.activity,'All formats');set('q',s.query);set('record',s.selected);const picked=categories.filter(c=>s.enabled.includes(c));if(picked.length!==5)p.set('categories',picked.join(',')||'none');if(s.browsing)p.set('panel','1');return '#/atlas'+(p.size?'?'+p.toString():'');}
function commit(s,replace=false){if(!window.location||!window.history)return;const target=hash(s);if(window.location.hash===target)return;window.history[replace?'replaceState':'pushState']({poeticsAtlas:true},'',target);}
window.PoeticsAtlasNavigation={read,hash,commit};
})();
