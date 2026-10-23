#!/usr/bin/env python3
"""studio.py — the one front door for the series. Plain Python 3 (no packages): runs in the cloud workspace AND on the Mac.

  studio.py next  [videoNN]                  what to do now: the step card for this episode's stage + the creator's rules.
                                             START EVERY CHAT WITH THIS (no argument = series status).
  studio.py new   videoNN --title T --ep NN  create the project AND assign its palette + music (cloud workspace only)
  studio.py look  videoNN [--set ID] [--family F]   assign / show the Vox-style palette  -> docs/look.json + docs/look.md
  studio.py music videoNN [--set ID]         assign / show the music preset              -> audio_config.json
  studio.py check videoNN --stage build|final   objective rule checks; prints STUDIO PASS or the FAIL lines
  studio.py status [--root DIR] [--write]    every episode: stage, who is waiting, length, look, music -> _series/STATUS.md
  studio.py close videoNN STAGE [--note T]   LAST command of every chat: state + status document (+ tracker when delivered)

Rotation is by episode number, so no history file is needed: music = preset[(ep-1) % 5]; palette = bank[(ep-1) % 14], skipping
a colour family used by one of the three previous episodes (read from sibling videoNN/docs/look.json when they are visible)."""
import argparse, colorsys, copy, datetime as dt, json, pathlib, re, shutil, subprocess, sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
STAGES = ['plan', 'brief-approved', 'script-approved', 'folders-ready', 'vo-received', 'style-approved', 'built', 'preview-approved', 'delivered']
FINALS = ['*_reel_9x16.mp4', '*_feed_4x5.mp4', 'cover_reel_9x16.png', 'cover_feed_4x5.png', 'captions.bn_IN.srt', 'captions.en_US.srt', 'publish.txt']


# ---------------------------------------------------------------- helpers
def data(name):
    for d in (HERE, HERE / 'studio', HERE.parent / 'studio', pathlib.Path.cwd() / '_series' / 'tools', pathlib.Path.cwd() / '.studio'):
        f = d / name
        if f.exists(): return json.loads(f.read_text(encoding='utf-8'))
    sys.exit(f'studio.py: cannot find {name} (looked next to the tool and in ../studio). Copy it into _series/tools/.')


def find_tool(name):
    for d in (HERE, HERE.parent / 'tools', pathlib.Path.cwd() / '_series' / 'tools'):
        if (d / name).exists(): return d / name
    return None


def proj(arg):
    p = pathlib.Path(arg).resolve()
    if not p.is_dir(): sys.exit(f'studio.py: {p} is not a folder')
    if not (p / 'state.json').exists() and not (p / 'index.html').exists():       # episodes 1-2 keep the project one level down
        subs = [s for s in p.iterdir() if s.is_dir() and ((s / 'state.json').exists() or (s / 'index.html').exists())]
        if len(subs) == 1: return subs[0]
    return p


def jload(f, default=None):
    f = pathlib.Path(f)
    try: return json.loads(f.read_text(encoding='utf-8'))
    except Exception: return default


def jsave(f, obj): pathlib.Path(f).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def ep_of(p):
    st = jload(p / 'state.json', {}) or {}
    if st.get('ep'): return int(re.sub(r'\D', '', str(st['ep'])) or 0)
    m = re.search(r'(\d+)\s*$', p.name) or re.search(r'(\d+)', p.name)
    return int(m.group(1)) if m else 1


def hexes(s): return {h.lower() for h in re.findall(r'#[0-9a-fA-F]{6}\b', s)}


def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def dist(a, b): return sum((x - y) ** 2 for x, y in zip(rgb(a), rgb(b))) ** 0.5


def is_neutral(h):
    r, g, b = [c / 255 for c in rgb(h)]
    return colorsys.rgb_to_hsv(r, g, b)[1] < 0.12


def sibling_families(p, ep):
    """colour families used by the three previous episodes: look.json where it exists, else the seeded history."""
    hist = data('rules.json').get('history_families', {})
    fam = {}
    for n in range(max(1, ep - 3), ep):
        d = p.parent / f'video{n:02d}'
        lk = jload(proj(str(d)) / 'docs' / 'look.json') if d.is_dir() else None
        fam[n] = (lk or {}).get('family') or hist.get(str(n))
    return {f for f in fam.values() if f}


