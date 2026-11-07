// Run after extracting site.zip and applying the checked updates.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2] || '_site/geki.html', 'utf8');
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)];
let checked = 0;
for (const [, attrs, code] of scripts) {
  if (/type=["'](?:application\/json|text\/plain|javascript\/worker)/.test(attrs)) continue;
  try { new vm.Script(code); checked++; } catch (error) { throw Error(attrs + ': ' + error.message); }
}
const start = html.indexOf('const GekiOperationCatalog = '), end = html.indexOf('</script>', start);
const context = { module: { exports: {} } }; vm.createContext(context);
vm.runInContext(html.slice(start, end), context);
const { shrineBoxPlan } = context.module.exports;
const plan = (remaining, transit) => shrineBoxPlan({ target: 43 + remaining, current: 39, overhead: 4, boxTransit: transit });
assert.equal(plan(100, 0).births, 2); assert.equal(plan(100, 0).boxes, 12);
assert.equal(plan(100, '').births, 50); assert.equal(plan(100, '').boxes, 0);
assert.equal(plan(100, 4).births, 0); assert.equal(plan(100, 4).boxes, 12);
assert.equal(plan(0, 0).boxes, 0); assert.equal(plan(13, 0), null);
assert.equal(plan(15, 1).boxes, 1); assert.equal(plan(15, 1).births, 3);
assert.throws(() => plan(100, -1)); assert.throws(() => plan(100, 0.5));
// Compare the chosen mix against exhaustive search, including route overhead.
for (let n = 0; n <= 400; n++) for (let t = 0; t < 20; t++) {
  const actual = plan(n, t), costs = [];
  if (n % 2 === 0) costs.push(n);
  for (let boxes = 1; boxes * 8 + t <= n; boxes++) {
    const rest = n - boxes * 8 - t;
    if (rest % 2 === 0) costs.push((boxes + rest / 2) * 2);
  }
  assert.equal(actual?.presses ?? null, costs.length ? Math.min(...costs) : null);
  if (actual) assert.equal(actual.births * 2 + actual.boxes * 8 + actual.transit, n);
}
console.log('PASS: ' + checked + ' scripts parsed; mixed planner agrees with 8,020 exhaustive cases.');

// Provided hardware observation: fast start, six previews, first entry at draw 43.
const core = scripts.find(([,attrs,code]) => !attrs.includes("type=") && code.includes("class RareEngine"));
const engineContext = { module: {exports:{}} }; vm.createContext(engineContext);vm.runInContext(core[2],engineContext);
const rstart=html.indexOf('class GekiStateRng {'),rend=html.indexOf('class GekiMasterScanner',rstart);
vm.runInContext(html.slice(rstart,rend)+';this.Rng=GekiStateRng;',engineContext);
const rng=new engineContext.Rng([0,0,0,0]);rng.init(3258188431);rng.skip(42);const pool=rng.next();assert.equal(pool,0xC73BC117);
const engine=new engineContext.module.exports.RareEngine(JSON.parse(html.match(/<script id="embeddedData"[^>]*>([\s\S]*?)<\/script>/)[1]));
assert.equal(engine.generate(pool,[])[2].name,'しずく');
for(const [target,births,boxes] of [[43,0,0],[45,1,0],[51,0,1],[53,1,1]]) {
 const out=shrineBoxPlan({target,current:39,overhead:4,boxTransit:0});assert.equal(out.births,births);assert.equal(out.boxes,boxes);
}
assert.equal(shrineBoxPlan({target:44,current:39,overhead:4,boxTransit:0}),null);
assert.equal(shrineBoxPlan({target:43,current:39,overhead:4,boxTransit:0}).remaining,0);
console.log('PASS: supplied fast-route pool and 43/45/51/53 step counts');

const {capturePlan,captureText,captureRows}=context.module.exports;
// Independent exact DP: opening the book once costs 10 draws / 4 inputs;
// a cursor movement while it remains open costs 10 draws / 1 input.
for(const transit of [null,0,1,2,3,4,8,17]) {
 const size=2000,cost=Array.from({length:size+1},()=>Array(4).fill(Infinity));cost[0][0]=0;
 for(let n=0;n<=size;n++)for(let flags=0;flags<4;flags++){
  const moves=[[2,2,flags]];
  if(transit!==null)moves.push([8+(flags&1?0:transit),2,flags|1]);
  moves.push([10,flags&2?1:4,flags|2]);
  for(const [draws,inputs,next] of moves)if(n+draws<=size)cost[n+draws][next]=Math.min(cost[n+draws][next],cost[n][flags]+inputs);
 }
 for(let n=0;n<=size;n++){
  const p=capturePlan({target:n+43,current:39,overhead:4,boxTransit:transit});const expected=Math.min(...cost[n]);
  assert.equal(p?.presses??Infinity,expected,'continuous book at '+n+' transit '+transit);
  if(p)assert.equal(p.births*2+p.boxes*8+(p.bookVisits?10+p.scrolls*10:0)+p.transit,n);
 }
}
for(const [n,scrolls] of [[10,0],[20,1],[30,2]]){
 const p=capturePlan({target:43+n,current:39,overhead:4,boxTransit:0});assert.equal(p.bookVisits,1);assert.equal(p.scrolls,scrolls);
}
const screenshot=capturePlan({target:9083,current:39,overhead:4,boxTransit:0});assert.equal(screenshot.bookVisits,1);assert.equal(screenshot.scrolls,903);assert.equal(screenshot.births,0);assert.equal(screenshot.boxes,0);
const rows=captureRows(screenshot);assert.equal(rows.length,1);assert.equal(rows[0].unit,'スクロール');assert.equal(rows[0].count,903);assert(!captureText(screenshot).includes('セット'));assert(!captureText(screenshot).includes('出生確認'));
const large=capturePlan({target:4000000043,current:39,overhead:4,boxTransit:0});assert.equal(large.births*2+large.boxes*8+(large.bookVisits?10+large.scrolls*10:0),4000000000);
console.log('PASS: continuous book matches 16,008 exact cases; 9083 uses one opening and 903 scrolls');

const openOnly=captureRows(capturePlan({target:53,current:39,overhead:4,boxTransit:0}));assert.equal(openOnly[0].count,1);assert.equal(openOnly[0].unit,'回');assert.equal(openOnly[0].label,'記録手帳を開閉');
