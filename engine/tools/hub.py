#!/usr/bin/env python3
"""hub.py (v0.11) — builds the VIDEO GEN/00_HUB overview from the episode folders. Read-only on every videoNN folder.

  python3 engine/tools/hub.py             (run from the series folder, e.g. VIDEO GEN; or set HUB_ROOT)
  bash _series/es.sh hub                  (same, through es.sh)

Writes (all generated — never edit them by hand, edit the episode files instead):
  00_HUB/HUB.html          one offline page: status, copy-paste text with copy buttons, commands, covers
  00_HUB/STATUS.md         every video: stage, next step, files, uploaded
  00_HUB/COPY_SHORTS.md    title / description / hashtags / pinned comment for every Short (final + drafts)
  00_HUB/COPY_LONG.md      the same for long videos (project.json "format": "long")
  00_HUB/COMMANDS.md       render + cover commands per video, with folder paths
User-owned (created once, never overwritten — the hub only reads them):
  00_HUB/published.txt     uploads + performance, one line per episode, e.g. "46 yt fb up=2026-11-24 views=1200 stayed=62% avd=0:35"
  00_HUB/IDEAS.md          topic backlog: "- [ ] idea — note", "- [x]" when it became an episode

Why generated: several build chats run at once. Each chat only writes its own videoNN files; this script rebuilds the
hub from them in < 1 s, writes a file only when its content changed, and swaps it in atomically — no merge conflicts,
no hand-edited tracker getting overwritten. es.sh runs it after every state-changing tool."""
import ast, datetime as dt, html, json, os, pathlib, re, sys
sys.dont_write_bytecode = True

_HERE = pathlib.Path(__file__).resolve()
# the series root (the folder holding _series/ and the videoNN folders): HUB_ROOT, else this file's _series/tools home,
# else the current folder (es.sh runs every tool from the series root, so the copy inside the engine kit lands here)
ROOT = pathlib.Path(os.environ['HUB_ROOT']).resolve() if os.environ.get('HUB_ROOT') else (
    _HERE.parents[2] if _HERE.parent.parent.name == '_series' else pathlib.Path.cwd())
HUB = ROOT / '00_HUB'
MAC_ROOT = os.environ.get('HUB_MAC_ROOT') or (
    '/Users/mizan/Documents/VIDEO GEN' if ('/mnt/' in str(ROOT) or str(ROOT).startswith('/sessions')) else str(ROOT))
QUIET = '--quiet' in sys.argv
STAGES = ['plan', 'brief-approved', 'script-approved', 'folders-ready', 'vo-received', 'style-approved', 'built',
          'preview-approved', 'delivered']
NEXT = {
    'plan': 'Plan chat: research + script',
    'brief-approved': 'Plan chat: write the script',
    'script-approved': 'Plan chat: VO text + image list + folders',
    'folders-ready': 'YOU: record the VO + add photos, then a new chat "Build episode {n}"',
    'vo-received': 'Build chat: style + scenes + preview',
    'style-approved': 'Build chat: scenes + preview',
    'built': 'YOU: watch the preview, then say "go ahead" in the Build chat',
    'preview-approved': 'Same Build chat: cover + final render + deliver',
    'delivered': 'YOU: upload (text in COPY_SHORTS)',
}
PUB_KEYS = ('TITLE', 'ALT TITLE', 'DESCRIPTION', 'HASHTAGS', 'PINNED COMMENT', 'PHOTO CREDITS')


# ---------- small readers (all tolerant: a half-written file in a running chat must never break the hub) ----------
def rjson(p):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {}


def rtext(p):
    try: return p.read_text(encoding='utf-8')
    except Exception: return ''


def proj_dir(V):
    """eps 01-02 keep the project one level down (video01/taka-1000)."""
    if (V / 'index.html').exists() or (V / 'state.json').exists(): return V
    for c in sorted(V.iterdir()):
        if c.is_dir() and (c / 'index.html').exists(): return c
    return V


def newest(globs):
    fs = [f for g in globs for f in g if f.is_file() and not f.name.startswith('._')]
    return max(fs, key=lambda f: f.stat().st_mtime) if fs else None


def publish_sections(txt):
    S, cur = {}, None
    for line in txt.splitlines():
        m = re.match(r'(ALT TITLE|TITLE|DESCRIPTION|HASHTAGS|PINNED COMMENT|PHOTO CREDITS)\s*(\(.*\))?\s*$', line.strip())
        if m: cur = m.group(1); S[cur] = []; continue
        if cur: S[cur].append(line)
    return {k: '\n'.join(v).strip() for k, v in S.items()}


def titles_doc():
    """titles_descriptions.md → {ep: {name, title, desc, tags}} (the hand-finalised short copy)."""
    out, cur = {}, None
    for line in rtext(ROOT / 'titles_descriptions.md').splitlines():
        m = re.match(r'##\s+(\d+)\s*[—-]\s*(.*)', line)
        if m: cur = out.setdefault(m.group(1).zfill(2), {'name': m.group(2).strip(), 'title': '', 'desc': [], 'tags': ''}); continue
        if cur is None: continue
        if line.strip() == '---': cur = None; continue
        m = re.match(r'\*\*TITLE:\*\*\s*(.*)', line)
        if m: cur['title'] = m.group(1).strip(); continue
        if line.startswith('**DESCRIPTION'): continue
        if line.strip().startswith('#'): cur['tags'] = line.strip(); continue
        if line.strip(): cur['desc'].append(line.strip())
    for v in out.values(): v['desc'] = '\n'.join(v['desc'])
    return out


