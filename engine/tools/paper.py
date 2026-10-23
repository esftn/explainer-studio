"""Generate paper textures: img/paper.jpg (light) and img/paper_dark.jpg.
usage: python paper.py <project> [--seed 3]"""
import sys, pathlib, argparse
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def tex(base, seed, w=1160, h=2000):
    r = np.random.default_rng(seed)
    fib = gaussian_filter(r.standard_normal((h, w)), (0.6, 7)) * 3.5        # horizontal fibres
    blot = gaussian_filter(r.standard_normal((h, w)), 60) * 260              # large mottling
    grain = r.standard_normal((h, w)) * 3.0
    yy, xx = np.mgrid[0:h, 0:w]
    vig = -((xx / w - .5) ** 2 + (yy / h - .5) ** 2) * 38                    # soft vignette
    v = fib + blot + grain + vig
    img = np.clip(np.array(base)[None, None, :] + v[..., None] * np.array([1, .96, .9]), 0, 255)
    return Image.fromarray(img.astype(np.uint8))


def map_tex(path, seed=4, W=1160, H=2000):
    """Faint street-map lines (white on transparent) for the t-teal / .map background."""
    import random
    from PIL import ImageDraw
    random.seed(seed); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for _ in range(38):
        x = random.randint(-200, W + 200); y = random.randint(-200, H + 200); ang = random.choice([(1, .15), (.2, 1), (1, -.35), (.6, 1)])
        L = random.randint(500, 1800); w = random.choice([3, 4, 6, 10])
        d.line([(x, y), (x + ang[0] * L, y + ang[1] * L)], fill=(255, 255, 255, 70 if w < 6 else 95), width=w)
    for _ in range(60):
        x = random.randint(0, W); y = random.randint(0, H); sz = random.randint(30, 90)
        d.rectangle([x, y, x + sz, y + sz * .7], outline=(255, 255, 255, 35), width=2)
    im.save(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--seed', type=int, default=3)
    a = ap.parse_args(); d = pathlib.Path(a.project) / 'img'; d.mkdir(parents=True, exist_ok=True)
    tex((239, 231, 214), a.seed).save(d / 'paper.jpg', quality=88)
    tex((30, 28, 26), a.seed + 1).save(d / 'paper_dark.jpg', quality=88)
    map_tex(d / 'tex_map.png')
    print('wrote', d / 'paper.jpg', d / 'paper_dark.jpg', d / 'tex_map.png')
