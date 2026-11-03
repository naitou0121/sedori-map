#!/usr/bin/env python3
"""src/body.html → index.html（PWA用の頭・SW登録・更新バナーを付ける）。sw.js のキャッシュ名も版を進める。"""
import re, pathlib, datetime
root=pathlib.Path(__file__).parent
body=(root/'src/body.html').read_text()
body=body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
ver=datetime.datetime.now().strftime('%Y%m%d%H%M')
head=f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="仕入れマップ">
<meta name="theme-color" content="#8a5a2b">
<meta name="app-version" content="{ver}">
<link rel="manifest" href="./manifest.webmanifest">
<link rel="apple-touch-icon" href="./icon-180.png">
<link rel="icon" href="./icon-192.png">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}[hidden]{{display:none!important}}
#updBar{{position:fixed;left:16px;right:16px;top:calc(12px + env(safe-area-inset-top,0px));z-index:50;background:#8a5a2b;color:#fff;border-radius:12px;padding:10px 14px;font:15px -apple-system,system-ui,sans-serif;display:flex;justify-content:space-between;align-items:center;gap:10px;box-shadow:0 6px 20px rgba(0,0,0,.25)}}
#updBar button{{font:inherit;font-weight:700;color:#8a5a2b;background:#fff;border:0;border-radius:8px;padding:6px 12px}}</style>
'''
i=body.index('<style>')
sw='''
<script>
if('serviceWorker' in navigator){navigator.serviceWorker.register('./sw.js').then(function(reg){
  function show(){ if(document.getElementById('updBar')) return; var b=document.createElement('div'); b.id='updBar'; b.innerHTML='<span>新しい版があります</span><button type="button">更新する</button>'; b.querySelector('button').onclick=function(){ location.reload(); }; document.body.appendChild(b); }
  var t0=Date.now(); var early=function(){ return Date.now()-t0<15000; };
  function arrived(w){ if(early()){ try{ w&&w.postMessage&&w.postMessage('skip'); }catch(e){} setTimeout(function(){ location.reload(); },300); } else show(); }
  reg.addEventListener('updatefound',function(){ var w=reg.installing; w&&w.addEventListener('statechange',function(){ if(w.state==='installed'&&navigator.serviceWorker.controller) arrived(w); }); });
  if(reg.waiting&&navigator.serviceWorker.controller) arrived(reg.waiting);
  var hadCtrl=!!navigator.serviceWorker.controller; var reloaded=false; navigator.serviceWorker.addEventListener('controllerchange',function(){ if(reloaded||!hadCtrl) return; reloaded=true; if(early()) location.reload(); });
  reg.update().catch(function(){});
}).catch(function(){});}
</script>
'''
out=head+body[:i]+'</head><body>'+body[i:]+sw+'</body></html>'
(root/'index.html').write_text(out)
swp=root/'sw.js'; t=swp.read_text(); t=re.sub(r'const C="sedori-map-[^"]*"',f'const C="sedori-map-{ver}"',t); swp.write_text(t)
print('built',ver)
