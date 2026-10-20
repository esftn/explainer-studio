"""Contact sheets for visual review (Claude must LOOK at every sheet before render).
usage: python review.py <project> [--step 1.0] [--times 3.2,10.5] [--scene 7]
Writes out/review_N.jpg (7x3 frames for 9:16, 4x5 for 16:9, timestamp + scene number burned in)."""
import argparse
from PIL import Image, ImageDraw
from es import project, page, size

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--step', type=float, default=1.0)
ap.add_argument('--times'); ap.add_argument('--scene', type=int)
a = ap.parse_args(); P = project(a.project); (P / 'out').mkdir(exist_ok=True)
Wd, Hd = size(P); TW, TH = (480, 270) if Wd > Hd else (300, 533); C, R = (4, 5) if Wd > Hd else (7, 3)
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
        im = Image.open(f).convert('RGB').resize((TW, TH)); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 112, 22], fill='black'); d.text((4, 5), f'{t:.1f}s  S{sc}', fill='yellow'); ims.append(im)
    (P / 'out' / '_r.png').unlink(missing_ok=True)
n = 0
for k in range(0, len(ims), C * R):
    sh = Image.new('RGB', (C * TW, R * TH), 'white')
    for j, im in enumerate(ims[k:k + C * R]): sh.paste(im, ((j % C) * TW, (j // C) * TH))
    sh.save(P / 'out' / f'review_{k // (C * R)}.jpg', quality=80); n += 1
print(f'{len(ims)} frames → out/review_0..{n - 1}.jpg')
