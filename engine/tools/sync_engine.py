#!/usr/bin/env python3
"""sync_engine.py (v0.9.1) — bring episodes' own engine copy (<videoNN>/engine/) up to the plugin's engine/template.
usage: python3 engine/tools/sync_engine.py <videoNN|series root> [...] [--apply] [--include-delivered]
Each episode keeps its own copy of engine.js, engine.css, presets/*.css and scenes/*.html (new_project.py copies them).
This copies every changed or missing template file in; the replaced copies go to <videoNN>/_to_delete/engine_<old version>/
(the Mac folder cannot delete). Built scenes live in the episode's index.html and are never touched.
Delivered episodes are skipped unless --include-delivered (they are finished; a new engine could change a re-render).
Without --apply it only lists what it would change. `studio.py next` warns when an episode's engine is out of date."""
import argparse, hashlib, json, pathlib, re, shutil, sys
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
T = HERE.parent / 'template'


def files():
    out = [('engine.js', T / 'engine.js'), ('engine.css', T / 'engine.css')]
    out += [(f'presets/{f.name}', f) for f in sorted((T / 'presets').glob('*.css'))]
    out += [(f'scenes/{f.name}', f) for f in sorted((T / 'scenes').glob('*.html'))]
    return out


def h(f): return hashlib.md5(f.read_bytes()).hexdigest() if f.exists() else None


def stale(P):
    """list of (relative path, 'changed'|'missing') where P/engine differs from the template."""
    return [(r, 'missing' if not (P / 'engine' / r).exists() else 'changed') for r, src in files() if h(P / 'engine' / r) != h(src)]


def version():
    try: return json.loads((HERE.parent / 'studio' / 'rules.json').read_text(encoding='utf-8')).get('version', '?')
    except Exception: return '?'


def stage(P):
    try: return json.loads((P / 'state.json').read_text(encoding='utf-8')).get('stage', '')
    except Exception: return ''


def episodes(arg):
    p = pathlib.Path(arg).resolve()
    if (p / 'engine').is_dir() and (p / 'project.json').exists(): return [p]
    return sorted(d for d in p.iterdir() if d.is_dir() and re.fullmatch(r'video\d+', d.name) and (d / 'engine').is_dir())


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('paths', nargs='+'); ap.add_argument('--apply', action='store_true')
    ap.add_argument('--include-delivered', action='store_true'); a = ap.parse_args()
    v = version(); n_up = 0
    for arg in a.paths:
        for P in episodes(arg):
            s = stale(P); st = stage(P)
            if not s: print(f'{P.name}: up to date ({v})'); continue
            if st == 'delivered' and not a.include_delivered: print(f'{P.name}: delivered — skipped ({len(s)} file(s) differ; --include-delivered to update)'); continue
            print(f'{P.name} [{st or "?"}]: {len(s)} file(s) ' + ('updated' if a.apply else 'to update') + ': ' + ', '.join(f'{r} ({k})' for r, k in s))
            if a.apply:
                bk = P / '_to_delete' / f'engine_before_{v}'
                for r, k in s:
                    dst = P / 'engine' / r
                    if dst.exists(): (bk / r).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(dst, bk / r)
                    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(dict(files())[r], dst)
                n_up += 1
    if not a.apply: print('dry run — re-run with --apply')
    else: print(f'{n_up} episode(s) updated to the plugin engine {v}')
