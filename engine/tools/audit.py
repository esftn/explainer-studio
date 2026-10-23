"""QA gate. Runs every automatic check; on success writes .qa_pass (render.py refuses to run without it).
Also exports cues.json + scenes.json so the audio is always built from the audited timeline, and qa.json
(flagged moments) for review.py --keys.
usage: python audit.py <project> [--step 0.1] [--density 0.55] [--max-len N] [--fast]

FAIL (blocks render)
  · text out of frame / into the source band (every 0.1 s)   · missing images, console errors, missing VO
  · data-say word not found in that scene's VO, or lands after the scene ends     · video longer than max_len
  · text on text · text covered by a graphic                 · text outside the 4:5 feed zone (y 285–1635)
  · text too small (< 26 px, source line excepted)           · text contrast too low against what is behind it
WARN (Claude looks at each flagged frame on the key-moment sheet)
  · text touching a graphic's edge · busy background behind text · key number (count/stamp/slam) with no
    data-say/data-at · on-screen number not found in facts.json · low density · font weight faked
Opt-outs, used sparingly and only on purpose: data-qa="ok", data-zone="band", data-density="off"."""
import argparse, io, json, re, time, sys
from es import project, cfg, page, timeline_hash, TOOLS, bn_digits_to_int

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--step', type=float, default=0.1)
ap.add_argument('--density', type=float, default=0.55); ap.add_argument('--max-len', type=float)
ap.add_argument('--fast', action='store_true', help='skip legibility screenshots (iterating only; render still needs a full pass)')
a = ap.parse_args(); P = project(a.project); C = cfg(P)
max_len = a.max_len if a.max_len is not None else C.get('max_len', 0)
Z0, Z1 = C.get('feed_zone', [285, 1635])
fails, warns, flags = [], [], []


def lum(rgb):
    def ch(c):
        c = c / 255; return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(rgb[0]) + 0.7152 * ch(rgb[1]) + 0.0722 * ch(rgb[2])


def contrast(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2); return (hi + 0.05) / (lo + 0.05)


def rgba(s):
    v = [float(x) for x in re.findall(r'[\d.]+', s)]; return (v + [1])[:4] if len(v) >= 3 else [0, 0, 0, 1]


