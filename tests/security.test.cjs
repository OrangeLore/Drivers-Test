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

const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
function builtins(){
  const ctx={window:{}};vm.createContext(ctx);
  for(const f of ['ontario.js','questions_more.js','questions.js']) vm.runInContext(fs.readFileSync(path.join(__dirname,'..',f),'utf8'),ctx,{filename:f});
  return {alberta:ctx.window.DATASET_ALBERTA,ontario:ctx.window.DATASET_ONTARIO};
}
test('Alberta school area and posted-speed zone are distinct',()=>{
  const {alberta}=builtins();const area=alberta.questions.find(q=>q.id===213);const zone=alberta.questions.find(q=>q.id===621);
  assert.match(area.options[area.answer],/school area/i);
  assert.doesNotMatch(area.options[area.answer],/zone or area/i);
  assert.equal(zone.image,'images/school-zone.svg');
  assert.match(zone.options[zone.answer],/30 km\/h/);
});
test('sign descriptions match the actual Canadian handbook pictures',()=>{
  const {alberta,ontario}=builtins();const get=id=>alberta.questions.find(q=>q.id===id);
  assert.match(get(607).alt,/upward.*arrow/i);
  assert.match(get(214).alt,/yellow diamond/i);
  assert.match(get(211).alt,/white.*rectang/i);
  assert.match(get(215).alt,/yellow diamond/i);
  assert.doesNotMatch(get(215).alt,/two letter R|round yellow/i);
  assert.match(get(604).options[get(604).answer],/reserved/i);
  assert.match(get(620).options[get(620).answer],/taxi/i);
  assert.match(ontario.questions.find(q=>q.id===19).options[0],/unsafe to pass/i);
});
test('every illustrated question has an image, alternatives and a valid answer',()=>{
  const sets=builtins();let images=new Set();
  for(const d of Object.values(sets))for(const q of d.questions){
    if(q.image){assert.ok(security.safeImage(q.image));assert.ok(fs.existsSync(path.join(__dirname,'..',q.image)));assert.ok(q.alt);images.add(q.image);}
    assert.ok(Number.isInteger(q.answer)&&q.answer>=0&&q.answer<q.options.length);
  }
  assert.equal(images.size,48);
});
test('automatic handbook pictures retain the checked built-in question and answer mappings',()=>{
  const {alberta}=builtins();
  const profile=JSON.parse(fs.readFileSync(path.join(__dirname,'..','tools','sign_assets.json'),'utf8'));
  for(const asset of profile.assets){
    const question=alberta.questions.find(q=>q.image==='images/'+asset.file);
    assert.ok(question,asset.file);
    for(const field of ['q','answer','alt'])assert.equal(asset.question[field],question[field],asset.file+' '+field);
    assert.deepEqual(asset.question.options,Array.from(question.options),asset.file);
  }
});
