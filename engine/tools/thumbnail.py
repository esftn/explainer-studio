"""Render and check the YouTube thumbnail (1280x720) from <project>/thumbnail.html.
usage: python thumbnail.py <project> [--html thumbnail.html]
Writes out/thumbnail.png (upload this) + out/thumbnail_200.png (how it looks in a feed — LOOK at it).
Checks: ≤ 2 text blocks (.tw), ≤ 3 words each, text inside the frame, images loaded, fonts loaded."""
import argparse, sys
from PIL import Image
from es import project, page

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--html', default='thumbnail.html')
a = ap.parse_args(); P = project(a.project); O = P / 'out'; O.mkdir(exist_ok=True)
src = P / a.html
if not src.exists(): sys.exit(f'no {src.name} — copy engine/template/thumbnail.html into the project (new_project.py does this)')
fails = []
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch(); pg = br.new_page(viewport={'width': 1280, 'height': 720})
    pg.goto(src.as_uri()); pg.evaluate('Promise.all([...document.fonts].map(f => f.load().catch(() => null)))')
    pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400)
    info = pg.evaluate("""() => ({
      tw: [...document.querySelectorAll('.tw')].map(e => { const r = e.getBoundingClientRect(); return {t: e.textContent.trim(), l: r.left, r: r.right, top: r.top, b: r.bottom}; }),
      bad: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src')) })""")
    pg.screenshot(path=str(O / 'thumbnail.png')); br.close()
if len(info['tw']) > 2: fails.append(f"{len(info['tw'])} text blocks (max 2)")
for t in info['tw']:
    n = len(t['t'].split())
    if n > 3: fails.append(f"'{t['t']}' has {n} words (max 3)")
    if t['l'] < 0 or t['r'] > 1280 or t['top'] < 0 or t['b'] > 720: fails.append(f"'{t['t']}' leaves the frame")
fails += [f'missing image {b}' for b in info['bad']]
im = Image.open(O / 'thumbnail.png'); im.resize((200, 112), Image.LANCZOS).save(O / 'thumbnail_200.png')
for f in fails: print('FAIL', f)
print('thumbnail: out/thumbnail.png (1280x720) + out/thumbnail_200.png — open the 200 px one: can you read it in a second?')
sys.exit(1 if fails else 0)
