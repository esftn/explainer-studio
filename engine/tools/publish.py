"""Publish pack + Gate 4 checklist: out/publish.md (titles, description with sources and credits, chapters,
hashtags, final QA ticks) and out/screen_off.m4a (audio only, for the screen-off listen).
usage: python publish.py <project>            # write/refresh out/publish.md (keeps titles/caption you already wrote)
       python publish.py <project> --check    # verify: 3 titles ≤ 60 chars, no TODO left, chapters valid
Run after render.py. Claude writes the titles, hook line and hashtags into publish.md, then runs --check."""
import argparse, csv, json, re, subprocess, sys
from es import project, cfg, page

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--check', action='store_true')
a = ap.parse_args(); P = project(a.project); O = P / 'out'; O.mkdir(exist_ok=True); C = cfg(P)
md = O / 'publish.md'

if a.check:
    if not md.exists(): sys.exit('no out/publish.md — run publish.py first')
    s = md.read_text(encoding='utf-8'); bad = []
    titles = re.findall(r'^\d\. (.+)$', s.split('## Titles')[1].split('##')[0], re.M) if '## Titles' in s else []
    if len(titles) < 3: bad.append(f'{len(titles)} title options (need 3)')
    bad += [f'title over 60 characters ({len(t)}): {t}' for t in titles if len(t) > 60]
    if 'TODO' in s: bad.append(f'{s.count("TODO")} TODO left in publish.md')
    for b in bad: print('FAIL', b)
    print('publish.md OK' if not bad else ''); sys.exit(1 if bad else 0)

with page(P) as pg:
    S = pg.evaluate('SCENES'); total = pg.evaluate('TOTAL')
    srcs = pg.evaluate("[...document.querySelectorAll('.scene .src')].map(e=>e.textContent.trim()).filter(Boolean)")
    used = set(pg.evaluate("[...document.querySelectorAll('.scene img')].map(i=>i.getAttribute('src'))"))
used |= {re.sub(r'^img/cut_(.+)\.png$', r'img/\1.jpg', u) for u in used if u}
def mmss(t): t = int(t); return f'{t // 60}:{t % 60:02d}'
# chapters from scene tags (merge runs of the same tag); YouTube: first at 0:00, ≥ 3 chapters, each ≥ 10 s
ch = []
for s in S:
    tag = (s.get('tag') or '').strip()
    if not tag: continue
    if ch and ch[-1][1] == tag: continue
    ch.append([s['start'], tag])
if ch: ch[0][0] = 0
ok_ch = len(ch) >= 3 and all(b[0] - a_[0] >= 10 for a_, b in zip(ch, ch[1:] + [[total, '']]))
sources = []
for x in srcs:
    for part in re.split(r'\s*[·|;]\s*', x):
        part = re.sub(r'^[^:]{1,14}:\s*', '', part).strip()          # drop labels like "সূত্র:", "ছবি:", "Source:"
        if part and part != '…' and part not in sources: sources.append(part)
credits, ai = [], 0
L = P / 'licences.csv'
if L.exists():
    for r in csv.DictReader(L.open(encoding='utf-8')):
        if r.get('file', '').strip() not in used: continue           # credit only what is actually in the video
        ai += (r.get('ai') or '').lower() == 'yes'
        c = f"{r.get('source', '').strip()} ({r.get('licence', '?').strip()})"
        if r.get('source') and c not in credits: credits.append(c)
old = md.read_text(encoding='utf-8') if md.exists() else ''
def keep(section, default):
    m = re.search(r'## ' + section + r'\n(.*?)(?=\n## |\Z)', old, re.S)
    return m.group(1).strip() if m and 'TODO' not in m.group(1) else default
out = [f"# Publish pack — {C.get('title', P.name)}", '',
       f"Length {mmss(total)} · {C.get('aspect', '9:16')} · {'monetised' if C.get('monetized') else 'not monetised'}", '',
       '## Titles', keep('Titles', '1. TODO (≤ 60 characters, the hook\'s words)\n2. TODO\n3. TODO'), '',
       '## Description', keep('Description', 'TODO hook line (one sentence, no promise the video does not keep)\n\nTODO 2–3 lines of context'), '',
       '## Sources', '\n'.join(f'- {x}' for x in sources) or '- (no .src bands found)', '',
       '## Credits', '\n'.join(f'- {x}' for x in credits) or '- (licences.csv empty)', '',
       '## Hashtags', keep('Hashtags', 'TODO 3–5, Bangla + English'), '']
if C.get('aspect') == '16:9' or ok_ch:
    out += ['## Chapters', '\n'.join(f'{mmss(t)} {tag}' for t, tag in ch) if ch else '(no .tag chips)',
            '' if ok_ch else '> WARN: YouTube needs ≥ 3 chapters, the first at 0:00, each ≥ 10 s — merge or retag scenes.', '']
out += ['## Disclosure', (f'{ai} AI-generated asset(s). Tick YouTube\'s "altered or synthetic content" setting if any of them looks realistic. '
        'Recreated documents are labelled in frame.') if ai else 'No AI-generated assets in licences.csv.', '',
        '## Gate 4 — creator ticks before publishing',
        '- [ ] Sound off: watched muted on a phone; every number and label readable, story still clear',
        '- [ ] Screen off: listened to out/screen_off.m4a only; narration makes sense without pictures',
        '- [ ] Facts: on-screen names, dates, numbers, maps, quotes match the source ledger',
        '- [ ] Rights: every asset has a source + licence; nothing non-commercial in a monetised video',
        '- [ ] AI honesty: AI visuals are illustration only; disclosure set if needed',
        '', '## Next time', keep('Next time', 'TODO one line: what to improve in the next video'), '']
md.write_text('\n'.join(out), encoding='utf-8')
final = max(O.glob('*_final.mp4'), key=lambda x: x.stat().st_mtime, default=None)
srcaudio = final or (O / 'mix.wav' if (O / 'mix.wav').exists() else None)
if srcaudio:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(srcaudio), '-vn', '-c:a', 'aac', '-b:a', '160k', str(O / 'screen_off.m4a')], check=True)
print(f'out/publish.md written ({len(sources)} sources, {len(credits)} credits, {len(ch)} chapters'
      f'{"" if ok_ch or C.get("aspect") != "16:9" else ", chapters need fixing"}); out/screen_off.m4a for the screen-off check.')
print('Next: write the titles/description/hashtags into publish.md, then publish.py --check.')
