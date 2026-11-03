#!/bin/zsh
# 直し方：src/body.html を編集 → このファイルを実行（ビルド・コミット・push・Pages反映）
set -e
cd "$(dirname "$0")"
python3 build.py
git add -A
git commit -m "${1:-update $(date +%Y-%m-%d_%H:%M)}" || true
git push origin main
echo "pushed. 1〜2分後に https://naitou0121.github.io/sedori-map/ に反映"
