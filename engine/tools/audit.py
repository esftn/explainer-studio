"""QA gate. Runs every automatic check; on success writes .qa_pass (render.py refuses to run without it).
Also exports cues.json + scenes.json so the audio is always built from the audited timeline.
usage: python audit.py <project> [--step 0.1] [--density 0.55] [--max-len 0]
Checks: text inside frame & above source band at every step · no missing images · fonts loaded · licences ·
        every data-vo scene has a VO duration · no console errors · visual density per scene · total length."""
import argparse, json, time, sys
from es import project, cfg, page, timeline_hash

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--step', type=float, default=0.1)
ap.add_argument('--density', type=float, default=0.55); ap.add_argument('--max-len', type=float, default=0)
a = ap.parse_args(); P = project(a.project)
fails, warns = [], []
with page(P) as pg:
    if pg.errs: fails += [f'console: {e}' for e in pg.errs]
    total = pg.evaluate('TOTAL'); scenes = pg.evaluate('SCENES')
    missing = pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src'))")
    fails += [f'missing image: {m}' for m in sorted(set(missing))]
    fonts = pg.evaluate("[...document.fonts].filter(f=>f.status!=='loaded').map(f=>f.family+' '+f.weight)")
    combos = pg.evaluate("""[...new Set([...document.querySelectorAll('.scene *')].filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))
        .map(e=>{const cs=getComputedStyle(e);return cs.fontFamily.split(',')[0].replace(/["']/g,'').trim()+'|'+cs.fontWeight}))]""")
    faces = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family.replace(/[\"']/g,'')+'|'+f.weight)")
    for c in combos:
        if c not in faces: warns.append(f'font {c.replace("|", " weight ")} used but that weight is not loaded (browser fakes it) — add its @fontsource css')
    for i, s in enumerate(scenes):
        if s.get('voMissing'):
            fails.append(f'scene {i+1}: data-vo={s["vo"]} but no VO duration (run vo_prep.py)')
    bad = pg.evaluate(f'AUDIT({a.step})')
    for b in bad:
        fails.append(f"text out of frame: scene {b['scene']} t={b['t']}s '{b['txt']}' box l{b['l']} r{b['r']} t{b['top']} b{b['b']}")
    dens = pg.evaluate('DENSITY(0.5)')
    by = {}
    for d in dens: by.setdefault(d['scene'], []).append(d['fill'])
    skip = pg.evaluate("[...document.querySelectorAll('.scene')].map((s,i)=>s.dataset.density==='off'?i+1:0).filter(Boolean)")
    for sc, v in sorted(by.items()):
        if sc in skip: continue
        avg = sum(v) / len(v); low = sum(1 for x in v if x < 0.35)
        if avg < a.density: warns.append(f'scene {sc}: low visual density {avg:.0%} (target ≥{a.density:.0%}) — add a photo/graphic')
        if low >= 4: warns.append(f'scene {sc}: {low * 0.5:.1f}s of near-empty frame')
    json.dump(pg.evaluate('CUES'), open(P / 'cues.json', 'w'), ensure_ascii=False)
    json.dump(scenes, open(P / 'scenes.json', 'w'))
    # source band present on scenes with facts
    nosrc = pg.evaluate("[...document.querySelectorAll('.scene')].map((s,i)=>[i+1,!!s.querySelector('.src'),s.querySelectorAll('[data-a=count],.blk,.blkr,.stamp').length]).filter(x=>!x[1]&&x[2]>0).map(x=>x[0])")
    warns += [f'scene {n}: has numbers/claims but no .src source band' for n in nosrc]
    used = sorted(set(pg.evaluate("[...document.querySelectorAll('.scene img')].map(i=>i.getAttribute('src'))")))
if a.max_len and total > a.max_len: fails.append(f'length {total:.1f}s > max {a.max_len}s')

# ---- licence ledger: every image used needs a row; monetised projects need commercial=yes on all of them ----
import csv, re
C = cfg(P); mon = bool(C.get('monetized'))
L = P / 'licences.csv'
led = {r['file'].strip(): r for r in csv.DictReader(L.open(encoding='utf-8'))} if L.exists() else {}
ai_n = 0
for src in used:
    if not src or src.startswith('data:') or re.search(r'img/paper(_dark)?\.jpg$', src): continue
    base = re.sub(r'^img/cut_(.+)\.png$', r'img/\1.jpg', src)            # a cutout inherits its photo's licence
    r = led.get(src) or led.get(base)
    if not r: fails.append(f'licence: {src} has no row in licences.csv (file,source,licence,commercial,ai,notes)'); continue
    lic, com, ai = (r.get('licence') or '?').strip(), (r.get('commercial') or '?').strip().lower(), (r.get('ai') or '?').strip().lower()
    ai_n += ai == 'yes'
    if mon and com != 'yes': fails.append(f'licence: {src} is commercial={com or "?"} on a monetised project ({lic})')
    elif lic == '?' or com == '?': warns.append(f'licence: {src} source/licence unknown — fill licences.csv before publishing')
    elif com == 'no': warns.append(f'licence: {src} is non-commercial ({lic}) — fine only while the video is not monetised')

# ---- beat mix (data-type on scenes) ----
types = [s.get('type') for s in scenes]
if any(types):
    from collections import Counter
    cnt = Counter(t or '?' for t in types); n = len(types)
    print('beat mix: ' + ' · '.join(f'{k} {v} ({v / n:.0%})' for k, v in cnt.most_common()))
    run = mx = 0
    for t in types:
        run = run + 1 if t == 'COLLAGE' else 0; mx = max(mx, run)
    if mx > 3: warns.append(f'beat mix: {mx} COLLAGE (AI) scenes in a row — max 3; swap one for a MAP/CHART/PHOTO')
    if cnt.get('COLLAGE', 0) / n > 0.6: warns.append(f'beat mix: COLLAGE {cnt["COLLAGE"] / n:.0%} of scenes — over 60% even for the VOX look')
if ai_n: print(f'AI assets in use: {ai_n} → tick YouTube\'s altered/synthetic setting if any looks realistic')
print(f'TOTAL {total:.2f}s, {len(scenes)} scenes')
for w in warns: print('WARN ', w)
for f in fails: print('FAIL ', f)
qa = P / '.qa_pass'
if fails:
    if qa.exists(): qa.unlink()
    print(f'\n{len(fails)} failures — fix them, then re-run audit.py. Render is blocked.'); sys.exit(1)
qa.write_text(json.dumps({'hash': timeline_hash(P), 'time': time.strftime('%Y-%m-%d %H:%M'), 'total': total, 'warnings': warns}, ensure_ascii=False))
print(f'\nQA PASS ({len(warns)} warnings). Next: review.py (look at every sheet), audio.py, render.py')
