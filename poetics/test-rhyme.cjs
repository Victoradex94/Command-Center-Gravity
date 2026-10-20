const assert=require('node:assert/strict');
const E=require('./dist/engine.js');
let passed = false;
for (let i = 0; i < 50; i++) {
    const s2 = E.create(100 + i);
    s2.money = 10000;
    s2.energy = 100;
    s2.poem = "A cat sat on a mat with a bat and a hat. This is very long and has many rhymes inside.";
    let result2 = E.act(s2, 'openmic');
    if (result2.message.includes('double') || result2.message.includes('loved your rhymes')) {
        passed = true;
        console.log("Random Seed:", 100 + i);
        console.log(result2.message);
        break;
    }
}
if(!passed) console.log("Failed to find rhyme");