def covers_from_gen_all():
    """thumbnail_redesign/all_covers/src/gen_all.py holds the v2 cover words for eps 1-46 — read it (no exec)."""
    src = ROOT / 'thumbnail_redesign' / 'all_covers' / 'src' / 'gen_all.py'
    out = {}
    try:
        tree = ast.parse(rtext(src)); col = {'R': 'r', 'G': 'g', 'Y': 'y'}; D = pick = None
        for n in tree.body:
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
                if n.targets[0].id == 'D': D = n.value
                if n.targets[0].id == 'pick': pick = ast.literal_eval(n.value)
        T = ROOT / 'thumbnail_redesign'
        idx, m25, m34 = rjson(T / '_photos_idx.json'), rjson(T / '_match_25_31.json'), rjson(T / '_meta_34_46.json')
        photo = {1: 'video01/images/pixabay.com:photos:money-bills-currency-taka-5964118 19661338-money-5964118.jpg'}
        for i, k in (pick or {}).items():
            try: photo[i] = idx[str(i)][k]
            except Exception: pass
        for m in (m25, m34):
            for k, v in m.items(): photo[int(k)] = v.get('photo', '')
        for k, v in zip(D.keys, D.values):
            i = k.value; e = [x.value if isinstance(x, ast.Constant) else col.get(getattr(x, 'id', ''), 'r') for x in v.elts]
            out[i] = dict(chip=e[0], line=e[1], hero=e[2], block=e[3], color=e[4], note=e[5],
                          side='l' if i % 2 == 0 else 'r', photo=photo.get(i, ''), src='thumbnail_redesign/all_covers/src/gen_all.py')
    except Exception: pass
    return out


def cover_from_html(P):
    """the episode's own cover_v2.html (written by cover_v2.py)."""
    t = rtext(P / 'cover_v2.html')
    if not t: return None
    g = lambda rx: (lambda m: html.unescape(m.group(1)) if m else '')(re.search(rx, t, re.S))
    bg = re.search(r'class="blk" id="blk" style="background:(#\w+)', t)
    col = {'#E2452B': 'r', '#1FA36B': 'g', '#FFD23F': 'y'}.get(bg.group(1) if bg else '', 'r')
    side = 'l' if re.search(r'class="note n-g" style="left', t) else 'r'
    return dict(chip=g(r'class="chip"[^>]*>(.*?)</span>'), line=g(r'class="c line"[^>]*>(.*?)</div>'),
                hero=g(r'id="hero">(.*?)</span>'), block=g(r'id="blk"[^>]*>(.*?)</span>'),
                note=g(r'class="note n-g"[^>]*>(.*?)</div>'), color=col, side=side,
                photo=g(r'<img class="ph" src="([^"]+)"').replace('%20', ' '), src=f'{P.name}/cover_v2.html', rel=True)


def q(s): return "'" + str(s).replace("'", "'\\''") + "'"


def cover_cmd(P, c):
    if not c: return ''
    ph = c.get('photo', '')
    if not c.get('rel'):                                   # gen_all paths are from VIDEO GEN; cover_v2 wants them from the episode
        ph = os.path.relpath(ROOT / ph, P)
    a = [f'bash _series/es.sh cover_v2 {P.relative_to(ROOT).as_posix()}', f'--photo {q(ph)}', f'--chip {q(c["chip"])}', f'--line {q(c["line"])}']
    if c.get('hero'): a.append(f'--hero {q(c["hero"])}')
    a += [f'--block {q(c["block"])}', f'--color {c.get("color", "r")}']
    if c.get('note'): a.append(f'--note {q(c["note"])}')
    a.append(f'--side {c.get("side", "r")}')
    return ' \\\n    '.join(a)


PUB_HEAD = """# Uploads + performance — YOURS to edit. The hub only reads this file (a chat can fill it for you: "log ep 46: 1,200 views, 62% stayed").
# One line per episode:  <ep> [where…] [up=YYYY-MM-DD] [views=N] [stayed=N%] [avd=M:SS] [likes=N] [checked=YYYY-MM-DD] [url=…]
#   where   = yt / fb / tt (any words)        up      = upload date
#   views   = views when you checked          stayed  = YouTube Studio "stayed to watch" (target 70%)
#   avd     = average view duration           checked = the day you read the numbers (aim: 2-3 days after upload)
# A later line for the same episode replaces the earlier one, so you can just add a new line when you re-check.
# Examples:
#   46 yt fb up=2026-11-24 views=1200 stayed=62% avd=0:35 checked=2026-11-27
#   45 yt up=2026-11-20
"""
PUB_OLD_HEAD = ('# Uploaded episodes — yours to edit; the hub only reads this file.\n'
                '# One line per episode: number, then anything (where, date). Examples:\n#   46 yt fb 2026-11-24\n#   45 yt\n')


def num(v):
    t = str(v).replace(',', '').replace('%', '').strip().upper(); mul = 1
    if t.endswith('K'): t, mul = t[:-1], 1000
    elif t.endswith('M'): t, mul = t[:-1], 1000000
    try: return float(t) * mul
    except Exception: return None


