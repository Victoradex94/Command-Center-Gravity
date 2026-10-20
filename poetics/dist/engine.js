(function(root){
'use strict';
const roster=[['Tomi','imagery','publish'],['Bayo','satire','compete'],['Sade','rhythm','collaborate'],['Nnamdi','structure','practice'],['Zara','imagery','publish'],['Femi','performance','compete'],['Ada','structure','mentor'],['Kola','rhythm','practice'],['Muna','imagery','collaborate'],['Dami','satire','publish'],['Ife','performance','compete'],['Reni','rhythm','mentor']];
const lines=['The rain rehearses on a roof / before the morning finds its voice.','A bus keeps all our borrowed names / and leaves the silence at the stop.','I fold the day into a pocket / where an unfinished song can sleep.','The market counts its little suns / in oranges and open palms.'];
function create(seed=2010){
    let s={version:1,seed,day:1,name:'New voice',dna:'Sad',path:'Page Poet',city:'Ogbomoso',energy:80,money:3000,craft:12,delivery:10,reputation:0,prepared:0,research:0,poem:'',wall:[],log:['You arrive in a fictional Ogbomoso poetry community, January 2010.'],npcs:[],entered:[],posts:0};

    let realNames = [];
    if (root.PoeticsDirectoryData && root.PoeticsDirectoryData.rows) {
      realNames = root.PoeticsDirectoryData.rows.filter(r => r.category === 'People').map(r => r.name);
    }

    let namesToUse = [];
    for (let i = 0; i < 12; i++) {
      if (realNames.length > 0 && rand(s) < 0.3) {
        namesToUse.push(realNames[Math.floor(rand(s) * realNames.length)]);
      } else {
        namesToUse.push(roster[i][0]);
      }
    }

    s.npcs = roster.map((_,i)=>({id:i,name:namesToUse[i],style:roster[i][1],goal:roster[i][2],relationship:0,skill:14+i,funds:500+i*100,works:0,activity:'Working on a first draft',memory:[]}));
    return s;
  }

function countRhymes(text) {
    if (!text) return 0;
    const words = text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(w => w.length > 2);
    if (words.length < 2) return 0;

    let rhymes = 0;
    const endings = words.map(w => w.slice(-2));

    for (let i = 0; i < endings.length; i++) {
        for (let j = i + 1; j < endings.length; j++) {
            if (endings[i] === endings[j]) {
                rhymes++;
            }
        }
    }
    return rhymes;
}

function rand(s){s.seed=(Math.imul(s.seed,1664525)+1013904223)>>>0;return s.seed/4294967296;}
function note(s,msg){s.log.unshift(msg);s.log=s.log.slice(0,80);}
function tick(s){s.day++;s.energy=Math.min(100,s.energy+12);s.npcs.forEach(n=>{const r=rand(s);if(n.goal==='publish'&&r<.5){n.works++;n.activity='Posted a new miniature';s.wall.unshift({author:n.name,text:lines[(n.id+s.day)%lines.length],day:s.day,fiction:true});}else if(n.goal==='compete'&&n.funds>=150&&r<.7){n.funds-=150;n.skill++;n.activity='Rehearsed for the next slam';}else if(n.goal==='collaborate'&&r<.6){n.activity='Invited a peer to a joint reading';n.skill++;}else if(n.goal==='mentor'&&r<.6){n.activity='Hosted a critique circle';n.funds+=50;}else {n.activity='Revised a draft between other obligations';n.skill+=.25;n.funds+=100;}});s.wall=s.wall.slice(0,40);if(root.PoeticsOpportunities)root.PoeticsOpportunities.onDay(s);
let struggleEvent = "";
let r = rand(s);
if(r < 0.1) {
    if(r < 0.03) {
        struggleEvent = ' Struggle: A gig paid you in "exposure". No funds added.';
    } else if (r < 0.06) {
        s.energy = Math.max(0, s.energy - 10);
        struggleEvent = ' Struggle: MC introduced you as a "comedian". Energy -10.';
    } else {
        s.money = Math.max(0, s.money - 200);
        struggleEvent = ' Struggle: Travel costs to an uncalled open mic drained your funds. ₦-200.';
    }
}
note(s,'Day '+s.day+': the community advances; poets pursue their own plans.' + struggleEvent);}
function act(s,type,arg){const costs={coach:[18,350],research:[10,200],rehearse:[16,0],post:[12,0],feedback:[10,0],openmic:[20,150],slam:[25,400],travel:[20,600]};if(type==='rest'){tick(s);s.energy=Math.min(100,s.energy+25);return {ok:true,message:'A new day begins.'};}if(type==='work'){tick(s);s.energy=Math.max(0,s.energy-15);s.money+=450;note(s,'You take a paid shift: +₦450.');return {ok:true,message:'Paid shift complete.'};}if(type==='write'){if(typeof arg!=='string'||arg.length>4000)return {ok:false,message:'Keep your draft within 4,000 characters.'};s.poem=arg;return {ok:true,message:'Draft saved on this device.'};}if(type==='name'){s.name=String(arg).trim().slice(0,40)||'New voice';return {ok:true,message:'Your pen name is saved.'};}if(type==='dna'){if(!['Angry','Love','Sad','Happy'].includes(arg))return {ok:false,message:'Invalid DNA.'};s.dna=arg;return {ok:true,message:'Your poetic DNA is saved.'};}if(type==='path'){if(!['Page Poet','Slam Poet','Promoter'].includes(arg))return {ok:false,message:'Invalid path.'};s.path=arg;return {ok:true,message:'Your path is saved.'};}if(!costs[type])return {ok:false,message:'Unknown action.'};const [energy,money]=costs[type];if(s.energy<energy||s.money<money)return {ok:false,message:'You need '+energy+' energy and ₦'+money+' for this action. Rest or take a paid shift.'};if(['post','openmic','slam'].includes(type)&&s.poem.trim().length<40)return {ok:false,message:'Write at least 40 characters before sharing or performing.'};if(type==='slam'&&s.entered.includes(s.day))return {ok:false,message:'You have already entered today’s slam. Advance to another day.'};if(type==='travel'&&!['Ogbomoso','Ibadan','Lagos','Aba','Abuja'].includes(arg))return {ok:false,message:'Choose a destination on the fictional circuit.'};if(type==='travel'&&arg===s.city)return {ok:false,message:'You are already in '+s.city+'.'};if(type==='feedback'&&!s.npcs[arg])return {ok:false,message:'Choose a poet.'};s.energy-=energy;s.money-=money;
let msg='';if(type==='coach'){s.craft+=4;msg='Coach: choose one concrete image, then cut the explanation after it. Craft +4.';}if(type==='research'){s.research=Math.min(3,s.research+1);msg='Researcher: Bayo favours satire; Sade rehearses rhythm. A contrasting delivery can help. This is fictional opponent research.';}if(type==='rehearse'){s.delivery+=3;s.prepared=Math.min(5,s.prepared+1);msg='You rehearse pauses and breath. Delivery +3; preparation +1.';}if(type==='post'){s.wall.unshift({author:s.name,text:s.poem,day:s.day,fiction:true});s.wall=s.wall.slice(0,40);s.posts++;s.reputation+=2;msg='Your original draft reaches the wall. Reputation +2.';}if(type==='feedback'){const n=s.npcs[arg];n.relationship+=2;n.memory.push('Received your feedback on day '+s.day);s.craft++;msg='You exchange a concrete revision note with '+n.name+'. Relationship +2; craft +1.';}if(type==='travel'){s.city=arg;msg='You travel to '+arg+'. A new room, the same unfinished poem.';}if(type==='openmic'){
    let r = rand(s);
    if(r < 0.2) {
        msg='You travel to the fictional Lion’s Lines open mic, but the list was full. You weren\'t called. Energy and time spent.';
    } else {
        let rep_gain = 4;
        let del_gain = 2;
        let rhyme_msg = '';
        if (countRhymes(s.poem) > 2) {
            rep_gain *= 2;
            del_gain *= 2;
            rhyme_msg = ' The crowd loved your rhymes! Rewards doubled.';
        }
        s.reputation+=rep_gain;s.delivery+=del_gain;msg='You perform at the fictional Lion’s Lines open mic. Reputation +'+rep_gain+'; delivery +'+del_gain+'.' + rhyme_msg;
    }
}if(type==='slam'){const words=s.poem.trim().split(/\s+/).length;let fit=arg==='intimate'?s.craft:arg==='rhythmic'?s.delivery:(s.craft+s.delivery)/2;let score=Math.round(35+Math.min(15,words/8)+(s.craft+s.delivery)*.45+fit*.3+s.prepared*3+s.research*2+rand(s)*10);
let rhyme_msg = '';
if (countRhymes(s.poem) > 2) {
    score += 15;
    rhyme_msg = ' Sick rhymes gave you a score boost!';
}
const rivals=s.npcs.filter(n=>n.goal==='compete').map(n=>({name:n.name,score:Math.round(45+n.skill*.7+rand(s)*15)}));const rank=1+rivals.filter(n=>n.score>=score).length;s.entered.push(s.day);
let rep_gain = rank===1?10:3;
let money_gain = rank===1?700:0;
if (countRhymes(s.poem) > 2) {
    rep_gain *= 2;
    money_gain *= 2;
    rhyme_msg += ' Double rewards!';
}
s.reputation+=rep_gain;
if(rank===1)s.money+=money_gain;
msg='Fictional slam: '+score+' points; place '+rank+' of '+(rivals.length+1)+'. '+rivals.map(n=>n.name+': '+n.score).join(' · ')+'. '+(rank===1?'Prize +₦'+money_gain+'.':'Reputation +'+rep_gain+' for showing up.')+rhyme_msg+' Game points reflect preparation, delivery choice and chance; they are not a literary verdict.';s.prepared=0;s.research=0;}note(s,msg);return {ok:true,message:msg};}
function valid(s){return s&&(!s.opportunities||(Array.isArray(s.opportunities.read)&&s.opportunities.read.every(x=>typeof x==='string')&&s.opportunities.submissions&&typeof s.opportunities.submissions==='object'&&!Array.isArray(s.opportunities.submissions)&&Object.values(s.opportunities.submissions).every(e=>e&&typeof e.poem==='string'&&e.poem.length<=4000&&typeof e.author==='string'&&Number.isInteger(e.day)&&Number.isInteger(e.deadline)&&Number.isFinite(e.craft)&&['competition','anthology'].includes(e.type))&&s.opportunities.resolved&&typeof s.opportunities.resolved==='object'&&!Array.isArray(s.opportunities.resolved)&&Object.values(s.opportunities.resolved).every(e=>e&&typeof e.message==='string'&&typeof e.success==='boolean'&&Number.isInteger(e.day))))&&s.version===1&&Number.isInteger(s.day)&&s.day>0&&Number.isInteger(s.seed)&&typeof s.poem==='string'&&s.poem.length<=4000&&typeof s.name==='string'&&typeof s.dna==='string'&&['Angry','Love','Sad','Happy'].includes(s.dna)&&typeof s.path==='string'&&['Page Poet','Slam Poet','Promoter'].includes(s.path)&&s.name.length<=40&&['Ogbomoso','Ibadan','Lagos','Aba','Abuja'].includes(s.city)&&['energy','money','craft','delivery','reputation','prepared','research'].every(k=>Number.isFinite(s[k])&&s[k]>=0)&&s.energy<=100&&Array.isArray(s.npcs)&&s.npcs.length===12&&s.npcs.every((n,i)=>n.id===i&&n.style===roster[i][1]&&n.goal===roster[i][2]&&['relationship','skill','funds','works'].every(k=>Number.isFinite(n[k])&&n[k]>=0)&&typeof n.activity==='string'&&Array.isArray(n.memory)&&n.memory.every(x=>typeof x==='string'))&&Array.isArray(s.wall)&&s.wall.length<=40&&s.wall.every(p=>typeof p.author==='string'&&p.author.length<=40&&typeof p.text==='string'&&p.text.length<=4000&&Number.isInteger(p.day)&&p.fiction===true)&&Number.isInteger(s.posts)&&s.posts>=0&&Array.isArray(s.log)&&s.log.length<=80&&s.log.every(x=>typeof x==='string')&&Array.isArray(s.entered)&&s.entered.every(d=>Number.isInteger(d)&&d>0);}
const api={create,act,tick,valid};if(typeof module!=='undefined')module.exports=api;root.PoeticsEngine=api;
})(typeof window!=='undefined'?window:globalThis);
