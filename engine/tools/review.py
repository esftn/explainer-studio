"""Contact sheets for visual review.
usage: python review.py <project> [--step 1.0] [--times 3.2,10.5] [--scene 7]
       python review.py <project> --keys          (run audit.py first)

Default: out/review_N.jpg (7x3 frames, timestamp + scene burned in).
--keys : out/keys_N.jpg — the key-moment sheet. One frame for every graphic tied to a spoken word (data-say),
         every moment audit.py flagged (red box + reason), and the middle of each scene; under each frame the
         line being spoken at that moment with the current word highlighted. This is the sheet Claude reads
         instead of all frames, and the sheet the creator gets next to the preview."""
import argparse, base64, html, io, json, pathlib
from PIL import Image, ImageDraw
from es import project, page, cfg, load_vo, strip_tags, BREAK_PUNCT, TOOLS

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--step', type=float, default=1.0)
ap.add_argument('--times'); ap.add_argument('--scene', type=int); ap.add_argument('--keys', action='store_true')
a = ap.parse_args(); P = project(a.project); (P / 'out').mkdir(exist_ok=True)


def said(vo, n, t):
    """phrase spoken at clip time t, with the current word marked."""
    W = vo['words'][n] if n is not None and n < len(vo['words']) else []
    if not W or t < -0.2: return '' if not W else '…'
    cur = max((i for i, w in enumerate(W) if w[1] <= t + 0.05), default=0)
    s = cur
    while s > 0 and W[s - 1][0][-1:] not in BREAK_PUNCT: s -= 1
    e = cur
    while e < len(W) - 1 and W[e][0][-1:] not in BREAK_PUNCT: e += 1
    return ' '.join((f'<b>{html.escape(W[i][0])}</b>' if i == cur else html.escape(W[i][0])) for i in range(s, e + 1))