def published():
    """published.txt → {ep: {where, up, views, stayed, avd, likes, checked, summary}}."""
    out = {}
    for line in rtext(HUB / 'published.txt').splitlines():
        line = line.split('#')[0].strip()
        m = re.match(r'(\d+)\b\s*(.*)', line)
        if not m: continue
        d = {'where': []}
        for tok in m.group(2).split():
            if '=' in tok: k, v = tok.split('=', 1); d[k.lower()] = v
            elif re.match(r'\d{4}-\d\d-\d\d$', tok): d['up'] = tok
            else: d['where'].append(tok)
        d['where'] = ' '.join(d['where']) or 'yes'
        d['summary'] = d['where'] + (f' · {d["up"]}' if d.get('up') else '')
        out[m.group(1).zfill(2)] = d
    return out


def ideas():
    """IDEAS.md → [{done, text, note}] (lines '- [ ] idea — note' / '- [x] …' / '- idea')."""
    out = []
    for line in rtext(HUB / 'IDEAS.md').splitlines():
        m = re.match(r'\s*[-*]\s*(\[( |x|X)\])?\s*(.+)', line)
        if not m or line.lstrip().startswith('#'): continue
        t = m.group(3).strip(); parts = re.split(r'\s+[—–-]{1,2}\s+', t, maxsplit=1)
        out.append(dict(done=(m.group(2) or ' ').lower() == 'x', text=parts[0], note=parts[1] if len(parts) > 1 else ''))
    return out


IDEAS_HEAD = """# Topic ideas — YOURS to edit. The hub shows them in HUB.html (Ideas tab); it never changes this file.
# One idea per line. Tick it with [x] when it becomes an episode (add the ep number in the note if you like).
#   - [ ] idea — note (angle, source, why it could work)
#   - [x] idea — became ep 48
# Channel data: the viewer's own money or a thing they hold wins; policy topics lose. One question per video.

"""


def fmt_s(s):
    try: return f'{float(s):.1f} s'
    except Exception: return ''


# ---------- collect ----------
def collect():
    TD, GA, PUBD = titles_doc(), covers_from_gen_all(), published()
    now = dt.datetime.utcnow(); eps = []
    for V in sorted(ROOT.glob('video[0-9]*')):
        if not V.is_dir(): continue
        P = proj_dir(V); st = rjson(P / 'state.json'); pj = rjson(P / 'project.json')
        n = str(st.get('ep') or re.sub(r'\D', '', V.name)).zfill(2)
        out, drafts = P / 'out', P / 'drafts'
        reel = newest([out.glob('*_reel_9x16.mp4')]) or newest([out.glob('*_final.mp4')])
        prev = newest([drafts.glob('*_preview.mp4'), out.glob('*_preview.mp4')])
        cover = out / 'cover_reel_9x16.png'; cover = cover if cover.exists() else None
        pub_txt = rtext(out / 'publish.txt'); pub = publish_sections(pub_txt) if pub_txt else {}
        stage = st.get('stage') or ('delivered' if reel and cover else ('plan' if not st else '?'))
        log = st.get('log') or []
        last = (log[-1][:16] if log else '') or (dt.datetime.fromtimestamp((reel or prev or P).stat().st_mtime).strftime('%Y-%m-%d %H:%M'))
        kind = 'long' if (pj.get('format') == 'long' or (pj.get('max_len') or 0) > 180) else 'short'
        warn = []
        lk = rjson(P / '.lock.json')
        lock = ''
        if lk and not lk.get('released'):
            try: age = (now - dt.datetime.strptime(lk.get('renewed') or lk.get('since'), '%Y-%m-%dT%H:%M:%SZ')).total_seconds() / 3600
            except Exception: age = 0
            lock = f'{lk.get("who", "?")}'
            if age > 12: warn.append(f'stale lock "{lock}" from {(lk.get("renewed") or "")[:10]} — say "release the ep {n} lock" in a chat')
        if stage in STAGES and STAGES.index(stage) < STAGES.index('built') and prev:
            warn.append(f'state says {stage}, but a preview exists ({prev.relative_to(V).as_posix()})')
        if stage == 'delivered' and not reel: warn.append('delivered but no reel in out/')
        if stage == 'delivered' and not pub_txt: warn.append('no out/publish.txt')
        if st.get('reel_s') and float(st['reel_s']) > (pj.get('max_len') or 60) + 0.5: warn.append(f'reel {fmt_s(st["reel_s"])} > {pj.get("max_len", 60)} s')
        for o in st.get('open') or []: warn.append('open: ' + o)
        td = TD.get(n)
        if td and td.get('title'): ctitle, cstat = td['title'], 'FINAL'
        elif pub.get('TITLE'): ctitle, cstat = pub['TITLE'].splitlines()[0].strip(), 'DRAFT'
        else: ctitle, cstat = st.get('title') or pj.get('title') or '', 'WORKING TITLE'
        desc = td['desc'] if td and td.get('desc') else '\n'.join(
            l for l in pub.get('DESCRIPTION', '').splitlines() if l.strip() and not re.match(r'\s*(সূত্র|Sources)', l))
        src_line = next((l.strip() for l in pub.get('DESCRIPTION', '').splitlines() if re.match(r'\s*(সূত্র|Sources)', l)), '')
        tags = pub.get('HASHTAGS', '')
        yt = re.search(r'YouTube[^:]*:\s*(.*)', tags); fb = re.search(r'Facebook[^:]*:\s*(.*)', tags)
        yt = (td or {}).get('tags') or (yt.group(1).strip() if yt else '')
        fb = fb.group(1).strip() if fb else ''
        cj = rjson(P / 'docs' / 'cover_v2.json')
        if cj: cj['rel'] = True; cj['src'] = f'{V.name}/docs/cover_v2.json'
        cv = cj or cover_from_html(P) or GA.get(int(n)) if n.isdigit() else None
        rel = lambda f: (f.relative_to(ROOT).as_posix() if f else '')
        eps.append(dict(
            n=n, folder=V.name, proj=P.relative_to(ROOT).as_posix(), kind=kind,
            name=(td or {}).get('name', ''), work_title=st.get('title') or pj.get('title') or '',
            slug=st.get('slug') or (re.sub(r'_(reel_9x16|final|feed_4x5)$', '', reel.stem) if reel else ''), stage=stage, next=NEXT.get(stage, '?').format(n=n), last=last, lock=lock,
            uploaded=(PUBD.get(n) or {}).get('summary', ''), perf={k: v for k, v in (PUBD.get(n) or {}).items() if k != 'summary'},
            look=pj.get('look', ''), music=pj.get('music', ''),
            length=fmt_s(st.get('reel_s')) if st.get('reel_s') else '',
            reel=rel(reel), preview=rel(prev), cover=rel(cover), publish=rel(out / 'publish.txt') if pub_txt else '',
            copy_status=cstat, title=ctitle, alt_title=pub.get('ALT TITLE', ''), desc=desc, sources=src_line,
            yt=yt, fb=fb, pinned=pub.get('PINNED COMMENT', ''), credits=pub.get('PHOTO CREDITS', ''),
            cover_cmd=cover_cmd(P, cv), cover_src=(cv or {}).get('src', ''),
            all_cover=rel(ROOT / 'thumbnail_redesign' / 'all_covers' / f'TakaTheory_ep{n}_cover.png')
            if (ROOT / 'thumbnail_redesign' / 'all_covers' / f'TakaTheory_ep{n}_cover.png').exists() else '',
            warn=warn))
    return eps


