const assert=require('node:assert/strict');
const E=require('./dist/engine.js');

const s=E.create();
s.energy=100;
s.money=10000;
s.poem='A cat sat on a mat with a bat and a hat. This is very long and has many rhymes inside.';

const beforeMic=s.money;
const mic=E.act(s,'openmic');
assert(mic.ok);
assert(mic.message.includes('Rhyme relay bonus'));
assert.equal(s.money,beforeMic-150+25);

const slam=E.act(s,'slam','rhythmic');
assert(slam.ok);
assert(slam.message.includes('Rhyme precision'));
console.log('Rhyme relay and slam scoring passed.');
