'use strict';
(function(){
const data=window.PoeticsNigeria;
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const polygons=data.features.flatMap(f=>f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates);
const merc=lat=>Math.log(Math.tan(Math.PI/4+lat*Math.PI/360));
const points=polygons.flat(2),lons=points.map(p=>p[0]*Math.PI/180),ys=points.map(p=>merc(p[1]));
const bounds={left:Math.min(...lons),right:Math.max(...lons),top:Math.max(...ys),bottom:Math.min(...ys)};
const scale=Math.min(860/(bounds.right-bounds.left),710/(bounds.top-bounds.bottom));
const dx=(1000-(bounds.right-bounds.left)*scale)/2,dy=(850-(bounds.top-bounds.bottom)*scale)/2;
function project(lon,lat){return [dx+(lon*Math.PI/180-bounds.left)*scale,dy+(bounds.top-merc(lat))*scale];}
const path=polygons.map(poly=>poly.map(ring=>ring.map((p,i)=>(i?'L':'M')+project(...p).map(n=>n.toFixed(2)).join(',')).join(' ')+'Z').join(' ')).join(' ');
function render(locators,counts,selectedCity='All places'){
const labels={Lagos:[-30,35],Ibadan:[-55,-10],Ogbomoso:[-25,-28],Ilorin:[18,-16],Zaria:[-20,-24],Kaduna:[-25,26],Abuja:[-35,30],Enugu:[-25,-25],Calabar:[25,22],'Port Harcourt':[-55,28],Uyo:[20,-18]};
const markers=Object.entries(locators).filter(([city])=>counts[city]>0).map(([city,c])=>{const [x,y]=project(c.lon,c.lat),[lx,ly]=labels[city]||[0,-26];return `<g class="nigeria-city ${city===selectedCity?'selected':''}" role="button" tabindex="0" data-map-city="${escape(city)}" aria-label="${escape(city)}: ${counts[city]} entries" transform="translate(${x.toFixed(2)},${y.toFixed(2)})"><title>${escape(city)} · ${counts[city]} entries · city-centre association</title><circle class="city-hit" r="25"/><circle class="city-dot" r="13"/><text class="city-count" y="4" text-anchor="middle">${counts[city]}</text><text class="city-name" x="${lx}" y="${ly}" text-anchor="middle">${escape(city)}</text></g>`;}).join('');
return `<svg class="nigeria-gis" viewBox="0 0 1000 850" role="group" aria-label="Nigeria-only poetry atlas. Select a city to browse documented entries."><defs><linearGradient id="country-fill" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#353b34"/><stop offset="1" stop-color="#222b28"/></linearGradient><pattern id="country-grid" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M35 0H0V35" fill="none" stroke="#d9d5c3" stroke-opacity=".05"/></pattern><clipPath id="nigeria-only"><path d="${path}"/></clipPath></defs><path class="country-outline" d="${path}" fill="url(#country-fill)" fill-rule="evenodd"/><path d="${path}" fill="url(#country-grid)" fill-rule="evenodd"/><g clip-path="url(#nigeria-only)"><text class="country-name" x="520" y="450" text-anchor="middle">NIGERIA</text></g>${markers}</svg>`;
}
window.PoeticsNigeriaMap={render,project,path,bounds,source:data.metadata};
})();
