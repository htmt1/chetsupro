// Read-only analysis. Usage: node scripts/verify-geki-dumps.cjs _site/geki.html /path/to/dumps
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2], 'utf8'), folder = process.argv[3];
const a = html.indexOf('class GekiStateRng {'), b = html.indexOf('class GekiMasterScanner', a);
const context = {}; vm.createContext(context); vm.runInContext(html.slice(a, b) + ';this.Rng=GekiStateRng;', context);
const cases = [
  { seed: 2660044353, prefix: '2015-08-18T02-1', positions: [39,39,40], poolDraw: 43, pool: 0xC50994F4 },
  { seed: 1351027955, prefix: '2015-08-17T21-', positions: [39,41,42], poolDraw: 45, pool: 0x2FDCE1F7 },
  { seed: 2956948135, prefix: '2015-08-18T02-3', positions: [39,41,42], poolDraw: 45, pool: 0x96BE2F86 }
];
const offset = 0x005A8CFC - 0x00100000;
for (const c of cases) {
  const files = fs.readdirSync(folder).filter(f => f.endsWith('.bin') && f.includes(c.prefix)).sort();
  assert.equal(files.length, 3, 'Expected three dumps per case');
  const states = files.map(f => {
    const data = fs.readFileSync(path.join(folder, f));
    assert.ok(data.length >= offset + 16, 'Truncated dump');
    return [0,1,2,3].map(i => data.readUInt32LE(offset + i * 4));
  });
  const rng = new context.Rng([0,0,0,0]); rng.init(c.seed);
  const found = states.map(() => null); let output;
  for (let n=0; n<=100000; n++) {
    for (const [i,s] of states.entries()) if (found[i] === null && rng.state().every((x,j) => j ? x===s[j] : (x&0x7fffffff)===(s[j]&0x7fffffff))) found[i]=n;
    const v = rng.next(); if (n+1 === c.poolDraw) output=v;
    if (found.every(n => n!==null) && n+1 >= c.poolDraw) break;
  }
  assert.deepEqual(found, c.positions); assert.equal(output, c.pool);
  console.log(JSON.stringify({ bootSeed:c.seed, positions:found, toPrepay:found[1]-found[0], payment:found[2]-found[1], poolDraw:c.poolDraw, poolSeed:output.toString(16).padStart(8,'0').toUpperCase() }));
}
