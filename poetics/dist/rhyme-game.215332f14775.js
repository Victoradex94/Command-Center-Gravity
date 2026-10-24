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
  const p = String(promptWord??'').trim().toLowerCase();
  const c = String(candidateWord??'').trim().toLowerCase();
  if(c.length>64||!/^\p{L}[\p{L}\p{M}]*(?:['’-][\p{L}\p{M}]+)*$/u.test(c))return {valid:false,reason:"Enter one word using letters"};
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
    this.duration=Math.max(1,Math.min(300,Math.floor(Number(durationSeconds)||30)));
    this.timeLeft=this.duration;this.score=0;this.streak=0;this.longestStreak=0;
    this.wordsMatched=[];this.usedWords=new Set();this.prompt=getRhymeSprintPrompt();
    this.active=false;this.timerId=null;this.generation=0;this.streakDeadline=0;
  }
  start(onTick,onEnd) {
    this.stop();const generation=++this.generation;
    this.active=true;this.score=0;this.streak=0;this.longestStreak=0;this.wordsMatched=[];this.usedWords=new Set();
    this.timeLeft=this.duration;this.endsAt=Date.now()+this.duration*1000;this.streakDeadline=0;this.onEnd=onEnd;
    this.mountFeedback();this.paintFeedback();
    this.routeStop=()=>this.stop();if(typeof root.addEventListener==='function')root.addEventListener('hashchange',this.routeStop);
    this.timerId=setInterval(()=>{
      if(!this.active||this.generation!==generation)return;
      this.timeLeft=Math.max(0,Math.ceil((this.endsAt-Date.now())/1000));this.expireStreak();this.paintFeedback();
      if(typeof onTick==='function')onTick(this.timeLeft,this);
      if(this.active&&this.generation===generation&&this.timeLeft<=0)this.finish();
    },1000);
  }
  expireStreak(now=Date.now()) {if(this.streak&&now>=this.streakDeadline){this.streak=0;this.streakDeadline=0;}}
  streakState(now=Date.now()) {
    this.expireStreak(now);
    return {remainingMs:this.active?Math.max(0,this.streakDeadline-now):0,windowMs:this.streakWindowMs||5000,multiplier:Math.min(2,1+Math.max(0,this.streak-1)*.2)};
  }
  submitWord(word) {
    if(!this.active)return {ok:false,message:'Sprint is not active.'};
    if(Date.now()>=this.endsAt){this.timeLeft=0;this.finish();return {ok:false,message:'Sprint has finished.'};}
    this.expireStreak();const w=String(word??'').trim().toLowerCase();
    if(this.usedWords.has(w))return {ok:false,message:'Word already submitted this round!',streak:this.streak};
    const res=evaluateRhyme(this.prompt.word,w);
    if(!res.valid){this.streak=0;this.streakDeadline=0;this.paintFeedback();return {ok:false,message:res.reason,score:this.score};}
    this.streak++;this.longestStreak=Math.max(this.longestStreak,this.streak);
    this.streakWindowMs=Math.max(2000,5000-Math.min(3000,(this.streak-1)*400));this.streakDeadline=Date.now()+this.streakWindowMs;
    const streakMultiplier=Math.min(2,1+(this.streak-1)*.2),speedFactor=Math.max(1,Math.min(2,1+this.timeLeft/this.duration));
    const totalWordScore=Math.round(res.score*streakMultiplier*speedFactor);this.score+=totalWordScore;this.wordsMatched.push(w);this.usedWords.add(w);
    this.paintFeedback(res);
    return {ok:true,scoreGained:totalWordScore,totalScore:this.score,streak:this.streak,word:w,length:res.wordLength,lengthMultiplier:res.score/50,streakMultiplier};
  }
  nextPrompt(){this.prompt=getRhymeSprintPrompt();return this.prompt;}
  finish(){if(!this.active)return;const callback=this.onEnd;this.stop();if(typeof callback==='function')callback(this);}
  stop(){
    this.active=false;this.generation++;
    if(this.timerId!==null){clearInterval(this.timerId);this.timerId=null;}
    if(this.routeStop&&typeof root.removeEventListener==='function')root.removeEventListener('hashchange',this.routeStop);
    this.routeStop=null;this.paintFeedback();
  }
  mountFeedback(){
    const doc=root.document,streak=doc?.querySelector('#rhyme-streak');if(!streak?.parentElement)return;
    let clock=doc.querySelector('#rhyme-streak-clock');
    if(!clock){clock=doc.createElement('div');clock.id='rhyme-streak-clock';clock.innerHTML='<small data-combo-note></small><div role="progressbar" aria-label="Streak time remaining" aria-valuemin="0" aria-valuemax="100" style="height:4px;background:#dce4df;border-radius:4px;overflow:hidden"><i data-combo-bar style="display:block;height:100%;background:#2a9d8f;width:0"></i></div>';streak.parentElement.appendChild(clock);}
    this.feedbackNode=clock;
  }
  paintFeedback(result){
    const clock=this.feedbackNode;if(!clock||clock.isConnected===false)return;
    const state=this.streakState(),bar=clock.querySelector('[data-combo-bar]'),note=clock.querySelector('[data-combo-note]'),progress=clock.querySelector('[role="progressbar"]');
    const remaining=Math.max(0,Math.min(100,state.remainingMs/state.windowMs*100));
    if(bar){bar.style.width=remaining+'%';bar.style.transition=root.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'none':'width 1s linear';}
    if(progress)progress.setAttribute('aria-valuenow',String(Math.round(remaining)));
    if(result)this.lastLengthMultiplier=result.score/50;
    if(note)note.textContent=!this.active?'Streak inactive':this.streak?'Length ×'+(this.lastLengthMultiplier||1).toFixed(1)+' · streak ×'+state.multiplier.toFixed(1)+' · '+(state.remainingMs/1000).toFixed(1)+'s':'Submit a rhyme to build a streak';
    const streak=root.document?.querySelector('#rhyme-streak');if(streak)streak.textContent=this.streak+'🔥';
    if(result&&!root.matchMedia?.('(prefers-reduced-motion: reduce)').matches)root.document?.querySelector('#rhyme-prompt-box')?.animate?.([{boxShadow:'0 0 0 transparent'},{boxShadow:'0 0 18px #2a9d8f88'},{boxShadow:'0 0 0 transparent'}],{duration:320});
  }
}

const api = {
  rhymeDictionary,
  getRhymeSprintPrompt,
  evaluateRhyme,
  RhymeSprintSession
};

if (typeof module !== 'undefined') module.exports = api;
root.PoeticsRhymeGame = api;

})(typeof window !== 'undefined' ? window : globalThis);
