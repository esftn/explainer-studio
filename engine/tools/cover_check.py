"""Objective checks for a cover page (v0.7). Prints COVER PASS / COVER FAIL; exit 1 on FAIL.
usage: python3 engine/tools/cover_check.py <project> cover_<name>.html

FAIL  title font < 140 px · title > 8 words or > 3 lines · title outside y 440–1500 (centre-square crop)
      any text outside the 4:5 zone (y 285–1635) · other text < 44 px · more than 4 text elements
      text contrast < 3:1 (title) / < 4.5:1 (smaller text) · no hero or hero < 25 % of the 4:5 zone
      more than 2 colours that are not in the episode palette (docs/look.json)
      SPOILER: a number on the cover that the script only says in its second half (the answer), or a phrase in project.json "cover_spoilers"
WARN  title < 150 px · 8 words · text outside the centre square · hero < 33 % · no clickable device (mark / badge / ? / arrow) ·
      text over a photo (contrast not measurable: look at the sheet) · cover words copied from the last scene
The checker cannot judge taste: still LOOK at out/_cover_<name>_sheet.jpg (thumbnail tile) before sending.
"""
import json, pathlib, re, sys
from playwright.sync_api import sync_playwright

ZONE = (285, 1635); SQ = (420, 1500); TITLE_Y = (440, 1500)
P = pathlib.Path(sys.argv[1]).resolve(); page = P / sys.argv[2]
JS = r"""() => {
  const rgb = s => { const m = (s||'').match(/rgba?\(([^)]+)\)/); if (!m) return null; const v = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
                     return (v.length > 3 && v[3] === 0) ? null : v.slice(0,3).map(Math.round); };
  const bgOf = e => { for (let p = e; p; p = p.parentElement) { const c = rgb(getComputedStyle(p).backgroundColor); if (c) return {c, el: p}; } return null; };
  const overImg = e => { const r = e.getBoundingClientRect(), x = (r.left+r.right)/2, y = (r.top+r.bottom)/2;
                         return document.elementsFromPoint(x, y).some(n => n.tagName === 'IMG' && !e.contains(n)); };
  const out = {texts: [], heroes: [], devices: [], colours: []};
  const cvOf = e => { const p = e.closest('[data-cv]'); return p ? p.dataset.cv : ''; };
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    for (const k of ['color', 'backgroundColor', 'borderTopColor', 'webkitTextStrokeColor', 'fill', 'stroke']) {
      if (k === 'borderTopColor' && parseFloat(cs.borderTopWidth) === 0) continue;
      if ((k === 'fill' || k === 'stroke') && !(e instanceof SVGElement)) continue;
      if (k === 'color' && ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
      const c = rgb(cs[k]); if (c) out.colours.push(c);
    }
    const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    if (!own) continue;
    const r = e.getBoundingClientRect(); const bg = bgOf(e);
    out.texts.push({txt: own, cv: cvOf(e), size: parseFloat(cs.fontSize), top: r.top, bot: r.bottom, left: r.left, right: r.right,
                    color: rgb(cs.color), bg: bg ? bg.c : null, overImg: overImg(e), qmark: e.classList.contains('qmark') || /^[?!]$/.test(own)});
  }
  for (const e of document.querySelectorAll('[data-cv="hero"]')) { const r = e.getBoundingClientRect(); out.heroes.push([r.left, r.top, r.right, r.bottom]); }
  for (const e of document.querySelectorAll('[data-cv="mark"],[data-cv="badge"],.qmark,.mark,.badge')) out.devices.push(e.className);
  return out;
}"""

def lum(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= .03928 else ((v / 255 + .055) / 1.055) ** 2.4
    return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2])
