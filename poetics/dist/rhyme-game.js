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
    this.lastSubmitTime = null;
  }

  start(onTick, onEnd) {
    this.active = true;
    this.score = 0;
    this.streak = 0;
    this.wordsMatched = [];
    this.timeLeft = this.duration;
    this.prompt = getRhymeSprintPrompt();
    this.lastSubmitTime = Date.now();

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
    const nowTime = Date.now();
    const timeSinceLastSubmit = this.lastSubmitTime ? (nowTime - this.lastSubmitTime) / 1000 : 0;
    this.lastSubmitTime = nowTime;

    if (!res.valid) {
      this.streak = 0;
      return { ok: false, message: res.reason, score: this.score };
    }

    // Dynamic streak timer: if more than 5 seconds between valid submissions, reset streak
    if (timeSinceLastSubmit > 5) {
      this.streak = 1;
    } else {
      this.streak++;
    }

    if (this.streak > this.longestStreak) this.longestStreak = this.streak;

    // Cap streak multiplier at 2.0 (e.g. max 5 streak factor)
    const streakMultiplier = Math.min(2.0, 1 + (this.streak - 1) * 0.2);
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

if (typeof module !== 'undefined') module.exports = api;
root.PoeticsRhymeGame = api;

})(typeof window !== 'undefined' ? window : globalThis);
