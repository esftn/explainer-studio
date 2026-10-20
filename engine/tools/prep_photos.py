"""Prepare photos: resize into img/, build numbered contact sheets, make sticker cutouts.
usage:
  python prep_photos.py <project>                       # photos/* -> img/p_XX.jpg + img/_sheet_N.jpg + img/_index.txt
  python prep_photos.py <project> --cut p_03 p_11       # img/p_03.jpg -> img/cut_p_03.png (white sticker outline)
  python prep_photos.py <project> --cut p_03 --no-outline
Pick photos by LOOKING at the contact sheets (Read the jpg), never by filename."""
import argparse, pathlib, sys
from PIL import Image, ImageDraw, ImageOps

ap = argparse.ArgumentParser(); ap.add_argument('project')
ap.add_argument('--cut', nargs='*'); ap.add_argument('--no-outline', action='store_true')
ap.add_argument('--max', type=int, default=1600); ap.add_argument('--model', default='u2net_human_seg')
a = ap.parse_args()
P = pathlib.Path(a.project).resolve(); IMG = P / 'img'; IMG.mkdir(exist_ok=True)
EXT = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.jfif'}

if a.cut:
    try:
        from rembg import remove, new_session
    except ImportError:
        sys.exit('rembg not installed — run setup.sh (WITH_CUTOUTS=1)')
    import numpy as np
    from scipy.ndimage import binary_dilation
    sess = new_session(a.model)
    for name in a.cut:
        src = next((f for f in IMG.glob(name + '.*')), None)
        if not src: print('not found', name); continue
        im = Image.open(src).convert('RGB')
        cut = remove(im, session=sess)                     # RGBA
        al = np.array(cut)[..., 3]
        if al.mean() < 3: print('WARN empty cutout', name); continue
        if not a.no_outline:
            m = al > 120; r = max(6, im.width // 110)
            yy, xx = np.ogrid[-r:r + 1, -r:r + 1]; disk = xx * xx + yy * yy <= r * r
            ring = binary_dilation(m, disk)
            base = Image.new('RGBA', cut.size, (0, 0, 0, 0))
            white = Image.new('RGBA', cut.size, (255, 255, 255, 255))
            base.paste(white, mask=Image.fromarray((ring * 255).astype('uint8')))
            base.alpha_composite(cut); cut = base
        bb = cut.getbbox(); cut = cut.crop(bb)
        out = IMG / f'cut_{name}.png'; cut.save(out); print('cutout', out, cut.size)
    sys.exit()

srcs = sorted(f for f in (P / 'photos').rglob('*') if f.suffix.lower() in EXT)
if not srcs: sys.exit('no photos in photos/')
index, thumbs = [], []
for i, f in enumerate(srcs, 1):
    try:
        im = ImageOps.exif_transpose(Image.open(f)).convert('RGB')
    except Exception as e:
        print('skip', f.name, e); continue
    if min(im.size) < 500: print(f'WARN low-res {f.name} {im.size} — avoid using it large')
    im.thumbnail((a.max, a.max)); name = f'p_{i:02d}'
    im.save(IMG / f'{name}.jpg', quality=90)
    index.append(f'{name}\t{f.name}\t{im.size[0]}x{im.size[1]}')
    t = im.copy(); t.thumbnail((300, 300)); c = Image.new('RGB', (300, 330), 'white'); c.paste(t, ((300 - t.width) // 2, 0))
    d = ImageDraw.Draw(c); d.rectangle([0, 300, 300, 330], fill='black'); d.text((6, 308), f'{name} {im.size[0]}x{im.size[1]}', fill='yellow')
    thumbs.append(c)
(IMG / '_index.txt').write_text('\n'.join(index) + '\n')
C, R = 6, 5
for k in range(0, len(thumbs), C * R):
    sh = Image.new('RGB', (C * 300, R * 330), 'white')
    for j, t in enumerate(thumbs[k:k + C * R]): sh.paste(t, ((j % C) * 300, (j // C) * 330))
    sh.save(IMG / f'_sheet_{k // (C * R)}.jpg', quality=80)
print(f'{len(index)} photos -> img/, sheets: img/_sheet_*.jpg, index: img/_index.txt (keep source + credit for each one you use)')
