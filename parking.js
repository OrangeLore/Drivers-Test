/* Small deterministic sliding-car puzzles. Entertainment, not a driving simulator. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.RoadTripParking=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 var levels=[
  {id:'first-bay',name:'First bay',cars:[{id:'you',x:0,y:2,length:2,axis:'h',color:'#e65767'},{id:'a',x:2,y:1,length:2,axis:'v',color:'#4b9cc5'},{id:'b',x:4,y:2,length:2,axis:'v',color:'#7b62b4'}]},
  {id:'city-block',name:'City block',cars:[{id:'you',x:1,y:2,length:2,axis:'h',color:'#e65767'},{id:'a',x:3,y:0,length:3,axis:'v',color:'#4b9cc5'},{id:'b',x:4,y:2,length:2,axis:'v',color:'#7b62b4'},{id:'c',x:2,y:4,length:2,axis:'h',color:'#d59a37'},{id:'d',x:0,y:0,length:2,axis:'v',color:'#468862'}]},
  {id:'switchback',name:'Switchback',cars:[{id:'you',x:0,y:2,length:2,axis:'h',color:'#e65767'},{id:'a',x:2,y:0,length:3,axis:'v',color:'#4b9cc5'},{id:'b',x:1,y:4,length:2,axis:'h',color:'#d59a37'},{id:'c',x:3,y:3,length:3,axis:'v',color:'#7b62b4'}]}
 ];
 function start(id){var level=levels.filter(function(x){return x.id===id;})[0];return level?JSON.parse(JSON.stringify(level.cars)):null;}
 function cells(car){var out=[];for(var i=0;i<car.length;i++)out.push([car.x+(car.axis==='h'?i:0),car.y+(car.axis==='v'?i:0)]);return out;}
 function valid(cars){
  if(!Array.isArray(cars)||!cars.length)return false;var occupied={},ids={};
  return cars.every(function(c){if(!c||typeof c.id!=='string'||!['h','v'].includes(c.axis)||![2,3].includes(c.length)||!Number.isInteger(c.x)||!Number.isInteger(c.y)||Object.prototype.hasOwnProperty.call(ids,c.id))return false;ids[c.id]=true;
   return cells(c).every(function(p){var k=p.join(',');if(p[0]<0||p[0]>5||p[1]<0||p[1]>5||occupied[k])return false;occupied[k]=true;return true;});});
 }
 function move(cars,id,delta){
  if(!valid(cars)||!Number.isInteger(delta)||delta===0||Math.abs(delta)>5)return null;
  var index=cars.findIndex(function(c){return c.id===id;});if(index<0)return null;
  var next=cars.map(function(c){return Object.assign({},c);}),step=delta>0?1:-1;
  for(var i=0;i<Math.abs(delta);i++){var c=next[index];if(c.axis==='h')c.x+=step;else c.y+=step;if(!valid(next))return null;}
  return next;
 }
 function solved(cars){if(!valid(cars))return false;return cars.some(function(c){return c.id==='you'&&c.axis==='h'&&c.y===2&&c.x+c.length===6;});}
 return {levels:levels,start:start,valid:valid,move:move,solved:solved,cells:cells};
});
