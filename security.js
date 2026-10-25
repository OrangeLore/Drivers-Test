/* Validate untrusted imports before rendering; no third-party code or network calls. */
(function(root){
  'use strict';
  var reserved=['__proto__','constructor','prototype'];
  function identifier(value){ return typeof value==='string' && /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(value) && reserved.indexOf(value)<0; }
  function safeImage(value){
    if(typeof value!=='string' || value.length>2000000) return '';
    if(/^images\/[a-zA-Z0-9_-]+\.(svg|png|jpg|jpeg|webp)$/.test(value)) return value;
    if(/^data:image\/(png|jpeg|webp);base64,[a-zA-Z0-9+/]+=*$/.test(value)) return value;
    return '';
  }
  function text(value,max){ return typeof value==='string' && value.length<=max; }
  function positive(value,max){ return Number.isInteger(value) && value>0 && value<=max; }
  function validateDataset(d){
    if(!d || typeof d!=='object' || Array.isArray(d) || !identifier(d.key) || !text(d.name,150) || !d.name.trim()) return 'Invalid test-set key or name.';
    if(!Array.isArray(d.questions) || !d.questions.length || d.questions.length>5000) return 'Test sets need 1–5000 questions.';
    if(d.jurisdiction!==undefined && !text(d.jurisdiction,200)) return 'Invalid jurisdiction.';
    for(var i=0;i<d.questions.length;i++){
      var q=d.questions[i];
      if(!q || typeof q!=='object' || !text(q.q,10000) || !q.q.trim() || !Array.isArray(q.options) || q.options.length<2 || q.options.length>6 || !q.options.every(function(o){return text(o,5000)&&o.trim();}) || !Number.isInteger(q.answer) || q.answer<0 || q.answer>=q.options.length) return 'Question '+(i+1)+' is malformed.';
      if(q.diff===undefined) q.diff='standard';
      if(['easy','standard','hard'].indexOf(q.diff)<0) return 'Invalid difficulty.';
      if(q.topic===undefined) q.topic='General';
      if(!text(q.topic,200) || (q.source!==undefined && !text(q.source,2000)) || (q.alt!==undefined && !text(q.alt,1000))) return 'Invalid question text.';
      if(q.section!==undefined && q.section!==null && !identifier(q.section)) return 'Invalid section key.';
      if(q.image && !safeImage(q.image)) return 'Images must be local sign assets or embedded raster images.';
      q.id=i+1;
    }
    if(d.testSize===undefined) d.testSize=Math.min(30,d.questions.length);
    if(!positive(d.testSize,5000) || d.testSize>d.questions.length) return 'Invalid test size.';
    if(d.passMark===undefined) d.passMark=Math.ceil(d.testSize*0.8);
    if(!positive(d.passMark,d.testSize)) return 'Invalid pass mark.';
    if(d.sections!==undefined && d.sections!==null){
      if(!Array.isArray(d.sections) || !d.sections.length || d.sections.length>20) return 'Invalid sections.';
      var keys=[], total=0;
      for(var s of d.sections){
        if(!s || !identifier(s.key) || keys.indexOf(s.key)>=0 || !text(s.name,150) || !positive(s.size,5000) || !positive(s.pass,s.size) || d.questions.filter(function(q){return q.section===s.key;}).length<s.size) return 'Invalid section format or insufficient questions.';
        keys.push(s.key); total+=s.size;
      }
      if(total!==d.testSize) return 'Section sizes must match test size.';
    }
    return null;
  }
  var api={identifier:identifier,safeImage:safeImage,validateDataset:validateDataset};
  if(typeof module==='object' && module.exports) module.exports=api;
  else root.PracticeSecurity=api;
})(typeof window==='object'?window:globalThis);
