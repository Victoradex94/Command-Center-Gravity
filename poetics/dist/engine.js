(function(root){
'use strict';
const roster=[['Tomi','imagery','publish'],['Bayo','satire','compete'],['Sade','rhythm','collaborate'],['Nnamdi','structure','practice'],['Zara','imagery','publish'],['Femi','performance','compete'],['Ada','structure','mentor'],['Kola','rhythm','practice'],['Muna','imagery','collaborate'],['Dami','satire','publish'],['Ife','performance','compete'],['Reni','rhythm','mentor']];
const lines=['The rain rehearses on a roof / before the morning finds its voice.','A bus keeps all our borrowed names / and leaves the silence at the stop.','I fold the day into a pocket / where an unfinished song can sleep.','The market counts its little suns / in oranges and open palms.','Night settles on the metal bridge / where headlights write their briefest psalms.','We carried verses across the tracks / and traded salt for simple lines.','A handwritten notebook holds the town / between the margins of the dust.','The electric wire hums in the wind / like a guitar waiting for a tune.'];

const cityPeculiarities = {
  'Ogbomoso': { trait: 'Quiet workshop and campus circles', bonus: 'craft', desc: 'A quiet academic town where manuscripts are drafted with patient precision.' },
  'Ibadan': { trait: 'Literary heritage & classical verse', bonus: 'craft', desc: 'Home to the premier university tradition; depth, imagery, and poetic structure reign.' },
  'Lagos': { trait: 'Commercial slams & street hustle', bonus: 'delivery', desc: 'Fast, dynamic, and unapologetic; high crowd stakes, sharp critiques, and commercial arenas.' },
  'Jos': { trait: 'Acoustic calm & conscious circles', bonus: 'delivery', desc: 'Cool mountain air, soulful acoustic readings, and deeply communal open mics.' },
  'Enugu': { trait: 'Coal city grit & folkloric rhythm', bonus: 'craft', desc: 'Eastern oral cadence, proverb-laden metaphors, and cultural pride.' },
  'Abuja': { trait: 'National stages & institutional showcases', bonus: 'reputation', desc: 'Grand amphitheaters, diplomatic readings, and high-visibility festivals.' },
  'Aba': { trait: 'Vibrant trade & working-class verse', bonus: 'reputation', desc: 'Craft hammered out in commercial centers; direct, incisive, and unpretentious.' }
};

function create(seed=2010){
  return {
    version:1,
    seed,
    day:1,
    speed:'normal',
    name:'New voice',
    persona:{
      current:'page',
      unlocked:['page'],
      history:[{stage:'page',day:1,note:'Begun on the Page with a quiet notebook.'}]
    },
    city:'Ogbomoso',
    energy:80,
    money:3000,
    craft:12,
    delivery:10,
    reputation:0,
    prepared:0,
    research:0,
    poem:'',
    last_submitted_poem:'',
    wall:[],
    log:['You arrive in a fictional Ogbomoso poetry community, January 2010.'],
    weekly_digests:[],
    npcs:roster.map(([name,style,goal],i)=>({id:i,name,style,goal,relationship:0,skill:14+i,funds:500+i*100,works:0,activity:'Working on a first draft',memory:[]})),
    entered:[],
    posts:0
  };
}

function rand(s){s.seed=(Math.imul(s.seed,1664525)+1013904223)>>>0;return s.seed/4294967296;}
function note(s,msg){s.log.unshift(msg);s.log=s.log.slice(0,80);}

function countRhymes(text) {
  if (!text) return 0;
  const words = text.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(w => w.length > 2);
  if (words.length < 2) return 0;
  let rhymes = 0;
  const endings = words.map(w => w.slice(-2));
  for (let i = 0; i < endings.length; i++) {
    for (let j = i + 1; j < endings.length; j++) {
      if (endings[i] === endings[j]) rhymes++;
    }
  }
  return rhymes;
}

function tick(s){
  s.day++;
  s.energy = Math.min(100, s.energy + 12);
  s.npcs.forEach(n => {
    const r = rand(s);
    if(n.goal==='publish'&&r<.5){
      n.works++;
      n.activity='Posted a new miniature';
      s.wall.unshift({author:n.name,text:lines[(n.id+s.day)%lines.length],day:s.day,fiction:true});
    } else if(n.goal==='compete'&&n.funds>=150&&r<.7){
      n.funds-=150;
      n.skill++;
      n.activity='Rehearsed for the next slam';
    } else if(n.goal==='collaborate'&&r<.6){
      n.activity='Invited a peer to a joint reading';
      n.skill++;
    } else if(n.goal==='mentor'&&r<.6){
      n.activity='Hosted a critique circle';
      n.funds+=50;
    } else {
      n.activity='Revised a draft between other obligations';
      n.skill+=.25;
      n.funds+=100;
    }
  });
  s.wall=s.wall.slice(0,40);
  if (s.day % 7 === 0) {
    const digest = 'Week ' + (s.day / 7) + ' Digest: Day ' + s.day + ' reached. Craft: ' + Math.round(s.craft) + ', Delivery: ' + Math.round(s.delivery) + ', Stage: ' + s.persona.current.toUpperCase() + ', City: ' + s.city + '.';
    if (!s.weekly_digests) s.weekly_digests = [];
    s.weekly_digests.unshift(digest);
    s.weekly_digests = s.weekly_digests.slice(0, 20);
    note(s, digest);
  }
  if(root.PoeticsOpportunities)root.PoeticsOpportunities.onDay(s);
  note(s,'Day '+s.day+': the community advances; poets pursue their own plans.');
}

function act(s,type,arg){
  const costs={coach:[18,350],research:[10,200],rehearse:[16,0],post:[12,0],feedback:[10,0],openmic:[20,150],slam:[25,400],travel:[20,600]};
  if(type==='rest'){tick(s);s.energy=Math.min(100,s.energy+25);return {ok:true,message:'A new day begins.'};}
  if(type==='work'){tick(s);s.energy=Math.max(0,s.energy-15);s.money+=450;note(s,'You take a paid shift: +₦450.');return {ok:true,message:'Paid shift complete.'};}
  if(type==='write'){if(typeof arg!=='string'||arg.length>4000)return {ok:false,message:'Keep your draft within 4,000 characters.'};s.poem=arg;return {ok:true,message:'Draft saved on this device.'};}
  if(type==='name'){s.name=String(arg).trim().slice(0,40)||'New voice';return {ok:true,message:'Your pen name is saved.'};}
  if(type==='speed'){if(!['slow','normal','fast'].includes(arg))return {ok:false,message:'Valid speeds: slow, normal, fast.'};s.speed=arg;return {ok:true,message:'Pacing set to '+arg+'.'};}

  if(!costs[type])return {ok:false,message:'Unknown action.'};
  const [energy,money]=costs[type];
  if(s.energy<energy||s.money<money)return {ok:false,message:'You need '+energy+' energy and ₦'+money+' for this action. Rest or take a paid shift.'};
  if(['post','openmic','slam'].includes(type)&&s.poem.trim().length<40)return {ok:false,message:'Write at least 40 characters before sharing or performing.'};
  if(type==='slam'&&s.entered.includes(s.day))return {ok:false,message:'You have already entered today’s slam. Advance to another day.'};
  
  const allowedCities = ['Ogbomoso','Ibadan','Lagos','Jos','Enugu','Abuja','Aba'];
  if(type==='travel'&&!allowedCities.includes(arg))return {ok:false,message:'Choose a destination on the fictional circuit: ' + allowedCities.join(', ') + '.'};
  if(type==='travel'&&arg===s.city)return {ok:false,message:'You are already in '+s.city+'.'};
  if(type==='feedback'&&!s.npcs[arg])return {ok:false,message:'Choose a poet.'};

  s.energy-=energy;
  s.money-=money;
  let msg='';

  if(type==='coach'){s.craft+=4;msg='Coach: choose one concrete image, then cut the explanation after it. Craft +4.';}
  if(type==='research'){s.research=Math.min(3,s.research+1);msg='Researcher: Bayo favours satire; Sade rehearses rhythm. A contrasting delivery can help. This is fictional opponent research.';}
  if(type==='rehearse'){s.delivery+=3;s.prepared=Math.min(5,s.prepared+1);msg='You rehearse pauses and breath. Delivery +3; preparation +1.';}
  if(type==='post'){s.wall.unshift({author:s.name,text:s.poem,day:s.day,fiction:true});s.wall=s.wall.slice(0,40);s.posts++;s.reputation+=2;msg='Your original draft reaches the wall. Reputation +2.';}
  
  if(type==='feedback'){
    const n=s.npcs[arg];
    n.relationship+=2;
    n.memory.push('Received your feedback on day '+s.day);
    s.craft++;
    const wrrRemarks = [
      'WRR Critique: Commended your concrete imagery; suggested checking the syllable rhythm in line 3.',
      'WRR Critique: Strong emotional resonance and metaphor; watch out for forced rhyme endings.',
      'WRR Critique: Admired the authentic local atmosphere; recommended tightening the opening stanza.'
    ];
    const remark = wrrRemarks[(n.id + s.day) % wrrRemarks.length];
    msg = 'You exchange notes with ' + n.name + '. ' + remark + ' Relationship +2; craft +1.';
  }

  if(type==='travel'){
    s.city=arg;
    const pec = cityPeculiarities[arg] || { trait: 'Local literary circle', bonus: 'craft', desc: 'A lively room of poets.' };
    if (pec.bonus === 'craft') s.craft += 0.5;
    if (pec.bonus === 'delivery') s.delivery += 0.5;
    if (pec.bonus === 'reputation') s.reputation += 0.5;
    msg='You travel to '+arg+' ('+pec.trait+'). '+pec.desc;
  }

  if(type==='openmic'){
    let unlockNote = '';
    if (!s.persona.unlocked.includes('spoken_word')) {
      s.persona.unlocked.push('spoken_word');
      s.persona.current = 'spoken_word';
      s.persona.history.push({stage:'spoken_word', day:s.day, note:'Attended first Open Mic. Unlocked Spoken Word: your verses meet a live audience.'});
      unlockNote = ' [TEACHABLE MOMENT: Spoken Word Unlocked! Words leave the page; delivery and breath now matter.]';
    }

    const isRepeat = (s.last_submitted_poem === s.poem.trim());
    s.last_submitted_poem = s.poem.trim();

    let repGain = isRepeat ? 2 : 4;
    let delGain = isRepeat ? 1 : 2;
    let rhymeBonus = 0;
    let rhymeMsg = '';

    if (countRhymes(s.poem) >= 2) {
      rhymeBonus = Math.min(25, 10 + countRhymes(s.poem) * 2);
      s.money += rhymeBonus;
      rhymeMsg = ' Rhyme relay bonus: +₦' + rhymeBonus + '.';
    }

    s.reputation += repGain;
    s.delivery += delGain;
    msg = 'You perform at the fictional Lion’s Lines open mic. Reputation +' + repGain + '; delivery +' + delGain + '.' + (isRepeat ? ' (Repeat reading: revise your text for full gains).' : '') + rhymeMsg + unlockNote;
  }

  if(type==='slam'){
    if (!s.persona.unlocked.includes('slam')) {
      if (!s.persona.unlocked.includes('spoken_word')) {
        return {ok:false, message:'Slam is locked! Attend an Open Mic first to unlock Spoken Word, then qualify for Slam.'};
      }
      s.persona.unlocked.push('slam');
      s.persona.current = 'slam';
      s.persona.history.push({stage:'slam', day:s.day, note:'Entered the tournament arena. Unlocked Slam: 3-minute rounds and competitive scoring.'});
    }

    const isRepeat = (s.last_submitted_poem === s.poem.trim());
    s.last_submitted_poem = s.poem.trim();

    const words = s.poem.trim().split(/\s+/).length;
    const fit = arg==='intimate'?s.craft:arg==='rhythmic'?s.delivery:(s.craft+s.delivery)/2;
    let score = Math.round(35 + Math.min(15, words/8) + (s.craft+s.delivery)*.45 + fit*.3 + s.prepared*3 + s.research*2 + rand(s)*10);
    
    let rhymeMsg = '';
    if (countRhymes(s.poem) >= 2) {
      const scoreBonus = Math.min(6, countRhymes(s.poem));
      score += scoreBonus;
      rhymeMsg = ' (Rhyme precision: +' + scoreBonus + ' pts)';
    }

    const rivals = s.npcs.filter(n=>n.goal==='compete').map(n=>({name:n.name, score:Math.round(45 + n.skill*.7 + rand(s)*15)}));
    const rank = 1 + rivals.filter(n=>n.score >= score).length;
    s.entered.push(s.day);

    let repGain = rank===1 ? 10 : 3;
    let prize = rank===1 ? 700 : 0;
    if (isRepeat) {
      repGain = Math.max(1, Math.floor(repGain / 2));
      prize = Math.floor(prize * 0.75);
    }

    s.reputation += repGain;
    s.money += prize;
    msg = 'Fictional slam: ' + score + ' points' + rhymeMsg + '; place ' + rank + ' of ' + (rivals.length+1) + '. ' + rivals.map(n=>n.name+': '+n.score).join(' · ') + '. ' + (rank===1?'Prize +₦'+prize+'.':'Reputation +'+repGain+' for showing up.') + (isRepeat ? ' (Unrevised draft: prize/reputation discounted).' : '') + ' Game points reflect preparation, delivery choice and chance; they are not a literary verdict.';
    s.prepared = 0;
    s.research = 0;
  }

  note(s, msg);
  return {ok:true, message:msg};
}

function exportPoem(s) {
  if (!s.poem || !s.poem.trim()) return '';
  const linesCount = s.poem.trim().split('\n').length;
  const wordCount = s.poem.trim().split(/\s+/).length;
  const rhymes = countRhymes(s.poem);
  const city = s.city || 'Ogbomoso';
  const stage = s.persona ? s.persona.current.toUpperCase() : 'PAGE';
  
  return [
    '# ' + (s.name || 'New Voice') + ' - Untitled Draft',
    '',
    s.poem.trim(),
    '',
    '—',
    '*Composed on Day ' + s.day + ' in ' + city + ' (' + stage + ' Poet)*',
    '*Metrics: ' + wordCount + ' words, ' + linesCount + ' lines, ' + rhymes + ' detected rhyme pairs*',
    '*Command Center Gravity: Poetics Literary Simulation*'
  ].join('\n');
}

function valid(s){
  return s &&
    (!s.opportunities || (
      Array.isArray(s.opportunities.read) && s.opportunities.read.every(x => typeof x === 'string') &&
      s.opportunities.submissions && typeof s.opportunities.submissions === 'object' && !Array.isArray(s.opportunities.submissions) &&
      Object.values(s.opportunities.submissions).every(e => e && typeof e.poem === 'string' && e.poem.length <= 4000 && typeof e.author === 'string' && Number.isInteger(e.day) && Number.isInteger(e.deadline) && Number.isFinite(e.craft) && ['competition','anthology'].includes(e.type)) &&
      s.opportunities.resolved && typeof s.opportunities.resolved === 'object' && !Array.isArray(s.opportunities.resolved) &&
      Object.values(s.opportunities.resolved).every(e => e && typeof e.message === 'string' && typeof e.success === 'boolean' && Number.isInteger(e.day))
    )) &&
    s.version === 1 &&
    Number.isInteger(s.day) && s.day > 0 &&
    Number.isInteger(s.seed) &&
    typeof s.poem === 'string' && s.poem.length <= 4000 &&
    typeof s.name === 'string' && s.name.length <= 40 &&
    ['Ogbomoso','Ibadan','Lagos','Jos','Enugu','Abuja','Aba'].includes(s.city) &&
    ['energy','money','craft','delivery','reputation','prepared','research'].every(k => Number.isFinite(s[k]) && s[k] >= 0) &&
    s.energy <= 100 &&
    Array.isArray(s.npcs) && s.npcs.length === 12 &&
    s.npcs.every((n,i) => n.id === i && n.style === roster[i][1] && n.goal === roster[i][2] && ['relationship','skill','funds','works'].every(k => Number.isFinite(n[k]) && n[k] >= 0) && typeof n.activity === 'string' && Array.isArray(n.memory) && n.memory.every(x => typeof x === 'string')) &&
    Array.isArray(s.wall) && s.wall.length <= 40 &&
    s.wall.every(p => typeof p.author === 'string' && p.author.length <= 40 && typeof p.text === 'string' && p.text.length <= 4000 && Number.isInteger(p.day) && p.fiction === true) &&
    Number.isInteger(s.posts) && s.posts >= 0 &&
    Array.isArray(s.log) && s.log.length <= 80 && s.log.every(x => typeof x === 'string') &&
    Array.isArray(s.entered) && s.entered.every(d => Number.isInteger(d) && d > 0);
}

const api = {create, act, tick, valid, exportPoem, cityPeculiarities};
if(typeof module !== 'undefined') module.exports = api;
root.PoeticsEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);