if not a.keys:
    with page(P) as pg:
        T = pg.evaluate('TOTAL'); S = pg.evaluate('SCENES')
        if a.times: ts = [float(x) for x in a.times.split(',')]
        elif a.scene:
            s = S[a.scene - 1]; ts = []; t = s['start'] + 0.5
            while t < s['start'] + s['dur']: ts.append(round(t, 2)); t += min(a.step, 0.5)
        else:
            ts = []; t = 0.6
            while t < T: ts.append(round(t, 2)); t += a.step
            ts.append(round(T - 0.05, 2))
        ims = []
        for t in ts:
            pg.evaluate(f'seek({t})'); f = P / 'out' / '_r.png'; pg.screenshot(path=str(f))
            sc = next((i + 1 for i, s in enumerate(S) if s['start'] <= t < s['start'] + s['dur']), len(S))
            im = Image.open(f).convert('RGB').resize((300, 533)); d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 112, 22], fill='black'); d.text((4, 5), f'{t:.1f}s  S{sc}', fill='yellow'); ims.append(im)
        (P / 'out' / '_r.png').unlink(missing_ok=True)
    C, R = 7, 3; n = 0
    for k in range(0, len(ims), C * R):
        sh = Image.new('RGB', (C * 300, R * 533), 'white')
        for j, im in enumerate(ims[k:k + C * R]): sh.paste(im, ((j % C) * 300, (j // C) * 533))
        sh.save(P / 'out' / f'review_{k // (C * R)}.jpg', quality=80); n += 1
    print(f'{len(ims)} frames → out/review_0..{n - 1}.jpg'); raise SystemExit

# ---------- key-moment sheet ----------
qa = json.loads((P / 'qa.json').read_text()) if (P / 'qa.json').exists() else {'flags': []}
vo = load_vo(P); off = cfg(P).get('voOffset', 0.3)
items = []
with page(P) as pg:
    S = pg.evaluate('SCENES')
    says = pg.evaluate("""[...document.querySelectorAll('.scene')].flatMap((s,i)=>[...s.querySelectorAll('[data-say-t]')]
        .map(e=>({scene:i+1,lt:+e.dataset.sayT+(+(e.dataset.d||0.7))+0.15,ct:+e.dataset.sayT+0.06,say:e.dataset.say})))""")
    for x in says: items.append({'scene': x['scene'], 't': S[x['scene'] - 1]['start'] + x['lt'], 'ct': S[x['scene'] - 1]['start'] + x['ct'], 'label': f"lands on “{x['say']}”", 'flag': None})
    for f in qa.get('flags', []): items.append({'scene': f['scene'], 't': f['t'], 'label': f['msg'], 'flag': f.get('box')})
    for i, s in enumerate(S):
        if not any(it['scene'] == i + 1 for it in items): items.append({'scene': i + 1, 't': s['start'] + s['dur'] * 0.6, 'label': 'scene', 'flag': None})
    items.sort(key=lambda x: x['t'])
    for it in items:
        pg.evaluate(f"seek({it['t']})")
        im = Image.open(io.BytesIO(pg.screenshot(type='jpeg', quality=85))).convert('RGB').resize((270, 480))
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=82); it['img'] = base64.b64encode(buf.getvalue()).decode()
        s = S[it['scene'] - 1]; it['said'] = said(vo, s['vo'], it.get('ct', it['t']) - s['start'] - off)
    fonts = ''.join(f'<link rel="stylesheet" href="{(P / "fonts" / f).as_uri()}">' for f in ('tiro-bangla/400.css', 'noto-sans-bengali/600.css') if (P / 'fonts' / f).exists())
    PER = 12; nsh = 0
    for k in range(0, len(items), PER):
        cells = []
        for it in items[k:k + PER]:
            box = ''
            if it['flag']:
                l, t, r, b = it['flag']; sx = 270 / 1080
                box = f'<div class="bx" style="left:{l * sx - 3:.0f}px;top:{t * sx - 3:.0f}px;width:{(r - l) * sx + 6:.0f}px;height:{(b - t) * sx + 6:.0f}px"></div>'
            cls = 'c fl' if it['flag'] else 'c'
            cells.append(f'<div class="{cls}"><div class="im"><img src="data:image/jpeg;base64,{it["img"]}">{box}'
                         f'<span class="ts">{it["t"]:.1f}s · S{it["scene"]}</span></div>'
                         f'<div class="lb">{html.escape(it["label"])}</div><div class="sd">{it["said"] or "—"}</div></div>')
        doc = (f'<html><head><meta charset="utf-8">{fonts}<style>body{{margin:0;background:#fff;font:15px "Noto Sans Bengali","Tiro Bangla",sans-serif;width:1160px}}'
               '.g{display:grid;grid-template-columns:repeat(4,282px);gap:8px;padding:8px}.c{border:1px solid #ccc;padding:5px}.fl{border:3px solid #e01e1e;padding:3px}'
               '.im{position:relative;width:270px;height:480px}.im img{width:270px;height:480px;display:block}'
               '.bx{position:absolute;border:3px solid #e01e1e;box-shadow:0 0 0 2px #fff}'
               '.ts{position:absolute;left:0;top:0;background:#000;color:#ffd23f;font:12px monospace;padding:2px 5px}'
               '.lb{font:600 12px sans-serif;color:#b00;margin:4px 0 2px}.c:not(.fl) .lb{color:#555}.sd{line-height:1.45;min-height:44px}.sd b{background:#ffe066}'
               f'</style></head><body><div class="g">{"".join(cells)}</div></body></html>')
        f = P / 'out' / f'_keys_{nsh}.html'; f.write_text(doc, encoding='utf-8')
        sp = pg.context.browser.new_page(viewport={'width': 1160, 'height': 800}); sp.goto(f.as_uri())
        sp.evaluate('document.fonts.ready'); sp.wait_for_timeout(300)
        sp.screenshot(path=str(P / 'out' / f'keys_{nsh}.jpg'), full_page=True, type='jpeg', quality=82); sp.close(); f.unlink()
        nsh += 1
nflag = sum(1 for it in items if it['flag'])
print(f'{len(items)} key moments ({nflag} flagged) → out/keys_0..{nsh - 1}.jpg')