def cr(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + .05) / (lb + .05)
hexrgb = lambda h: [int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
BN = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
nums = lambda s: {re.sub(r'[,.]$', '', x) for x in re.findall(r'[0-9][0-9,.]*', s.translate(BN))}

with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto('file://' + str(page)); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(500)
    try: pg.wait_for_function('window.COVER_READY || !document.querySelector(".title")', timeout=4000)
    except Exception: pass
    D = pg.evaluate(JS); b.close()

fails, warns = [], []
texts = [t for t in D['texts'] if not t['qmark']]
title = [t for t in texts if t['cv'] == 'title']
others = [t for t in texts if t['cv'] != 'title']
if not title: fails.append('no title found (mark the title block data-cv="title")')
else:
    ts = min(t['size'] for t in title); words = sum(len(t['txt'].split()) for t in title); top = min(t['top'] for t in title); bot = max(t['bot'] for t in title)
    if ts < 140: fails.append(f'title {ts:.0f}px < 140 px: unreadable at feed/thumbnail size; shorten the title so it can be bigger')
    elif ts < 150: warns.append(f'title {ts:.0f}px (aim for >= 150 px)')
    if words > 8: fails.append(f'title has {words} words (max 7): cut it')
    elif words == 8: warns.append('title has 8 words (aim for <= 7)')
    if len(title) > 3: fails.append(f'title on {len(title)} lines (max 3)')
    if top < TITLE_Y[0] or bot > TITLE_Y[1]: fails.append(f'title spans y {top:.0f}–{bot:.0f}: must stay inside y {TITLE_Y[0]}–{TITLE_Y[1]} (profile-grid square crop)')
n_el = (1 if title else 0) + len(others)
if n_el > 4: fails.append(f'{n_el} text elements (max 4: title + note + up to 2 labels/badge): a cover is read in one second')
for t in texts:
    tag = f"'{t['txt'][:24]}'"
    if t['top'] < ZONE[0] or t['bot'] > ZONE[1]: fails.append(f'{tag} outside the 4:5 feed zone (y {ZONE[0]}–{ZONE[1]})')
    elif t['cv'] != 'title' and (t['top'] < SQ[0] or t['bot'] > SQ[1]): warns.append(f'{tag} outside the centre square (y {SQ[0]}–{SQ[1]}): cut in the profile grid')
    if t['cv'] != 'title' and t['size'] < 44: fails.append(f'{tag} {t["size"]:.0f}px < 44 px: invisible at thumbnail size')
    if t['overImg'] and (not t['bg'] or t['bg'] == [0, 0, 0] and False): warns.append(f'{tag} sits over a photo: check its contrast on the sheet')
    elif t['bg'] and t['color']:
        need = 3.0 if t['size'] >= 70 else 4.5; c = cr(t['color'], t['bg'])
        if c < need: fails.append(f'{tag} contrast {c:.1f}:1 < {need}:1')
if not D['heroes']: fails.append('no hero image / vector (data-cv="hero"): covers need one big picture to be clickable')
else:
    x0 = min(h[0] for h in D['heroes']); y0 = max(min(h[1] for h in D['heroes']), ZONE[0]); x1 = max(h[2] for h in D['heroes']); y1 = min(max(h[3] for h in D['heroes']), ZONE[1])
    area = sum(max(0, min(h[2], 1080) - max(h[0], 0)) * max(0, min(h[3], ZONE[1]) - max(h[1], ZONE[0])) for h in D['heroes']) / (1080 * (ZONE[1] - ZONE[0]))
    if area < .25: fails.append(f'hero covers {area:.0%} of the 4:5 zone (min 25 %, aim 35–50 %): make it bigger')
    elif area < .33: warns.append(f'hero covers {area:.0%} of the 4:5 zone (aim 35–50 %)')
if not D['devices']: warns.append('no clickable device (marker circle, arrow, "?", VS badge): Vox covers always point at something')
look = json.loads((P / 'docs' / 'look.json').read_text()) if (P / 'docs' / 'look.json').exists() else None
if look:
    base = [hexrgb(h) for h in look['colors'].values()]; pap = hexrgb(look['colors']['paper'])
    pal = base + [[round(c[i] * (1 - k) + pap[i] * k) for i in range(3)] for c in base for k in (.14, .28)] + [[255, 255, 255], [0, 0, 0]]   # softened tints are allowed
    odd = {tuple(c) for c in D['colours'] if min(sum(abs(a - b) for a, b in zip(c, p)) for p in pal) > 24}
    # colour-mix tints of palette colours are fine: accept colours on the line between a palette colour and transparent/bg
    if len(odd) > 2: fails.append(f'{len(odd)} colours outside the episode palette ({look["id"]}): ' + ', '.join('#%02x%02x%02x' % c for c in list(odd)[:5]))
    elif odd: warns.append('off-palette colour(s): ' + ', '.join('#%02x%02x%02x' % c for c in odd))
else: warns.append('no docs/look.json: palette not checked')
# ---- spoilers
cover_txt = ' '.join(t['txt'] for t in texts)
scr = next((json.loads(f.read_text()) for f in (P / 'script.json', P / 'docs' / 'script.json') if f.exists()), None)
if isinstance(scr, dict) and scr:
    keys = sorted(scr, key=lambda k: int(re.sub(r'\D', '', k) or 0)); half = len(keys) // 2
    early = ' '.join(str(scr[k]) for k in keys[:half]); late = ' '.join(str(scr[k]) for k in keys[half:])
    for n in sorted(nums(cover_txt)):
        if n in nums(late) and n not in nums(early) and len(n) > 1:
            fails.append(f'SPOILER: "{n}" is said only in the second half of the script (the answer): ask the question, don\'t show the result')
    last = str(scr[keys[-1]]).split(); tw = cover_txt.split()
    if any(' '.join(tw[i:i + 3]) in ' '.join(last) for i in range(max(0, len(tw) - 2))):
        warns.append('cover repeats 3+ words of the last scene (the conclusion): check it does not give the ending away')
else: warns.append('no script.json: spoiler check skipped')
for s in (json.loads((P / 'project.json').read_text()).get('cover_spoilers', []) if (P / 'project.json').exists() else []):
    if s and s in cover_txt: fails.append(f'SPOILER: cover shows "{s}" (listed in project.json cover_spoilers)')
for w in warns: print('WARN', w)
for f in fails: print('FAIL', f)
print('COVER FAIL' if fails else 'COVER PASS', f'({len(fails)} fail, {len(warns)} warn) — now LOOK at out/_cover_{page.stem.replace("cover_", "")}_sheet.jpg')
sys.exit(1 if fails else 0)
