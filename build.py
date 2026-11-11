#!/usr/bin/env python3
"""ビルド（配布物を作り直す）。やること：
  1. data/sources/*.json（チェーンごとの店データ）→ data/stores.json に合流
  2. src/body.html → index.html（PWA用の頭・SW登録・更新バナーを付ける）
  3. README.md → guide.html（スマホで読める手引き）
  4. sw.js のキャッシュ名と配布ファイル一覧を更新
直し方は README.md「改造する」。"""
import re, json, html, pathlib, datetime
root=pathlib.Path(__file__).parent
ver=datetime.datetime.now().strftime('%Y%m%d%H%M')

# ---- 1. 店データの合流 ----
chains=[]; stores=[]; seen=set()
for f in sorted((root/'data/sources').glob('*.json')):
    j=json.loads(f.read_text())
    ch=j.get('chain') or {'id':f.stem,'name':f.stem}
    ch.setdefault('id',f.stem); ch.setdefault('name',ch['id']); ch.setdefault('short',ch['name'][:2]); ch.setdefault('color','#8a5a2b'); ch.setdefault('books',False)
    ch['fetchedAt']=j.get('fetchedAt',''); n=0
    for s in j.get('stores',[]):
        if not (isinstance(s.get('lat'),(int,float)) and isinstance(s.get('lng'),(int,float))): continue
        s['chain']=ch['id']
        if s['id'] in seen: s['id']=ch['id']+'_'+s['id']
        seen.add(s['id']); stores.append(s); n+=1
    ch['count']=n; chains.append(ch); print(f"  {ch['name']}: {n}店 ({f.name})")
# ---- 1.5 ブックチケットの対象店に印を付ける（data/ticket.json・店名と県で突き合わせる） ----
import unicodedata
ticket_meta=None
tf=root/'data/ticket.json'
if tf.exists():
    tj=json.loads(tf.read_text())
    def _n(x, paren=False):
        x=unicodedata.normalize('NFKC',x).lower()
        if not paren: x=re.sub(r'\(.*?\)','',x)
        x=re.sub(r'^(book\s*off)\s*(super\s*bazaar|plus|総合買取窓口)?','',x.strip())
        x=''.join(chr(ord(c)+0x60) if 'ぁ'<=c<='ゖ' else c for c in x)  # ひらがな→カタカナ（プロぺ/プロペ の揺れ）
        return re.sub(r'[\s・\-ｰー]','',x)
    for s in stores: s.pop('tk',None)
    hit=0; miss=[]
    for x in tj['stores']:
        pool=[s for s in stores if s.get('chain')=='bookoff' and s.get('pref')==x['pref']]
        _h=lambda v: v['name'].split(' / ')[0]  # 「A店 / 併設B店」は先頭だけ見る
        c=[s for s in pool if _n(_h(s),True)==_n(x['name'],True)] or [s for s in pool if _n(_h(s))==_n(x['name'])]
        if len(c)>1:
            b=[s for s in c if '本' in s['name'].replace('本店','')]
            if b: c=b
        if not c: miss.append(x['pref']+' '+x['name']); continue
        for s in c: s['tk']=x['region']
        hit+=1
    ticket_meta={'name':tj.get('name','ブックチケット'),'fetchedAt':tj.get('fetchedAt',''),'count':hit,'source':tj.get('source',''),'open':tj.get('open','https://www.sub-ticket.jp/mypage/'),'regions':{r['name']:r['id'] for r in tj.get('regions',[])}}
    print(f"  ブックチケット: {hit}/{len(tj['stores'])}店に印" + (f" ・ 合わなかった店 {miss}" if miss else ''))
(root/'data/stores.json').write_text(json.dumps({'builtAt':datetime.date.today().isoformat(),'chains':chains,'count':len(stores),'ticket':ticket_meta,'stores':stores},ensure_ascii=False,separators=(',',':')))

# ---- 2. index.html ----
body=(root/'src/body.html').read_text()
body=body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
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
(root/'index.html').write_text(head+body[:i]+'</head><body>'+body[i:]+sw+'</body></html>')

