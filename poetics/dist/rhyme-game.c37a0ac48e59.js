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

function normalizeWord(value) {
  return String(value ?? '').trim().toLowerCase().replace(/[’‘]/g, "'");
}

function pronunciationRimes(word) {
  const lexicon = root.PoeticsRhymeLexicon;
  const keys = lexicon?.wordRimes?.[normalizeWord(word)];
  return Array.isArray(keys) ? keys : [];
}

function evaluateRhyme(promptWord, candidateWord) {
  const p = normalizeWord(promptWord);
  const c = normalizeWord(candidateWord);
  if(c.length>64||!/^\p{L}[\p{L}\p{M}]*(?:['’-][\p{L}\p{M}]+)*$/u.test(c))return {valid:false,reason:"Enter one word using letters"};
  if (!c || c === p) return { valid: false, reason: "Same word or empty" };
  if (c.length < 2) return { valid: false, reason: "Too short" };

  const known = rhymeDictionary[p] || [];
  const candidateRimes = pronunciationRimes(c);
  const isCuratedNearRhyme = known.includes(c) && candidateRimes.length > 0;
  const promptRimes = pronunciationRimes(p);
  if (!root.PoeticsRhymeLexicon?.wordRimes) return { valid: false, reason: "The pronunciation dictionary is not loaded yet" };
  if (!candidateRimes.length && !isCuratedNearRhyme) return { valid: false, reason: "Word not found in the pronunciation dictionary" };
  const rimeSet = new Set(promptRimes);
  const phoneticMatch = candidateRimes.some(rime => rimeSet.has(rime));
  const valid = isCuratedNearRhyme || phoneticMatch;
  if (!valid) return { valid: false, reason: "The word is recognised, but its pronunciation does not rhyme with the prompt" };

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

let screenGeneration = 0;
let activeScreenSession = null;

async function renderScreen(main, onBack, isCurrent = () => true) {
  const generation = ++screenGeneration;
  activeScreenSession?.stop();
  activeScreenSession = null;
  main.innerHTML = `<section class="page-top"><button id="rhyme-load-back" class="btn">← Back to Games</button><h1>Rhyme Sprint</h1><p class="caption" role="status">Loading the pronunciation dictionary…</p></section>`;
  const backButton = main.querySelector('#rhyme-load-back');
  backButton.onclick = () => { screenGeneration++; onBack?.(); };

  try {
    await root.PoeticsLoadAsset('rhyme-lexicon');
    if (!root.PoeticsRhymeLexicon?.wordRimes) throw new Error('Pronunciation dictionary unavailable');
  } catch {
    if (generation !== screenGeneration || !isCurrent()) return null;
    main.innerHTML = `<section class="page-top"><h1>Rhyme Sprint could not load its word list.</h1><p>Check your connection and retry. Your game progress is unchanged.</p><button id="rhyme-load-retry" class="primary">Try again</button><button id="rhyme-load-back" class="btn">Back to Games</button></section>`;
    main.querySelector('#rhyme-load-retry').onclick = () => renderScreen(main, onBack, isCurrent);
    main.querySelector('#rhyme-load-back').onclick = () => { screenGeneration++; onBack?.(); };
    return null;
  }
  if (generation !== screenGeneration || !isCurrent()) return null;

  const session = new RhymeSprintSession(30);
  activeScreenSession = session;
  main.innerHTML = `
    <div class="page-top">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
        <button id="btn-back-hub" class="btn" style="padding:4px 10px;font-size:12px;">← Back to Games</button>
        <span class="stage-badge" style="background:#f77f00;border-color:#f77f00;color:#fff;">Rhyme Sprint</span>
      </div>
      <h1>The Rhyme Sprint</h1>
      <p>Submit real words that rhyme with the prompt before the timer expires. Rhymes are checked by pronunciation, not just spelling.</p>
    </div>
    <section class="panel" style="max-width:680px;margin:20px auto;padding:24px;text-align:center;">
      <div style="display:flex;justify-content:space-around;align-items:center;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:14px;margin-bottom:20px;">
        <div><span style="font-size:12px;color:#8b949e;text-transform:uppercase;">Time Remaining</span><div id="rhyme-timer" style="font-size:32px;font-weight:800;color:#58a6ff;">30s</div></div>
        <div><span style="font-size:12px;color:#8b949e;text-transform:uppercase;">Score</span><div id="rhyme-score" style="font-size:32px;font-weight:800;color:#f77f00;">0</div></div>
        <div><span style="font-size:12px;color:#8b949e;text-transform:uppercase;">Current Streak</span><div id="rhyme-streak" style="font-size:32px;font-weight:800;color:#2a9d8f;">0🔥</div></div>
      </div>
      <div id="rhyme-prompt-box" style="background:rgba(255,255,255,0.04);border:2px dashed rgba(255,255,255,0.2);border-radius:10px;padding:24px;margin-bottom:20px;">
        <span style="font-size:13px;color:#8b949e;text-transform:uppercase;letter-spacing:1px;">Rhyme Against Prompt</span>
        <h2 id="rhyme-prompt-word" style="font-size:42px;margin:8px 0;color:#fff;letter-spacing:1px;">${session.prompt.word.toUpperCase()}</h2>
        <p class="caption" style="margin:0;">Spelling clue only: <strong>${session.prompt.targetEndings.join(', ')}</strong></p>
      </div>
      <form id="rhyme-input-form" style="display:flex;gap:10px;max-width:480px;margin:0 auto 16px;">
        <input id="rhyme-word-input" autocomplete="off" placeholder="Type a real rhyming word…" required style="flex:1;padding:12px 16px;font-size:16px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);background:rgba(0,0,0,0.4);color:#fff;">
        <button type="submit" class="primary" style="padding:12px 20px;font-size:16px;cursor:pointer;">Submit</button>
      </form>
      <div id="rhyme-feedback" role="status" aria-live="polite" style="min-height:24px;font-size:14px;font-weight:600;margin-bottom:16px;"></div>
      <div style="text-align:left;background:rgba(0,0,0,0.2);border-radius:6px;padding:12px;border:1px solid rgba(255,255,255,0.06);">
        <strong style="font-size:12px;color:#8b949e;text-transform:uppercase;">Matched Words This Round:</strong>
        <div id="rhyme-matches-list" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;"><span style="font-size:13px;color:#6e7681;font-style:italic;">No matches yet…</span></div>
      </div>
      <p class="caption">Pronunciations: CMUdict, North American English. Local pronunciation additions are reviewed separately. <a href="https://github.com/cmusphinx/cmudict" target="_blank" rel="noopener">Source and credits</a>.</p>
      <div id="rhyme-gameover-dialog" style="display:none;margin-top:20px;padding:20px;background:rgba(47,111,235,0.15);border:1px solid #2f6feb;border-radius:8px;">
        <h3 style="margin:0 0 6px;color:#fff;">Sprint Finished!</h3><p id="rhyme-final-summary" style="font-size:16px;margin:0 0 16px;color:#e6edf3;"></p><button id="btn-replay-rhyme" class="primary" style="padding:10px 20px;font-size:15px;cursor:pointer;">Play Again</button>
      </div>
    </section>`;

  const query = selector => main.querySelector(selector);
  const timer = query('#rhyme-timer'), score = query('#rhyme-score'), streak = query('#rhyme-streak');
  const feedback = query('#rhyme-feedback'), matches = query('#rhyme-matches-list'), input = query('#rhyme-word-input');
  query('#btn-back-hub').onclick = () => { session.stop(); activeScreenSession = null; onBack?.(); };
  session.start(seconds => { timer.textContent = seconds + 's'; if (seconds <= 5) timer.style.color = '#e63946'; }, finished => {
    timer.textContent = '0s'; query('#rhyme-input-form').style.display = 'none'; query('#rhyme-gameover-dialog').style.display = 'block';
    query('#rhyme-final-summary').innerHTML = `Final Score: <strong>${finished.score}</strong> points across <strong>${finished.wordsMatched.length}</strong> rhyming words! Longest Streak: <strong>${finished.longestStreak}</strong>🔥`;
  });
  query('#rhyme-input-form').onsubmit = event => {
    event.preventDefault(); const result = session.submitWord(input.value); input.value = '';
    streak.textContent = session.streak + '🔥'; feedback.style.color = result.ok ? '#2a9d8f' : '#e63946';
    feedback.textContent = result.ok ? `✓ '${result.word}' matched! (+${result.scoreGained} pts, length ${result.length})` : `✗ ${result.message}`;
    if (result.ok) { score.textContent = result.totalScore; matches.innerHTML = session.wordsMatched.map(word => `<span style="background:rgba(42,157,143,0.2);border:1px solid #2a9d8f;color:#e6edf3;padding:3px 8px;border-radius:4px;font-size:12px;">${word} (${word.length})</span>`).join(''); }
    input.focus();
  };
  query('#btn-replay-rhyme').onclick = () => renderScreen(main, onBack, isCurrent);
  input.focus();
  return session;
}

const api = {
  rhymeDictionary,
  getRhymeSprintPrompt,
  evaluateRhyme,
  RhymeSprintSession,
  pronunciationRimes,
  renderScreen
};

if (typeof module !== 'undefined') module.exports = api;
root.PoeticsRhymeGame = api;

})(typeof window !== 'undefined' ? window : globalThis);
