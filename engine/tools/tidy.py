#!/usr/bin/env python3
"""Tidy an episode folder after delivery (v0.5). usage: tidy.py <project> [--apply]
Without --apply it only lists what it would do. out/ keeps finals only: everything else in out/ moves to drafts/
(key sheets -> drafts/keys/, previews/un-baked videos stay in drafts/). Creates missing standard folders
(vo/unused, drafts, docs, img). Lists what is left in _to_delete/ for the creator to empty (the connected folder can't delete)."""
import argparse, fnmatch, pathlib, shutil, sys
# keep in sync with pack.py (pack.py has no import guard, so the lists are repeated here)
LAYOUT = ['out', 'docs', 'drafts', 'vo/raw', 'vo/unused', 'img', 'images', '_to_delete', '.studio']
FINALS = ['*_reel_9x16.mp4', '*_feed_4x5.mp4', 'cover_reel_9x16.png', 'cover_feed_4x5.png', 'captions.bn_IN.srt', 'captions.en_US.srt', 'publish.txt']
ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
P = pathlib.Path(a.project); out = P / 'out'; moves = []
if out.exists():
    for f in sorted(out.iterdir()):
        if f.is_file() and not any(fnmatch.fnmatch(f.name, g) for g in FINALS):
            moves.append((f, P / 'drafts' / ('keys' if f.name.startswith('keys_') else '') / f.name))
for f, t in moves:
    print(('MOVE ' if a.apply else 'would move ') + f'{f.relative_to(P)} -> {t.relative_to(P)}')
    if a.apply: t.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(f), str(t))
for d in LAYOUT:
    if not (P / d).exists():
        print(('MKDIR ' if a.apply else 'would create ') + d)
        if a.apply: (P / d).mkdir(parents=True, exist_ok=True)
left = [x.name for x in (P / '_to_delete').glob('*')] if (P / '_to_delete').exists() else []
print(f'_to_delete/: {len(left)} item(s) for the creator to empty' if left else '_to_delete/: empty')
if not a.apply and moves: print('re-run with --apply')
