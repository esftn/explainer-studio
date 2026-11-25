#!/bin/zsh
# Double-click to open Remotion Studio (no Terminal typing).
# First run: finds your Remotion project (in Documents, Desktop, Developer, Projects) and remembers it in
# VIDEO GEN/00_HUB/.remotion_project. To switch projects later, delete that file and double-click again.
cd "$(dirname "$0")"; HERE="$PWD"; CONF="$HERE/00_HUB/.remotion_project"
export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh" >/dev/null 2>&1
[ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
P="$(cat "$CONF" 2>/dev/null)"
if [[ -z "$P" || ! -d "$P" ]]; then
  echo "Looking for your Remotion project (first run only)…"
  found=()
  while IFS= read -r d; do [[ -n "$d" ]] && found+=("$d"); done < <(
    find "$HOME/Documents" "$HOME/Desktop" "$HOME/Developer" "$HOME/Projects" "$HOME/Sites" -maxdepth 5 \
      \( -name node_modules -o -name .git -o -name Library -o -name '.*' \) -prune -o \
      \( -name 'remotion.config.ts' -o -name 'remotion.config.js' -o -name 'remotion.config.mjs' \) -print 2>/dev/null \
      | while IFS= read -r f; do dirname "$f"; done | sort -u)
  if (( ${#found} == 1 )); then P="${found[1]}"
  elif (( ${#found} > 1 )); then
    echo "Found several Remotion projects — type the number of the one to open:"
    select P in "${found[@]}"; do [[ -n "$P" ]] && break; done
  else
    echo "No Remotion project found automatically."
    echo "Drag your Remotion project folder into this window, then press Enter:"
    read -r P; P="${P%/}"; P="${P//\\ / }"; P="${P#\'}"; P="${P%\'}"
  fi
  [[ -d "$P" ]] || { echo "Not a folder: $P"; read -k1 "?Press any key to close"; exit 1; }
  print -r -- "$P" > "$CONF"; echo "Remembered: $P"
fi
cd "$P" || exit 1
if ! command -v npx >/dev/null; then echo "Node.js (npx) not found — install Node, then try again."; read -k1 "?Press any key to close"; exit 1; fi
[[ -d node_modules ]] || { echo "Installing packages (first time only)…"; npm install; }
echo "Starting Remotion Studio for: $P"
echo "It opens in your browser. Keep this window open while you use it; close it (or press Ctrl+C) to stop."
npx remotion studio
