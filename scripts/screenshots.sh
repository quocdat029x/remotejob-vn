#!/usr/bin/env bash
# Take light/dark screenshots at 1280 and 390 px with headless Chrome. Requires a local server (see README).
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8765}"
OUT="${OUT:-screenshots}"
CHROME="${CHROME:-google-chrome}"
mkdir -p "$OUT"
declare -A PAGES=(
  [home]="/"
  [companies]="/cong-ty/"
  [company]="/cong-ty/covergo/"
  [jobs]="/viec-lam/"
  [job]="/viec-lam/covergo-senior-full-stack-engineer-net-vue-react-fully-remote/"
  [tools]="/cong-cu/"
)
for name in "${!PAGES[@]}"; do
  for scheme in light dark; do
    [ "$scheme" = dark ] && pcs=0 || pcs=1
    for w in 1280 390; do
      h=$([ "$w" = 1280 ] && echo 2000 || echo 2400)
      "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --no-first-run \
        --blink-settings=preferredColorScheme=$pcs --force-device-scale-factor=1 \
        --window-size=$w,$h --virtual-time-budget=3000 \
        --screenshot="$OUT/$name-$scheme-$w.png" "$BASE${PAGES[$name]}" >/dev/null 2>&1
    done
  done
done
ls "$OUT"
