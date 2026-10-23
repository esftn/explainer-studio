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


def timeline_hash(p):
    """Hash of everything that changes what a frame looks like or when."""
    h = hashlib.sha256()
    files = [p / 'index.html', p / 'vo.js', p / 'project.json']
    files += sorted((p / 'engine').rglob('*.js')) + sorted((p / 'engine').rglob('*.css'))
    for f in files:
        if f.exists():
            h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:16]


@contextlib.contextmanager
def page(p, w=W, h=H):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
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


# ---------- text helpers (Bangla-aware) ----------
import re as _re
TAG_RE = _re.compile(r'\[[^\]]*\]')                 # ElevenLabs audio tags: [curious], [excited] …
PUNCT = ',।?!—–-…;:"\'“”‘’()|.'
BREAK_PUNCT = ',।?!—…;:'


def strip_tags(t):
    return _re.sub(r'\s+', ' ', TAG_RE.sub(' ', t)).strip()


def speak_chars(t):
    """Number of spoken characters (letters/digits/marks), ignoring tags, spaces, punctuation and joiners."""
    t = strip_tags(t)
    return sum(1 for ch in t if not ch.isspace() and ch not in PUNCT and ch not in '‌‍')


def norm_word(w):
    return ''.join(ch for ch in w if ch not in PUNCT and ch not in '‌‍').strip()


def load_script(p):
    f = p / 'script.json'
    if not f.exists():
        sys.exit(f'ERROR: {f} missing — write script.json ({{"1": "VO text of scene 1", ...}})')
    d = json.loads(f.read_text())
    return {int(k): v for k, v in d.items() if str(k).isdigit()}


def file_hash(*files):
    h = hashlib.sha256()
    for f in files:
        f = pathlib.Path(f)
        if f.exists(): h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:16]


def load_vo(p):
    vj = p / 'vo.js'
    if not vj.exists(): return {'durs': [], 'anchors': [], 'words': []}
    m = _re.search(r'window\.VO=(\{.*\});', vj.read_text(), _re.S)
    txt = m.group(1)
    txt = _re.sub(r'([{,])\s*(durs|anchors|words)\s*:', r'\1"\2":', txt)
    d = json.loads(txt); d.setdefault('words', []); return d


def bn_digits_to_int(s):
    return s.translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))