# ---------- render ----------
def mac(p): return f'{MAC_ROOT}/{p}' if p else ''


def status_md(eps, stamp):
    act = [e for e in eps if e['stage'] != 'delivered']
    done = [e for e in eps if e['stage'] == 'delivered']
    up = sum(1 for e in done if e['uploaded'])
    L = [f'# Status — all videos', f'_Generated {stamp} from the videoNN folders. Do not edit; open HUB.html for the clickable version._', '',
         f'**{len(done)} delivered** ({up} marked uploaded in published.txt) · **{len(act)} in progress**', '']
    if act:
        L += ['## In progress', '', '| Ep | Title | Stage | Next step | Last activity | Notes |', '|---|---|---|---|---|---|']
        for e in act:
            L.append(f'| {e["n"]} | {e["title"] or e["work_title"]} | {e["stage"]} | {e["next"]} | {e["last"]} | {"; ".join(e["warn"])} |')
        L.append('')
    L += ['## Delivered', '', '| Ep | Title | Length | Uploaded | Last activity | Notes |', '|---|---|---|---|---|---|']
    for e in reversed(done):
        L.append(f'| {e["n"]} | {e["title"] or e["work_title"]} | {e["length"]} | {e["uploaded"] or "—"} | {e["last"]} | {"; ".join(e["warn"])} |')
    perf = [e for e in done if e['perf']]
    if perf:
        L += ['', '## Performance (from published.txt)', '', '| Ep | Title | Where | Uploaded | Views | Stayed | Avg view | Checked |', '|---|---|---|---|---|---|---|---|']
        for e in reversed(perf):
            p = e['perf']
            L.append(f'| {e["n"]} | {e["title"] or e["work_title"]} | {p.get("where", "")} | {p.get("up", "")} | {p.get("views", "")} | '
                     f'{p.get("stayed", "")} | {p.get("avd", "")} | {p.get("checked", "")} |')
        st = [num(e['perf'].get('stayed')) for e in perf if num(e['perf'].get('stayed')) is not None]
        if st: L.append(f'\nAverage stayed-to-watch: **{sum(st) / len(st):.0f} %** over {len(st)} episodes (target 70 %).')
    I = ideas()
    if I:
        L += ['', f'## Ideas backlog ({sum(not i["done"] for i in I)} open)', '']
        L += [f'- {i["text"]}' + (f' — {i["note"]}' if i['note'] else '') for i in I if not i['done']]
    L += ['', f'Folders: `{MAC_ROOT}/videoNN`. Uploads and views: `00_HUB/published.txt`. Topic ideas: `00_HUB/IDEAS.md`.', '']
    return '\n'.join(L)


