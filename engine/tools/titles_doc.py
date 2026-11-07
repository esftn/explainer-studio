#!/usr/bin/env python3
"""titles_doc.py (v0.9) — copy an episode's out/publish.txt into the series copy sheet titles_descriptions.md,
so every title, description, hashtag set and pinned comment can be copied from one place.
usage: python3 titles_doc.py <videoNN> [<videoNN> …] [--doc <path>]
The doc defaults to titles_descriptions.md in the series root (the folder holding _series/ and the videoNN folders).
The episode's section ("## NN — …") is replaced if it exists, otherwise inserted in episode order. Nothing else is touched.
finish.py --verify runs this automatically after a delivery."""
import argparse, json, pathlib, re, sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import publint                                                        # noqa: E402


def ep_no(P):
    try: e = json.loads((P / 'state.json').read_text(encoding='utf-8')).get('ep')
    except Exception: e = None
    return str(e or re.sub(r'\D', '', P.name)).zfill(2)


def short_name(P, title):
    for f in ('state.json', 'project.json'):
        try:
            t = json.loads((P / f).read_text(encoding='utf-8')).get('title')
            if t: return t.strip()
        except Exception: pass
    return title


def section(P):
    pub = P / 'out' / 'publish.txt'
    if not pub.exists(): raise SystemExit(f'{P.name}: out/publish.txt missing')
    S, _ = publint.sections(pub.read_text(encoding='utf-8'))
    first = lambda k: next((l.strip() for l in S.get(k, '').splitlines() if l.strip()), '')
    title, alt = first('TITLE'), first('ALT TITLE')
    tags = [l.strip() for l in S.get('HASHTAGS', '').splitlines() if l.strip()]
    n = ep_no(P)
    L = [f'## {n} — {short_name(P, title)}', f'**TITLE:** {title}']
    if alt: L.append(f'**ALT TITLE:** {alt}')
    L += ['', '**DESCRIPTION:**', S.get('DESCRIPTION', '').strip(), '']
    if tags: L += ['**HASHTAGS:**'] + [t + '  ' for t in tags] + ['']
    if S.get('PINNED COMMENT', '').strip(): L += ['**PINNED COMMENT:**', S['PINNED COMMENT'].strip(), '']
    return n, '\n'.join(L).rstrip() + '\n'


def upsert(doc, n, body):
    t = doc.read_text(encoding='utf-8') if doc.exists() else '# TakaTheory — titles and descriptions\n\n---\n'
    parts = re.split(r'(?m)^(?=## \d+ — )', t)                         # [head, sec, sec, …]
    head, secs = parts[0], parts[1:]
    key = lambda s: int(re.match(r'## (\d+)', s).group(1))
    new = body + '\n---\n\n'
    secs = [s for s in secs if key(s) != int(n)] + [new]
    secs.sort(key=key)
    secs = [s if s.rstrip().endswith('---') else s.rstrip() + '\n\n---\n\n' for s in secs]
    doc.write_text(head + ''.join(secs).rstrip() + '\n', encoding='utf-8')


def series_root(P):
    return next((c for c in [P, *P.parents] if (c / '_series').is_dir()), P.parent)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('projects', nargs='+'); ap.add_argument('--doc'); a = ap.parse_args()
    for p in a.projects:
        P = pathlib.Path(p).resolve()
        doc = pathlib.Path(a.doc).resolve() if a.doc else series_root(P) / 'titles_descriptions.md'
        n, body = section(P); upsert(doc, n, body)
        print(f'titles_doc: ep {n} written to {doc.name}')
