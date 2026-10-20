"""Burn-free captions: out/captions.srt from script.json + VO timing (pause anchors split the lines).
usage: python make_srt.py <project> [--max-chars 42]
script.json = {"1": "VO text for vo_01", "2": "...", ...}. Upload the .srt to Facebook/YouTube; most viewers watch muted."""
import argparse, json, re
from es import project, cfg

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--max-chars', type=int, default=42)
a = ap.parse_args(); P = project(a.project); off = cfg(P).get('voOffset', 0.3)
script = json.loads((P / 'script.json').read_text()); scenes = json.loads((P / 'scenes.json').read_text())
vo = json.loads(re.search(r'window\.VO=(\{.*\});', (P / 'vo.js').read_text(), re.S).group(1))
def ts(t):
    ms = int(round(t * 1000)); return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'
def chunks(text):
    parts = [p.strip() for p in re.split(r'(?<=[।?!,—])\s+', text) if p.strip()]; out = []
    for p in parts:
        while len(p) > a.max_chars:
            cut = p.rfind(' ', 0, a.max_chars); cut = cut if cut > 10 else a.max_chars; out.append(p[:cut].strip()); p = p[cut:].strip()
        if p: out.append(p)
    return out
cues = []
for s in scenes:
    n = s['vo']
    if n is None or str(n) not in script or n >= len(vo['durs']) or vo['durs'][n] is None: continue
    t0, d = s['start'] + off, vo['durs'][n]; lines = chunks(script[str(n)]); tot = sum(len(l) for l in lines)
    t = t0
    for l in lines:
        dt = d * len(l) / tot; cues.append((t, t + dt - 0.05, l)); t += dt
(P / 'out').mkdir(exist_ok=True)
(P / 'out' / 'captions.srt').write_text(''.join(f'{i}\n{ts(a_)} --> {ts(b)}\n{l}\n\n' for i, (a_, b, l) in enumerate(cues, 1)), encoding='utf-8')
print(f'{len(cues)} captions → out/captions.srt')
