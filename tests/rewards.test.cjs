const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
test('optional rewards engine is available without a server',()=>{
 assert.ok(fs.existsSync(path.join(__dirname,'..','rewards.js')),'Offline rewards engine has not been implemented');
});
const R=require('../rewards.js');
function session(id,correct=true){return {id:id,dataset:'alberta',date:100000000,questions:Array.from({length:10},(_,i)=>({id:i+1,correct:correct}))};}
test('reward consent starts undecided and can be disabled without erasing a collection',()=>{
 let s=R.fresh();assert.equal(s.enabled,null);s=R.setEnabled(s,true);assert.ok(s.owned.includes('card-first-mile'));
 s.coins=25;s=R.setEnabled(s,false);assert.equal(s.coins,25);assert.equal(s.enabled,false);
});
test('disabled achievements never award coins or track question mastery',()=>{
 const s=R.setEnabled(R.fresh(),false);const result=R.awardSession(s,session('one'));
 assert.deepEqual(result.state,s);assert.equal(result.coins,0);
});
test('new learning earns coins once and cannot be farmed by replaying or rapidly repeating a test',()=>{
 let s=R.setEnabled(R.fresh(),true);const one=R.awardSession(s,session('one'));
 assert.equal(one.coins,65);assert.equal(one.state.sessions,1);assert.equal(one.state.perfect,1);
 assert.equal(R.awardSession(one.state,session('one')).coins,0);
 assert.equal(R.awardSession(one.state,session('two')).coins,0);
 assert.equal(one.state.questions['alberta:1'].mastered,false);
 const later=session('later');later.date+=6*60*60*1000;
 const spaced=R.awardSession(one.state,later);assert.equal(spaced.mastered,10);assert.equal(spaced.coins,95);
 assert.equal(R.awardSession(spaced.state,Object.assign(session('again'),{date:later.date+1})).coins,0);
});
test('earned coins buy chosen cosmetics once, never produce negative balances, and only owned items equip',()=>{
 let s=R.awardSession(R.setEnabled(R.fresh(),true),session('one')).state;
 const buy=R.buy(s,'card-city');assert.equal(buy.ok,true);assert.equal(buy.state.coins,40);
 assert.equal(R.buy(buy.state,'card-city').state.coins,40);
 assert.equal(R.buy(buy.state,'car-electric').ok,false);
 assert.equal(R.buy(buy.state,'not-real').ok,false);
 assert.equal(R.equip(buy.state,'car-electric').ok,false);
 const star=R.buy(buy.state,'sticker-star');assert.equal(R.equip(star.state,'sticker-star').state.selected.sticker,'sticker-star');
 assert.equal(R.buy(R.setEnabled(s,false),'card-city').ok,false);
});
test('parking rewards unlock from learning and each sequential level pays only once',()=>{
 let s=R.setEnabled(R.fresh(),true);assert.equal(R.parkingUnlocked(s),false);
 assert.equal(R.claimParking(s,'first-bay').ok,false);
 s=R.awardSession(s,session('one')).state;assert.equal(R.parkingUnlocked(s),true);
 assert.equal(R.claimParking(s,'city-block').ok,false);
 const won=R.claimParking(s,'first-bay');assert.equal(won.ok,true);assert.equal(won.state.coins,70);
 assert.equal(R.claimParking(won.state,'first-bay').state.coins,70);
 assert.equal(R.claimParking(won.state,'city-block').ok,true);
});
test('repairing mistakes is recorded without paying a question twice or deleting owned rewards',()=>{
 let s=R.awardSession(R.setEnabled(R.fresh(),true),session('first')).state;
 s=R.awardSession(s,session('wrong',false)).state;const again=R.awardSession(s,session('repair'));
 assert.equal(again.coins,0);assert.equal(again.recovered,10);assert.equal(again.state.recovered,10);
 assert.deepEqual(again.state.owned,s.owned);assert.equal(again.state.coins,s.coins);
});
test('a mistake must be repaired before a later spaced answer counts as mastery',()=>{
 let s=R.awardSession(R.setEnabled(R.fresh(),true),session('first')).state;
 const wrong=session('wrong',false);wrong.date+=7*60*60*1000;s=R.awardSession(s,wrong).state;
 const repair=session('repair');repair.date=wrong.date+1000;const result=R.awardSession(s,repair);
 assert.equal(result.mastered,0);assert.equal(result.state.questions['alberta:1'].mastered,false);
 const later=session('later');later.date=repair.date+6*60*60*1000;assert.equal(R.awardSession(result.state,later).mastered,10);
});
test('malformed saved data, duplicate question IDs and wrong input types cannot mint extra rewards',()=>{
 let s=R.setEnabled(R.fresh(),true);const original=JSON.stringify(s);const dup=session('dups');dup.questions=Array(10).fill({id:'__proto__',correct:true});
 assert.equal(R.awardSession(s,dup).coins,5);assert.equal(JSON.stringify(s),original);assert.equal({}.polluted,undefined);
 assert.equal(R.awardSession(s,Object.assign(session('bad'),{date:NaN})).coins,0);
 assert.equal(R.restore({version:1,coins:-25,selected:{car:'car-electric'}}).coins,0);
 assert.equal(R.restore({version:1,selected:{car:'car-electric'}}).selected.car,'car-sky');
});
test('sarcastic topic achievements require a correct answer and unlock once per profile',()=>{
 let s=R.setEnabled(R.fresh(),true);const wrong=session('mirror-wrong',false);
 wrong.questions[0].q='Why must you check your mirrors?';
 let result=R.awardSession(s,wrong);
 assert.ok(Array.isArray(result.achievements),'Achievement announcements are missing');
 assert.ok(!result.achievements.some(a=>a.id==='mirror'));
 const correct=session('mirror-correct');correct.questions[0].q='Why must you check your mirrors?';
 result=R.awardSession(result.state,correct);
 const mirror=result.achievements.find(a=>a.id==='mirror');assert.ok(mirror);assert.match(mirror.body,/beautiful face/i);
 assert.ok(R.restore(JSON.parse(JSON.stringify(result.state))).unlocked.includes('mirror'));
 assert.ok(!R.awardSession(result.state,session('generic')).achievements.some(a=>a.id==='mirror'));
 const repeat=R.awardSession(result.state,Object.assign(correct,{id:'mirror-again'}));assert.ok(!repeat.achievements.some(a=>a.id==='mirror'));
 const disabled=R.awardSession(R.setEnabled(result.state,false),session('off'));assert.deepEqual(disabled.achievements,[]);
});
test('old saves migrate safely and silent pop-ups still retain earned badges',()=>{
 const s=R.restore({version:1,enabled:true,coins:41,earned:80,popups:false,unlocked:['mirror','mirror','unknown'],owned:['car-coral'],selected:{car:'car-coral'}});
 assert.equal(s.coins,41);assert.equal(s.selected.car,'car-coral');assert.deepEqual(s.unlocked,['mirror']);assert.equal(s.popups,false);
 const result=R.awardSession(s,session('silent'));assert.equal(result.state.popups,false);assert.ok(result.state.unlocked.includes('first-session'));
 assert.equal(R.achievements.length,13);assert.equal(new Set(R.achievements.map(a=>a.id)).size,13);
});
