#!/usr/bin/env python3
"""ブックオフ公式の各店ページから「駐車場」の欄を取り、data/parking.json に書く。
店舗検索のAPIには駐車場の項目が無いので、店のページ（1店1ページ）を1.2秒間隔で読む（780店で約16分）。
途中で止まっても、もう一度実行すれば続きから取る。全部取り直す時は --all を付ける。
このあと python3 build.py で data/stores.json に合流する（README「駐車場」参照）。"""
import json, re, sys, time, html, pathlib, datetime, urllib.request
root=pathlib.Path(__file__).parent
out=root/'data/parking.json'
src=json.loads((root/'data/sources/bookoff.json').read_text())['stores']
old=json.loads(out.read_text()) if out.exists() and '--all' not in sys.argv else {}
got=dict(old.get('stores',{}))
def cell(page):
    m=re.search(r'<th>\s*駐車場\s*</th>\s*<td>(.*?)</td>',page,re.S)
    if not m: return None
    t=re.sub(r'<br\s*/?>','\n',m.group(1)); t=html.unescape(re.sub(r'<[^>]+>','',t))
    return re.sub(r'[ \t　]+',' ',re.sub(r'\s*\n\s*',' / ',t.strip())).strip()
def save():
    out.write_text(json.dumps({'source':'bookoff.co.jp 各店のページ「駐車場」欄','fetchedAt':datetime.date.today().isoformat(),'stores':got},ensure_ascii=False,indent=0,sort_keys=True))
todo=[s for s in src if s['id'] not in got]
print(f'{len(src)}店中 {len(todo)}店を取る',flush=True)
miss=[]
for n,s in enumerate(todo,1):
    try:
        req=urllib.request.Request(s['url'],headers={'User-Agent':'Mozilla/5.0 (sedori-map parking fetch)'})
        page=urllib.request.urlopen(req,timeout=30).read().decode('utf-8','replace')
        v=cell(page)
        if v is None: miss.append(s['id']+' '+s['name']+'（欄なし）')
        else: got[s['id']]=v
    except Exception as e:
        miss.append(s['id']+' '+s['name']+f'（{type(e).__name__}）')
    if n%25==0: save(); print(n,len(todo),flush=True)
    time.sleep(1.2)
save()
print('total',len(got),'/',len(src))
if miss: print('取れなかった店:',*miss,sep='\n  ')
