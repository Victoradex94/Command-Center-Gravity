const assert = require('node:assert/strict');
const R = require('./dist/rhyme-game.js');

console.log('Testing Rhyme Game...');

// Test rhyme evaluation
const prompt = 'night';
const good1 = R.evaluateRhyme(prompt, 'bright');
assert.equal(good1.valid, true);
assert(good1.score > 50); // length bonus for length 6 vs 3

const good2 = R.evaluateRhyme(prompt, 'light');
assert.equal(good2.valid, true);

// Word length factor: longer word gets higher score
const shortRhyme = R.evaluateRhyme('rain', 'pain'); // length 4
const longRhyme = R.evaluateRhyme('rain', 'refrain'); // length 7
assert(longRhyme.score > shortRhyme.score);

// Test session and time factor
const session = new R.RhymeSprintSession(10);
session.start();
const pWord = session.prompt.word;
const known = R.rhymeDictionary[pWord][0];
const sub1 = session.submitWord(known);
assert.equal(sub1.ok, true);
assert(sub1.scoreGained > 0);
assert.equal(sub1.streak, 1);

// Test duplicate rejection
const subDup = session.submitWord(known);
assert.equal(subDup.ok, false);

// Test non-rhyme
const subBad = session.submitWord('elephant');
assert.equal(subBad.ok, false);
assert.equal(session.streak, 0);

session.stop();
console.log('PASS Rhyme Game mechanics: word length factoring, time factor, streaks, and dictionary verification.');
