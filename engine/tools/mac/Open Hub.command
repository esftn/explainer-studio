#!/bin/zsh
# Double-click: refresh the overview from the episode folders, then open 00_HUB/HUB.html in your browser.
cd "$(dirname "$0")"
if xcode-select -p >/dev/null 2>&1 || [ -x /opt/homebrew/bin/python3 ]; then
  python3 _series/tools/hub.py || echo "(refresh failed — showing the last saved hub)"
fi
open "00_HUB/HUB.html"
