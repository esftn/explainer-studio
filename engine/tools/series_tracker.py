#!/usr/bin/env python3
"""series_tracker.py (v0.6) — the episode tracker is GENERATED from the folders, never typed by hand.

  python3 _series/tools/series_tracker.py [--root "VIDEO GEN"] [--write] [--json] [--no-ssim]

Reads every videoNN folder (state.json, out/ finals, ffprobe, captions, publish.txt lint, state_check, lock, _to_delete size)
and prints a Markdown tracker. --write saves it as <root>/_series/episode-tracker.md (a plain overwrite: two chats running
it at the same time produce the same file, so nothing is ever lost). Hand-written notes and open issues live in the
APPEND-ONLY file <root>/_series/issues.md; its text is appended below the generated table. Add to issues.md with
    python3 _series/tools/series_tracker.py --note "ep 22 Build: …"        (adds a dated line, never rewrites)
    python3 _series/tools/series_tracker.py --issue "ep 19: TIN figure wrong"   (adds an OPEN issue line)
    python3 _series/tools/series_tracker.py --close 7                         (adds 'CLOSED #7' line — history stays)
Needs only python3 (+ ffprobe/ffmpeg for durations and cover check)."""
import argparse, datetime as dt, json, pathlib, re, shutil, subprocess, sys
sys.dont_write_bytecode = True      # the Mac folder can't delete: no __pycache__ litter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import state_check, publint                                      # noqa: E402
try:
    import guard                                                  # noqa: E402
except Exception:
    guard = None

FIN = {'reel': '*_reel_9x16.mp4', 'feed': '*_feed_4x5.mp4', 'cover_reel': 'cover_reel_9x16.png', 'cover_feed': 'cover_feed_4x5.png',
       'srt_bn': 'captions.bn_IN.srt', 'srt_en': 'captions.en_US.srt', 'publish': 'publish.txt'}


def project_dir(d):
    """videoNN itself, or (episodes 1–2) its single nested project folder."""
    if (d / 'out').is_dir() or (d / 'index.html').exists(): return d
    subs = [s for s in d.iterdir() if s.is_dir() and ((s / 'out').is_dir() or (s / 'index.html').exists())] if d.is_dir() else []
    return subs[0] if len(subs) == 1 else d


def probe(f):
    if not shutil.which('ffprobe'): return None
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,duration:format=duration', '-of', 'json', str(f)],
                       capture_output=True, text=True)
    try: j = json.loads(r.stdout)
    except Exception: return None
    v = next((s for s in j.get('streams', []) if s['codec_type'] == 'video'), {}); a = next((s for s in j.get('streams', []) if s['codec_type'] == 'audio'), {})
    num = lambda x: float(x) if x not in (None, 'N/A') else None
    return {'w': v.get('width'), 'h': v.get('height'), 'v': num(v.get('duration')) or num(j.get('format', {}).get('duration')), 'a': num(a.get('duration'))}


def srt_cues(f):
    t = pathlib.Path(f).read_text(encoding='utf-8-sig', errors='replace')
    out = []
    for m in re.finditer(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', t):
        g = [int(x) for x in m.groups()]
        out.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000))
    return out


def cover_ssim(reel, cover):
    """SSIM between frame 1 of the reel and the 9:16 cover (≥0.95 = the cover is baked in as the first frame)."""
    if not shutil.which('ffmpeg'): return None
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f0 = pathlib.Path(td) / 'f0.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(reel), '-frames:v', '1', str(f0)], capture_output=True)
        if not f0.exists(): return None
        r = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(f0), '-i', str(cover), '-filter_complex',
                            '[0:v]scale=540:960,format=rgb24[a];[1:v]scale=540:960,format=rgb24[b];[a][b]ssim', '-f', 'null', '-'],
                           capture_output=True, text=True)
    m = re.search(r'All:([0-9.]+)', r.stderr)
    return float(m.group(1)) if m else None


def du(p):
    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.is_dir() else 0


