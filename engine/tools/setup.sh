#!/usr/bin/env bash
# One-time setup for the Explainer Studio engine. Safe to re-run.
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
echo "== engine: $HERE"
command -v ffmpeg >/dev/null || { echo "ffmpeg missing: install it (apt install ffmpeg / brew install ffmpeg)"; exit 1; }
command -v node >/dev/null || { echo "node missing: install Node 18+"; exit 1; }
PIP="python3 -m pip install -q"
$PIP playwright numpy scipy soundfile pyloudnorm pillow 2>/dev/null || $PIP --break-system-packages playwright numpy scipy soundfile pyloudnorm pillow
if [ "${WITH_CUTOUTS:-1}" = "1" ]; then
  $PIP "rembg[cpu]" 2>/dev/null || $PIP --break-system-packages "rembg[cpu]" || echo "WARN: rembg not installed — cutouts disabled"
fi
# Chromium: use a preinstalled one if Playwright already finds it
python3 - <<'PY' || python3 -m playwright install chromium
from playwright.sync_api import sync_playwright
with sync_playwright() as p: p.chromium.launch().close()
print("chromium ok")
PY
cd "$HERE" && npm install --silent --no-audit --no-fund
python3 "$HERE/tools/font_test.py" --engine-only
echo "== setup done"
