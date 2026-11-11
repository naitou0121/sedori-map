#!/usr/bin/env python3
"""ブックオフ公式の店舗ページから「駐車場」と「アクセス」の項目を読み、data/shopinfo.json に書く（店ID→公式の表記そのまま）。
1店1リクエスト・2.6秒間隔・途中から再開できる。429/503 が出たらその場で止まる。
営業時間と同じく、変わることがあるので数か月に1回やり直す → python3 build.py。"""
import json, re, html, time, urllib.request, urllib.error, pathlib, datetime, sys
root=pathlib.Path(__file__).parent; out=root/'data/shopinfo.json'
UA={'User-Agent':'Mozilla/5.0 (Macintosh) sedori-map/shopinfo (github.com/naitou0121/sedori-map)'}
stores=json.loads((root/'data/sources/bookoff.json').read_text())['stores']
done=json.loads(out.read_text()) if out.exists() else {'fetchedAt':'','source':'bookoff.co.jp 各店舗ページの「駐車場」「アクセス」','stores':{}}
def lines(h):
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',h,flags=re.S); t=html.unescape(re.sub(r'<[^>]+>','\n',t)); return [l.strip() for l in t.split('\n') if l.strip()]
n=0
for s in stores:
    if s['id'] in done['stores'] or not s.get('url'): continue
    try:
        h=urllib.request.urlopen(urllib.request.Request(s['url'],headers=UA),timeout=30).read().decode('utf-8','replace')
        L=lines(h); v=L[L.index('駐車場')+1] if '駐車場' in L and L.index('駐車場')+1<len(L) else ''
        ac=[]
        if 'アクセス' in L:
            for l in L[L.index('アクセス')+1:L.index('アクセス')+8]:
                if l.startswith('【'): ac.append(l[:320])
                else: break
        done['stores'][s['id']]={'pk':v[:60],'ac':ac}
    except urllib.error.HTTPError as e:
        if e.code in (429,503): print('STOP',e.code,s['id'],flush=True); break
        done['stores'][s['id']]={'pk':'','ac':[]}; print('http',e.code,s['id'],flush=True)
    except Exception as e:
        print('err',s['id'],str(e)[:80],flush=True)
    n+=1
    if n%25==0:
        done['fetchedAt']=datetime.date.today().isoformat(); out.write_text(json.dumps(done,ensure_ascii=False,indent=0)); print(n,len(done['stores']),flush=True)
    time.sleep(2.6)
done['fetchedAt']=datetime.date.today().isoformat(); out.write_text(json.dumps(done,ensure_ascii=False,indent=0)); print('DONE',len(done['stores']),'/',len(stores),flush=True)
