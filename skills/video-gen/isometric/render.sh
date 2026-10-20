#!/bin/bash
# Render isometric diagrams with headless Chrome.
#
#   render.sh stills <dir>                          every <dir>/*.svg -> .png (3200x1800)
#   render.sh video <page.html> <out.mp4> [seconds] CSS animation -> 1080p60 MP4
#
# Video goes through video/capture/capture.mjs at 4K, then downscales to 1080p
# (crisper hairlines than capturing at 1080p). CHROME overrides the browser;
# it defaults to the installed Google Chrome because Playwright's bundled
# Chromium has failed to launch on this setup.
set -euo pipefail

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
abspath() { echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; }

case "${1:-}" in
  stills)
    for f in "$2"/*.svg; do
      png="${f%.svg}.png"
      "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
        --window-size=1600,900 --virtual-time-budget=4000 \
        --screenshot="$(abspath "$png")" "file://$(abspath "$f")" >/dev/null 2>&1
      echo "$png"
    done
    ;;
  video)
    html="$(abspath "$2")"
    out="$3"
    secs="${4:-10}"
    repo="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
    tmp="$(mktemp -d)"
    (cd "$repo/video/capture" && { [ -d node_modules ] || npm install --silent; })
    CHROME="$CHROME" FPS=60 SCALE=2 SECONDS="$secs" \
      node "$repo/video/capture/capture.mjs" "file://$html" "$tmp/4k.mp4"
    ffmpeg -loglevel error -y -i "$tmp/4k.mp4" -vf "scale=1920:1080:flags=lanczos" \
      -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$out"
    rm "$tmp/4k.mp4"
    echo "$out"
    ;;
  *)
    sed -n '2,10p' "$0"
    exit 1
    ;;
esac