# ---------------------------------------------------------------- look + music
def cmd_look(a):
    p = proj(a.folder); ep = ep_of(p); bank = data('palettes.json'); pals = bank['palettes']
    old = jload(p / 'docs' / 'look.json')
    if old and not a.set and not a.family and not a.again:
        pal = next((x for x in pals if x['id'] == old['id']), old)          # already assigned: show, don't change
    else:
        if a.set:
            pal = next((x for x in pals if x['id'] == a.set), None) or sys.exit(f'unknown palette {a.set}; ids: {[x["id"] for x in pals]}')
        else:
            avoid = sibling_families(p, ep); n = len(pals); order = [pals[(ep - 1 + k) % n] for k in range(n)]
            if a.family: order = [x for x in order if x['family'] == a.family] + order
            pal = next((x for x in order if x['family'] not in avoid), order[0])
    look = {'id': pal['id'], 'label': pal['label'], 'family': pal['family'], 'motif': pal['motif'], 'colors': pal['colors'], 'themes': pal['themes'],
            'music': (old or {}).get('music')}
    (p / 'docs').mkdir(exist_ok=True); jsave(p / 'docs' / 'look.json', look)
    md = [f"# Look — {pal['label']}  (episode {ep:02d})", '',
          'Use ONLY these colours (Vox / Johnny Harris style). `studio.py check` flags anything else.', '',
          '| role | hex |', '|---|---|'] + [f'| {k} | {v} |' for k, v in pal['colors'].items()] + ['', '## Ready-made scene themes (text contrast >= 4.5:1)', '',
          '| bg | text | highlight | pop |', '|---|---|---|---|'] + [f"| {t['bg']} | {t['text']} | {t['highlight']} | {t['pop']} |" for t in pal['themes']] + \
         ['', f"## Motif for this episode\n{pal['motif']}", '', '## Rules'] + [f'- {r}' for r in bank['rules']] + \
         ['- Own style elements and own top/bottom bands: do not reuse an earlier episode\'s objects (series brief cover log).']
    (p / 'docs' / 'look.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    pj = jload(p / 'project.json', {}); pj['look'] = pal['id']; jsave(p / 'project.json', pj) if (p / 'project.json').exists() else None
    print(f"look: {pal['label']} ({pal['id']}, family {pal['family']})  -> docs/look.md")
    print('themes: ' + ' | '.join(f"{t['bg']} on {t['text']} +{t['highlight']}" for t in pal['themes']))
    print('motif: ' + pal['motif'])


def cmd_music(a):
    p = proj(a.folder); ep = ep_of(p); bank = data('music_bank.json'); pre = bank['presets']
    lk = jload(p / 'docs' / 'look.json', {}) or {}; cur = (jload(p / 'audio_config.json', {}) or {}).get('music_id')
    if cur and not a.set and not a.again:
        pr = next((x for x in pre if x['id'] == cur), pre[(ep - 1) % len(pre)])
    elif a.set:
        pr = next((x for x in pre if x['id'] == a.set), None) or sys.exit(f'unknown music {a.set}; ids: {[x["id"] for x in pre]}')
    else:
        pr = pre[(ep - 1) % len(pre)]
    base = jload(find_tool('audio_config.example.json') or '', {}) or {}
    cfg = copy.deepcopy(base)
    for k, v in bank['defaults'].items(): cfg[k] = {**cfg.get(k, {}), **v} if isinstance(v, dict) else v
    for k, v in pr.items():
        if k not in ('id', 'label'): cfg[k] = v
    cfg['music_id'] = pr['id']
    jsave(p / 'audio_config.json', cfg)
    lk['music'] = pr['id']
    if (p / 'docs').is_dir(): jsave(p / 'docs' / 'look.json', {**lk, 'id': lk.get('id')}) if lk.get('id') else None
    pj = jload(p / 'project.json', {}); pj['music'] = pr['id']
    if (p / 'project.json').exists(): jsave(p / 'project.json', pj)
    print(f"music: {pr['label']} ({pr['id']}) -> audio_config.json; sound effects are automatic (auto_sfx)")


def cmd_new(a):
    np_ = find_tool('new_project.py') or sys.exit('studio.py new needs the plugin engine (new_project.py) - run it in the cloud workspace.')
    ep = int(re.sub(r'\D', '', a.ep)); bank = data('music_bank.json'); pr = bank['presets'][(ep - 1) % len(bank['presets'])]
    r = subprocess.run([sys.executable, str(np_), a.folder, '--title', a.title, '--ep', f'{ep:02d}', '--preset', 'vox-money', '--palette', pr['palette']] + (['--slug', a.slug] if a.slug else []))
    if r.returncode: sys.exit(r.returncode)
    p = pathlib.Path(a.folder).resolve()
    shutil.copy(HERE / 'studio.py', p / '.studio' / 'studio.py')
    for f in ('rules.json',):
        src = HERE.parent / 'studio' / f
        if src.exists(): shutil.copy(src, p / '.studio' / f)
    ns = argparse.Namespace(folder=str(p), set=None, family=a.family, again=True); cmd_look(ns)
    ns = argparse.Namespace(folder=str(p), set=None, again=True); cmd_music(ns)
    print(f'project ready: {p}\nnext: python3 engine/tools/studio.py next {p.name}')


# ---------------------------------------------------------------- check
def cmd_check(a):
    p = proj(a.folder); R = data('rules.json'); K = R['checks']; fails, warns = [], []
    pj = jload(p / 'project.json', {}) or {}
    if pj.get('preset') != K['preset']: fails.append(f"preset is '{pj.get('preset')}', must be {K['preset']} (series typeface Tiro Bangla)")
    lk = jload(p / 'docs' / 'look.json')
    if not lk: fails.append('no docs/look.json: run studio.py look')
    ac = jload(p / 'audio_config.json', {}) or {}
    if not ac.get('music_id'): fails.append('audio_config.json has no music_id: run studio.py music')
    elif lk and lk.get('music') and lk['music'] != ac['music_id']: fails.append(f"music was changed by hand ({ac['music_id']} instead of {lk['music']})")
    html = (p / 'index.html').read_text(encoding='utf-8', errors='replace') if (p / 'index.html').exists() else ''
    if a.stage == 'build':
        if not html: fails.append('no index.html')
        scenes = re.findall(r'<section[^>]*class="[^"]*\bscene\b[^"]*"[^>]*>', html)
        moods = [re.search(r'data-mood="(\w+)"', s) for s in scenes]; moods = [m.group(1) if m else None for m in moods]
        if scenes and moods[0] != 'intro': fails.append('first scene needs data-mood="intro"')
        if scenes and moods[-1] != 'end': fails.append('last scene needs data-mood="end" (closing chord)')
        if len(scenes) > 2 and len({m for m in moods if m}) < 3: warns.append('few data-mood changes: music will sound flat (use build/drive/somber/answer)')
        if re.search(r'class="[^"]*\btag\b[^"]*"', html): warns.append('a chapter chip/tag (class "tag") is in index.html - the creator does not want scene labels on screen')
        if lk:
            allowed = {c.lower() for c in lk['colors'].values()} | {t[k].lower() for t in lk['themes'] for k in ('bg', 'text', 'highlight', 'pop')} | set(K['allowed_neutrals'])
            off = sorted(h for h in hexes(html) if h not in allowed and not is_neutral(h) and min(dist(h, c) for c in allowed) > 34)
            if len(off) > 20: fails.append(f'{len(off)} colours are not in the palette {lk["id"]} (e.g. {", ".join(off[:5])})')
            elif len(off) > K['max_offpalette_colours']: warns.append(f'{len(off)} off-palette colours (e.g. {", ".join(off[:5])}) - use the themes in docs/look.md')
        ar = p / 'out' / 'audio_report.txt'
        if not ar.exists(): fails.append('run audio.py first (out/audio_report.txt missing)')
        else:
            rep = ar.read_text(encoding='utf-8'); m = re.search(r'sfx used: (.*)', rep)
            n = sum(int(x) for x in re.findall(r'×(\d+)', m.group(1))) if m else 0
            ns = max(1, len(scenes)); per = n / ns
            if per < K['min_sfx_cues_per_scene']: fails.append(f'sound effects missing or too few ({n} cues for {ns} scenes). Check project.json autoSfx is not false and no data-sfx="none" everywhere')
            elif per > 6: warns.append(f'{n} sound-effect cues ({per:.1f} per scene): may be distracting')
            if 'FAIL' in rep: fails.append('audio_report.txt contains a FAIL line')
        if ac.get('end_fade_s', 1) > 1.2 or ac.get('end_chord_s', 4) < 3: fails.append('ending audio changed: the closing chord must ring and the last line must not fade')
        if float(pj.get('end_hold', 3.0)) < K['min_end_hold_s'] - 1e-6: fails.append(f"end_hold {pj.get('end_hold')} s is below {K['min_end_hold_s']} s")
    if a.stage == 'final':
        out = p / 'out'
        for pat in FINALS:
            if not any(out.glob(pat)): fails.append(f'out/ is missing {pat}')
        extra = [f.name for f in out.iterdir() if f.is_file() and not any(f.match(pt) for pt in FINALS)] if out.is_dir() else []
        if extra: fails.append(f'out/ must hold finals only; move to drafts/: {", ".join(sorted(extra)[:6])}')
        pt = out / 'publish.txt'
        if pt.exists() and re.search(r'\[[^\]]{2,60}\]|যোগ করুন|TODO|TBD', pt.read_text(encoding='utf-8', errors='replace')): fails.append('publish.txt still has a placeholder')
    for w in warns: print('WARN ' + w)
    for f in fails: print('FAIL ' + f)
    print('STUDIO PASS' if not fails else f'STUDIO FAIL ({len(fails)})')
    sys.exit(1 if fails else 0)


# ---------------------------------------------------------------- status
def find_root(arg=None):
    if arg: return pathlib.Path(arg).resolve()
    for start in (HERE, pathlib.Path.cwd()):
        for c in [start, *start.parents]:
            if any(x.is_dir() for x in c.glob('video[0-9][0-9]')): return c
    return pathlib.Path.cwd()


def reel_len(p):
    for f in sorted((p / 'out').glob('*_reel_9x16.mp4')) if (p / 'out').is_dir() else []:
        if shutil.which('ffprobe'):
            r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(f)], capture_output=True, text=True)
            try: return float(r.stdout.strip())
            except Exception: pass
    return None


