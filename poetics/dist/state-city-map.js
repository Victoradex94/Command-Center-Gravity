'use strict';
(function(){
const d=window.PoeticsOSMStateLocators,h=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
if(!d)return;
const mercator=([lon,lat])=>[lon,Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))*180/Math.PI];
const rings=d.geometry.coordinates.map(r=>r.map(mercator)),points=rings.flat();
const bounds=[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))];
const scale=Math.min(600/(bounds[2]-bounds[0]),470/(bounds[3]-bounds[1])),cx=(bounds[0]+bounds[2])/2,cy=(bounds[1]+bounds[3])/2;
function project(coordinates){const [x,y]=mercator(coordinates);return [372+(x-cx)*scale,320-(y-cy)*scale];}
const path=d.geometry.coordinates.map(r=>r.map((p,i)=>{const [x,y]=project(p);return (i?'L':'M')+x.toFixed(3)+' '+y.toFixed(3);}).join(' ')+'Z').join(' ');
function render(state,cityCounts,values,selectedCity='All places',maximum=0){
if(state!==d.state)return '';
const m=window.PoeticsStateMap,total=Object.values(values).reduce((a,b)=>a+b,0),band=m.frequencyBand(total,maximum),parts=m.categories.filter(c=>values[c]>0);
const markers=d.cities.map(c=>{const [x,y]=project(c.coordinates),count=cityCounts[c.name]||0;return `<g class="state-city-locator ${selectedCity===c.name?'selected':''}" data-map-city="${h(c.name)}" tabindex="0" role="button" aria-label="${h(c.name)} city centre: ${count} matching entries" transform="translate(${x.toFixed(3)},${y.toFixed(3)})"><title>${h(c.name)} · approximate city-centre locator · ${count} matching entries</title><circle class="city-hit" r="22" fill="transparent"/><circle class="city-centre-dot" r="8"/><text x="16" y="-10" class="city-locator-label">${h(c.name)}</text><text x="16" y="10" class="city-locator-count">${count} entries</text></g>`;}).join('');
const badges=parts.map((c,i)=>`<g role="button" tabindex="0" data-category-state="Kaduna" data-category-count="${h(c)}" data-count="${values[c]}" aria-label="Kaduna: ${values[c]} ${h(c)} entries" transform="translate(${270+i*48},48)"><circle r="17" fill="${m.colors[c]}" stroke="#fffaf3" stroke-width="1"/><text text-anchor="middle" y="5" fill="${['People','Publications'].includes(c)?'#fffaf3':'#171717'}">${values[c]}</text></g>`).join('');
return `<svg class="nigeria-gis state-city-gis" viewBox="0 0 744 600" role="group" aria-label="Kaduna state outline with Kaduna and Zaria city-centre locators"><text x="372" y="16" text-anchor="middle" class="state-city-heading">Kaduna · ${total} matching entries</text>${badges}<path class="osm-state-outline" d="${path}" fill="${band.fill}" fill-rule="evenodd"/>${markers}</svg><p class="state-city-source">City-centre locators · city-area outlines pending. <a href="https://www.openstreetmap.org/relation/3709353" target="_blank" rel="noopener">State outline</a> · source tag 2013 · export 14 Oct 2026 · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors / ODbL</a></p>`;
}
window.PoeticsStateCityMap={has:state=>state===d.state,project,render,data:d,path};
})();