def episode(d, ssim=True):
    P = project_dir(d); out = P / 'out'; e = {'ep': d.name[5:], 'dir': d.name + ('/' + P.name if P != d else ''), 'problems': [], 'notes': []}
    st = {}
    try: st = json.loads((P / 'state.json').read_text(encoding='utf-8'))
    except Exception: pass
    e['stage'] = st.get('stage') or ('delivered?' if out.is_dir() else ('planned' if any(P.glob('vo/raw/*')) else 'empty'))
    e['title'] = (st.get('title') or '')
    present = {k: (list(out.glob(p)) if out.is_dir() else []) for k, p in FIN.items()}
    e['finals'] = sum(1 for v in present.values() if v)
    e['finals_missing'] = [k for k, v in present.items() if not v]
    if not e['title'] and present['publish']:
        s, _ = publint.sections(present['publish'][0].read_text(encoding='utf-8'))
        e['title'] = next((l.strip() for l in s.get('TITLE', '').splitlines() if l.strip() and not l.lower().startswith('alt')), '')
    e['dur'] = None; e['av'] = None; e['cover'] = None
    if present['reel']:
        pr = probe(present['reel'][0])
        if pr:
            e['dur'] = pr['v']; e['av'] = (abs(pr['v'] - pr['a']) if pr['v'] and pr['a'] else None); e['res'] = f"{pr['w']}x{pr['h']}"
            if e['av'] is not None and e['av'] > 0.15: e['problems'].append(f"reel audio/video lengths differ by {e['av']:.2f} s")
            if pr['w'] != 1080 or pr['h'] != 1920: e['problems'].append(f"reel is {pr['w']}x{pr['h']}, not 1080x1920")
        if ssim and present['cover_reel']:
            s = cover_ssim(present['reel'][0], present['cover_reel'][0]); e['cover'] = s
            if s is not None and s < 0.95: e['problems'].append(f'first frame of the reel is not the cover (SSIM {s:.2f})')
    if present['feed']:
        pf = probe(present['feed'][0])
        if pf and (pf['w'], pf['h']) != (1080, 1350): e['problems'].append(f"feed is {pf['w']}x{pf['h']}, not 1080x1350")
    e['cues'] = None
    if present['srt_bn'] and present['srt_en']:
        a, b = srt_cues(present['srt_bn'][0]), srt_cues(present['srt_en'][0]); e['cues'] = (len(a), len(b))
        if len(a) != len(b): e['problems'].append(f'captions: {len(a)} bn cues vs {len(b)} en cues')
        end = e['dur'] or 1e9
        if a and a[-1][1] > end + 0.2: e['problems'].append('captions: last cue ends after the video')
        if any(a[i][1] > a[i + 1][0] + 0.001 for i in range(len(a) - 1)): e['notes'].append('bn cues overlap')
    elif out.is_dir() and (present['reel'] or present['feed']): e['problems'].append('captions pair incomplete')
    e['pub'] = None
    if present['publish']:
        f, w = publint.lint(present['publish'][0], P / 'facts.json' if (P / 'facts.json').exists() else None)
        e['pub'] = (len(f), len(w))
        for x in f[:3]: e['problems'].append('publish.txt: ' + x)
    # extra files in out/ (out = finals only)
    if out.is_dir():
        extra = [f.name for f in out.iterdir() if not f.name.startswith('.') and not any(f.match(p) for p in FIN.values())]
        if extra: e['problems'].append('out/ holds non-final file(s): ' + ', '.join(extra[:3]))
    if st:
        sc = state_check.check(P, fix=False)
        for m in sc: e['problems'].append('state.json: ' + m)
    elif e['stage'] not in ('empty', 'planned'): e['notes'].append('no state.json (pre-pipeline)')
    L = guard.read_lock(P) if guard else None
    e['lock'] = (L['who'] + ' · ' + L.get('stage', '') + ' · since ' + L['since']) if L and not L.get('released') and guard.live(L, 12) else ''
    e['td'] = du(P / '_to_delete') / 1e6
    return e