def episodes(root):
    rows = []
    for d in sorted(root.glob('video[0-9][0-9]')):
        p = proj(str(d)); st = jload(p / 'state.json', {}) or {}; lk = jload(p / 'docs' / 'look.json', {}) or {}
        stage = st.get('stage') or ('delivered' if (p / 'out').is_dir() and all(any((p / 'out').glob(x)) for x in FINALS) else 'plan')
        if stage != 'delivered' and (p / 'out').is_dir() and all(any((p / 'out').glob(x)) for x in FINALS): stage = 'delivered?'
        rows.append({'n': ep_of(d), 'dir': d.name, 'title': st.get('title') or '', 'stage': stage, 'open': st.get('open') or [],
                     'look': lk.get('id') or (jload(p / 'project.json', {}) or {}).get('look') or '-', 'music': lk.get('music') or (jload(p / 'audio_config.json', {}) or {}).get('music_id') or '-',
                     'len': st.get('reel_s') or reel_len(p)})
    return rows


def render_status(root):
    R = data('rules.json'); rows = episodes(root); now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    done = [r for r in rows if r['stage'].startswith('delivered')]; todo = [r for r in rows if not r['stage'].startswith('delivered')]
    cut = lambda s, n: (s[:n] + '…') if len(s) > n else s
    L = [f'# Series status — {now}', '', f'**{len(done)} delivered · {len(todo)} in progress**', '']
    you = [r for r in todo if R['stage_waiting_on'].get(r['stage'], '').startswith('YOU')]
    if you: L += ['## Waiting on you'] + [f"- ep {r['n']:02d} ({cut(r['title'], 40)}): {R['stage_waiting_on'][r['stage']].replace('NN', '%02d' % r['n'])}" for r in you] + ['']
    if todo:
        L += ['## In progress', '', '| Ep | Title | Stage | Waiting on | Look | Music |', '|---|---|---|---|---|---|']
        L += [f"| {r['n']:02d} | {cut(r['title'], 34)} | {r['stage']} | {R['stage_waiting_on'].get(r['stage'], '?').replace('NN', '%02d' % r['n'])} | {r['look']} | {r['music']} |" for r in todo] + ['']
    L += ['## Delivered', '', '| Ep | Title | Length | Look | Music |', '|---|---|---|---|---|']
    L += [f"| {r['n']:02d} | {cut(r['title'], 40)} | {('%.1f s' % r['len']) if r['len'] else '-'} | {r['look']} | {r['music']} |" for r in done]
    flags = [(r['n'], o) for r in rows for o in r['open']]
    if flags: L += ['', '## Open flags'] + [f'- ep {n:02d}: {cut(o, 140)}' for n, o in flags]
    return '\n'.join(L) + '\n'