def copy_md(eps, kind, stamp):
    sel = [e for e in eps if e['kind'] == kind]
    head = 'Shorts / Reels' if kind == 'short' else 'Long videos'
    L = [f'# Copy-paste text — {head}', f'_Generated {stamp}. FINAL = from titles_descriptions.md (hand-finalised); '
         'DRAFT = from the episode\'s out/publish.txt; WORKING TITLE = no publish text yet. Newest first._', '']
    if not sel: L += ['_None yet. A video counts as long when its project.json has `"format": "long"`._', '']
    for e in reversed(sel):
        L += [f'## {e["n"]} — {e["title"] or e["work_title"]}', f'`{e["copy_status"]}` · stage: {e["stage"]}'
              + (f' · uploaded: {e["uploaded"]}' if e['uploaded'] else ''), '']
        if e['title']: L += ['**TITLE**', '```', e['title'], '```']
        if e['alt_title']: L += ['**ALT TITLE**', '```', e['alt_title'], '```']
        if e['desc']: L += ['**DESCRIPTION**', '```', e['desc'] + (('\n' + e['sources']) if e['sources'] else ''), '```']
        if e['yt']: L += ['**HASHTAGS — YouTube**', '```', e['yt'], '```']
        if e['fb']: L += ['**HASHTAGS — Facebook**', '```', e['fb'], '```']
        if e['pinned']: L += ['**PINNED COMMENT**', '```', e['pinned'], '```']
        if e['credits']: L += ['**PHOTO CREDITS**', '```', e['credits'], '```']
        files = [f'reel `{mac(e["reel"])}`' if e['reel'] else '', f'cover `{mac(e["cover"])}`' if e['cover'] else '']
        if any(files): L += ['Files: ' + ' · '.join(f for f in files if f)]
        L += ['', '---', '']
    return '\n'.join(L)


def cmds(e):
    f, s = e['proj'], e['slug'] or 'Slug'
    return [
        ('Where to run', f'Paste any line into a Claude chat in this project ("run: …"). Claude runs it in its Mac shell from {MAC_ROOT}.\n'
                         'They do not run in the Mac Terminal app (the renderer is a Linux build inside Claude\'s shell).'),
        ('Status card (what is next)', f'bash _series/es.sh studio next {f}'),
        ('Preview render (540×960, ~1 min)', f'bash _series/es.sh audit {f} && bash _series/es.sh audio {f} && bash _series/es.sh render {f} --preview'),
        ('Full render + cover bake + deliver (run again while it prints RESUME)', f'bash _series/es.sh finish {f} --local --slug {s}'),
        ('Force a fresh full render of a delivered video', f'bash _series/es.sh finish {f} --local --slug {s} --render'),
        ('Re-make the v2 cover (then run the finish line to bake it in)', e['cover_cmd'] or '(no stored cover words — see 00_HUB/COMMANDS.md top for the template)'),
        ('Check the final file', f'bash _series/es.sh check_final {f}'),
    ]


def commands_md(eps, stamp):
    L = ['# Commands — render + cover, per video', f'_Generated {stamp}._', '',
         '**Run these by pasting them into a Claude chat in the Video Generation project** — e.g. `run: bash _series/es.sh finish video46 --local --slug Gas_Gap`.',
         f'Claude runs them in its Mac shell, from `{MAC_ROOT}`. They write straight into the episode folder. '
         'They can\'t run in the Mac Terminal app (the renderer is a Linux Chromium build inside Claude\'s shell). '
         'Render one full video at a time: the shell has 4 cores, so two full renders at once each run about twice as long.', '',
         '## General', '```', 'bash _series/es.sh hub                      # rebuild this hub now (also runs by itself after every step)',
         'bash _series/es.sh version                  # render kit version', '```', '',
         '### Cover template (cover style v2)', '```',
         "bash _series/es.sh cover_v2 videoNN --photo 'images/x.jpg' --chip '…' --line '…' [--hero '৳১০০'] \\\n"
         "    --block 'প্রশ্ন?' [--color r|g|y] [--note '…'] [--side l|r]",
         '```', 'hero = the key number (leave out if none) · block = the question, never the answer · writes out/cover_reel_9x16.png; '
         'the finish line then bakes it into the reel.', '']
    for e in reversed(eps):
        L += [f'## {e["n"]} — {e["title"] or e["work_title"]}', f'Folder: `{mac(e["proj"])}` · slug `{e["slug"]}` · stage {e["stage"]}', '']
        for k, c in cmds(e)[1:]:
            L += [f'**{k}**', '```', c, '```']
        if e['cover_src']: L += [f'_Cover words from `{e["cover_src"]}`._']
        L += ['']
    return '\n'.join(L)


def readme_md(stamp):
    return f'''# 00_HUB — one place for every TakaTheory video
_Generated {stamp}._

Open **HUB.html** (double-click, or use "Open Hub.command" in the VIDEO GEN folder — it refreshes first).

| File | What's in it |
|---|---|
| HUB.html | Everything below on one page, with search and copy buttons |
| STATUS.md | Every video: stage, the next step and who does it, files, uploaded or not |
| COPY_SHORTS.md | Title, description, hashtags, pinned comment for every Short — finals and drafts |
| COPY_LONG.md | The same for long videos (none yet) |
| COMMANDS.md | Preview/full render, finish and cover commands for every video, with folder paths |
| published.txt | **Yours to edit**: uploads + views per episode (`46 yt fb up=2026-11-24 views=1200 stayed=62% avd=0:35`). Shown in the Performance tab |
| IDEAS.md | **Yours to edit**: topic backlog (`- [ ] idea — note`). Shown in the Ideas tab |

How it stays current: every Claude chat runs its tools through `_series/es.sh`; after any step that changes an episode
(state, studio, finish, cover…) es.sh rebuilds the hub in under a second. Chats never edit these files directly, so
several chats can run at once without overwriting each other. Manual refresh: `bash _series/es.sh hub` in a chat, or
"Open Hub.command" on the Mac. Generator: `_series/tools/hub.py`.
Sources it reads: each `videoNN/state.json`, `project.json`, `out/`, `drafts/`, `out/publish.txt`, `titles_descriptions.md`,
cover words (`videoNN/docs/cover_v2.json`, `cover_v2.html`, `thumbnail_redesign/all_covers/src/gen_all.py`).
'''


