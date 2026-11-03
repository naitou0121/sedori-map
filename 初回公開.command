#!/bin/zsh
# 初回だけ：GitHubに公開リポジトリを作って Pages を有効にする（2回目以降は deploy.sh）
cd "$(dirname "$0")"
set -e
echo "▶ GitHubにリポジトリ naitou0121/sedori-map を作成して push します"
gh repo create naitou0121/sedori-map --public --source=. --remote=origin --push --description "仕入れマップ（本せどり用・ブックオフ店舗＋営業時間）"
echo "▶ GitHub Pages を有効化"
gh api repos/naitou0121/sedori-map/pages -X POST -f build_type=legacy -f 'source[branch]=main' -f 'source[path]=/' >/dev/null
echo "▶ 反映待ち（最大3分）"
for i in {1..18}; do
  code=$(curl -s -o /dev/null -w '%{http_code}' https://naitou0121.github.io/sedori-map/)
  [ "$code" = "200" ] && break
  sleep 10; printf '.'
done
echo; echo "HTTP $code  https://naitou0121.github.io/sedori-map/"
[ "$code" = "200" ] && open https://naitou0121.github.io/sedori-map/
echo "（このウィンドウは閉じてOK）"
