#!/usr/bin/env python3
"""Build a server-free Android edition using official SDK tools and Java 21.

No Gradle, cloud build, native libraries or runtime Python dependencies are required.
Signing keys must be supplied from outside the repository; passwords come from an env variable.
"""
import argparse
import base64
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
WEB_FILES=('questions.js','questions_more.js','ontario.js','security.js','rewards.js','parking.js','rewards-ui.js','rewards.css','achievement-popups.css')


def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Desktop UI changed: Android adapter anchor must be reviewed')
    return text.replace(old,new,1)


def build_assets(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    html=once(html,'  var KV_ON = false;        // true once the server store has hydrated','  var rewardUI=null, rewardSessionId=null;')
    html=once(html,"    if(KV_ON){ fetch('/api/kv',{method:'POST',headers:{'Content-Type':'application/json','X-AC7-Request':'1'},body:JSON.stringify({k:k,v:s})}).catch(function(){}); }",'')
    start=html.index('  function hydrateStore(done){');end=html.index('  function uid()',start)
    html=html[:start]+'''  function hydrateStore(done){done();}
  function removeProfileData(id){
    Object.keys(KV).concat(Object.keys(LS)).forEach(function(k){
      if(k==='rt_rewards_'+id||k==='ac7_set_'+id||k.indexOf('ac7_hist_'+id+'_')===0){delete KV[k];try{LS.removeItem(k);}catch(e){}}
    });
  }
'''+html[end:]
    html=once(html,'var id=b.dataset.delp; save','var id=b.dataset.delp; removeProfileData(id); save')
    html=once(html,"if(activeProfileId()===id) save('ac7_active_profile'","if(load('ac7_active_profile','default')===id) save('ac7_active_profile'")
    start=html.index('      <hr',html.index('<h2>Test sets (jurisdictions)</h2>'));end=html.index('      <p class="muted" id="importMsg"',start);end=html.index('</p>',end)+4
    html=html[:start]+'<p class="muted">Offline phone edition: Alberta and Ontario are included. Handbook generation and test-set import/export remain in the desktop edition.</p>'+html[end:]
    start=html.index('  // ---------- dynamic auto-import');end=html.index('  // ---------- study flags',start)
    html=html[:start]+html[end:]
    html='\n'.join(line for line in html.splitlines() if not any(needle in line for needle in ["getElementById('genFile').addEventListener","getElementById('genFormat').addEventListener","getElementById('importFile').addEventListener","getElementById('exportDs').addEventListener"]))+'\n'
    html=html.replace('renderManage(); checkHealth();','renderManage();')
    html=once(html,"'history','manage','settings'].forEach", "'history','manage','settings','garage'].forEach")
    html=once(html,'    mode=which;','    if(rewardUI&&!rewardUI.ensureChoice())return;\n    rewardSessionId=uid();\n    mode=which;')
    html=once(html,'    showResults(score,current.length,passed,detail,sectionResults);',"    if(rewardUI)rewardUI.complete({id:rewardSessionId,dataset:activeDatasetKey(),date:Date.now(),questions:detail.map(function(d){return {id:d.id,correct:d.correct,q:d.q,correctText:d.options[d.answer]};})});\n    showResults(score,current.length,passed,detail,sectionResults);\n    if(rewardUI){document.getElementById('resultMsg').textContent+=rewardUI.resultMessage();rewardUI.showPending();}")
    for name in ('renderHome','renderManage'):
        html=once(html,'  function '+name+'(){','  function '+name+'(){\n    if(rewardUI)rewardUI.refresh();')
    html=once(html,"    show('home');\n  });",'''    rewardUI=RoadTripUI.mount({get:function(){return load('rt_rewards_'+activeProfileId(),null);},put:function(s){save('rt_rewards_'+activeProfileId(),s);},profile:activeProfileId,navigate:show});
    show('home');
    window.roadTripBack=function(){var dialog=document.querySelector('dialog[open]');if(dialog){dialog.dispatchEvent(new Event('cancel',{cancelable:true}));return true;}if(!document.getElementById('screen-home').classList.contains('hidden'))return false;if(!document.getElementById('screen-test').classList.contains('hidden')&&!confirm('Leave this test? Unfinished answers will not be saved.'))return true;show('home');return true;};
  });''')
    html=once(html,'<script src="security.js"></script>','<script src="security.js"></script>\n<script src="rewards.js"></script>\n<script src="parking.js"></script>\n<script src="rewards-ui.js"></script>')
    # Android uses its installed offline speech engine, never a network voice.
    html=once(html,'  function speak(text,btn){ if(!synth)',"  function speak(text,btn){ if(window.NativeSpeech){if(!NativeSpeech.speak(String(text).slice(0,12000),Number(settings.rate)||0.95))note('Install an offline English text-to-speech voice in Android Settings to use read-aloud.');return;} if(!synth)")
    html=once(html,'  function stopSpeak(){ if(synth)', '  function stopSpeak(){ if(window.NativeSpeech)NativeSpeech.stop(); if(synth)')
    html=once(html,"    if(synth){ loadVoices(); setTimeout(loadVoices,300); note('If no voices appear, they may load a moment after the page opens.'); }","    if(window.NativeSpeech){note('Read-aloud uses an installed offline English Android voice.');document.getElementById('voiceSel').innerHTML='<option>Android offline English</option>';document.getElementById('voiceSel').disabled=true;} else if(synth){ loadVoices(); setTimeout(loadVoices,300); note('If no voices appear, they may load a moment after the page opens.'); }")
    html=once(html,'</head>','<link rel="stylesheet" href="rewards.css">\n<link rel="stylesheet" href="achievement-popups.css">\n</head>')
    hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()+"'" for script in re.findall(r'<script>(.*?)</script>',html,re.S))
    csp="default-src 'none'; script-src 'self' "+hashes+"; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'none'; font-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; frame-src 'none'"
    html=once(html,'<head>','<head>\n<meta http-equiv="Content-Security-Policy" content="'+csp+'">')
    if '/api/' in html or 'fetch(' in html or 'genFile' in html:
        raise ValueError('Server dependency remains in Android HTML')
    (output/'index.html').write_text(html,encoding='utf-8',newline='\n')
    for name in WEB_FILES:shutil.copyfile(ROOT/name,output/name)
    (output/'images').mkdir(exist_ok=True)
    for image in sorted((ROOT/'images').glob('*.svg')):shutil.copyfile(image,output/'images'/image.name)
    shutil.copyfile(ROOT/'LICENSE',output/'LICENSE.txt')
    shutil.copyfile(ROOT/'docs'/'SIGN-REVIEW.md',output/'SIGN-REVIEW.txt')
    return ['index.html',*WEB_FILES,'LICENSE.txt','SIGN-REVIEW.txt']+['images/'+image.name for image in sorted((ROOT/'images').glob('*.svg'))]


