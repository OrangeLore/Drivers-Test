const test = require('node:test');
const assert = require('node:assert/strict');
const security = require('../security.js');
function dataset() { return { key:'sample', name:'Sample', questions:[{q:'Which answer?', options:['A','B','C','D'],answer:0}] }; }
test('rejects attribute injection and prototype keys', () => {
  for (const key of ['x" onclick="alert(1)', '__proto__', 'constructor', '../escape']) {
    const d=dataset(); d.key=key; assert.ok(security.validateDataset(d));
  }
});
test('rejects injected difficulty, remote image and invalid numbers', () => {
  const d=dataset(); d.questions[0].diff='hard"><img src=x onerror=alert(1)>';
  assert.ok(security.validateDataset(d));
  const image=dataset(); image.questions[0].image='https://tracker.invalid/pixel';
  assert.ok(security.validateDataset(image));
  const count=dataset(); count.testSize=-2; assert.ok(security.validateDataset(count));
});
test('accepts safe imports and local images', () => {
  const d=dataset(); d.questions[0].image='images/stop.svg';
  assert.equal(security.validateDataset(d),null);
  assert.equal(d.questions[0].diff,'standard');
  assert.equal(d.testSize,1);
});
test('image allowlist blocks external fetches, SVG data and traversal', () => {
  for (const image of ['//tracker.invalid/x','javascript:alert(1)','data:image/svg+xml,<svg/>','images/../private.png','/api/kv/all','images/x.svg?track=1']) assert.equal(security.safeImage(image),'');
  assert.equal(security.safeImage('images/stop.svg'),'images/stop.svg');
});
