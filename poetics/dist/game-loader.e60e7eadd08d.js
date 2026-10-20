'use strict';
(function(){
 const loaded=new Map();let pending;
 function loadScript(url){
  if(loaded.has(url))return loaded.get(url);
  const task=new Promise((resolve,reject)=>{
   const script=document.createElement('script');script.src=url;script.async=false;
   script.onload=()=>resolve();script.onerror=()=>{loaded.delete(url);script.remove();reject(new Error('Games could not load'));};
   document.head.append(script);
  });loaded.set(url,task);return task;
 }
 window.PoeticsLoadGames=()=>{
  if(pending)return pending;
  const files=window.PoeticsGameAssets||[];
  if(!files.length)return Promise.reject(new Error('Games assets unavailable'));
  pending=Promise.all(files.map(loadScript)).catch(error=>{pending=null;throw error;});
  return pending;
 };
 window.PoeticsLoadAsset=name=>{
  const file=(window.PoeticsLazyAssets||{})[name];
  return file?loadScript(file):Promise.reject(new Error('Route asset unavailable'));
 };
})();
