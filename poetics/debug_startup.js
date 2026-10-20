const fs = require('fs');
const current = fs.readFileSync('dist/index.html', 'utf8');
const baseline = fs.readFileSync('dist/atlas-preview-75.html', 'utf8');

function asset(name){
  const p = 'dist/' + name;
  if(fs.existsSync(p)) return fs.readFileSync(p);
  if(name === 'contribute.676d669df152.js') return fs.readFileSync('test-fixtures/' + name);
  throw Error('Missing referenced asset: ' + name);
}

const initial = index => [...index.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g)].map(m => asset(m[1]));
const assetsA = initial(baseline);
const assetsB = initial(current);
const sum = a => a.reduce((n,b) => n + b.length, 0);

console.log('sum(assetsA):', sum(assetsA), 'sum(assetsB):', sum(assetsB), 'ratio:', sum(assetsB)/sum(assetsA));
console.log('baseline files:', [...baseline.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g)].map(m => m[1]));
console.log('current files:', [...current.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g)].map(m => m[1]));
