'use strict';
(function(){
const A = window.PoeticsAtlas;

function haversine(lat1, lon1, lat2, lon2) {
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
  return 6371 * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
}

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const C = ['Lagos', 'Abuja', 'Port Harcourt', 'Kano', 'Enugu', 'Ibadan'];

let onFocus = null;
let reqId = 0;

function injectStyles() {
  if (document.getElementById('nm-styles')) return;
  const s = document.createElement('style');
  s.id = 'nm-styles';
  s.textContent = `
.nm-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:1000;display:flex;align-items:center;justify-content:center}
.nm-dialog{background:#fffdf9;border-radius:12px;width:90%;max-width:400px;max-height:80vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.2)}
.nm-header{padding:16px;background:#0f5163;color:#fffaf4;display:flex;justify-content:space-between;align-items:center}
.nm-header h2{margin:0;font-size:18px}
.nm-close{background:transparent;border:none;color:#fffaf4;font-size:24px;cursor:pointer}
.nm-controls{padding:12px 16px;border-bottom:1px solid #e5ddd3;display:flex;justify-content:space-between;align-items:center;font-size:14px}
.nm-dist-btn{background:#edf3f0;border:1px solid #dce4df;border-radius:8px;padding:6px 12px;cursor:pointer}
.nm-results{padding:16px;overflow-y:auto;flex:1}
.nm-item{display:flex;justify-content:space-between;width:100%;text-align:left;padding:12px;margin-bottom:8px;background:#fcfcfc;border:1px solid #e5ddd3;border-radius:8px;cursor:pointer}
.nm-item:hover{background:#edf3f0}
.nm-empty{text-align:center;color:#666;font-style:italic}
.nm-fallback-cities{display:flex;flex-wrap:wrap;gap:8px;padding:16px}
.nm-city-btn{background:#edf3f0;border:1px solid #dce4df;border-radius:8px;padding:8px 16px;cursor:pointer}
.nm-msg{padding:16px 16px 0;color:#a3375a}
.nm-loading{padding:32px;text-align:center;color:#fff;display:flex;flex-direction:column;align-items:center;gap:16px}
.map-city-toolbar #near-me-btn{min-height:48px;padding:10px 18px;border:1px solid #0f5163;border-radius:0 12px 12px 0;background:#edf3f0;color:#0f5163;font-weight:600;white-space:nowrap;margin-left:-1px}
.map-city-toolbar #near-me-btn:hover{background:#dce4df}
  `;
  document.head.appendChild(s);
}

function handleKey(e, close) { if (e.key === 'Escape') close(); }

function inNigeria(lat, lon) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return false;
  const inside = ring => { let hit = false; for (let i=0,j=ring.length-1;i<ring.length;j=i++) { const [x,y]=ring[i], [u,v]=ring[j]; if ((y>lat)!==(v>lat) && lon<(u-x)*(lat-y)/(v-y)+x) hit=!hit; } return hit; };
  return (window.PoeticsNigeria?.features || []).some(f => { const g=f.geometry; const polygons=g?.type==='Polygon'?[g.coordinates]:g?.type==='MultiPolygon'?g.coordinates:[]; return polygons.some(([outer,...holes])=>inside(outer)&&!holes.some(inside)); });
}
function recordedPoint(r) {
  const c=r.coordinates||r.pilot?.coordinates;
  const g=r.geometry?.type==='Point'?r.geometry.coordinates:null;
  const lat=g?.[1]??c?.lat??c?.latitude??r.latitude??r.lat;
  const lon=g?.[0]??c?.lon??c?.longitude??r.longitude??r.lon;
  if (lat===null || lat===undefined || lon===null || lon===undefined || lat==='' || lon==='') return null;
  const a=Number(lat),b=Number(lon);
  return Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a)<=90&&Math.abs(b)<=180 ? {lat:a,lon:b,approx:!/venue|site|address|exact/i.test(c?.precision||r.coordinatePrecision||'')} : null;
}

