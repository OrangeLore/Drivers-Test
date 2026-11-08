/* Android-only UI adapter. All state is owned by the active local nickname profile. */
(function(root){'use strict';root.RoadTripUI={mount:function(ctx){
 var R=root.RoadTripRewards,P=root.RoadTripParking,garage,board=null,level=P.levels[0].id,selected='you',moves=0,last=null,lastProfile=null,pending=[];
 function el(tag,text,cls){var e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
 function button(text,fn){var e=el('button',text,'btn secondary');e.type='button';e.addEventListener('click',fn);return e;}
 function state(){return R.restore(ctx.get());}function persist(s){ctx.put(s);refresh();}
 var nav=button('🏁 Garage',function(){ctx.navigate('garage');refresh();});nav.id='rtOpen';document.querySelector('.toolbar').appendChild(nav);
 var consent=el('dialog');consent.id='rtConsent';consent.setAttribute('aria-labelledby','rtConsentTitle');
 var title=el('h2','Choose how you practise');title.id='rtConsentTitle';consent.appendChild(title);
 consent.appendChild(el('p','Would you like optional achievements, collectible cards and garage rewards for this nickname profile?'));
 consent.appendChild(el('p','Earn items by learning. No money, ads, random draws, daily streak losses or penalties for mistakes. You can change this in Settings.','muted'));
 var choices=el('div',undefined,'row');
 function choose(on){persist(R.setEnabled(state(),on));if(consent.open&&consent.close)consent.close();else consent.removeAttribute('open');}
 choices.appendChild(button('Enable achievements & rewards',function(){choose(true);}));choices.appendChild(button('No thanks — just practise',function(){choose(false);}));consent.appendChild(choices);
 consent.addEventListener('cancel',function(e){e.preventDefault();choose(false);});document.body.appendChild(consent);
 var announcement=el('dialog');announcement.id='rtAchievement';announcement.setAttribute('role','alertdialog');announcement.setAttribute('aria-labelledby','rtAchievementTitle');announcement.setAttribute('aria-describedby','rtAchievementBody');
 announcement.appendChild(el('p','NEW ACHIEVEMENT!','rt-announcement-label'));
 var achievementIcon=el('div',undefined,'rt-announcement-icon');announcement.appendChild(achievementIcon);
 var achievementTitle=el('h2');achievementTitle.id='rtAchievementTitle';achievementTitle.tabIndex=-1;achievementTitle.setAttribute('autofocus','');announcement.appendChild(achievementTitle);
 var achievementBody=el('p');achievementBody.id='rtAchievementBody';announcement.appendChild(achievementBody);
 var achievementCount=el('p',undefined,'muted');announcement.appendChild(achievementCount);
 announcement.appendChild(el('p','Comedy, not driving instruction. Your actual road rules are in the handbook.','rt-announcement-note'));
 function closeAnnouncement(){if(announcement.open&&announcement.close)announcement.close();else announcement.removeAttribute('open');}
 function showPending(){if(announcement.open||!pending.length)return;var s=state();if(!s.enabled||!s.popups){pending=[];return;}var a=pending.shift();achievementIcon.textContent=a.icon;achievementTitle.textContent=a.title;achievementBody.textContent=a.body;achievementCount.textContent=pending.length?pending.length+' more achievement'+(pending.length===1?'':'s')+' queued':'';if(announcement.showModal)announcement.showModal();else announcement.setAttribute('open','');achievementTitle.focus({preventScroll:true});announcement.scrollTop=0;}
 function queueAchievements(items){if(state().enabled&&state().popups)pending=pending.concat(items||[]);}
 var announcementButtons=el('div',undefined,'row');announcementButtons.appendChild(button('Accept this tremendous honour',function(){closeAnnouncement();showPending();}));
 announcementButtons.appendChild(button('Dismiss all',function(){pending=[];closeAnnouncement();}));
 announcementButtons.appendChild(button('Read announcement',function(){var text='New achievement! '+achievementTitle.textContent+'. '+achievementBody.textContent;if(root.NativeSpeech){if(!root.NativeSpeech.speak(text,0.95))achievementCount.textContent='Install an offline English voice in Android text-to-speech settings to hear announcements.';}else if(root.speechSynthesis&&root.SpeechSynthesisUtterance){root.speechSynthesis.cancel();root.speechSynthesis.speak(new root.SpeechSynthesisUtterance(text));}}));
 announcement.appendChild(announcementButtons);announcement.addEventListener('cancel',function(e){e.preventDefault();pending=[];closeAnnouncement();});document.body.appendChild(announcement);
 var settings=el('div',undefined,'card');settings.appendChild(el('h2','Optional achievements & rewards'));
 var toggle=button('Achievements: off',function(){var s=state();persist(R.setEnabled(s,s.enabled!==true));});toggle.id='rtToggle';toggle.setAttribute('aria-pressed','false');settings.appendChild(toggle);
 var popupToggle=button('Sarcastic pop-ups: on',function(){var s=state();s.popups=!s.popups;persist(s);if(!s.popups){pending=[];closeAnnouncement();}});popupToggle.id='rtPopupToggle';settings.appendChild(popupToggle);
 settings.appendChild(el('p','Per nickname profile. Turning rewards off keeps your collection but stops new rewards and hides the game. Uninstalling or clearing app data removes local progress.','muted'));
 document.querySelector('#screen-settings').appendChild(settings);
 var home=el('div',undefined,'card');home.id='rtHome';document.querySelector('#screen-home').appendChild(home);
 garage=el('section');garage.id='screen-garage';garage.className='hidden';document.querySelector('main').insertBefore(garage,document.querySelector('#footnote'));
 function openConsent(){if(consent.open)return;if(typeof consent.showModal==='function')consent.showModal();else consent.setAttribute('open','');}
 function openLevel(id){level=id;board=P.start(id);selected='you';moves=0;renderGame();}
 function panel(title){var p=el('div',undefined,'card');p.appendChild(el('h2',title));return p;}
 function refresh(){
  if(lastProfile!==ctx.profile()){lastProfile=ctx.profile();board=null;level=P.levels[0].id;selected='you';moves=0;last=null;pending=[];closeAnnouncement();}
  var s=state(),on=s.enabled===true;
  nav.classList.toggle('hidden',!on);nav.textContent='🏁 Garage · '+s.coins+' coins';
  toggle.textContent='Achievements: '+(on?'on':'off');toggle.setAttribute('aria-pressed',String(on));home.classList.toggle('hidden',!on);
  popupToggle.textContent='Sarcastic pop-ups: '+(s.popups?'on':'off');popupToggle.setAttribute('aria-pressed',String(s.popups));popupToggle.disabled=!on;
  if(!on){pending=[];closeAnnouncement();}
  home.replaceChildren(el('h2','Your road trip'),el('p',s.coins+' coins · '+s.owned.filter(function(id){return id.indexOf('card-')===0;}).length+' collectible cards'));
  home.appendChild(button('Visit your garage',function(){ctx.navigate('garage');refresh();}));
  if(s.enabled===null)openConsent();
  renderGarage(s);
 }
 function renderGarage(s){
  garage.replaceChildren();var heading=panel('Road Trip Garage');heading.appendChild(el('p','Chosen rewards, earned by learning. A game for your breaks — not a driving simulator.','muted'));
  heading.appendChild(button('Back to practice',function(){ctx.navigate('home');}));garage.appendChild(heading);
  if(!s.enabled){heading.appendChild(el('p','Rewards are off for this profile. Turn them on in Settings if you want to play.'));return;}
  var theme=R.catalog.find(function(x){return x.id===s.selected.theme;}),car=R.catalog.find(function(x){return x.id===s.selected.car;}),sticker=R.catalog.find(function(x){return x.id===s.selected.sticker;});
  var scene=el('div',undefined,'rt-scene');scene.style.backgroundColor=theme.color;
  scene.appendChild(el('p',theme.icon+' '+theme.name,'rt-scene-title'));
  var vehicle=el('div',undefined,'rt-car');vehicle.style.setProperty('--car-color',car.color);vehicle.appendChild(el('span',sticker?sticker.icon:'🚘','rt-decal'));scene.appendChild(vehicle);scene.appendChild(el('p',car.name,'rt-car-name'));heading.appendChild(scene);
  var mastered=Object.values(s.questions).filter(function(q){return q.mastered;}).length,everMastered=Object.values(s.questions).filter(function(q){return q.paidMastery;}).length;
  heading.appendChild(el('p',s.coins+' coins available · '+mastered+' questions mastered across your test sets','rt-wallet'));
  var badges=panel('Achievements');var list=el('div',undefined,'rt-badges');
  R.achievements.forEach(function(a){var earned=s.unlocked.indexOf(a.id)>=0;list.appendChild(el('span',(earned?'✓ ':'○ ')+a.icon+' '+a.title,earned?'rt-badge earned':'rt-badge'));});badges.appendChild(list);garage.appendChild(badges);
  var shop=panel('Cards & garage shop');shop.appendChild(el('p','Choose what to unlock. Prices are earned coins only; nothing can be purchased with real money.','muted'));var grid=el('div',undefined,'rt-catalog');
  R.catalog.forEach(function(item){var owned=s.owned.indexOf(item.id)>=0,chosen=s.selected[item.kind]===item.id;var cell=el('div',undefined,'rt-item '+(owned?'owned':''));cell.appendChild(el('div',item.icon,'rt-icon'));cell.appendChild(el('h3',item.name));cell.appendChild(el('p',owned?'In your collection':item.cost+' coins'));
   if(!owned){var buy=button('Unlock',function(){var result=R.buy(state(),item.id);if(result.ok){persist(result.state);queueAchievements(result.achievements);showPending();}});buy.disabled=s.coins<item.cost;buy.setAttribute('aria-label','Unlock '+item.name+' for '+item.cost+' coins');cell.appendChild(buy);}
   else if(item.kind!=='card'){var equip=button(chosen?'Equipped':'Equip',function(){var result=R.equip(state(),item.id);if(result.ok)persist(result.state);});equip.disabled=chosen;equip.setAttribute('aria-label',(chosen?'Equipped: ':'Equip ')+item.name);cell.appendChild(equip);}
   grid.appendChild(cell);
  });shop.appendChild(grid);garage.appendChild(shop);
  var rules=panel('How you earn rewards');rules.appendChild(el('p','First correct answer to a question: 5 coins. Correct it again in a different mixed session at least 6 hours later: 8 mastery coins, once per question.'));
  rules.appendChild(el('p','A mixed session has at least 5 different questions. If you made new learning progress, finishing one adds 5 coins; a perfect test with at least 10 questions adds 10 more. Repeating already-rewarded questions does not pay again. Mistakes never take your coins or items away.'));
  garage.appendChild(rules);var game=panel('Parking puzzle');game.id='rtGame';garage.appendChild(game);
  if(!R.parkingUnlocked(s)){game.appendChild(el('p','Unlock by earning 60 learning coins. There is no timer or daily deadline.'));return;}
  renderGame();
 }
 function renderGame(){
  var area=document.querySelector('#rtGame');if(!area||!R.parkingUnlocked(state()))return;
  var s=state();area.replaceChildren(el('h2','Parking puzzle'));
  area.appendChild(el('p','Move the red car to the exit on the right. Select a vehicle, then use its arrow buttons. Vehicles slide only along their own length. This is a logic puzzle, not a driving lesson.','muted'));
  var tabs=el('div',undefined,'row');P.levels.forEach(function(l,i){var b=button(l.name,function(){openLevel(l.id);});b.disabled=i>0&&s.parkingWins.indexOf(P.levels[i-1].id)<0;b.setAttribute('aria-pressed',String(level===l.id));tabs.appendChild(b);});area.appendChild(tabs);
  if(!board)board=P.start(level);
  var wrap=el('div',undefined,'rt-board-wrap'),play=el('div',undefined,'rt-board');play.id='rtBoard';play.setAttribute('role','group');play.setAttribute('aria-label','Six by six parking puzzle. Exit is on the right of row three.');
  board.forEach(function(c){var b=button(c.id==='you'?'YOU':c.id.toUpperCase(),function(){selected=c.id;renderGame();});b.className='rt-vehicle';b.style.gridColumn=(c.x+1)+' / span '+(c.axis==='h'?c.length:1);b.style.gridRow=(c.y+1)+' / span '+(c.axis==='v'?c.length:1);b.style.backgroundColor=c.color;b.setAttribute('aria-pressed',String(selected===c.id));b.setAttribute('aria-label',(c.id==='you'?'Your red car':'Vehicle '+c.id.toUpperCase())+', '+(c.axis==='h'?'horizontal':'vertical')+', row '+(c.y+1)+', column '+(c.x+1));b.dataset.vehicle=c.id;play.appendChild(b);});wrap.appendChild(play);wrap.appendChild(el('div','EXIT →','rt-exit'));area.appendChild(wrap);
  var selectedCar=board.find(function(c){return c.id===selected;});
  var status=el('p','Moves: '+moves+(P.solved(board)?' · Solved!':' · Selected: '+(selected==='you'?'your car':selected.toUpperCase())));status.id='rtPuzzleStatus';status.setAttribute('aria-live','polite');area.appendChild(status);
  function shift(delta){var next=P.move(board,selected,delta);if(!next){status.textContent='That move is blocked. Try another vehicle.';return;}board=next;moves++;if(P.solved(board)){var prize=R.claimParking(state(),level);if(prize.ok){ctx.put(prize.state);refresh();queueAchievements(prize.achievements);}else renderGame();var msg=document.querySelector('#rtPuzzleStatus');msg.textContent='Puzzle solved! '+(prize.ok?'5 coins earned.':'You already earned this puzzle’s reward; replay for fun.');showPending();}else renderGame();}
  var controls=el('div',undefined,'row');var back=button(selectedCar.axis==='h'?'← Move left':'↑ Move up',function(){shift(-1);});var forward=button(selectedCar.axis==='h'?'Move right →':'Move down ↓',function(){shift(1);});back.id='rtMoveBack';forward.id='rtMoveForward';back.disabled=forward.disabled=P.solved(board);controls.appendChild(back);controls.appendChild(forward);controls.appendChild(button('Reset puzzle',function(){openLevel(level);}));area.appendChild(controls);
 }
 function complete(session){last=R.awardSession(state(),session);ctx.put(last.state);refresh();queueAchievements(last.achievements);return last;}
 function resultMessage(){if(state().enabled!==true)return '';return last&&last.coins?' Road trip: +'+last.coins+' coins'+(last.mastered?' · '+last.mastered+' newly mastered':'')+'. Visit your garage to choose a reward.':' No coins lost. Earn more by learning new questions or revisiting them after a rest.';}
 refresh();return {refresh:refresh,complete:complete,showPending:showPending,resultMessage:resultMessage,ensureChoice:function(){if(state().enabled===null){openConsent();return false;}return true;}};
}};})(window);
