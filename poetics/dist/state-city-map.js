'use strict';
(function(){
const d=window.PoeticsOSMStateLocators,h=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
if(!d)return;
const mercator=([lon,lat])=>[lon,Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))*180/Math.PI];
const stateLayer=window.PoeticsGeography?.get('osm-kaduna-state'),geometry=stateLayer?.geometry||d.geometry;
const rings=geometry.coordinates.map(r=>r.map(mercator)),points=rings.flat();
const bounds=[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1])),Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))];
const scale=Math.min(600/(bounds[2]-bounds[0]),470/(bounds[3]-bounds[1])),cx=(bounds[0]+bounds[2])/2,cy=(bounds[1]+bounds[3])/2;
function project(coordinates){const [x,y]=mercator(coordinates);return [372+(x-cx)*scale,320-(y-cy)*scale];}
const path=geometry.coordinates.map(r=>r.map((p,i)=>{const [x,y]=project(p);return (i?'L':'M')+x.toFixed(3)+' '+y.toFixed(3);}).join(' ')+'Z').join(' ');
const urban=window.PoeticsGeography?.forState('Kaduna').filter(l=>l.role==='urban-extent')||[];
const urbanPath=g=>g.coordinates.map(poly=>poly.map(r=>r.map((p,i)=>{const [x,y]=project(p);return (i?'L':'M')+x.toFixed(3)+' '+y.toFixed(3);}).join(' ')+'Z').join(' ')).join(' ');
function render(state,cityCounts,values,selectedCity='All places',maximum=0){
if(state!==d.state)return '';
const m=window.PoeticsStateMap,total=Object.values(values).reduce((a,b)=>a+b,0),band=m.frequencyBand(total,maximum),parts=m.categories.filter(c=>values[c]>0);
const extents=urban.map(l=>`<path class="urban-extent ${selectedCity===l.city?'selected':''}" d="${urbanPath(l.geometry)}" fill-rule="evenodd" data-map-city="${h(l.city)}" tabindex="0" role="button" aria-label="${h(l.city)} urban extent, 2020: ${cityCounts[l.city]||0} matching entries"><title>${h(l.city)} · Urban extent · 2020 · not a legal city boundary</title></path>`).join('');
const markers=d.cities.map(c=>{const [x,y]=project(c.coordinates),count=cityCounts[c.name]||0;return `<g class="state-city-locator ${selectedCity===c.name?'selected':''}" data-map-city="${h(c.name)}" tabindex="0" role="button" aria-label="${h(c.name)} city centre: ${count} matching entries" transform="translate(${x.toFixed(3)},${y.toFixed(3)})"><title>${h(c.name)} · approximate city-centre locator · ${count} matching entries</title><circle class="city-hit" r="22" fill="transparent"/><circle class="city-centre-dot" r="8"/><text x="16" y="-10" class="city-locator-label">${h(c.name)}</text><text x="16" y="10" class="city-locator-count">${count} entries</text></g>`;}).join('');
const badges=parts.map((c,i)=>`<g role="button" tabindex="0" data-category-state="Kaduna" data-category-count="${h(c)}" data-count="${values[c]}" aria-label="Kaduna: ${values[c]} ${h(c)} entries" transform="translate(${270+i*48},48)"><circle r="17" fill="${m.colors[c]}" stroke="#fffaf3" stroke-width="1"/><text text-anchor="middle" y="5" fill="${['People','Publications'].includes(c)?'#fffaf3':'#171717'}">${values[c]}</text></g>`).join('');
return `<svg class="nigeria-gis state-city-gis" viewBox="0 0 744 600" role="group" aria-label="Kaduna state with Kaduna and Zaria urban extents from 2020"><defs><clipPath id="kaduna-urban-clip"><path d="${path}" fill-rule="evenodd" clip-rule="evenodd"/></clipPath></defs><text x="372" y="16" text-anchor="middle" class="state-city-heading">Kaduna · ${total} matching entries</text>${badges}<path class="osm-state-outline" d="${path}" fill="${band.fill}" fill-rule="evenodd"/><g clip-path="url(#kaduna-urban-clip)">${extents}</g>${markers}</svg><p class="state-city-source"><span class="urban-extent-key" aria-hidden="true"></span> Urban extent · 2020 · <a href="https://docs.digitalearthafrica.org/en/latest/data_specs/Africapolis_urban_specs.html" target="_blank" rel="noopener">Africapolis / OECD-SWAC &amp; e-Geopolis</a> · CC BY 4.0. Settlement footprints, not legal city limits or current boundaries. City-centre dots are approximate locators. <a href="urban-extents-kaduna-2020.geojson" download>Download layer</a><br><a href="https://www.openstreetmap.org/relation/3709353" target="_blank" rel="noopener">State outline</a> · source tag 2013 · export 14 Oct 2026 · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors / ODbL</a></p>`;
}
window.PoeticsStateCityMap={has:state=>state===d.state,project,render,data:d,path};
})();
