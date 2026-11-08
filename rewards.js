/* Offline, opt-in cosmetic rewards. No network, real currency or random draws. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.RoadTripRewards=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 var CATALOG=[
  {id:'car-sky',kind:'car',name:'Sky hatchback',icon:'🚙',color:'#359fd6',cost:0},
  {id:'theme-sunrise',kind:'theme',name:'Sunrise garage',icon:'🌅',color:'#ffe6a7',cost:0},
  {id:'card-first-mile',kind:'card',name:'First mile',icon:'🛣️',cost:0},
  {id:'sticker-star',kind:'sticker',name:'Star decals',icon:'⭐',cost:15},
  {id:'card-city',kind:'card',name:'City explorer',icon:'🌆',cost:25},
  {id:'card-mountain',kind:'card',name:'Mountain roads',icon:'🏔️',cost:25},
  {id:'card-coast',kind:'card',name:'Coastal cruise',icon:'🌊',cost:30},
  {id:'card-night',kind:'card',name:'Night navigator',icon:'🌙',cost:35},
  {id:'sticker-bolt',kind:'sticker',name:'Lightning decals',icon:'⚡',cost:35},
  {id:'theme-forest',kind:'theme',name:'Forest garage',icon:'🌲',color:'#d5efdc',cost:60},
  {id:'theme-space',kind:'theme',name:'Space garage',icon:'🌌',color:'#c9c4f4',cost:75},
  {id:'car-coral',kind:'car',name:'Coral coupe',icon:'🚗',color:'#f78282',cost:80},
  {id:'car-electric',kind:'car',name:'Electric explorer',icon:'🚘',color:'#8edfc9',cost:120},
  {id:'card-aurora',kind:'card',name:'Aurora expedition',icon:'🌠',cost:90}
 ];
 var ACHIEVEMENTS=[
  {id:'mirror',icon:'🪞',title:'MIRROR MIRACLE',body:'You learned what mirrors are for. Congratulations. Your head can now do more than present your beautiful face to the world.'},
  {id:'signal',icon:'💡',title:'TELEPATHY: STILL NOT INSTALLED',body:'You answered a turn-signal question. Other humans may now receive advance notice of your brilliant plans. Revolutionary.'},
  {id:'seatbelt',icon:'🔒',title:'REMAIN INSIDE THE VEHICLE',body:'You answered a seat-belt question. A strap has convinced you that staying inside the car is a worthwhile ambition. Excellent negotiations.'},
  {id:'blindspot',icon:'👀',title:'OBJECT PERMANENCE: UNLOCKED',body:'You answered a blind-spot question. Invisible to the mirror does not mean imaginary. An absolutely shocking plot twist.'},
  {id:'stop',icon:'🛑',title:'THE OCTAGON WAS A CLUE',body:'You answered a STOP-sign question. The enormous red shape and the word STOP were apparently trying to tell us something.'},
  {id:'pedestrian',icon:'🚶',title:'OTHER HUMANS DETECTED',body:'You answered a pedestrian question. Congratulations on remembering that the map contains people, not just convenient parking spaces.'},
  {id:'speed',icon:'🐢',title:'NUMBERS HAVE CONSEQUENCES',body:'You answered a speed-limit question. Those numbers are instructions, not a high-score challenge. Your racing career can wait.'},
  {id:'first-session',icon:'🛣️',title:'BUTTONS WERE PRESSED. LEARNING OCCURRED.',body:'You finished a practice session. Against all odds, this rectangle full of buttons has produced educational activity.'},
  {id:'repair',icon:'🛠️',title:'THE BRAIN ACCEPTS PATCHES',body:'You corrected an earlier mistake. The evidence suggests you can learn. Please try not to look so surprised.'},
  {id:'perfect',icon:'🌟',title:'ONE AUTHORISED SMUG SMILE',body:'Perfect answers on a mixed test. Please remain calm. The imaginary committee has authorised one extremely smug smile.'},
  {id:'mastery',icon:'🧠',title:'YOUR BRAIN HAS A SAVE FUNCTION',body:'Ten questions mastered after spaced practice. You remembered things after a break. Apparently the information did not evaporate. Remarkable.'},
  {id:'collector',icon:'🃏',title:'CARDBOARD TYCOON',body:'You collected three cards. Your coin wallet is lighter. Your entirely fictional social status is now unbearable.'},
  {id:'parking',icon:'🅿️',title:'THE RECTANGLES ACCEPT YOUR LEADERSHIP',body:'You solved a parking puzzle. The rectangles have agreed to move aside. This does not, regrettably, count as a driving licence.'}
 ];
 var has=function(o,k){return Object.prototype.hasOwnProperty.call(o,k);};
 function fresh(){return {version:1,enabled:null,popups:true,unlocked:[],coins:0,earned:0,questions:{},sessions:0,perfect:0,recovered:0,claims:[],owned:['car-sky','theme-sunrise'],selected:{car:'car-sky',theme:'theme-sunrise',sticker:null},parkingWins:[]};}
 function integer(n,cap){return Number.isSafeInteger(n)&&n>=0&&n<=cap?n:0;}
 function restore(raw){
  var s=fresh();if(!raw||typeof raw!=='object'||raw.version!==1)return s;
  s.enabled=typeof raw.enabled==='boolean'?raw.enabled:null;
  s.popups=raw.popups!==false;
  if(Array.isArray(raw.unlocked))s.unlocked=raw.unlocked.filter(function(id,i,a){return ACHIEVEMENTS.some(function(x){return x.id===id;})&&a.indexOf(id)===i;});
  ['coins','earned','sessions','perfect','recovered'].forEach(function(k){s[k]=integer(raw[k],10000000);});
  if(raw.questions&&typeof raw.questions==='object')Object.keys(raw.questions).slice(0,20000).forEach(function(k){
   if(!/^[a-z0-9-]{1,40}:[a-zA-Z0-9_-]{1,60}$/.test(k))return;
   var q=raw.questions[k];if(!q||typeof q!=='object')return;
   s.questions[k]={first:integer(q.first,8640000000000000),last:integer(q.last,8640000000000000),missed:q.missed===true,mastered:q.mastered===true,paidMastery:q.paidMastery===true};
  });
  if(Array.isArray(raw.claims))s.claims=raw.claims.filter(function(x){return typeof x==='string'&&/^[a-zA-Z0-9_-]{1,80}$/.test(x);}).slice(-2000);
  if(Array.isArray(raw.owned))raw.owned.forEach(function(id){if(CATALOG.some(function(x){return x.id===id;})&&s.owned.indexOf(id)<0)s.owned.push(id);});
  if(raw.selected&&typeof raw.selected==='object')['car','theme','sticker'].forEach(function(kind){var id=raw.selected[kind];if(s.owned.indexOf(id)>=0&&CATALOG.some(function(x){return x.id===id&&x.kind===kind;}))s.selected[kind]=id;});
  if(Array.isArray(raw.parkingWins))s.parkingWins=raw.parkingWins.filter(function(x,i,a){return ['first-bay','city-block','switchback'].indexOf(x)>=0&&a.indexOf(x)===i;});
  return s;
 }
 function setEnabled(raw,on){var s=restore(raw);s.enabled=on===true;if(s.enabled&&s.owned.indexOf('card-first-mile')<0)s.owned.push('card-first-mile');return s;}
 function unlockEligible(s,items){
  if(!s.enabled)return [];
  var ids=[],topics={mirror:/\bmirrors?\b/i,signal:/\bturn[ -]?signals?|\bsignal(?:ling|ing)? your turn\b/i,seatbelt:/\bseat[ -]?belts?\b/i,blindspot:/\bblind[ -]?spots?\b/i,stop:/\bstop[ -]?sign\b/i,pedestrian:/\bpedestrians?|\bcrosswalks?\b/i,speed:/\bspeed[ -]?limits?\b/i};
  (items||[]).forEach(function(q){if(!q.correct)return;var text=(typeof q.q==='string'?q.q.slice(0,10000):'')+' '+(typeof q.correctText==='string'?q.correctText.slice(0,5000):'');Object.keys(topics).forEach(function(id){if(topics[id].test(text)&&ids.indexOf(id)<0)ids.push(id);});});
  if(s.sessions>0)ids.push('first-session');if(s.recovered>0)ids.push('repair');if(s.perfect>0)ids.push('perfect');
  if(Object.values(s.questions).filter(function(q){return q.paidMastery;}).length>=10)ids.push('mastery');
  if(s.owned.filter(function(id){return id.indexOf('card-')===0;}).length>=3)ids.push('collector');if(s.parkingWins.length)ids.push('parking');
  var unlocked=[];ids.forEach(function(id){if(s.unlocked.indexOf(id)<0){s.unlocked.push(id);unlocked.push(ACHIEVEMENTS.find(function(x){return x.id===id;}));}});return unlocked;
 }
 function awardSession(raw,session){
  var s=restore(raw),result={state:s,coins:0,mastered:0,recovered:0,achievements:[]};
  if(s.enabled!==true||!session||typeof session.id!=='string'||!/^[a-zA-Z0-9_-]{1,80}$/.test(session.id)||s.claims.indexOf(session.id)>=0||!Array.isArray(session.questions)||!/^[a-z0-9-]{1,40}$/.test(session.dataset)||!Number.isSafeInteger(session.date)||session.date<=0)return result;
  var seen=Object.create(null),items=session.questions.filter(function(q){if(!q||typeof q.correct!=='boolean'||!['string','number'].includes(typeof q.id))return false;var id=String(q.id);if(!/^[a-zA-Z0-9_-]{1,60}$/.test(id)||has(seen,id))return false;seen[id]=true;return true;}).slice(0,500);
  if(!items.length)return result;
  var mixed=items.length>=5;
  items.forEach(function(q){
   var key=session.dataset+':'+q.id,p=has(s.questions,key)?s.questions[key]:{first:0,last:0,missed:false,mastered:false,paidMastery:false};
   if(q.correct){
    if(p.missed){s.recovered++;result.recovered++;}
    if(!p.first){result.coins+=5;p.first=session.date;}
    else if(mixed&&!p.missed&&session.date-p.last>=6*60*60*1000){p.mastered=true;if(!p.paidMastery){result.coins+=8;result.mastered++;p.paidMastery=true;}}
    p.last=Math.max(p.last,session.date);p.missed=false;
   }else {p.missed=true;p.mastered=false;}
   s.questions[key]=p;
  });
  s.sessions++;s.claims.push(session.id);s.claims=s.claims.slice(-2000);
  if(mixed&&result.coins>0){result.coins+=5;if(items.length>=10&&items.every(function(q){return q.correct;})){result.coins+=10;s.perfect++;}}
  s.coins=Math.min(10000000,s.coins+result.coins);s.earned=Math.min(10000000,s.earned+result.coins);
  result.achievements=unlockEligible(s,items);
  return result;
 }
 function buy(raw,id){var s=restore(raw),item=CATALOG.filter(function(x){return x.id===id;})[0];
  if(!s.enabled||!item||s.owned.indexOf(id)>=0||s.coins<item.cost)return {state:s,ok:false};
  s.coins-=item.cost;s.owned.push(id);return {state:s,ok:true,achievements:unlockEligible(s)};
 }
 function equip(raw,id){var s=restore(raw),item=CATALOG.filter(function(x){return x.id===id;})[0];
  if(!s.enabled||!item||item.kind==='card'||s.owned.indexOf(id)<0)return {state:s,ok:false};
  s.selected[item.kind]=id;return {state:s,ok:true};
 }
 function parkingUnlocked(raw){var s=restore(raw);return s.enabled===true&&s.earned>=60;}
 function claimParking(raw,id){var s=restore(raw),levels=['first-bay','city-block','switchback'],i=levels.indexOf(id);
  if(!parkingUnlocked(s)||i<0||s.parkingWins.indexOf(id)>=0||(i>0&&s.parkingWins.indexOf(levels[i-1])<0))return {state:s,ok:false};
  s.parkingWins.push(id);s.coins=Math.min(10000000,s.coins+5);s.earned=Math.min(10000000,s.earned+5);return {state:s,ok:true,achievements:unlockEligible(s)};
 }
 return {fresh:fresh,restore:restore,setEnabled:setEnabled,catalog:CATALOG,achievements:ACHIEVEMENTS,awardSession:awardSession,buy:buy,equip:equip,parkingUnlocked:parkingUnlocked,claimParking:claimParking};
});