def render(eps, issues_text):
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    L = ['# Episode tracker — বাংলা অর্থনীতি রিলস',
         f'**GENERATED {now} by `_series/tools/series_tracker.py` from the videoNN folders — do not edit this file.** '
         'Notes and open issues are kept in `_series/issues.md` (append-only; its text is repeated at the bottom). '
         'Regenerate: `python3 _series/tools/series_tracker.py --write`.', '',
         '**Rules (short):** one chat per stage per episode (Plan → Build NN → Finish NN) · claim the episode first '
         '(`guard.py claim`) and release it at the end · never push over a changed Mac copy (`pack --guard`) · '
         'close-out = `finish.py` / `state_check --fix` · no stage the creator did not ask for · reports brief.', '']
    deliv = [e for e in eps if e['stage'] == 'delivered' or (e['stage'] == 'delivered?' and e['finals'] == 7)]
    L.append(f"**{len(deliv)} delivered · {sum(1 for e in eps if e['stage'] not in ('delivered', 'delivered?', 'empty', 'planned'))} in progress · "
             f"{sum(1 for e in eps if e['stage'] in ('empty', 'planned'))} empty/planned · {sum(1 for e in eps if e['problems'])} with file problems**")
    L += ['', '| Ep | Title | Stage | Lock | Reel | Finals | Captions | Cover | publish | Problems |', '|---|---|---|---|---|---|---|---|---|---|']
    for e in eps:
        dur = f"{e['dur']:.1f} s" + (' ⚠>60' if e['dur'] and e['dur'] > 60.05 else '') if e['dur'] else '–'
        cues = f"{e['cues'][0]}/{e['cues'][1]}" if e['cues'] else '–'
        cov = ('baked' if e['cover'] and e['cover'] >= 0.95 else f"NOT baked ({e['cover']:.2f})" if e['cover'] else '–')
        pub = 'ok' if e['pub'] == (0, 0) else ('–' if e['pub'] is None else f"{e['pub'][0]} fail / {e['pub'][1]} warn")
        pr = '; '.join(e['problems'] + e['notes']) or ''
        L.append(f"| {e['ep']} | {e['title'][:40]} | {e['stage']} | {e['lock'] or ''} | {dur} | {e['finals']}/7 | {cues} | {cov} | {pub} | {pr} |")
    td = [(e['dir'], e['td']) for e in eps if e['td'] > 1]
    if td: L += ['', '**_to_delete/ not empty (creator can delete):** ' + ', '.join(f'{n} {m:.0f} MB' for n, m in td)]
    L += ['', '## Issues and notes (from `_series/issues.md`)', '', issues_text.strip() or '(none yet)', '']
    return '\n'.join(L)


def find_root(arg):
    if arg: return pathlib.Path(arg).resolve()
    for start in (HERE, pathlib.Path.cwd()):
        for c in [start, *start.parents]:
            if any(p.is_dir() for p in c.glob('video[0-9][0-9]')): return c
    return pathlib.Path.cwd()


def append(f, line):
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, 'a', encoding='utf-8') as fh:
        if f.exists() and f.stat().st_size and not f.read_text(encoding='utf-8').endswith('\n'): fh.write('\n')
        fh.write(line + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root'); ap.add_argument('--write', action='store_true'); ap.add_argument('--json', action='store_true')
    ap.add_argument('--no-ssim', action='store_true'); ap.add_argument('--note'); ap.add_argument('--issue'); ap.add_argument('--close')
    a = ap.parse_args(); R = find_root(a.root); I = R / '_series' / 'issues.md'
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')
    if a.note: append(I, f'- {stamp} NOTE: {a.note}'); print('noted in', I); return
    if a.issue:
        ids = [int(x) for x in re.findall(r'(?m)^- #(\d+) OPEN', I.read_text(encoding='utf-8'))] if I.exists() else []
        n = max(ids + [0]) + 1; append(I, f'- #{n} OPEN {stamp}: {a.issue}'); print(f'issue #{n} added'); return
    if a.close: append(I, f'- {stamp} CLOSED #{a.close.lstrip("#")}'); print('close line added'); return
    eps = [episode(d, not a.no_ssim) for d in sorted(R.glob('video[0-9][0-9]')) if d.is_dir()]
    issues = I.read_text(encoding='utf-8') if I.exists() else ''
    if a.json: print(json.dumps(eps, ensure_ascii=False, indent=1, default=str)); return
    md = render(eps, issues)
    if a.write:
        (R / '_series').mkdir(exist_ok=True); (R / '_series' / 'episode-tracker.md').write_text(md, encoding='utf-8'); print(f'written: {R / "_series" / "episode-tracker.md"} ({len(eps)} episodes)')
    else: print(md)


if __name__ == '__main__':
    main()
