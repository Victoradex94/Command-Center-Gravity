/* Shared presentation only. Existing local navigation destinations remain owned by each site. */
(()=>{if(typeof document==='undefined')return;function initialise(){
 'use strict';
 if(location.hostname!=='stagingvicadex.local'||document.querySelector('#vx-ecosystem'))return;
 const path=location.pathname;
 const isAtlas=path.startsWith('/poetics/');
 const isWor=/^\/(wordsonrampage|wor-poet|submit-a-poem|poetry\/the-archive|category\/wordsonrampage)(\/|$)/.test(path);
 const family=document.querySelector('.sp-family-menu');
 const site=isAtlas?'atlas':isWor?'wor':family?'60sp':'vicadex';
 const sites=[['vicadex','Vic’Adex','/'],['60sp','60 Seconds Poetry','/60-seconds-poetry/'],['wor','Words on Rampage','/wordsonrampage/'],['atlas','Poetics Atlas','/poetics/']];
 const current=sites.find(s=>s[0]===site);
 const bar=document.createElement('div');bar.id='vx-ecosystem';bar.dataset.site=site;
 const shortNames={'vicadex':'Vic’Adex','60sp':'60SP','wor':'WOR','atlas':'Poetics'};
 const links=()=>sites.map(s=>`<a href="${s[2]}" aria-label="${s[1]}"${s[0]===site?' aria-current="true" data-active="true"':''}><span class="vx-dot" aria-hidden="true"></span><span class="vx-name-full">${s[1]}</span><span class="vx-name-short" aria-hidden="true">${shortNames[s[0]]}</span></a>`).join('');
 bar.innerHTML=`<div class="vx-eco-inner"><span class="vx-eco-label">The Vic’Adex ecosystem</span><nav class="vx-eco-desktop" aria-label="Ecosystem websites">${links()}</nav></div>`;
 document.body.prepend(bar);
 document.body.classList.add('vx-ecosystem-ready','vx-site-'+site);
 // Atlas updates current links across its SPA; keep the ecosystem's separate current-site state.
 if(site==='atlas')new MutationObserver(()=>{bar.querySelectorAll('[data-active]').forEach(a=>{if(a.getAttribute('aria-current')!=='true')a.setAttribute('aria-current','true');});}).observe(bar,{subtree:true,attributes:true,attributeFilter:['aria-current']});
 bar.querySelectorAll('details').forEach(d=>{
   d.addEventListener('keydown',e=>{if(e.key==='Escape'){d.open=false;d.querySelector('summary').focus();}});
   document.addEventListener('click',e=>{if(!d.contains(e.target))d.open=false;});
 });
 // Normalise only existing local bars, never create duplicate navigation.
 const header=document.querySelector('header.header-area');
 let local=site==='60sp'?family:site==='wor'?document.querySelector('.wor-widebar,.wor-local-masthead'):site==='atlas'?document.querySelector('body>header'):header;
 if(site==='wor'&&local&&header?.contains(local))header.before(local);
 if(local){document.body.classList.add('vx-has-local');local.classList.add('vx-local-nav');
   if(site==='wor'){
     const nav=local.querySelector('nav');
     if(nav){const toggle=document.createElement('button');toggle.type='button';toggle.className='vx-local-toggle';toggle.textContent='Menu';toggle.setAttribute('aria-expanded','false');nav.id=nav.id||'vx-wor-local-links';toggle.setAttribute('aria-controls',nav.id);local.insertBefore(toggle,nav);toggle.addEventListener('click',()=>{const open=local.classList.toggle('vx-menu-open');toggle.setAttribute('aria-expanded',String(open));});local.addEventListener('keydown',e=>{if(e.key==='Escape'){local.classList.remove('vx-menu-open');toggle.setAttribute('aria-expanded','false');toggle.focus();}});}
   }
 }
 function measure(){
   if(window.scrollY>64)bar.classList.add('vx-eco-scrolled');
   else if(window.scrollY<24)bar.classList.remove('vx-eco-scrolled');
   if(site==='vicadex'&&header)header.classList.toggle('vx-nav-scrolled',window.scrollY>bar.offsetHeight);
   const admin=document.getElementById('wpadminbar');const rect=admin?.getBoundingClientRect();
   const top=rect&&getComputedStyle(admin).display!=='none'?Math.max(0,rect.bottom):0;
   document.documentElement.style.setProperty('--vx-admin',top+'px');
   const slip=bar.getBoundingClientRect().height;
   document.documentElement.style.setProperty('--vx-slip-height',slip+'px');
   if(site==='60sp'){
     document.documentElement.style.setProperty('--v60sp-primary-height',slip+'px');
     if(local)local.style.setProperty('top','calc(var(--vx-admin,0px) + var(--vx-slip-height,33px))','important');
   }
   document.documentElement.style.setProperty('--vx-viewport',document.documentElement.clientWidth+'px');
   const height=local?.getBoundingClientRect().height||0;
   document.documentElement.style.setProperty('--vx-local-height',height+'px');
   if(site==='60sp')document.documentElement.style.setProperty('--v60sp-sticky-stack',(top+slip+height)+'px');
 }
 measure();window.addEventListener('resize',measure,{passive:true});window.addEventListener('scroll',measure,{passive:true});
 if(local&&window.ResizeObserver)new ResizeObserver(measure).observe(local);
}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialise,{once:true});else initialise();})();