def page_html(eps, stamp):
    data = []
    for e in eps:
        d = dict(e); d['cmds'] = cmds(e)[1:]; data.append(d)
    J = json.dumps(dict(eps=data, stamp=stamp, mac=MAC_ROOT, ideas=ideas()), ensure_ascii=False).replace('</', '<\\/')
    return HTML.replace('/*DATA*/', J)


HTML = r'''<!doctype html><html lang="bn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TakaTheory Hub</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#16181b;--mut:#6b6f76;--line:#e4e0d6;--acc:#00a86b;--warn:#c2410c;--chip:#eef6f1}
@media(prefers-color-scheme:dark){:root{--bg:#141517;--card:#1d1f22;--ink:#ecebe7;--mut:#9a9ea5;--line:#2d3034;--chip:#1f2b25}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Noto Sans Bengali","Segoe UI",sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 24px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
h1{font-size:18px;margin:0;font-weight:700}h1 b{color:var(--acc)}.stamp{color:var(--mut);font-size:12px}
nav{display:flex;gap:4px}nav button{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 12px;border-radius:8px;cursor:pointer;font:inherit}
nav button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
input[type=search]{margin-left:auto;padding:7px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);font:inherit;min-width:240px}
main{padding:20px 24px;max-width:1200px;margin:auto}
.kpis{display:flex;gap:12px;margin-bottom:18px;flex-wrap:wrap}.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 16px}.kpi b{font-size:22px;display:block}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}th{font-size:12px;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.st{display:inline-block;padding:1px 8px;border-radius:99px;background:var(--chip);font-size:12px;white-space:nowrap}
.w{color:var(--warn);font-size:12px}a{color:var(--acc)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px}
.card h3{margin:0 0 4px;font-size:16px}.meta{color:var(--mut);font-size:12px;margin-bottom:10px}
.f{margin:8px 0}.f .k{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em;display:flex;justify-content:space-between;align-items:center}
.f pre{margin:3px 0 0;white-space:pre-wrap;font:inherit;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.f pre.code{font:12.5px/1.45 ui-monospace,Menlo,monospace}
.cp{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;font-size:11px;padding:2px 8px;cursor:pointer}.cp.ok{background:var(--acc);color:#fff;border-color:var(--acc)}
.tag{font-size:11px;padding:1px 7px;border-radius:99px;border:1px solid var(--line);margin-left:6px}.FINAL{background:#d9f5e6;color:#0b5d3b;border-color:#bfe9d2}.DRAFT{background:#fff1d6;color:#7a4b00;border-color:#f3dca9}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px}.grid .card{padding:8px}.grid img{width:100%;border-radius:6px;display:block;aspect-ratio:9/16;object-fit:cover;background:var(--line)}
.note{color:var(--mut);font-size:13px;margin:0 0 14px}
</style></head><body>
<header><h1><b>৳</b> TakaTheory Hub</h1><span class="stamp" id="stamp"></span>
<nav><button data-t="status" class="on">Status</button><button data-t="copy">Copy text</button><button data-t="cmd">Commands</button><button data-t="cov">Covers</button><button data-t="perf">Performance</button><button data-t="ideas">Ideas</button></nav>
<input type="search" id="q" placeholder="Search ep, title, stage…"></header>
<main id="m"></main>
<script>
const D=/*DATA*/;const $=s=>document.querySelector(s);let tab='status';
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const href=p=>p?('../'+p.split('/').map(encodeURIComponent).join('/')):'';
function copy(btn,txt){const done=()=>{btn.classList.add('ok');btn.textContent='Copied';setTimeout(()=>{btn.classList.remove('ok');btn.textContent='Copy'},1200)};
 if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(txt).then(done,()=>fb())}else fb();
 function fb(){const t=document.createElement('textarea');t.value=txt;document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();done()}}
const T={};let tid=0;
const field=(k,v,code)=>{if(!v)return'';const id='t'+(tid++);T[id]=v;return `<div class="f"><div class="k">${esc(k)}<button class="cp" data-id="${id}">Copy</button></div><pre${code?' class="code"':''}>${esc(v)}</pre></div>`};
const match=e=>{const q=$('#q').value.trim().toLowerCase();if(!q)return true;return [e.n,e.title,e.work_title,e.stage,e.name,e.slug,e.next].join(' ').toLowerCase().includes(q)};
function status(){const E=D.eps.filter(match),act=E.filter(e=>e.stage!=='delivered'),done=E.filter(e=>e.stage==='delivered');
 const all=D.eps.filter(e=>e.stage==='delivered');
 let h=`<div class="kpis"><div class="kpi"><b>${all.length}</b>delivered</div><div class="kpi"><b>${all.filter(e=>e.uploaded).length}</b>marked uploaded</div><div class="kpi"><b>${D.eps.length-all.length}</b>in progress</div></div>`;
 const row=e=>`<tr><td><b>${e.n}</b></td><td>${esc(e.title||e.work_title)}${e.lock?`<div class="w">🔒 ${esc(e.lock)}</div>`:''}</td><td><span class="st">${esc(e.stage)}</span></td><td>${esc(e.next)}${e.uploaded?`<div class="meta">uploaded: ${esc(e.uploaded)}</div>`:''}</td><td>${esc(e.length)}</td><td>${esc(e.last)}</td><td>${e.reel?`<a href="${href(e.reel)}">reel</a> `:''}${e.preview&&!e.reel?`<a href="${href(e.preview)}">preview</a> `:''}${e.cover?`<a href="${href(e.cover)}">cover</a>`:''}</td><td>${e.warn.map(w=>`<div class="w">${esc(w)}</div>`).join('')}</td></tr>`;
 const tbl=(t,L)=>L.length?`<h2>${t}</h2><table><tr><th>Ep</th><th>Title</th><th>Stage</th><th>Next step</th><th>Length</th><th>Last activity</th><th>Files</th><th>Notes</th></tr>${L.map(row).join('')}</table>`:'';
 return h+tbl('In progress',act)+tbl('Delivered',done.slice().reverse())+`<p class="note" style="margin-top:14px">Mark an upload: add a line like <code>46 yt fb</code> to 00_HUB/published.txt.</p>`}
function copyv(){const E=D.eps.filter(match).slice().reverse();let h='<p class="note">FINAL = hand-finalised in titles_descriptions.md · DRAFT = from the episode\'s publish.txt · Shorts first; long videos are listed after them.</p>';
 for(const kind of['short','long']){const L=E.filter(e=>e.kind===kind);if(kind==='long'&&!L.length)continue;h+=`<h2>${kind==='short'?'Shorts / Reels':'Long videos'}</h2>`;
 for(const e of L)h+=`<div class="card"><h3>${e.n} — ${esc(e.title||e.work_title)}<span class="tag ${e.copy_status}">${e.copy_status}</span></h3><div class="meta">${esc(e.stage)}${e.uploaded?' · uploaded: '+esc(e.uploaded):''}</div>`
  +field('Title',e.title)+field('Alt title',e.alt_title)+field('Description',e.desc+(e.sources?'\n'+e.sources:''))+field('Hashtags — YouTube',e.yt)+field('Hashtags — Facebook',e.fb)+field('Pinned comment',e.pinned)+field('Photo credits',e.credits)+'</div>'}
 return h}
function cmd(){let h=`<p class="note">Paste a line into a Claude chat in this project (e.g. “run: …”). Claude runs it in its Mac shell from <code>${esc(D.mac)}</code>. These don't run in the Mac Terminal app. Render one full video at a time.</p>`;
 h+=`<div class="card">${field('Rebuild this hub','bash _series/es.sh hub',1)}${field('Cover template (style v2)',"bash _series/es.sh cover_v2 videoNN --photo 'images/x.jpg' --chip '…' --line '…' [--hero '৳১০০'] --block 'প্রশ্ন?' [--color r|g|y] [--note '…'] [--side l|r]",1)}</div>`;
 for(const e of D.eps.filter(match).slice().reverse())h+=`<div class="card"><h3>${e.n} — ${esc(e.title||e.work_title)}</h3><div class="meta">${esc(D.mac+'/'+e.proj)} · slug ${esc(e.slug)} · ${esc(e.stage)}</div>${e.cmds.map(([k,c])=>field(k,c,1)).join('')}${field('Folder path',D.mac+'/'+e.proj,1)}</div>`;
 return h}
function cov(){return `<p class="note">The cover in each episode's out/ folder. Click to open full size; the re-make command is under Commands.</p><div class="grid">`+D.eps.filter(match).slice().reverse().map(e=>`<div class="card">${e.cover?`<a href="${href(e.cover)}"><img loading="lazy" src="${href(e.cover)}"></a>`:'<div style="aspect-ratio:9/16;display:grid;place-items:center;color:var(--mut)">no cover yet</div>'}<div class="meta" style="margin:6px 2px 0"><b>${e.n}</b> ${esc(e.title||e.work_title)}</div></div>`).join('')+'</div>'}
const nm=v=>{let t=String(v??'').replace(/[,%]/g,'').trim().toUpperCase(),m=1;if(t.endsWith('K')){t=t.slice(0,-1);m=1e3}else if(t.endsWith('M')){t=t.slice(0,-1);m=1e6}const x=parseFloat(t);return isNaN(x)?null:x*m};
function perf(){const all=D.eps.filter(e=>e.stage==='delivered'),E=all.filter(match).slice().reverse();
 const P=all.filter(e=>e.perf&&e.perf.where),st=P.map(e=>nm(e.perf.stayed)).filter(x=>x!==null),vw=P.map(e=>nm(e.perf.views)).filter(x=>x!==null);
 const avg=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:null;
 let h=`<div class="kpis"><div class="kpi"><b>${P.length}</b>uploaded</div><div class="kpi"><b>${all.length-P.length}</b>delivered, not uploaded</div><div class="kpi"><b>${avg(st)===null?'—':avg(st).toFixed(0)+'%'}</b>avg stayed (target 70%)</div><div class="kpi"><b>${avg(vw)===null?'—':Math.round(avg(vw)).toLocaleString()}</b>avg views</div></div>`;
 h+=`<p class="note">From 00_HUB/published.txt — add a line per episode, e.g. <code>46 yt fb up=2026-11-24 views=1200 stayed=62% avd=0:35 checked=2026-11-27</code>, or ask a chat: “log ep 46: 1,200 views, 62% stayed”.</p>`;
 const sc=v=>{const x=nm(v);return x===null?'':(x>=70?'color:var(--acc);font-weight:600':x<55?'color:var(--warn)':'')};
 h+=`<table><tr><th>Ep</th><th>Title</th><th>Where</th><th>Uploaded</th><th>Views</th><th>Stayed</th><th>Avg view</th><th>Checked</th></tr>`+E.map(e=>{const p=e.perf||{};return `<tr><td><b>${e.n}</b></td><td>${esc(e.title||e.work_title)}</td><td>${p.where?esc(p.where):'<span class="w">not uploaded</span>'}${p.url?` <a href="${esc(p.url)}" target="_blank">open</a>`:''}</td><td>${esc(p.up)}</td><td>${esc(p.views)}</td><td style="${sc(p.stayed)}">${esc(p.stayed)}</td><td>${esc(p.avd)}</td><td>${esc(p.checked)}</td></tr>`}).join('')+'</table>';
 return h}
function ideasv(){const q=$('#q').value.trim().toLowerCase(),I=D.ideas.filter(i=>!q||(i.text+' '+i.note).toLowerCase().includes(q));
 const open=I.filter(i=>!i.done),done=I.filter(i=>i.done);
 let h=`<p class="note">From 00_HUB/IDEAS.md — one line per idea: <code>- [ ] idea — note</code>; tick with <code>[x]</code> when it becomes an episode. To start one, tell a chat: “plan the next episode from IDEAS”.</p>`;
 if(!D.ideas.length)return h+'<div class="card">No ideas yet.</div>';
 const li=i=>`<div class="card" style="padding:10px 14px${i.done?';opacity:.55':''}"><b>${i.done?'✓ ':''}${esc(i.text)}</b>${i.note?`<div class="meta" style="margin:2px 0 0">${esc(i.note)}</div>`:''}${!i.done?field('Copy',i.text+(i.note?' — '+i.note:'')).replace('<div class="k">Copy','<div class="k">'):''}</div>`;
 return h+`<h2>Open (${open.length})</h2>`+open.map(li).join('')+(done.length?`<h2>Done (${done.length})</h2>`+done.map(li).join(''):'')}
function draw(){tid=0;$('#m').innerHTML=({status,copy:copyv,cmd,cov,perf,ideas:ideasv})[tab]()}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));b.classList.add('on');tab=b.dataset.t;draw()});
$('#q').oninput=draw;$('#m').onclick=ev=>{const b=ev.target.closest('.cp');if(b)copy(b,T[b.dataset.id])};
$('#stamp').textContent='updated '+D.stamp;draw();
</script></body></html>'''


