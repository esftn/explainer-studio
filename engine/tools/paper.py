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


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--seed', type=int, default=3)
    a = ap.parse_args(); d = pathlib.Path(a.project) / 'img'; d.mkdir(parents=True, exist_ok=True)
    tex((239, 231, 214), a.seed).save(d / 'paper.jpg', quality=88)
    tex((30, 28, 26), a.seed + 1).save(d / 'paper_dark.jpg', quality=88)
    print('wrote', d / 'paper.jpg', d / 'paper_dark.jpg')
