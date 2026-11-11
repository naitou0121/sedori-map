#!/usr/bin/env python3
"""ブックオフ公式の店舗検索（サイトが裏で使っている公開API）から全国の店舗を取り、data/sources/bookoff.json に書く。
1都道府県1リクエスト・1.2秒間隔。営業時間が変わった時はこれを再実行 → python3 build.py → 公開.command。
各店に books（本を売っているか）と buyonly（買取専門か）も付ける。
他のチェーンを足す時はこのファイルは触らず tools/csv2json.py を使う（README「改造」参照）。"""
import json, time, urllib.parse, urllib.request, re, pathlib, datetime
API='https://as.blue.asp.appirits.com/bookoff2/search.json'
PREFS=['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']
out=[]
def clean(x):
    if isinstance(x,list): x=x[0] if x else ''
    return re.sub(r'<[^>]+>','',x or '').strip()
def codes(x):
    if isinstance(x,list): x=x[0] if x else ''
    return [c for c in str(x or '').split(':') if c]
for i,p in enumerate(PREFS,1):
    key=f'{i:02d}_{p}'
    page=1
    while True:
        q=urllib.parse.urlencode({'limit':100,'page':page,'facet':'false','sort':'store_kana asc','opt_prefecture':key})
        j=json.load(urllib.request.urlopen(API+'?'+q,timeout=30))
        items=j['result']['items']; total=j['result']['total']
        for it in items:
            tel=clean(it.get('tel_number')).split('\n')[0]; tel=re.match(r'[\d-]+',tel); tel=tel.group(0) if tel else ''
            # 取扱商品のコード（店のページの「売りたい商品／買いたい商品」と同じ。01＝本）。buy＝客が買える＝店が売っている
            buy,sell=codes(it.get('product_parents_buy')),codes(it.get('product_parents_sell'))
            out.append({'id':'bo'+str(it['id']),'chain':'bookoff','name':('BOOKOFF ' if not str(it['title']).startswith('BOOKOFF') else '')+it['title'],
                'brand':it.get('store_category') or 'BOOKOFF','address':clean(it.get('text')),'zip':clean(it.get('zip_code')),
                'pref':p,'city':clean(it.get('city')).split('_')[-1],'lat':it.get('lat'),'lng':it.get('lon'),
                'hours':clean(it.get('business_hours1')),'hours2':clean(it.get('business_hours2')),'tel':tel,
                'url':'https://www.bookoff.co.jp/shop/'+(it.get('url') or ''),
                **({'books':'01' in buy} if (buy or sell) else {}),**({'buyonly':True} if (sell and not buy) else {})})
        if page*100>=total: break
        page+=1; time.sleep(1.2)
    print(p,total,flush=True); time.sleep(1.2)
CHAIN={'id':'bookoff','name':'ブックオフ','short':'BO','color':'#1a5fb4','books':True,'source':'bookoff.co.jp 店舗検索','sourceUrl':'https://www.bookoff.co.jp/shop/'}
pathlib.Path(__file__).parent.joinpath('data/sources/bookoff.json').write_text(json.dumps({'chain':CHAIN,'fetchedAt':datetime.date.today().isoformat(),'stores':out},ensure_ascii=False,separators=(',',':')))
print('total',len(out))
