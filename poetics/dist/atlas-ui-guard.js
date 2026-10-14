'use strict';
/* Enforce the Atlas UI contract at the mounted document, including controls
   inserted by a legacy component after the directory has rendered. */
(function(){
 const ids=new Set(['map-zoom-in','map-zoom-out','map-country-reset']);
 const names=new Set(['zoom in','zoom out','show all nigeria']);
 const normal=s=>String(s||'').replace(/\s+/g,' ').trim().toLowerCase();
 function legacyControl(node){
  return ids.has(node.id)||names.has(normal(node.getAttribute('aria-label')))||names.has(normal(node.textContent));
 }
 function enforce(){
  const atlas=document.querySelector('#main .map-atlas');
  if(!atlas)return;
  // Exact identities/names only. "All Nigeria" and state-selection buttons stay.
  for(const node of document.querySelectorAll('button,[role="button"],input[type="button"]')){
   if(legacyControl(node))node.remove();
  }
  for(const shell of document.querySelectorAll('.country-map-controls'))shell.remove();
 }
 window.PoeticsAtlasUI={enforce};
 const observer=new MutationObserver(enforce);
 observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-label','id']});
 window.addEventListener('hashchange',enforce);
 enforce();
})();
