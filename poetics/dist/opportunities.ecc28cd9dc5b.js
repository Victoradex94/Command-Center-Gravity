(function(root){
'use strict';
const types=['openmic','slam','competition','anthology'];
function ensure(s){if(!s.opportunities)s.opportunities={read:[],submissions:{},resolved:{}};return s.opportunities;}
function list(s){const week=Math.floor((s.day-1)/7),o=ensure(s),out=[];for(let w=Math.max(0,week-1);w<=week;w++){const start=w*7+1;for(const [i,type]of types.entries()){const open=start+(type==='competition'?1:0),deadline=start+[1,2,5,6][i],id=w+'-'+type;const names={openmic:'Lion’s Lines open mic',slam:'Under-Verse slam',competition:'LadoTech writing competition',anthology:'Small Rooms anthology call'};const n={id,type,title:names[type],open,deadline,week:w,fiction:true,submitted:!!o.submissions[id],result:o.resolved[id]||null,unread:!o.read.includes(o.resolved[id]?id+'-result':id)};if(open<=s.day)out.push(n);}}return out.sort((a,b)=>b.week-a.week||a.deadline-b.deadline);}
function markRead(s,id){const o=ensure(s);if(!o.read.includes(id))o.read.push(id);if(o.resolved[id]&&!o.read.includes(id+'-result'))o.read.push(id+'-result');o.read=o.read.slice(-80);}
function submit(s,id){const n=list(s).find(x=>x.id===id);if(!n||!['competition','anthology'].includes(n.type))return {ok:false,message:'Choose a writing competition or anthology call.'};if(s.day>n.deadline)return {ok:false,message:'This call is closed.'};const o=ensure(s);if(o.submissions[id])return {ok:false,message:'Your poem is already submitted to this call.'};if(s.poem.trim().length<40)return {ok:false,message:'Write at least 40 characters before submitting.'};const energy=n.type==='competition'?20:10,money=n.type==='competition'?250:0;if(s.energy<energy||s.money<money)return {ok:false,message:'You need '+energy+' energy and ₦'+money+' for this submission.'};s.energy-=energy;s.money-=money;o.submissions[id]={poem:s.poem,author:s.name,day:s.day,craft:s.craft,deadline:n.deadline,type:n.type};markRead(s,id);const message='Submitted to fictional '+n.title+'. Result after day '+n.deadline+'. Your original poem remains on this device.';s.log.unshift(message);s.log=s.log.slice(0,80);return {ok:true,message};}
function onDay(s){const o=ensure(s);for(const [id,entry]of Object.entries(o.submissions)){if(s.day<=entry.deadline||o.resolved[id])continue;const hash=[...entry.poem+id].reduce((h,c)=>(Math.imul(h,31)+c.charCodeAt(0))>>>0,17);const success=entry.craft>=18||hash%3===0;const message=entry.type==='anthology'?(success?'Your poem was selected for the fictional Small Rooms anthology.':'The fictional anthology editors passed on this poem. Another call will open.'):(success?'You placed in the fictional LadoTech writing competition.':'Your fictional competition entry was not shortlisted.');o.resolved[id]={day:s.day,success,message};s.reputation+=success?4:1;if(success&&entry.type==='competition')s.money+=500;s.log.unshift(message+' Simulation outcome, not a literary verdict.');s.log=s.log.slice(0,80);}const oldest=Math.floor((s.day-1)/7)-8;for(const id of Object.keys(o.submissions))if(+id.split('-')[0]<oldest){delete o.submissions[id];delete o.resolved[id];}}
const api={ensure,list,markRead,submit,onDay};if(typeof module!=='undefined')module.exports=api;root.PoeticsOpportunities=api;
})(typeof window!=='undefined'?window:globalThis);

