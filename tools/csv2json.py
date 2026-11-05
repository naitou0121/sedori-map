#!/usr/bin/env python3
"""CSV（店名・住所・営業時間…）→ data/sources/<チェーンID>.json

使い方：
  python3 tools/csv2json.py tools/見本.csv --id furuhon --name 古本市場 --short 古本 --color "#2a7a3b" --books
  python3 build.py            # ← data/stores.json に合流・index.html を作り直す

CSVの列（1行目が見出し。name と address だけ必須、ほかは空でOK）：
  name     店名（必須）
  address  住所（必須。lat/lng が無い行はこの住所から位置を取る）
  hours    営業時間（例 10:00～20:00。アプリの営業中判定に使う）
  hours2   別の時間帯の記載（例 日祝 10:00～19:00。表示のみ）
  tel      電話
  url      公式ページ
  brand    業態・店の種類（空なら --name と同じ）
  lat,lng  座標（あれば住所検索を飛ばす）

位置は国土地理院の住所検索API（無料・キー不要）で取る。1件1秒あける。
取れなかった行は最後にまとめて表示するので、住所を直して再実行（取れた行は結果を使い回す）。
"""
import argparse, csv, json, pathlib, re, sys, time, urllib.parse, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
GSI = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q='
PREFS = ['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']

def z2h(t):
    t = re.sub(r'[０-９]', lambda m: chr(ord(m.group(0)) - 0xFEE0), t or '')
    return t.replace('　', ' ').replace('－', '-').replace('‐', '-').replace('―', '-')

def clean_addr(a):
    a = z2h(a)
    a = re.sub(r'〒\s*\d{3}-?\d{4}', ' ', a)
    return re.sub(r'\s+', ' ', a).strip()

def geocode(address):
    q = clean_addr(address)
    if not q:
        return None
    cands = [q, q.replace(' ', '')]
    m = re.match(r'^(.*?\d+(?:-\d+){0,2})', q.replace(' ', ''))
    if m:
        cands.append(m.group(1))
    for v in dict.fromkeys(cands):
        try:
            with urllib.request.urlopen(GSI + urllib.parse.quote(v), timeout=20) as r:
                j = json.load(r)
            if isinstance(j, list) and j and j[0].get('geometry', {}).get('coordinates'):
                lng, lat = j[0]['geometry']['coordinates']
                return {'lat': lat, 'lng': lng, 'title': j[0].get('properties', {}).get('title', '')}
        except Exception:
            pass
        time.sleep(1.0)
    return None

def split_pref_city(address):
    a = clean_addr(address)
    for p in PREFS:
        if a.startswith(p):
            rest = a[len(p):]
            m = re.match(r'^(.+?[市区町村])', rest)
            return p, (m.group(1) if m else '')
    return '', ''

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv', help='店のCSV')
    ap.add_argument('--id', required=True, help='チェーンID（半角英数。ファイル名と店IDの頭に使う。例 furuhon）')
    ap.add_argument('--name', required=True, help='チェーンの表示名（例 古本市場）')
    ap.add_argument('--short', default='', help='チップに出す短い名前（省略時は --name の先頭2文字）')
    ap.add_argument('--color', default='#8a5a2b', help='ピン・タグの色（#rrggbb）')
    ap.add_argument('--books', action='store_true', help='本を扱う店（「本がある店」フィルタに入れる）')
    ap.add_argument('--source', default='', help='データの出どころ（アプリの設定画面に出す）')
    a = ap.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9_-]{1,30}', a.id):
        sys.exit('--id は半角英小文字で始めて英数・_・- だけにしてください')

    out_path = ROOT / 'data' / 'sources' / f'{a.id}.json'
    prev = {}
    if out_path.exists():
        for s in json.loads(out_path.read_text()).get('stores', []):
            prev[(s['name'], s['address'])] = s

    rows = list(csv.DictReader(open(a.csv, encoding='utf-8-sig')))
    stores, failed = [], []
    for i, r in enumerate(rows, 1):
        name = (r.get('name') or '').strip(); address = (r.get('address') or '').strip()
        if not name or not address:
            failed.append((i, name or '(店名なし)', '店名か住所が空')); continue
        lat = r.get('lat'); lng = r.get('lng')
        try:
            lat = float(lat); lng = float(lng)
        except (TypeError, ValueError):
            lat = lng = None
        if lat is None:
            p = prev.get((name, address))
            if p and isinstance(p.get('lat'), (int, float)):
                lat, lng = p['lat'], p['lng']
            else:
                g = geocode(address); time.sleep(1.0)
                if not g:
                    failed.append((i, name, '住所から位置が取れない')); continue
                lat, lng = g['lat'], g['lng']
        pref, city = split_pref_city(address)
        stores.append({
            'id': f'{a.id}{i}', 'chain': a.id, 'name': name,
            'brand': (r.get('brand') or '').strip() or a.name,
            'address': address, 'pref': pref, 'city': city, 'lat': lat, 'lng': lng,
            'hours': z2h((r.get('hours') or '').strip()), 'hours2': (r.get('hours2') or '').strip(),
            'tel': (r.get('tel') or '').strip(), 'url': (r.get('url') or '').strip(),
        })
        print(f'{i:>4} {name}  {lat:.5f},{lng:.5f}', flush=True)

    out = {
        'chain': {'id': a.id, 'name': a.name, 'short': a.short or a.name[:2], 'color': a.color,
                  'books': bool(a.books), 'source': a.source or pathlib.Path(a.csv).name},
        'fetchedAt': datetime.date.today().isoformat(), 'stores': stores,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    print(f'\n書きました: {out_path.relative_to(ROOT)}  {len(stores)}店')
    if failed:
        print(f'\n⚠ 入らなかった行 {len(failed)}件（住所を直して再実行）')
        for i, n, why in failed:
            print(f'  {i}行目 {n}: {why}')
    print('次: python3 build.py')

if __name__ == '__main__':
    main()
