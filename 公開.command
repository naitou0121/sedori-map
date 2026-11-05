#!/bin/zsh
# 直したものを本番に出す：ビルド → GitHub に push → 反映を確認（2回目以降はいつもこれ）
cd "$(dirname "$0")"
set -e
MSG="${1:-update $(date +%Y-%m-%d_%H:%M)}"
echo "▶ ビルド"
python3 build.py
echo "▶ push"
git add -A
git commit -m "$MSG" || true
git push origin main
echo "▶ 反映待ち（最大3分）"
want=$(grep -o 'app-version" content="[0-9]*' index.html | grep -o '[0-9]*$')
for i in {1..18}; do
  got=$(curl -s https://naitou0121.github.io/sedori-map/ | grep -o 'app-version" content="[0-9]*' | grep -o '[0-9]*$')
  [ "$got" = "$want" ] && break
  sleep 10; printf '.'
done
echo
if [ "$got" = "$want" ]; then
  echo "✅ 本番に反映  版 $got  https://naitou0121.github.io/sedori-map/"
  open https://naitou0121.github.io/sedori-map/
else
  echo "⚠ まだ反映されていません（本番 $got / 手元 $want）。数分後にもう一度開いてみてください"
fi
echo "（このウィンドウは閉じてOK）"