(function(root){
'use strict';

const rhymeDictionary = {
  // Common poetic bases and rhyming word sets
  "night": ["light", "bright", "sight", "flight", "fight", "tight", "white", "knight", "height"],
  "heart": ["art", "part", "start", "dart", "chart", "smart", "apart", "depart"],
  "fire": ["desire", "wire", "inspire", "admire", "higher", "prior", "choir"],
  "rain": ["pain", "gain", "drain", "train", "chain", "stain", "remain", "refrain", "explain"],
  "voice": ["choice", "rejoice", "poise", "noise"],
  "road": ["load", "abode", "code", "bestowed", "implode", "overflowed"],
  "stone": ["bone", "alone", "throne", "unknown", "grown", "thrown"],
  "sound": ["ground", "bound", "round", "profound", "found", "around"],
  "dream": ["stream", "beam", "gleam", "seem", "redeem", "scheme", "supreme"],
  "sky": ["high", "fly", "cry", "sigh", "tie", "rely", "defy", "supply"],
  "sun": ["one", "run", "done", "begun", "spun", "won"],
  "word": ["heard", "bird", "occurred", "stirred", "preferred", "deferred"],
  "stage": ["page", "age", "rage", "sage", "cage", "engage", "gauge"],
  "crowd": ["loud", "proud", "cloud", "shroud", "avowed", "unbowed"],
  "breath": ["death", "depth"],
  "beat": ["feet", "street", "meet", "sweet", "complete", "defeat", "repeat"],
  "song": ["long", "strong", "along", "belong", "prolong"]
};

const wordPrompts = Object.keys(rhymeDictionary);

function getRhymeSprintPrompt() {
  const idx = Math.floor(Math.random() * wordPrompts.length);
  const word = wordPrompts[idx];
  return {
    word: word,
    targetEndings: [word.slice(-3), word.slice(-2)],
    knownRhymes: rhymeDictionary[word] || []
  };
}

function evaluateRhyme(promptWord, candidateWord) {
  const p = promptWord.trim().toLowerCase();
  const c = candidateWord.trim().toLowerCase();
  if (!c || c === p) return { valid: false, reason: "Same word or empty" };
  if (c.length < 2) return { valid: false, reason: "Too short" };

  const known = rhymeDictionary[p] || [];
  const isKnown = known.includes(c);
  
  // Phonetic/suffix check: ending match of 2-3 characters or known dictionary match
  const suffixMatch = (c.length >= 3 && p.length >= 3 && c.slice(-3) === p.slice(-3)) ||
                      (c.slice(-2) === p.slice(-2) && (c.slice(-3, -2) !== p.slice(-3, -2) || isKnown));

  const valid = isKnown || suffixMatch;
  if (!valid) return { valid: false, reason: "Does not rhyme" };

  // Length scoring: longer words give bonus points
  const lengthBonus = Math.max(0, c.length - 3) * 15;
  const basePoints = 50;
  const score = basePoints + lengthBonus;

  return {
    valid: true,
    score: score,
    wordLength: c.length,
    lengthBonus: lengthBonus,
    word: c
  };
}

class RhymeSprintSession {
  constructor(durationSeconds = 30) {
    this.duration = durationSeconds;
    this.timeLeft = durationSeconds;
    this.score = 0;
    this.streak = 0;
    this.longestStreak = 0;
    this.wordsMatched = [];
    this.prompt = getRhymeSprintPrompt();
    this.active = false;
    this.timerId = null;
  }

  start(onTick, onEnd) {
    this.active = true;
    this.score = 0;
    this.streak = 0;
    this.wordsMatched = [];
    this.timeLeft = this.duration;
    this.prompt = getRhymeSprintPrompt();

    if (this.timerId) clearInterval(this.timerId);
    this.timerId = setInterval(() => {
      this.timeLeft--;
      if (typeof onTick === 'function') onTick(this.timeLeft, this);
      if (this.timeLeft <= 0) {
        this.stop();
        if (typeof onEnd === 'function') onEnd(this);
      }
    }, 1000);
  }

  submitWord(word) {
    if (!this.active) return { ok: false, message: "Sprint is not active." };
    const w = word.trim().toLowerCase();
    if (this.wordsMatched.includes(w)) {
      return { ok: false, message: "Word already submitted this round!" };
    }
    const res = evaluateRhyme(this.prompt.word, w);
    if (!res.valid) {
      this.streak = 0;
      return { ok: false, message: res.reason, score: this.score };
    }

    this.streak++;
    if (this.streak > this.longestStreak) this.longestStreak = this.streak;
    const streakMultiplier = 1 + (this.streak - 1) * 0.2;
    // Speed factor: submitting faster in earlier seconds awards higher velocity points
    const speedFactor = Math.max(1, Math.min(2, 1 + (this.timeLeft / this.duration)));
    const totalWordScore = Math.round(res.score * streakMultiplier * speedFactor);
    this.score += totalWordScore;
    this.wordsMatched.push(w);

    return {
      ok: true,
      scoreGained: totalWordScore,
      totalScore: this.score,
      streak: this.streak,
      word: w,
      length: res.wordLength
    };
  }

  nextPrompt() {
    this.prompt = getRhymeSprintPrompt();
    this.wordsMatched = [];
    return this.prompt;
  }

  stop() {
    this.active = false;
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }
}

const api = {
  rhymeDictionary,
  getRhymeSprintPrompt,
  evaluateRhyme,
  RhymeSprintSession
};

if (typeof module !== 'undefined') { Object.assign(module.exports, api); }
root.PoeticsRhymeGame = api;

})(typeof window !== 'undefined' ? window : globalThis);