def cmd_status(a):
    root = find_root(a.root); txt = render_status(root)
    if a.write:
        (root / '_series').mkdir(exist_ok=True); (root / '_series' / 'STATUS.md').write_text(txt, encoding='utf-8'); print(f'written {root / "_series" / "STATUS.md"}')
    print(txt)


# ---------------------------------------------------------------- next / close
def cmd_next(a):
    if not a.folder: return cmd_status(argparse.Namespace(root=None, write=False))
    p = proj(a.folder); R = data('rules.json'); st = jload(p / 'state.json', {}) or {}; stage = st.get('stage', 'plan'); card = R['stage_card'].get(stage)
    nn = f'{ep_of(p):02d}'; name = p.name if p.name.startswith('video') else f'video{nn}'
    lk = jload(p / 'docs' / 'look.json', {}) or {}
    print(f"== {name} · ep {nn} · {st.get('title') or '(no title yet)'} · stage: {stage}"); print(f"   waiting on: {R['stage_waiting_on'].get(stage, '?').replace('NN', nn)}")
    if lk: print(f"   look: {lk.get('label')} ({lk.get('id')}) · music: {lk.get('music')}")
    if not card: print('   Done. Nothing to do; log the cover in the series brief only if the creator asks.'); return
    print(); [print(l.replace('videoNN', name).replace('NN', nn)) for l in R['cards'][card]]
    print('\nRULES (always)'); [print(f'- {l}') for l in R['always']]
    keys = {'plan': ['script', 'vo_and_images', 'ready'], 'build': ['missing', 'preview'], 'finish': ['cover', 'delivered']}[card]
    print('\nREPORT TEMPLATES (use exactly; no extra text)'); [print(f'- {k}: {R["reports"][k]}') for k in keys]


