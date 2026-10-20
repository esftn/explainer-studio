"""Glyph test for Bangla fonts — catches broken digits (the ১৯৯৩ bug) and missing conjuncts BEFORE building.
usage: python font_test.py [<project>] [--engine-only] [--font "Hind Siliguri"]
Checks every weight actually loads, that each Bangla digit renders with a distinct shape, and that
conjuncts shape (ligature width < sum of parts). Writes font_test.png for a visual look."""
import argparse, pathlib, sys, json
from es import ENGINE

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--engine-only', action='store_true')
ap.add_argument('--font', action='append', default=[])
a = ap.parse_args()
base = pathlib.Path(a.project).resolve() / 'fonts' if a.project else ENGINE / 'node_modules' / '@fontsource'
fams = {'Noto Sans Bengali': ('noto-sans-bengali', [500, 600, 700, 900]), 'Noto Serif Bengali': ('noto-serif-bengali', [500, 700])}
links = ''.join(f'<link rel="stylesheet" href="{(base / d / f"{w}.css").as_uri()}">' for _, (d, ws) in fams.items() for w in ws)
SAMPLE = '১৯৯৩ ২০২৫ ০১২৩৪৫৬৭৮৯ — ক্ষ জ্ঞ ন্ত্র স্ক্র শ্রী র‍্যাব হাদি কে? “উদ্ধৃতি”'
rows = ''
for fam, (_, ws) in fams.items():
    for w in ws:
        rows += f'<div style="font:{w} 54px \'{fam}\';white-space:nowrap">{fam} {w}: {SAMPLE}</div>'
for f in a.font:
    pkg = base / f.lower().replace(' ', '-') / '700.css'
    if pkg.exists(): links += f'<link rel="stylesheet" href="{pkg.as_uri()}">'
    rows += f'<div style="font:700 54px \'{f}\';white-space:nowrap">{f}: {SAMPLE}</div>'
html = f'<!doctype html><meta charset=utf-8>{links}<body style="background:#fff;padding:20px">{rows}</body>'
od = (pathlib.Path(a.project).resolve() / 'out') if a.project else ENGINE / '.cache'; od.mkdir(parents=True, exist_ok=True)
tmp = od / 'font_test.html'; tmp.write_text(html)
from playwright.sync_api import sync_playwright
problems = []
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width': 2400, 'height': 200 + 80 * 8})
    pg.goto(tmp.resolve().as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400)
    for fam, (_, ws) in list(fams.items()) + [(f, (None, [700])) for f in a.font]:
        for w in ws:
            ok = pg.evaluate("([fam,w])=>[...document.fonts].some(f=>f.family.replace(/[\"']/g,'')===fam&&String(f.weight)===String(w)&&f.status==='loaded')", [fam, w])
            r = pg.evaluate("""([fam,w])=>{const c=document.createElement('canvas').getContext('2d');
              c.font=`${w} 80px "${fam}"`; const D='০১২৩৪৫৬৭৮৯';
              const img=d=>{const cv=document.createElement('canvas');cv.width=90;cv.height=110;const x=cv.getContext('2d');
                x.font=`${w} 80px "${fam}"`;x.fillText(d,5,85);return Array.from(x.getImageData(0,0,90,110).data.filter((_,i)=>i%4==3)).join(',')};
              const sig=[...D].map(img); const dup=[];
              for(let i=0;i<10;i++)for(let j=i+1;j<10;j++) if(sig[i]===sig[j]) dup.push(D[i]+'='+D[j]);
              const blank=[...D].filter((d,i)=>!sig[i].split(',').some(v=>+v>0));
              const lig=c.measureText('ক্ষ').width < c.measureText('ক').width+c.measureText('্').width+c.measureText('ষ').width-1;
              return {dup,blank,lig}}""", [fam, w])
            if not ok: problems.append(f'{fam} {w}: not loaded')
            if r['dup']: problems.append(f'{fam} {w}: identical digit glyphs {r["dup"]}')
            if r['blank']: problems.append(f'{fam} {w}: blank digits {r["blank"]}')
            if not r['lig']: problems.append(f'{fam} {w}: conjunct ক্ষ not shaping')
    pg.screenshot(path=str(od / 'font_test.png'), full_page=True); br.close()
tmp.unlink()
print(f'{od / "font_test.png"} written — LOOK at it: ১ must be a full loop with a tail, not a broken stroke.')
if problems:
    print('FONT PROBLEMS:'); [print(' -', x) for x in problems]; sys.exit(1)
print('fonts ok')