# ---------- write (only when changed; atomic swap) ----------
def put(name, text):
    f = HUB / name
    if rtext(f) == text: return False
    tmp = HUB / f'.{name}.{os.getpid()}.tmp'
    tmp.write_text(text, encoding='utf-8'); os.replace(tmp, f); return True


def main():
    HUB.mkdir(exist_ok=True)
    eps = collect()
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    body = {'STATUS.md': status_md(eps, '{STAMP}'), 'COPY_SHORTS.md': copy_md(eps, 'short', '{STAMP}'),
            'COPY_LONG.md': copy_md(eps, 'long', '{STAMP}'), 'COMMANDS.md': commands_md(eps, '{STAMP}'),
            'README.md': readme_md('{STAMP}'), 'HUB.html': page_html(eps, '{STAMP}')}
    changed = []
    for name, t in body.items():                    # the stamp alone never counts as a change
        old = rtext(HUB / name)
        m = re.search(r'Generated (\d{4}-\d\d-\d\d \d\d:\d\d)|"stamp": "([^"]+)"', old)
        prev = (m.group(1) or m.group(2)) if m else None
        if prev and old == t.replace('{STAMP}', prev): continue
        if put(name, t.replace('{STAMP}', stamp)): changed.append(name)
    pf = HUB / 'published.txt'
    if not pf.exists() or rtext(pf) == PUB_OLD_HEAD: pf.write_text(PUB_HEAD, encoding='utf-8')   # untouched old header → new one
    if not (HUB / 'IDEAS.md').exists(): (HUB / 'IDEAS.md').write_text(IDEAS_HEAD, encoding='utf-8')
    if not QUIET:
        act = [e for e in eps if e['stage'] != 'delivered']
        print(f'HUB {len(eps)} videos · {len(act)} in progress · ' + (f'updated: {", ".join(changed)}' if changed else 'no changes'))
        for e in act: print(f'  ep{e["n"]} {e["stage"]} → {e["next"]}' + ''.join(f'\n     ! {w}' for w in e['warn']))


if __name__ == '__main__':
    main()