with page(P) as pg:
    if pg.errs: fails += [f'console: {e}' for e in pg.errs]
    total = pg.evaluate('TOTAL'); scenes = pg.evaluate('SCENES')
    missing = pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src'))")
    fails += [f'missing image: {m}' for m in sorted(set(missing))]
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
    nosrc = pg.evaluate("[...document.querySelectorAll('.scene')].map((s,i)=>[i+1,!!s.querySelector('.src'),s.querySelectorAll('[data-a=count],.blk,.blkr,.stamp').length]).filter(x=>!x[1]&&x[2]>0).map(x=>x[0])")
    warns += [f'scene {n}: has numbers/claims but no .src source band' for n in nosrc]

    # ---------- v0.4 checks ----------
    pg.add_script_tag(path=str(TOOLS / 'qa.js'))
    for k in pg.evaluate('QA_KEYS()'):
        if k['kind'] == 'untimed': warns.append(f"scene {k['scene']}: key number '{k['txt']}' is not tied to a spoken word — add data-say")
        else: fails.append(f"scene {k['scene']}: data-say '{k['txt']}' lands after the scene ends")
    for c in pg.evaluate('QA_COLLIDE(0.25)'):
        msg = {'text-over-text': f"text overlaps text: '{c['a']}' / '{c['b']}'",
               'text-covered': f"text covered by a graphic: '{c['a']}' under {c['b']}",
               'text-touches-graphic': f"text touches the edge of a graphic: '{c['a']}' / {c['b']}"}[c['kind']]
        line = f"scene {c['scene']} t={c['t']}s: {msg}"
        (fails if c['level'] == 'FAIL' else warns).append(line); flags.append({**c, 'msg': msg})
    T = pg.evaluate('QA_TARGETS()')
    screen_txt = []
    for e in T:
        screen_txt.append(e['txt']);
        if e['count']: screen_txt.append(str(e['count']))
        if e['skip']: continue
        top = min(l[1] for l in e['lines']); bot = max(l[3] for l in e['lines'])
        if not e['src'] and not e['band'] and (top < Z0 - 2 or bot > Z1 + 2):
            fails.append(f"scene {e['scene']} t={e['t']}s: text outside the 4:5 feed zone '{e['txt']}' (y {top}–{bot}; zone {Z0}–{Z1})")
            flags.append({'kind': 'zone', 'scene': e['scene'], 't': e['t'], 'msg': 'outside 4:5 zone', 'box': [min(l[0] for l in e['lines']), top, max(l[2] for l in e['lines']), bot]})
        if not e['src'] and e['size'] < 30: fails.append(f"scene {e['scene']}: text too small ({e['size']:.0f}px < 30) '{e['txt']}'")
        elif not e['src'] and e['size'] < (40 if e['words'] >= 3 else 34): warns.append(f"scene {e['scene']}: small text ({e['size']:.0f}px; running text should be >= 40) '{e['txt']}'")
        # v0.7 reading time: text must stay on screen long enough to read (0.6 s + 0.33 s per word; a number or 1-2 word label >= 1.2 s)
        if not e['src'] and not e['band']:
            need = min(4.5, max(1.2 if (e['words'] <= 2 or e['count']) else 0, 0.6 + 0.33 * e['words'])); have = e['end'] - (e['start'] + 0.25)
            if have < need - 0.15:
                fails.append(f"scene {e['scene']}: '{e['txt']}' is readable for only {max(0, have):.1f}s (needs {need:.1f}s): it appears too late or leaves too early; start it earlier (data-say lead / smaller data-t) or lengthen the scene")
                flags.append({'kind': 'reading', 'scene': e['scene'], 't': e['t'], 'msg': f'{have:.1f}s of {need:.1f}s', 'box': [min(l[0] for l in e['lines']), top, max(l[2] for l in e['lines']), bot]})
            elif have < need:
                warns.append(f"scene {e['scene']}: '{e['txt']}' is readable for {have:.1f}s (comfortable: {need:.1f}s)")
    # legibility: screenshot what is behind each text element (text made transparent) and measure contrast
    if not a.fast:
        import numpy as np
        from PIL import Image
        for e in T:
            if e['skip']: continue
            x0 = max(0, min(l[0] for l in e['lines']) - 4); y0 = max(0, min(l[1] for l in e['lines']) - 4)
            x1 = min(1080, max(l[2] for l in e['lines']) + 4); y1 = min(1920, max(l[3] for l in e['lines']) + 4)
            if x1 - x0 < 4 or y1 - y0 < 4: continue
            pg.evaluate(f'seek({e["t"]})')
            pg.evaluate(f"""(()=>{{const el=document.querySelector('[data-qa-id="{e["id"]}"]');el.dataset.qaSave=el.getAttribute('style')||'';
                el.style.setProperty('color','transparent','important');el.style.setProperty('-webkit-text-stroke-color','transparent','important');
                el.style.setProperty('text-shadow','none','important')}})()""")
            png = pg.screenshot(clip={'x': x0, 'y': y0, 'width': x1 - x0, 'height': y1 - y0})
            pg.evaluate(f"""(()=>{{const el=document.querySelector('[data-qa-id="{e["id"]}"]');el.setAttribute('style',el.dataset.qaSave);delete el.dataset.qaSave}})()""")
            px = np.asarray(Image.open(io.BytesIO(png)).convert('RGB'), float).reshape(-1, 3)
            L = np.array([lum(p) for p in px[::max(1, len(px) // 1500)]])
            bg_med = float(np.median(L)); p10, p90 = float(np.percentile(L, 10)), float(np.percentile(L, 90))
            c = rgba(e['color']); al = c[3] * e['opacity']
            bgc = np.median(px, 0)
            tl = lum([c[k] * al + bgc[k] * (1 - al) for k in range(3)])
            cr = contrast(tl, bg_med); worst = min(contrast(tl, p10), contrast(tl, p90))
            big = e['size'] >= 48
            need_f, need_w = (2.6, 3.0) if big else (3.5, 4.5)
            if e['src']: need_f, need_w = 2.2, 3.0
            outline = bool(e['stroke'] or e['shadow'])
            lvl = None
            if cr < need_f and not outline: lvl = 'FAIL'
            elif cr < need_w or (worst < 1.6 and (p90 - p10) > 0.25):
                lvl = 'WARN'
            if lvl:
                why = f'contrast {cr:.1f}:1' + (f', busy background (worst {worst:.1f}:1)' if worst < 1.6 and (p90 - p10) > 0.25 else '')
                (fails if lvl == 'FAIL' else warns).append(f"scene {e['scene']} t={e['t']}s: hard to read '{e['txt']}' — {why}")
                flags.append({'kind': 'legibility', 'scene': e['scene'], 't': e['t'], 'msg': why, 'box': [x0, y0, x1, y1]})

# on-screen numbers must come from the fact sheet
ff = P / 'facts.json'
if ff.exists():
    F = json.loads(ff.read_text()); known = set()
    def nums(s):
        out = []
        for m in re.findall(r'\d[\d,]*(?:\.\d+)?', bn_digits_to_int(str(s))):
            try: out.append(float(m.replace(',', '')))
            except ValueError: pass
        return out
    for f in F.get('facts', []) + F.get('math', []):
        for k in ('value', 'expect', 'claim', 'screen', 'date'):
            if k in f: known.update(nums(f[k]))
    for v in sorted({n for t in screen_txt for n in nums(t)}):
        if v <= 10 or v in known: continue
        if not any(abs(v - k) <= 0.005 * max(abs(k), 1) for k in known):
            warns.append(f'on-screen number {v:g} is not in facts.json — typo, or add the fact/derivation')

if max_len and total > max_len: fails.append(f'length {total:.1f}s > max {max_len}s')
print(f'TOTAL {total:.2f}s, {len(scenes)} scenes')
for w in warns: print('WARN ', w)
for f in fails: print('FAIL ', f)
json.dump({'flags': flags, 'warns': warns, 'fails': fails}, open(P / 'qa.json', 'w'), ensure_ascii=False)
qa = P / '.qa_pass'
if fails:
    if qa.exists(): qa.unlink()
    print(f'\n{len(fails)} failures — fix them, then re-run audit.py. Render is blocked.'); sys.exit(1)
if a.fast:
    if qa.exists(): qa.unlink()
    print(f'\nfast audit clean ({len(warns)} warnings) — run the full audit (without --fast) before rendering'); sys.exit(0)
qa.write_text(json.dumps({'hash': timeline_hash(P), 'time': time.strftime('%Y-%m-%d %H:%M'), 'total': total, 'warnings': warns}, ensure_ascii=False))
print(f'\nQA PASS ({len(warns)} warnings). Next: review.py --keys (look at every flagged frame), audio.py, render.py')
