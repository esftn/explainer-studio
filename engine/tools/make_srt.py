"""Burn-free captions (v0.5): out/captions.bn_IN.srt (Bangla) + out/captions.en_US.srt (English) from script.json + VO timing.
Facebook only accepts captions named <name>.<lang>_<COUNTRY>.srt; there is no Bangladesh variant, so Bangla = bn_IN.
English: run once, translate docs/captions_bn_cues.json line by line into docs/captions_en.json (same length, same order,
natural short English, numbers checked against facts.json), run again — the English file reuses the Bangla timings.
usage: python make_srt.py <project> [--max-chars 42]
Lines are split at punctuation (and at --max-chars). Each line starts when its first word is spoken (word times
from vo_prep.py, measured pauses + spoken-character share) — no even spread inside a scene. Falls back to the
character share of the scene only for projects prepared before v0.4 (no word times in vo.js)."""
import argparse, json, re
from es import project, cfg, load_vo, strip_tags

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--max-chars', type=int, default=42)
a = ap.parse_args(); P = project(a.project); off = cfg(P).get('voOffset', 0.3)
script = json.loads((P / 'script.json').read_text()); scenes = json.loads((P / 'scenes.json').read_text())
vo = load_vo(P)


def ts(t):
    ms = int(round(max(t, 0) * 1000)); return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def chunks(words):
    """words: list of tokens → list of (start, end_exclusive) caption lines: break after punctuation or at max chars."""
    out, s, n = [], 0, 0
    for i, w in enumerate(words):
        if n and n + len(w) + 1 > a.max_chars:
            out.append((s, i)); s, n = i, 0
        n += len(w) + 1
        if w[-1:] in '।?!,—':
            out.append((s, i + 1)); s, n = i + 1, 0
    if s < len(words): out.append((s, len(words)))
    # a one-word flash ("চলুন,") is hard to read: join a very short line with the next one when it fits
    m = []
    for x in out:
        if m and sum(len(w) + 1 for w in words[m[-1][0]:m[-1][1]]) < 10 and sum(len(w) + 1 for w in words[m[-1][0]:x[1]]) <= a.max_chars:
            m[-1] = (m[-1][0], x[1])
        else: m.append(x)
    return m


cues = []
for s in scenes:
    n = s['vo']
    if n is None or str(n) not in script or n >= len(vo['durs']) or vo['durs'][n] is None: continue
    t0, d = s['start'] + off, vo['durs'][n]
    toks = strip_tags(script[str(n)]).split()
    W = vo['words'][n] if n < len(vo['words']) and vo['words'][n] else None
    if not W or len(W) != len(toks):              # old project: spread by characters
        tot = sum(len(x) for x in toks) or 1; acc = 0; W = []
        for x in toks: W.append([x, d * acc / tot]); acc += len(x)
    lines = chunks(toks)
    for k, (i, j) in enumerate(lines):
        st = t0 + W[i][1]
        en = t0 + (W[lines[k + 1][0]][1] - 0.05 if k + 1 < len(lines) else d)
        cues.append((st, max(en, st + 0.4), ' '.join(toks[i:j])))
(P / 'out').mkdir(exist_ok=True); (P / 'docs').mkdir(exist_ok=True)


def srt(texts):
    return ''.join(f'{i}\n{ts(a_)} --> {ts(b)}\n{t}\n\n' for i, ((a_, b, _), t) in enumerate(zip(cues, texts), 1))


(P / 'out' / 'captions.bn_IN.srt').write_text(srt([c[2] for c in cues]), encoding='utf-8')
(P / 'docs' / 'captions_bn_cues.json').write_text(json.dumps([c[2] for c in cues], ensure_ascii=False, indent=0), encoding='utf-8')
old = P / 'out' / 'captions.srt'
if old.exists(): old.unlink()
print(f'{len(cues)} captions → out/captions.bn_IN.srt')
en = P / 'docs' / 'captions_en.json'
if en.exists():
    t = json.loads(en.read_text(encoding='utf-8'))
    if len(t) != len(cues): raise SystemExit(f'ERROR: docs/captions_en.json has {len(t)} lines, the Bangla file has {len(cues)} — must match one to one')
    (P / 'out' / 'captions.en_US.srt').write_text(srt(t), encoding='utf-8'); print('English → out/captions.en_US.srt')
else:
    print(f'NEXT: translate docs/captions_bn_cues.json ({len(cues)} lines) into docs/captions_en.json, then run make_srt.py again')
