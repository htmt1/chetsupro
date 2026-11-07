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