def cmd_close(a):
    p = proj(a.folder)
    if a.stage not in STAGES: sys.exit(f'stage must be one of {STAGES}')
    st_py = find_tool('state.py'); now = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    if st_py:
        subprocess.run([sys.executable, str(st_py), str(p), 'stage', a.stage], check=True, capture_output=True)
        if a.note and a.stage != 'delivered': subprocess.run([sys.executable, str(st_py), str(p), 'note', a.note], check=True, capture_output=True)
    st = jload(p / 'state.json', {}) or {}
    if not st_py:
        st.update({'stage': a.stage}); st.setdefault('log', []).append(f'{now} stage {a.stage}')
        if a.note and a.stage != 'delivered': st.setdefault('open', []).append(a.note)
    if a.stage == 'delivered':
        st['open'] = []; ln = reel_len(p)
        if ln: st['reel_s'] = round(ln, 2)
    jsave(p / 'state.json', st)
    print(f'{p.name}: stage -> {a.stage}')
    root = p.parent
    if any(x.is_dir() for x in root.glob('video[0-9][0-9]')) and (root / '_series').is_dir():
        (root / '_series' / 'STATUS.md').write_text(render_status(root), encoding='utf-8'); print('STATUS.md updated')
        if a.stage == 'delivered':
            tr = find_tool('series_tracker.py')
            if tr:
                subprocess.run([sys.executable, str(tr), '--root', str(root), '--write'], capture_output=True)
                if a.note: subprocess.run([sys.executable, str(tr), '--root', str(root), '--note', f'ep {ep_of(p):02d} delivered: {a.note}'], capture_output=True)
                print('episode-tracker.md regenerated')
    else:
        print('(not on the Mac: STATUS.md is written the next time studio.py close/status runs from VIDEO GEN)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('next'); s.add_argument('folder', nargs='?'); s.set_defaults(f=cmd_next)
    s = sp.add_parser('new'); s.add_argument('folder'); s.add_argument('--title', required=True); s.add_argument('--ep', required=True); s.add_argument('--slug'); s.add_argument('--family'); s.set_defaults(f=cmd_new)
    s = sp.add_parser('look'); s.add_argument('folder'); s.add_argument('--set'); s.add_argument('--family'); s.add_argument('--again', action='store_true'); s.set_defaults(f=cmd_look)
    s = sp.add_parser('music'); s.add_argument('folder'); s.add_argument('--set'); s.add_argument('--again', action='store_true'); s.set_defaults(f=cmd_music)
    s = sp.add_parser('check'); s.add_argument('folder'); s.add_argument('--stage', choices=['build', 'final'], required=True); s.set_defaults(f=cmd_check)
    s = sp.add_parser('status'); s.add_argument('--root'); s.add_argument('--write', action='store_true'); s.set_defaults(f=cmd_status)
    s = sp.add_parser('close'); s.add_argument('folder'); s.add_argument('stage'); s.add_argument('--note'); s.set_defaults(f=cmd_close)
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
