#!/bin/bash
# es.sh (v0.11) — run any explainer-studio tool in the Mac shell, straight on the episode folder. Nothing is copied to the cloud.
# Lives at VIDEO GEN/_series/es.sh; the kit (engine tools + templates) at VIDEO GEN/_series/mac_render/engine_kit_v*.tar.
#   bash _series/es.sh <tool> [args]        e.g.  bash _series/es.sh studio next video36
#                                                 bash _series/es.sh audit video36 --fast
#                                                 bash _series/es.sh finish video36 --local --slug Weak_Taka
#   bash _series/es.sh hub                  rebuild VIDEO GEN/00_HUB (status, copy text, commands)
#   bash _series/es.sh version              kit version (compare with the plugin's .claude-plugin/plugin.json)
# Every device_bash call is a fresh shell and the shell's home is wiped between Claude sessions: this script re-creates what is
# missing (Chromium ~5 s, Python packages ~30-60 s once per session) and is instant after that. Each call is capped at 3 min.
set -e
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; K="$R/_series/mac_render"; cd "$R"
export PYTHONDONTWRITEBYTECODE=1                       # the Mac folder can't delete: no __pycache__ litter
# 25 Nov 2026: the shell's home disk is shared and can be full ("No space left on device") — then keep packages,
# Chromium, the kit and render scratch in /tmp instead. Same layout, just a different base folder.
B="$HOME"; [ "$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2{print $4}')" -lt 1500000 ] 2>/dev/null && B="/tmp/es_home"
mkdir -p "$B"; [ "$B" != "$HOME" ] && mkdir -p "$B/tmp" && export PYTHONUSERBASE="$B/.local" PIP_NO_CACHE_DIR=1 TMPDIR="$B/tmp"
HUB="$B/es/engine/tools/hub.py"; [ -f "$HUB" ] || HUB="$R/_series/tools/hub.py"     # 00_HUB generator (kit copy, else the series copy)
if [ "$1" = hub ] && [ -f "$HUB" ]; then shift; exec python3 "$HUB" "$@"; fi      # hub needs no packages: never blocked by an install
if ! python3 -c "import playwright, numpy, scipy, soundfile, pyloudnorm, brotli, fontTools, PIL" 2>/dev/null; then
  echo "es.sh: installing Python packages (once per session)…" >&2
  python3 -m pip install -q --user playwright numpy scipy soundfile pyloudnorm brotli fonttools pillow >/dev/null 2>&1 \
    || python3 -m pip install -q --user --break-system-packages playwright numpy scipy soundfile pyloudnorm brotli fonttools pillow >/dev/null
fi
SP="$B/chrome/sp"
if [ ! -x "$SP/chromium" ]; then
  mkdir -p "$SP" && tar xf "$K/chromium-v153.0.0-pack.arm64.tar" -C "$SP"
  python3 - "$SP" <<'PY'
import brotli, tarfile, io, os, sys
d = sys.argv[1]
open(f'{d}/chromium', 'wb').write(brotli.decompress(open(f'{d}/chromium.br', 'rb').read())); os.chmod(f'{d}/chromium', 0o755)
for n in ('swiftshader', 'al2023', 'fonts'):
    tarfile.open(fileobj=io.BytesIO(brotli.decompress(open(f'{d}/{n}.tar.br', 'rb').read()))).extractall(f'{d}/{n}')
PY
fi
KIT="$(ls -t "$K"/engine_kit_v*.tar 2>/dev/null | head -1)"                 # newest kit file wins
[ -n "$KIT" ] || { echo "es.sh: no engine_kit_v*.tar in _series/mac_render — build it in the cloud: bash engine/tools/mac/make_kit.sh" >&2; exit 2; }
STAMP="$(basename "$KIT") $(stat -c %s.%Y "$KIT")"           # re-extract when the kit file changes, even at the same version
if [ "$(cat "$B/es/KIT" 2>/dev/null)" != "$STAMP" ]; then
  rm -rf "$B/es" && mkdir -p "$B/es" && tar xf "$KIT" -C "$B/es" && echo "$STAMP" > "$B/es/KIT"
fi
export LD_LIBRARY_PATH="$SP/al2023/lib:$SP/swiftshader" ES_CHROME="$SP/chromium" ES_TOOLS="$B/es/engine/tools"
export ES_SCRATCH="$B/es_scratch"                        # render chunks/segments stay in the VM, not the Mac folder
export PYTHONPATH="$ES_TOOLS/mac${PYTHONPATH:+:$PYTHONPATH}"     # sitecustomize.py: refused deletes become moves to _to_delete/_trash/
T="$1"; shift || true
case "$T" in
  ""|-h|--help) sed -n 2,9p "$0"; exit 0 ;;
  version) basename "$KIT" .tar | sed 's/engine_kit_//; s/-[0-9a-f]*$//'; exit 0 ;;
esac
# hub (25 Nov 2026): tools in _series/tools (hub, cover_v2, …) run too; after any step that changes an episode the
# 00_HUB overview is rebuilt (< 1 s, read-only on the episodes, atomic writes — safe with several chats at once).
if [ -f "$ES_TOOLS/$T.py" ]; then F="$ES_TOOLS/$T.py"; elif [ -f "$R/_series/tools/$T.py" ]; then F="$R/_series/tools/$T.py"
else echo "es.sh: no tool '$T' (tools: $(cd "$ES_TOOLS" && ls *.py | sed 's/\.py$//' | tr '\n' ' ') + $(cd "$R/_series/tools" && ls *.py | sed 's/\.py$//' | tr '\n' ' '))" >&2; exit 2; fi
case "$T" in
  state|studio|finish|guard|new_project|vo_prep|vo_split|words_import|titles_doc|cover_v2|bake_cover|render|render_resume|state_check|tidy)
    set +e; python3 "$F" "$@"; rc=$?
    H="$ES_TOOLS/hub.py"; [ -f "$H" ] || H="$R/_series/tools/hub.py"
    [ -f "$H" ] && { timeout 20 python3 "$H" --quiet >/dev/null 2>&1 || echo "es.sh: hub refresh skipped" >&2; }
    exit $rc ;;
esac
exec python3 "$F" "$@"
