"""Import exact word timings from ElevenLabs Speech to Text (Scribe) and derive the scene cuts (v0.8.1).
usage: python3 engine/tools/words_import.py <project> [--src docs/words.json] [--apply]

Reads an ElevenLabs export in any of its shapes ({"segments":[{"words":[...]}]}, {"words":[...]}, or a bare list; times as
start/end or start_time/end_time; "spacing" / blank entries skipped) and writes:
  docs/words_norm.json   [{"text","start","end"}] — what burn_captions.py --words and later tools read
  docs/words_script.json [{"text","start","end","scene"}] — the SCRIPT's words with those times (use this for captions)
  docs/words_cuts.json   {"cuts":[...], "scenes":[...]} — scene boundaries found by aligning script.json to the transcript
The cut between scene k and k+1 = the middle of the silence between the last spoken word of k and the first word of k+1.
It prints the cut list in vo_split.py's --cuts format and a per-scene match score; a scene with a low score is flagged.
--apply runs vo_split.py --cuts with them (so the take is split by real word times instead of guessing from pauses)."""
import argparse, difflib, json, pathlib, re, subprocess, sys

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--src', default='docs/words.json'); ap.add_argument('--apply', action='store_true')
ap.add_argument('--take', default='vo/raw/vo_full.mp3', help='the take, used to snap each cut into a real silence')
a = ap.parse_args(); P = pathlib.Path(a.project).resolve()
raw = json.loads((P / a.src).read_text(encoding='utf-8'))
items = []
if isinstance(raw, dict) and 'segments' in raw:
    for s in raw['segments']: items += s.get('words', [])
elif isinstance(raw, dict): items = raw.get('words', [])
else: items = raw
W = []
for w in items:
    t = (w.get('text') or '').strip()
    if not t or w.get('type') == 'spacing': continue
    s = w.get('start', w.get('start_time')); e = w.get('end', w.get('end_time'))
    if s is None or e is None: continue
    W.append({'text': t, 'start': round(float(s), 3), 'end': round(float(e), 3)})
if not W: sys.exit('no timed words found in ' + a.src)
(P / 'docs' / 'words_norm.json').write_text(json.dumps(W, ensure_ascii=False, indent=0), encoding='utf-8')

norm = lambda s: re.sub(r'[^ঀ-৿A-Za-z0-9]', '', s)
S = json.loads((P / 'script.json').read_text(encoding='utf-8')); keys = sorted(S, key=lambda k: int(re.sub(r'\D', '', str(k)) or 0))
raw_tok = [(k, t) for k in keys for t in re.sub(r'\[[^\]]*\]', ' ', str(S[k])).split() if norm(t)]
sw = [(k, norm(t)) for k, t in raw_tok]
tw = [norm(w['text']) for w in W]
sm = difflib.SequenceMatcher(None, [x for _, x in sw], tw, autojunk=False)
m = {}
for blk in sm.get_matching_blocks():
    for i in range(blk.size): m[blk.a + i] = blk.b + i
first, last, score = {}, {}, {}
for i, (k, _) in enumerate(sw):
    if i in m:
        first.setdefault(k, m[i]); last[k] = m[i]
    score.setdefault(k, [0, 0]); score[k][1] += 1; score[k][0] += i in m
# Scribe word ends often run into the pause (or stop early), so Scribe only says WHICH pause is the boundary;
# the cut goes in the middle of the real silence (ffmpeg silencedetect) nearest to it.
sil = []
take = P / a.take
if take.exists():
    out = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(take), '-af', 'silencedetect=n=-35dB:d=0.15', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    sil = list(zip(st, en))
else: print('WARN no take at', a.take, '— cuts use Scribe times only (check by ear)')
# captions: the script's own words (its spelling), timed by the transcript; replaced spans share their time evenly
cap = []
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal':
        cap += [{'text': raw_tok[i1 + n][1], 'start': W[j1 + n]['start'], 'end': W[j1 + n]['end'], 'scene': raw_tok[i1 + n][0]} for n in range(i2 - i1)]
    elif op in ('replace', 'delete') and i2 > i1:
        if j2 > j1: t0, t1 = W[j1]['start'], W[j2 - 1]['end']
        else: t0 = cap[-1]['end'] if cap else 0; t1 = t0
        d = (t1 - t0) / (i2 - i1)
        cap += [{'text': raw_tok[i1 + n][1], 'start': round(t0 + n * d, 3), 'end': round(t0 + (n + 1) * d, 3), 'scene': raw_tok[i1 + n][0]} for n in range(i2 - i1)]
(P / 'docs' / 'words_script.json').write_text(json.dumps(cap, ensure_ascii=False, indent=0), encoding='utf-8')
cuts, rep = [], []
for k, nk in zip(keys, keys[1:]):
    if k not in last or nk not in first: sys.exit(f'could not place the boundary between scenes {k} and {nk} (too few matching words)')
    e, s = W[last[k]]['end'], W[first[nk]]['start']; mid = (e + s) / 2; how = 'scribe'
    near = [g for g in sil if g[1] > e - 1.5 and g[0] < s + 0.5]
    if near:
        g = min(near, key=lambda g: abs((g[0] + g[1]) / 2 - mid)); mid = (g[0] + g[1]) / 2; e, s = g; how = 'silence'
    cuts.append(round(mid, 2)); rep.append((k, nk, e, s, how))
scenes = []
for k in keys:
    ok, n = score[k]; q = ok / n if n else 0
    scenes.append({'scene': k, 'match': round(q, 2), 'start': W[first[k]]['start'] if k in first else None, 'end': W[last[k]]['end'] if k in last else None})
(P / 'docs' / 'words_cuts.json').write_text(json.dumps({'cuts': cuts, 'scenes': scenes}, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'{len(W)} timed words, {len(keys)} scenes')
for (k, nk, e, s, how), c in zip(rep, cuts): print(f'  cut {k}|{nk}: {c:6.2f} s   ({how} gap {e:.2f}–{s:.2f}, {s - e:.2f} s)' + ('   WARN short gap' if s - e < .2 else ''))
low = [x for x in scenes if x['match'] < .6]
for x in scenes: print(f'  scene {x["scene"]}: match {x["match"]:.0%}')
if low: print('WARN low match (transcript differs from the script there — check by ear):', ', '.join(str(x['scene']) for x in low))
print('cuts for vo_split.py --cuts', ','.join(f'{c:.2f}' for c in cuts))
if a.apply:
    T = pathlib.Path(__file__).parent
    sys.exit(subprocess.run([sys.executable, str(T / 'vo_split.py'), str(P), '--cuts', ','.join(f'{c:.2f}' for c in cuts)]).returncode)