def sdk_tool(sdk,name):
    matches=list(Path(sdk).rglob(name))
    if len(matches)!=1:raise ValueError('Expected exactly one SDK '+name+'; supply an SDK folder with one build-tools/platform version')
    return str(matches[0])


def build_apk(sdk,work,out,keystore,password_env):
    work=Path(work);work.mkdir(parents=True,exist_ok=True);work=Path(tempfile.mkdtemp(prefix='build-',dir=work));out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    keystore=Path(keystore).resolve()
    if keystore.is_relative_to(ROOT) or not keystore.is_file():raise ValueError('Signing keystore must exist outside this repository')
    assets=work/'assets';asset_files=build_assets(assets)
    android_jar=sdk_tool(sdk,'android.jar');aapt=sdk_tool(sdk,'aapt2.exe' if __import__('os').name=='nt' else 'aapt2')
    align=sdk_tool(sdk,'zipalign.exe' if __import__('os').name=='nt' else 'zipalign')
    classes=work/'classes';classes.mkdir(exist_ok=True);dex=work/'dex';dex.mkdir(exist_ok=True)
    def run(*args):subprocess.run([str(x) for x in args],check=True)
    run('javac','--release','8','-g:none','-encoding','UTF-8','-classpath',android_jar,'-d',classes,ROOT/'android'/'MainActivity.java')
    run('java','-cp',sdk_tool(sdk,'d8.jar'),'com.android.tools.r8.D8','--min-api','26','--lib',android_jar,'--output',dex,*sorted(classes.rglob('*.class')))
    compiled=work/'resources.zip';run(aapt,'compile','--dir',ROOT/'android'/'res','-o',compiled)
    unsigned=work/'unsigned.apk';run(aapt,'link','-I',android_jar,'--manifest',ROOT/'android'/'AndroidManifest.xml','--min-sdk-version','26','--target-sdk-version','35','-o',unsigned,compiled)
    with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_DEFLATED) as package:
        package.write(dex/'classes.dex','classes.dex')
        for name in asset_files:package.write(assets/name,'assets/'+name)
    aligned=work/'aligned.apk';run(align,'-p','-f','4',unsigned,aligned)
    signer=sdk_tool(sdk,'apksigner.jar')
    run('java','-jar',signer,'sign','--ks',keystore,'--ks-pass','env:'+password_env,'--key-pass','env:'+password_env,'--v4-signing-enabled','false','--out',out,aligned)
    run('java','-jar',signer,'verify','--verbose','--print-certs',out)
    run(aapt,'dump','badging',out)
    digest=hashlib.sha256(out.read_bytes()).hexdigest();out.with_suffix('.apk.sha256').write_text(digest+'  '+out.name+'\n')
    print('APK verified:',out.name,'SHA256:',digest)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assets-only');p.add_argument('--sdk');p.add_argument('--work');p.add_argument('--out');p.add_argument('--keystore');p.add_argument('--store-pass-env',default='ROADTRIP_SIGNING_PASSWORD');a=p.parse_args()
    if a.assets_only:build_assets(Path(a.assets_only));return
    if not all((a.sdk,a.work,a.out,a.keystore)):p.error('Provide --sdk, --work, --out and --keystore, or use --assets-only')
    build_apk(a.sdk,a.work,a.out,a.keystore,a.store_pass_env)
if __name__=='__main__':main()
