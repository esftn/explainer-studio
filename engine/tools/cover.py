"""Render a designed cover page to 9:16 + 4:5 PNGs and a review sheet (see docs/cover-design.md).
usage: python cover.py <project> cover_<name>.html
Output: out/_cover_<name>_9x16.png, out/_cover_<name>_4x5.png, out/_cover_<name>_sheet.jpg
        (sheet = 9:16 · 4:5 crop · centre square · phone-thumbnail size, so you can judge every crop at once)"""
import argparse, pathlib
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('page')
a = ap.parse_args(); P = pathlib.Path(a.project).resolve(); src = P / a.page
name = src.stem.replace('cover_', '') or 'cover'; (P / 'out').mkdir(exist_ok=True)
full = P / 'out' / f'_cover_{name}_9x16.png'
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('requestfailed', lambda r: errs.append('missing ' + r.url))
    pg.goto('file://' + str(src)); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(600)
    if pg.evaluate("!!document.querySelector('.title') && document.querySelector('script') !== null && typeof window.COVER_READY === 'undefined'"):
        try: pg.wait_for_function('window.COVER_READY', timeout=4000)      # kit covers fit their title first
        except Exception: pass
    pg.screenshot(path=str(full)); b.close()
for e in errs: print('WARN', e)
im = Image.open(full).convert('RGB')
f45 = im.crop((0, 285, 1080, 1635)); f45.save(P / 'out' / f'_cover_{name}_4x5.png')
sq = im.crop((0, 420, 1080, 1500))
tiles = [(im.resize((450, 800)), '9:16 reel'), (f45.resize((450, 562)), '4:5 feed'), (sq.resize((450, 450)), 'square grid'), (im.resize((135, 240)), 'thumbnail size')]
W = sum(t.width for t, _ in tiles) + 20 * (len(tiles) + 1); sheet = Image.new('RGB', (W, 860), (240, 236, 228)); d = ImageDraw.Draw(sheet); x = 20
for t, lab in tiles:
    sheet.paste(t, (x, 40)); d.text((x, 14), lab, fill=(30, 30, 30)); x += t.width + 20
sheet.save(P / 'out' / f'_cover_{name}_sheet.jpg', quality=88)
print('wrote', full.name, f'_cover_{name}_4x5.png', f'_cover_{name}_sheet.jpg')
print(f'next: python3 engine/tools/cover_check.py {a.project} {a.page}   (must print COVER PASS)')
