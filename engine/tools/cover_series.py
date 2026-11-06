"""Series cover (v0.8): one cover per episode in the TakaTheory channel layout (decided 7 Nov 2026 from channel data).
Full-bleed real photo + top vignette, a small chip, one white line and a big rotated colour block (the question).
Writes cover_<name>.html in the project, then run cover.py + cover_check.py as usual (or pass --render).

usage: python3 engine/tools/cover_series.py videoNN --photo images/x.jpg --chip '১০০ টাকার বাজার' \
          --line 'সুপারশপের' --block 'লাভ কত?' [--name A] [--dy 0] [--px 50] [--block-size 164] \
          [--block-bg c2 --chip-bg c4] [--render]
  --dy     shift the photo down (px) so faces/subject sit below the title (the top is filled with a blurred copy)
  --px     horizontal focus of the photo in % (0 = left, 100 = right)
  --block-bg / --chip-bg   palette role (c1..c4) or a hex; default = the two brightest colours of docs/look.json
Rules: the block must fit on ONE line (shorten it or move words into --line); never show the answer;
faces stay below y ~ 830; bright accents only (no navy/violet/dark-brown base)."""
import argparse, colorsys, html, json, pathlib, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('--photo', required=True)
ap.add_argument('--chip', required=True); ap.add_argument('--line', required=True); ap.add_argument('--block', required=True)
ap.add_argument('--name', default='A'); ap.add_argument('--dy', type=int, default=0); ap.add_argument('--px', type=int, default=50)
ap.add_argument('--block-size', type=int, default=164); ap.add_argument('--block-bg'); ap.add_argument('--chip-bg')
ap.add_argument('--render', action='store_true')
a = ap.parse_args(); P = pathlib.Path(a.project).resolve()
photo = (P / a.photo)
if not photo.exists(): sys.exit(f'missing photo {photo}')

hx = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
def lum(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= .03928 else ((v / 255 + .055) / 1.055) ** 2.4
    return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2])
def ink_for(bg):   # black or white text, whichever contrasts more
    L = lum(hx(bg)); return '#111111' if (L + .05) / (lum((17, 17, 17)) + .05) >= 1.05 / (L + .05) else '#ffffff'
look = json.loads((P / 'docs' / 'look.json').read_text()) if (P / 'docs' / 'look.json').exists() else {'colors': {'c1': '#FFD23F', 'c2': '#E2452B', 'c3': '#1F7F79', 'c4': '#FFFFFF'}}
cols = {k: v for k, v in look['colors'].items() if k.startswith('c')}
def vivid(h):   # bright + saturated first; dark colours (navy, plum, forest) last
    r, g, b = (x / 255 for x in hx(h)); hh, ll, ss = colorsys.rgb_to_hls(r, g, b); return (ll > .32) * 2 + ss * (ll > .32) + lum(hx(h))
ranked = sorted(cols.values(), key=vivid, reverse=True)
pick = lambda v, i: (cols.get(v, v) if v else ranked[min(i, len(ranked) - 1)])
bbg, cbg = pick(a.block_bg, 0), pick(a.chip_bg, 1)
if lum(hx(bbg)) < .12: print(f'WARN block colour {bbg} is dark: the series uses bright accents (pass --block-bg)')
bfg, cfg = ink_for(bbg), ink_for(cbg)
paper = look['colors'].get('paper', '#F6EFDD')
e = html.escape
blk = e(a.block[:-1]) + '<span class="qmark">?</span>' if a.block.endswith('?') else e(a.block)
rel = pathlib.Path(a.photo).as_posix(); TOP = 330; mask = 140 if a.dy else 0
e = html.escape
page = f"""<!doctype html><html lang="bn"><head><meta charset="utf-8">
<link rel="stylesheet" href="fonts/tiro-bangla/400.css">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#111;font-family:'Tiro Bangla',serif}}
.bg{{position:absolute;inset:-60px;background:url('{rel}') center top/cover;filter:blur(38px) brightness(.62) saturate(1.15)}}
.ph{{position:absolute;left:0;top:{a.dy}px;width:1080px;height:1920px;object-fit:cover;object-position:{a.px}% top;
  -webkit-mask-image:linear-gradient(transparent 0,#000 {mask}px)}}
.vig{{position:absolute;inset:0;background:linear-gradient(rgba(10,8,6,.62),rgba(10,8,6,.30) 34%,rgba(10,8,6,0) 50%,rgba(10,8,6,0) 80%,rgba(10,8,6,.45))}}
.t{{position:absolute;left:60px;width:960px;text-align:center}}
.chip{{display:inline-block;background:{cbg};color:{cfg};font-size:72px;line-height:1.22;padding:4px 30px 14px;box-shadow:8px 8px 0 #000;transform:rotate(-1.2deg)}}
.line{{color:{paper};font-size:116px;line-height:1.2;text-shadow:0 4px 22px rgba(0,0,0,.85),0 2px 4px rgba(0,0,0,.6)}}
.blk{{display:inline-block;background:{bbg};color:{bfg};font-size:{a.block_size}px;line-height:1.18;padding:0 34px 18px;box-shadow:10px 10px 0 #000;transform:rotate(-1.5deg);white-space:nowrap}}
</style></head><body>
<div class="bg"></div><img class="ph" data-cv="hero" src="{rel}"><div class="vig"></div>
<div class="t" style="top:{TOP}px"><span class="chip" data-cv="label">{e(a.chip)}</span></div>
<div class="t line" data-cv="note" style="top:{TOP + 125}px">{e(a.line)}</div>
<div class="t" style="top:{TOP + 270}px"><span class="blk" data-cv="title">{blk}</span></div>
<script>window.COVER_READY=false;document.fonts.ready.then(()=>{{const b=document.querySelector('.blk');let s={a.block_size};
while(b.getBoundingClientRect().width>1000&&s>140){{s-=4;b.style.fontSize=s+'px'}}window.COVER_READY=true}})</script>
</body></html>"""
out = P / f'cover_{a.name}.html'; out.write_text(page, encoding='utf-8')
print('wrote', out.name, f'(block {bbg} / chip {cbg})')
if a.render:
    T = pathlib.Path(__file__).parent
    subprocess.run([sys.executable, str(T / 'cover.py'), str(P), out.name], check=True)
    sys.exit(subprocess.run([sys.executable, str(T / 'cover_check.py'), str(P), out.name]).returncode)
print(f'next: python3 engine/tools/cover.py {a.project} {out.name} && python3 engine/tools/cover_check.py {a.project} {out.name}')
