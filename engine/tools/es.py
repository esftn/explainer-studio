"""Shared helpers for Explainer Studio tools."""
import hashlib, json, pathlib, sys, contextlib

W, H, FPS = 1080, 1920, 30
TOOLS = pathlib.Path(__file__).resolve().parent
ENGINE = TOOLS.parent


def project(arg=None):
    p = pathlib.Path(arg or '.').resolve()
    if not (p / 'index.html').exists():
        sys.exit(f'ERROR: {p} has no index.html — pass the project folder (made by new_project.py).')
    return p


def cfg(p):
    f = p / 'project.json'
    return json.loads(f.read_text()) if f.exists() else {}


def size(p):
    """(width, height) of the project's canvas: 1080x1920 (9:16, default) or 1920x1080 (16:9)."""
    c = cfg(p)
    return int(c.get('width', W)), int(c.get('height', H))


def timeline_hash(p):
    """Hash of everything that changes what a frame looks like or when."""
    h = hashlib.sha256()
    files = [p / 'index.html', p / 'vo.js', p / 'project.json', p / 'licences.csv']
    files += sorted((p / 'engine').rglob('*.js')) + sorted((p / 'engine').rglob('*.css'))
    for f in files:
        if f.exists():
            h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:16]


@contextlib.contextmanager
def page(p, w=None, h=None):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        if w is None: w, h = size(p)
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': w, 'height': h})
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type in ('warning', 'error') and 'Failed to load resource' not in m.text else None)
        pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
        pg.on('requestfailed', lambda r: errs.append('missing file: ' + r.url.split('/')[-1] + ' (' + r.url + ')'))
        pg.goto((p / 'index.html').as_uri())
        # load EVERY face now: hidden scenes would otherwise load fonts lazily and the first frames render in a fallback font
        pg.evaluate('Promise.all([...document.fonts].map(f => f.load().catch(() => null)))')
        pg.evaluate('document.fonts.ready')
        pg.wait_for_timeout(600)
        pg.errs = errs
        try:
            yield pg
        finally:
            br.close()
