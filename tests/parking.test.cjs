const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
test('offline parking minigame engine is present',()=>assert.ok(fs.existsSync(path.join(__dirname,'..','parking.js')),'Parking minigame is missing'));
const P=require('../parking.js');
test('cars cannot leave the grid, overlap, or jump through blockers',()=>{
 const s=P.start('first-bay');assert.ok(P.valid(s));
 assert.equal(P.move(s,'you',-1),null);assert.equal(P.move(s,'you',4),null);assert.equal(P.move(s,'not-a-car',1),null);
 assert.equal(P.move(s,'a',-2),null);assert.equal(P.move(s,'you',1.5),null);assert.equal(P.solved(s),false);
});
function solution(start){
 const key=s=>s.map(c=>c.x+','+c.y).join(';');const queue=[[start,[]]],seen=new Set([key(start)]);let at=0;
 while(at<queue.length&&at<100000){const [s,path]=queue[at++];if(P.solved(s))return path;
  for(const car of s)for(let d=-5;d<=5;d++){if(!d)continue;const n=P.move(s,car.id,d);if(!n)continue;const k=key(n);if(seen.has(k))continue;seen.add(k);queue.push([n,path.concat([[car.id,d]])]);}
 }return null;
}
test('every shipped puzzle has a verified legal solution',()=>{
 for(const level of P.levels){let s=P.start(level.id);assert.ok(P.valid(s));const moves=solution(s);assert.ok(moves&&moves.length>0,level.id);
  for(const [id,delta] of moves){s=P.move(s,id,delta);assert.ok(s);assert.ok(P.valid(s));}
  assert.ok(P.solved(s),level.id);console.log('Verified puzzle solution:',level.id,JSON.stringify(moves));
 }
});
