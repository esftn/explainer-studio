"""TakaTheory cover v2 (approved 24 Nov 2026) — the standard cover for every episode.
Writes videoNN/cover_v2.html and renders it to videoNN/out/cover_reel_9x16.png (then `finish` bakes it as frame 1).
usage (from VIDEO GEN):
  python3 _series/tools/cover_v2.py videoNN --photo images/x.jpg --chip '…' --line '…' [--hero '৳১০০'] --block 'প্রশ্ন?' \
      [--color r|g|y] [--note '…'] [--side l|r] [--out out/cover_reel_9x16.png]
Rules: hero = the episode's key number (omit if none); block = the question, never the answer; note = a short true hook.
Spec: VIDEO GEN/thumbnail_redesign/README.md (shared css: thumbnail_redesign/base.css + v2/kit.css)."""
import argparse, html, os, pathlib, sys
ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('--photo', required=True); ap.add_argument('--chip', required=True)
ap.add_argument('--line', required=True); ap.add_argument('--hero', default=''); ap.add_argument('--block', required=True)
ap.add_argument('--color', default='r', choices='rgy'); ap.add_argument('--note', default=''); ap.add_argument('--side', default='r', choices='lr')
ap.add_argument('--out', default='out/cover_reel_9x16.png')
a = ap.parse_args(); P = pathlib.Path(a.project).resolve(); ROOT = P.parent
if not (P / a.photo).exists(): sys.exit(f'missing photo {P / a.photo}')
T = os.path.relpath(ROOT / 'thumbnail_redesign', P)
R, G, Y = '#E2452B', '#1FA36B', '#FFD23F'; bc = {'r': R, 'g': G, 'y': Y}[a.color]
chipbg = Y if bc == G else '#FFFFFF'; bfg = '#111' if bc == Y else '#fff'; left = a.side == 'l'; E = html.escape
ph = a.photo.replace(' ', '%20'); btop = 800 if a.hero else 500
LOGO = '<div class="logo"><svg viewBox="0 0 100 100"><rect width="100" height="100" rx="20" fill="#00C782"/><text x="22" y="80" font-family="Noto Sans Bengali" font-weight="900" font-size="78" fill="#111214">৳</text><path d="M44 66 L58 52 L66 59 L84 38" fill="none" stroke="#F4F1EA" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><path d="M72 34 L88 33 L87 49 Z" fill="#F4F1EA"/></svg><span>টাকা থিওরি</span></div>'
arrow = ('<svg class="mk" style="left:330px;top:1500px" width="220" height="200" viewBox="0 0 220 200"><path d="M30 170 C70 150 130 110 180 40" stroke="#F4F1EA" stroke-width="12"/><path d="M190 92 L184 30 L124 46" stroke="#F4F1EA" stroke-width="12"/></svg>' if left else
         '<svg class="mk" style="left:560px;top:1500px" width="220" height="200" viewBox="0 0 220 200"><path d="M190 170 C150 150 90 110 40 40" stroke="#F4F1EA" stroke-width="12"/><path d="M30 92 L36 30 L96 46" stroke="#F4F1EA" stroke-width="12"/></svg>')
note = (arrow + f'<div class="note n-g" style="{"left" if left else "right"}:90px;top:1690px;font-size:62px;transform:rotate({3 if left else -3}deg)">{E(a.note)}</div>') if a.note else ''
hero = f'<div class="c hero" style="top:460px;white-space:nowrap"><span id="hero">{E(a.hero)}</span></div>' if a.hero else ''
page = f'''<!doctype html><html lang="bn"><head><meta charset="utf-8">
<link rel="stylesheet" href="fonts/tiro-bangla/400.css"><link rel="stylesheet" href="fonts/noto-sans-bengali/900.css"><link rel="stylesheet" href="{T}/brand/fonts/baloo-da-2/800.css"><link rel="stylesheet" href="{T}/base.css"><link rel="stylesheet" href="{T}/v2/kit.css">
<style>.ph{{top:300px;object-position:50% 35%;-webkit-mask-image:linear-gradient(transparent 0,#000 220px)}}.vig{{background:linear-gradient(rgba(10,8,6,.88) 0,rgba(10,8,6,.75) 30%,rgba(10,8,6,.3) 50%,rgba(10,8,6,0) 62%,rgba(10,8,6,0) 82%,rgba(10,8,6,.55))}}</style></head><body>
<div class="bg" style="background-image:url('{ph}')"></div><img class="ph" src="{ph}"><div class="vig"></div>
{LOGO}
<div class="c" style="top:230px"><span class="chip" style="background:{chipbg};color:#111">{E(a.chip)}</span></div>
<div class="c line" style="top:350px">{E(a.line)}</div>
{hero}
<div class="c" style="top:{btop}px"><span class="blk" id="blk" style="background:{bc};color:{bfg}">{E(a.block)}</span></div>
{note}
<script>window.COVER_READY=false;document.fonts.ready.then(()=>{{for(const [id,min] of [['hero',150],['blk',96]]){{const e=document.getElementById(id);if(!e)continue;let s=parseFloat(getComputedStyle(e).fontSize);
while(e.getBoundingClientRect().width>990&&s>min){{s-=6;e.style.fontSize=s+'px'}}}}window.COVER_READY=true}})</script>
</body></html>'''
src = P / 'cover_v2.html'; src.write_text(page, encoding='utf-8'); print('wrote', src.name)
import json                                                                    # hub: keep the words so 00_HUB/COMMANDS.md can re-make this cover
(P / 'docs').mkdir(exist_ok=True)
(P / 'docs' / 'cover_v2.json').write_text(json.dumps({k: getattr(a, k) for k in ('photo', 'chip', 'line', 'hero', 'block', 'color', 'note', 'side')}, ensure_ascii=False, indent=1), encoding='utf-8')
from playwright.sync_api import sync_playwright
exe = os.environ.get('ES_CHROME') or next((p for p in (os.path.expanduser('~/chrome/sp/chromium'), '/tmp/sp/chromium') if os.path.exists(p)), None)
kw = {'executable_path': exe, 'args': ['--no-sandbox', '--disable-gpu', '--allow-file-access-from-files']} if exe else {}
out = P / a.out; out.parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(**kw); pg = b.new_page(viewport={'width': 1080, 'height': 1920}); errs = []
    pg.on('requestfailed', lambda r: errs.append('missing ' + r.url))
    pg.goto(src.as_uri()); pg.wait_for_function('window.COVER_READY', timeout=8000); pg.wait_for_timeout(300)
    pg.screenshot(path=str(out)); b.close()
for e in errs: print('WARN', e)
print('COVER V2', 'WARN' if errs else 'PASS', out.relative_to(P))