# ---- 3. README.md → guide.html（外部ライブラリなしの小さな変換） ----
def md2html(md):
    out=[]; lines=md.split('\n'); k=0; inlist=None
    def inline(t):
        t=html.escape(t,quote=False)
        t=re.sub(r'`([^`]+)`',r'<code>\1</code>',t)
        t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
        t=re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',r'<a href="\2" target="_blank" rel="noopener">\1</a>',t)
        t=re.sub(r'(?<!["\'>=])(https?://[^\s<)]+)',r'<a href="\1" target="_blank" rel="noopener">\1</a>',t)
        return t
    def close():
        nonlocal inlist
        if inlist: out.append(f'</{inlist}>'); inlist=None
    while k<len(lines):
        l=lines[k]
        if l.startswith('```'):
            close(); buf=[]; k+=1
            while k<len(lines) and not lines[k].startswith('```'): buf.append(lines[k]); k+=1
            out.append('<pre>'+html.escape('\n'.join(buf))+'</pre>'); k+=1; continue
        m=re.match(r'^(#{1,4}) (.*)',l)
        if m: close(); n=len(m.group(1)); out.append(f'<h{n}>{inline(m.group(2))}</h{n}>'); k+=1; continue
        if l.startswith('|'):
            close(); rows=[]
            while k<len(lines) and lines[k].startswith('|'): rows.append([c.strip() for c in lines[k].strip('|').split('|')]); k+=1
            rows=[r for r in rows if not all(re.fullmatch(r':?-+:?',c) for c in r)]
            out.append('<table>'+''.join('<tr>'+''.join(f'<{"th" if ri==0 else "td"}>{inline(c)}</{"th" if ri==0 else "td"}>' for c in r)+'</tr>' for ri,r in enumerate(rows))+'</table>'); continue
        m=re.match(r'^(\d+)\. (.*)',l)
        if m:
            if inlist!='ol': close(); out.append('<ol>'); inlist='ol'
            out.append(f'<li>{inline(m.group(2))}</li>'); k+=1; continue
        m=re.match(r'^[-・] (.*)',l)
        if m:
            if inlist!='ul': close(); out.append('<ul>'); inlist='ul'
            out.append(f'<li>{inline(m.group(1))}</li>'); k+=1; continue
        if l.startswith('> '): close(); out.append(f'<blockquote>{inline(l[2:])}</blockquote>'); k+=1; continue
        if l.strip()=='---': close(); out.append('<hr>'); k+=1; continue
        if not l.strip(): close(); k+=1; continue
        close(); out.append(f'<p>{inline(l)}</p>'); k+=1
    close(); return '\n'.join(out)
readme=(root/'README.md').read_text()
guide=f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>仕入れマップ 手引き</title><meta name="theme-color" content="#8a5a2b"><link rel="icon" href="./icon-192.png">
<style>
:root{{--bg:#f6f3ee;--surface:#fff;--ink:#2b2420;--muted:#7a6f66;--line:#e6dfd5;--accent:#8a5a2b;--accent-soft:#f1e6d8;--code:#f3eee6}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1c1917;--surface:#26211e;--ink:#f1ebe4;--muted:#a79c92;--line:#3a332e;--accent:#d9a86c;--accent-soft:#3a2d20;--code:#2e2824}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 -apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif;-webkit-text-size-adjust:100%}}
.wrap{{max-width:720px;margin:0 auto;padding:20px 16px 60px}}
.top{{display:flex;align-items:center;gap:12px;margin-bottom:8px}}.top img{{width:44px;height:44px;border-radius:11px}}.top a{{color:var(--accent);text-decoration:none;font-weight:700;margin-left:auto;font-size:14px}}
h1{{font-size:24px;margin:8px 0 4px;line-height:1.3}}h2{{font-size:19px;margin:36px 0 8px;padding-top:14px;border-top:1px solid var(--line)}}h3{{font-size:16px;margin:22px 0 6px}}h4{{font-size:15px;margin:16px 0 4px;color:var(--muted)}}
p{{margin:8px 0}}ul,ol{{padding-left:22px;margin:6px 0}}li{{margin:3px 0}}a{{color:var(--accent)}}
code{{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);padding:1px 6px;border-radius:6px;word-break:break-all}}
pre{{background:var(--code);border:1px solid var(--line);border-radius:12px;padding:12px 14px;overflow-x:auto;font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0;display:block;overflow-x:auto}}th,td{{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}}th{{background:var(--accent-soft)}}
blockquote{{margin:10px 0;padding:8px 14px;border-left:4px solid var(--accent);background:var(--surface);border-radius:0 10px 10px 0;color:var(--muted)}}hr{{border:0;border-top:1px solid var(--line);margin:28px 0}}
.foot{{margin-top:40px;color:var(--muted);font-size:13px}}
</style></head><body><div class="wrap">
<div class="top"><img src="./icon-192.png" alt=""><span style="font-weight:700">仕入れマップ</span><a href="./">← アプリへ</a></div>
{md2html(readme)}
<div class="foot">この手引きは README.md から自動で作っています（版 {ver}）。</div>
</div></body></html>'''
(root/'guide.html').write_text(guide)

# ---- 4. sw.js ----
assets=['./','./index.html','./guide.html','./leaflet.js','./leaflet.css','./data/stores.json','./manifest.webmanifest','./icon-180.png','./icon-192.png','./icon-512.png','./icon-512-maskable.png']
swp=root/'sw.js'; t=swp.read_text()
t=re.sub(r'const C="sedori-map-[^"]*"',f'const C="sedori-map-{ver}"',t)
t=re.sub(r'const ASSETS=\[[^\]]*\]','const ASSETS='+json.dumps(assets),t)
swp.write_text(t)
print('built',ver,f'{len(stores)}店 / {len(chains)}チェーン')