function renderRadar(container, lat, lon, fallback, getRows) {
  const id = ++reqId;
  const coords = A.placeCoordinates || {};
  const entries = [];
  
  for (const r of getRows()) {
    if (!['Places', 'Platforms'].includes(r.category) || r.placeType==='City') continue;
    const point=recordedPoint(r);
    if (point) { entries.push({r,d:haversine(lat,lon,point.lat,point.lon),approx:point.approx}); continue; }
    if (!r.city) continue;
    const cities = String(r.city).split(/\s*\/\s*|;\s*/);
    let minD = Infinity;
    let approx = false;
    for (const c of cities) {
      if (coords[c]) {
        const d = haversine(lat, lon, coords[c].lat, coords[c].lon);
        if (d < minD) {
          minD = d;
          approx = true;
        }
      }
    }
    if (minD < Infinity) entries.push({ r, d: minD, approx });
  }
  entries.sort((a, b) => a.d - b.d);
  
  const dists = [25, 50, 100, Infinity];
  let distIdx = 0;
  
  const close = () => {
    if (id !== reqId) return;
    ++reqId;
    container.remove();
    document.removeEventListener('keydown', container._key);
    document.getElementById('near-me-btn')?.focus();
  };

  const renderList = () => {
    if (id !== reqId) return;
    const max = dists[distIdx];
    const f = entries.filter(e => e.d <= max);
    const html = f.length === 0 
      ? '<p class="nm-empty">No events or platforms found within this radius.</p>' 
      : f.map(e => `<button class="nm-item" data-node="${esc(e.r.id)}"><strong>${esc(e.r.name)}</strong><span>${e.d < 1 ? '<1' : Math.round(e.d)} km${e.approx ? ' (approx)' : ''}</span></button>`).join('');
    
    container.querySelector('.nm-results').innerHTML = html;
    container.querySelectorAll('.nm-item').forEach(b => {
      b.onclick = () => { close(); if (onFocus) onFocus(b.dataset.node); };
    });
  };

  const dLabel = d => d === Infinity ? 'Nearest' : `${d} km`;

  container.innerHTML = `
    <div class="nm-dialog" role="dialog" aria-label="Near Me">
      <div class="nm-header">
        <h2>Near Me ${fallback ? `(${esc(fallback)})` : ''}</h2>
        <button class="nm-close" aria-label="Close">×</button>
      </div>
      <div class="nm-controls">
        <label>Radius:</label>
        <button class="nm-dist-btn">${dLabel(dists[distIdx])}</button>
      </div>
      <div class="nm-results" tabindex="0"></div>
    </div>
  `;
  
  container.querySelector('.nm-close').onclick = close;
  container.querySelector('.nm-dist-btn').onclick = (e) => {
    if (id !== reqId) return;
    distIdx = (distIdx + 1) % dists.length;
    e.target.textContent = dLabel(dists[distIdx]);
    renderList();
  };
  
  container._key = (e) => handleKey(e, close);
  document.addEventListener('keydown', container._key);
  
  renderList();
  container.querySelector('.nm-results').focus();
}

function renderFallback(container, msg, getRows) {
  const id = ++reqId;
  const close = () => {
    if (id !== reqId) return;
    ++reqId;
    container.remove();
    document.removeEventListener('keydown', container._key);
    document.getElementById('near-me-btn')?.focus();
  };

  const c = A.placeCoordinates || {};
  const hubs = C.filter(x => c[x]);

  container.innerHTML = `
    <div class="nm-dialog" role="dialog" aria-label="Location Fallback">
      <div class="nm-header">
        <h2>Location Unavailable</h2>
        <button class="nm-close" aria-label="Close">×</button>
      </div>
      <p class="nm-msg">${esc(msg)}</p>
      <div class="nm-fallback-cities">
        ${hubs.map(x => `<button class="nm-city-btn" data-city="${esc(x)}">${esc(x)}</button>`).join('')}
      </div>
    </div>
  `;
  
  container.querySelector('.nm-close').onclick = close;
  container.querySelectorAll('.nm-city-btn').forEach(b => {
    b.onclick = () => {
      if (id !== reqId) return;
      const city = b.dataset.city;
      document.removeEventListener('keydown', container._key);
      renderRadar(container, c[city].lat, c[city].lon, city, getRows);
    };
  });

  container._key = (e) => handleKey(e, close);
  document.addEventListener('keydown', container._key);
  container.querySelector('.nm-close').focus();
}

function init(cb, getRows) {
  injectStyles();
  onFocus = cb;
  const id = ++reqId;
  
  let c = document.getElementById('nm-container');
  if (!c) {
    c = document.createElement('div');
    c.id = 'nm-container';
    c.className = 'nm-overlay';
    document.body.appendChild(c);
  } else if (c._key) {
    document.removeEventListener('keydown', c._key);
  }

  const close = () => {
    if (id !== reqId) return;
    ++reqId;
    c.remove();
    document.removeEventListener('keydown', c._key);
    document.getElementById('near-me-btn')?.focus();
  };

  c.innerHTML = `<div class="nm-loading" role="dialog" aria-label="Locating..."><p>Locating...</p><button class="nm-close-btn" style="padding:8px 16px;border-radius:8px;border:none;background:#fff;color:#0f5163;cursor:pointer;">Cancel</button></div>`;
  c.querySelector('.nm-close-btn').onclick = close;
  c._key = (e) => handleKey(e, close);
  document.addEventListener('keydown', c._key);
  c.querySelector('.nm-close-btn').focus();

  if (!navigator.geolocation) {
    document.removeEventListener('keydown', c._key);
    return renderFallback(c, "Geolocation unsupported.", getRows);
  }

  navigator.geolocation.getCurrentPosition(
    p => {
      if (id !== reqId) return;
      document.removeEventListener('keydown', c._key);
      const lat = p.coords.latitude, lon = p.coords.longitude;
      if (!inNigeria(lat,lon)) renderFallback(c, "Outside the mapped Nigeria boundary. Select a city.", getRows);
      else renderRadar(c, lat, lon, null, getRows);
    },
    e => {
      if (id !== reqId) return;
      document.removeEventListener('keydown', c._key);
      renderFallback(c, e.code === 1 ? "Permission denied." : e.code === 3 ? "Timed out." : "Location unavailable.", getRows);
    },
    { timeout: 10000 }
  );
}

window.PoeticsNearMe = { init, haversine };

})();
