#!/bin/bash
# make_kit.sh (v0.10) — CLOUD: build the Mac engine kit from this plugin copy, for _series/mac_render/ on the Mac.
#   bash engine/tools/mac/make_kit.sh [outdir]      -> <outdir>/engine_kit_v<version>-<hash>.tar + es.sh (default /mnt/user-data/outputs/kit)
# Then commit both files: engine_kit_v<version>.tar -> VIDEO GEN/_series/mac_render/, es.sh -> VIDEO GEN/_series/es.sh
# Needed only when `bash _series/es.sh version` on the Mac differs from the plugin version.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"; cd "$ROOT"
V="$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")"
O="${1:-/mnt/user-data/outputs/kit}"; mkdir -p "$O"
rm -f "$O"/engine_kit_v*.tar
tar cf "$O/kit.tmp" --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' engine/tools engine/studio engine/template
H="$(md5sum "$O/kit.tmp" | cut -c1-7)"; mv "$O/kit.tmp" "$O/engine_kit_v$V-$H.tar"     # unique name per build (file transfer caches by name)
cp engine/tools/mac/es.sh "$O/es.sh"
ls -la "$O"
echo "commit: $O/engine_kit_v$V-$H.tar -> ~/Documents/VIDEO GEN/_series/mac_render/engine_kit_v$V-$H.tar ; $O/es.sh -> ~/Documents/VIDEO GEN/_series/es.sh"
echo "(es.sh always uses the newest engine_kit_v*.tar; older kits can go to _to_delete/)"
