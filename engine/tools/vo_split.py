"""Split ONE voiceover take into per-scene clips, automatically and with a hard check.
usage: python vo_split.py <project> [--file path/to/take.mp3] [--force]

Input : vo/raw/vo_full.(mp3|wav|m4a). If it is missing, the newest audio file in the project is shown and the
        tool stops (exit 2) so Claude can confirm it with the creator, then re-run with --file.
Output: vo/raw/vo_01.wav … vo_NN.wav (cut in the middle of each scene-break pause), vo/split_report.txt.
        Older vo_NN files move to vo/unused/.

How it cuts (tested on the real ep. 03 take, Oct 2026):
  CLEAN      the take has real scene-break pauses (vo_text.py puts a "[pause]" line between scenes): the N-1 longest
             pauses are clearly longer than every other pause → they are the cuts, whatever the speaking speed.
             (ep. 03 take with 0.75 s added at the true cuts: 8/8 right.)
  AMBIGUOUS  no clear scene pauses (ep. 03 as recorded: breaks 0.4–0.5 s, same as sentence pauses; natural speed
             varies −16 %…+24 % between scenes, so neither pauses nor speed find the cuts: 1–5 of 8 wrong) →
             exit 3, no clips. Fix: re-generate the take from vo_paste.txt; or listen to the candidate excerpts
             in vo/check/ and pass the times with --cuts.
  FAIL       a scene's speed is off by more than ±45 % (a phrase is in the wrong scene), or the take reads an
             older script than vo_paste.txt.
On FAIL no clips are written."""
import argparse, json, pathlib, shutil, subprocess, sys, time
import numpy as np
from es import project, cfg, load_script, speak_chars, strip_tags, file_hash

AUDIO = ('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac')
ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--file')
ap.add_argument('--force', action='store_true', help='write clips even with FAILs (only after a human checked)')
ap.add_argument('--cuts', help='comma-separated cut times (s) chosen after listening to vo/check/ excerpts')
a = ap.parse_args(); P = project(a.project); C = cfg(P).get('vo', {})
SC = load_script(P); N = len(SC); keys = sorted(SC)
if keys != list(range(1, N + 1)): sys.exit(f'script.json scenes must be 1..N, got {keys}')
raw = P / 'vo' / 'raw'; raw.mkdir(parents=True, exist_ok=True)

# ---------- find the take ----------
if a.file:
    src = pathlib.Path(a.file).resolve()
else:
    src = next((f for f in sorted(raw.glob('vo_full.*')) if f.suffix.lower() in AUDIO), None)
if not src:
    skip = ('node_modules', 'out', 'drafts', 'unused', '_to_delete')
    cands = [f for f in P.rglob('*') if f.is_file() and f.suffix.lower() in AUDIO
             and not any(s in f.relative_to(P).parts for s in skip)
             and not (f.parent == raw and f.stem.startswith('vo_') and f.stem[3:].isdigit())
             and not (f.parent == P / 'vo' and f.stem.startswith('vo_'))]
    if not cands: sys.exit('NO TAKE: put the downloaded voiceover in vo/raw/ as vo_full.mp3')
    c = max(cands, key=lambda f: f.stat().st_mtime)
    print(f'CONFIRM: vo/raw/vo_full.* not found. Newest audio in the project:\n  {c.relative_to(P)}  '
          f'({time.strftime("%Y-%m-%d %H:%M", time.localtime(c.stat().st_mtime))}, {c.stat().st_size / 1e6:.1f} MB)\n'
          f'Ask the creator to confirm, then: python vo_split.py {P} --file "{c}"'); sys.exit(2)
if not src.exists(): sys.exit(f'no such file {src}')
if src.parent != raw or not src.stem == 'vo_full':
    dst = raw / ('vo_full' + src.suffix.lower()); shutil.copy2(src, dst); print(f'copied take → {dst.relative_to(P)}'); src = dst

# ---------- the take must match the text the creator pasted ----------
fails, warns = [], []
pj = P / 'vo' / 'vo_paste.json'
if pj.exists():
    if json.loads(pj.read_text()).get('script_hash') != file_hash(P / 'script.json'):
        fails.append('script.json changed after vo_paste.txt was made — the take reads the OLD text. '
                     'Revert the script, or make a new VO text (vo_text.py) and a new take.')
else:
    warns.append('no vo/vo_paste.json — this take was not recorded from vo_text.py output (no scene-break pauses guaranteed)')

# ---------- speech / silence ----------
SR = 16000
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(src), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32); hop = SR // 100
fr = x[:len(x) // hop * hop].reshape(-1, hop)
db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
loud = np.percentile(db, 95); thr = max(loud - 32, -52)
sil = db < thr
# fill tiny speech blips (< 40 ms) inside silence, tiny gaps (< 60 ms) inside speech
def runs(b):
    out, i, n = [], 0, len(b)
    while i < n:
        j = i
        while j < n and b[j] == b[i]: j += 1
        out.append((bool(b[i]), i, j)); i = j
    return out
for v, i, j in runs(sil):
    if not v and j - i < 4: sil[i:j] = True
for v, i, j in runs(sil):
    if v and j - i < 6: sil[i:j] = False
R = runs(sil)
sp = [(i, j) for v, i, j in R if not v]
if not sp: sys.exit('FAIL: no speech found in the take')
s0, s1 = sp[0][0] / 100, sp[-1][1] / 100
gaps = [(i / 100, j / 100) for v, i, j in R if v and i > 0 and j < len(sil) and (j - i) >= 8]   # ≥ 80 ms, inside speech
total_speech = sum(j - i for i, j in sp) / 100
if len(gaps) < N - 1:
    sys.exit(f'FAIL: only {len(gaps)} pauses found in the take for {N} scenes — is this the whole take?')

# ---------- expected boundaries (speech-only timeline) ----------
w = np.array([speak_chars(SC[k]) for k in keys], float)
cum = np.cumsum(w)[:-1] / w.sum()
def speech_before(t):
    return sum(max(0, min(j / 100, t) - i / 100) for i, j in sp)
G = len(gaps)
gpos = np.array([speech_before((g0 + g1) / 2) / total_speech for g0, g1 in gaps]) if G else np.zeros(0)
glen = np.array([g1 - g0 for g0, g1 in gaps]) if G else np.zeros(0)
med = float(np.median(glen)) if G else 0.3
minb = C.get('scene_break_min', 0.45)

def solve(beta):
    """N-1 gaps minimising (distance from expected boundary)² − beta·log(gap length)."""
    sw = 1.0 / N
    def cost(k, j):
        return ((gpos[j] - cum[k]) / sw) ** 2 * 2.0 - beta * np.log(max(glen[j], 0.08) / max(med, 0.08))
    INF = 1e18; D = np.full((N - 1, G), INF); B = np.zeros((N - 1, G), int)
    for j in range(G): D[0, j] = cost(0, j)
    for k in range(1, N - 1):
        best, bj = INF, -1
        for j in range(G):
            if j - 1 >= 0 and D[k - 1, j - 1] < best: best, bj = D[k - 1, j - 1], j - 1
            if best < INF: D[k, j] = best + cost(k, j); B[k, j] = bj
    j = int(np.argmin(D[N - 2])); ch = [j]
    for k in range(N - 2, 0, -1): j = int(B[k, j]); ch.append(j)
    return ch[::-1]


def evaluate_cuts(inner):
    cuts = [max(0.0, s0 - 0.12)] + list(inner) + [s1 + 0.25]
    rows = []
    for k in range(N):
        a0, a1 = cuts[k], cuts[k + 1]
        spk = sum(max(0, min(j / 100, a1) - max(i / 100, a0)) for i, j in sp)
        rows.append({'scene': k + 1, 'start': round(a0, 2), 'end': round(a1, 2), 'speech': round(spk, 2),
                     'chars': int(w[k]), 'rate': round(w[k] / spk, 2) if spk > 0 else 0})
    r = np.array([x['rate'] for x in rows]); m = float(np.median(r))
    return cuts, rows, m


mid = lambda j: (gaps[j][0] + gaps[j][1]) / 2
status, uncertain, choose = '', [], []
if a.cuts:                                         # times picked by a human after listening
    inner = [float(x) for x in a.cuts.split(',')]
    if len(inner) != N - 1: sys.exit(f'--cuts needs {N - 1} times, got {len(inner)}')
    status = 'MANUAL (times given with --cuts)'
elif N == 1:
    inner = []; status = 'single scene'
else:
    longest = sorted(np.argsort(-glen)[:N - 1].tolist())
    lo = min(glen[longest]); others = np.delete(glen, longest); hi = float(others.max()) if len(others) else 0
    if lo >= minb and lo >= max(1.3 * hi, hi + 0.2):
        # the take has real scene-break pauses: they are the cuts, whatever the speaking rate does
        choose = longest; inner = [mid(j) for j in choose]
        status = f'CLEAN — the {N - 1} scene pauses ({lo:.2f}s+) are clearly longer than any other pause ({hi:.2f}s)'
    else:
        # without clear scene pauses no method is reliable (ep. 03's real take: every weighting got 1–5 cuts wrong, and
        # agreeing methods were still wrong) — so never cut automatically; offer candidates per cut for a listen
        sols = [solve(b) for b in (2.2, 1.2, 0.5)]
        choose = sols[1]; inner = [mid(j) for j in choose]
        sw = total_speech / N
        for k in range(N - 1):
            cand = {round(mid(sol[k]), 2) for sol in sols}
            exp_t = next((g0 for (g0, g1), p in zip(gaps, gpos) if p >= cum[k]), mid(choose[k]))
            for j, (g0, g1) in enumerate(gaps):                     # other real pauses near the expected boundary
                if g1 - g0 >= 0.3 and abs(mid(j) - exp_t) <= 0.6 * sw: cand.add(round(mid(j), 2))
            uncertain.append((k, sorted(cand)))
        status = 'NO CLEAR SCENE PAUSES — cuts cannot be found reliably from this take'
        warns.append('the take has no clear scene-break pauses: re-generate it from vo/vo_paste.txt (with the "[pause]" lines)')

cuts, rows, mr = evaluate_cuts(inner)
for r in rows:
    dev = r['rate'] / mr - 1 if mr else 0
    r['dev'] = round(dev * 100)
    # natural speed varies ±25 % between scenes (ep. 03: −16 %…+24 %), so rate alone never proves a cut right
    if abs(dev) > 0.45: fails.append(f"scene {r['scene']}: {r['rate']} chars/s vs median {mr:.1f} ({dev:+.0%}) — a phrase is in the wrong scene")

rep = [f'take: {src.relative_to(P)}   speech {s0:.2f}–{s1:.2f}s   median rate {mr:.1f} chars/s', f'breaks: {status}', '']
rep.append(' scene   start    end   speech  chars  chars/s   dev   first words … last words')
for r in rows:
    t = strip_tags(SC[r['scene']]).split()
    rep.append(f" {r['scene']:>5} {r['start']:7.2f} {r['end']:6.2f} {r['speech']:7.2f} {r['chars']:6} {r['rate']:8.1f} "
               f"{r['dev']:+4d}%   {' '.join(t[:3])} … {' '.join(t[-3:])}")
if choose:
    rep.append('\n breaks (pause length s): ' + ', '.join(f'{k + 1}|{k + 2} {glen[j]:.2f}' for k, j in enumerate(choose)))
chk = P / 'vo' / 'check'
if uncertain:
    chk.mkdir(parents=True, exist_ok=True)
    rep.append('\n Best fix: re-generate the take from vo/vo_paste.txt (one paste, ~2 min). Only if that is impossible,\n listen to the excerpts in vo/check/ and pick one time per cut:')
    for k, ts in uncertain:
        t1, t2 = strip_tags(SC[k + 1]).split(), strip_tags(SC[k + 2]).split()
        rep.append(f"   {k + 1}|{k + 2}: {', '.join(f'{t:.2f}s' for t in ts)}   (scene {k + 1} ends “… {' '.join(t1[-3:])}”, "
                   f"scene {k + 2} starts “{' '.join(t2[:3])} …”)")
        for t in ts:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, t - 2.5):.2f}', '-to', f'{t + 2.5:.2f}', '-i', str(src),
                            '-af', f'afade=t=out:st={min(2.5, t) - 0.05:.2f}:d=0.05,afade=t=in:st={min(2.5, t) + 0.25:.2f}:d=0.05',
                            str(chk / f'cut_{k + 1}-{k + 2}_at_{t:.2f}s.mp3')], check=True)
    rep.append('   Each excerpt dips briefly at its candidate cut: the right one dips between the two scenes’ words.')
    rep.append(f"   Then: vo_split.py --cuts t1,t2,… ({N - 1} times, one per cut).")
rep += [''] + [f'WARN {m}' for m in warns] + [f'FAIL {m}' for m in fails]
(P / 'vo').mkdir(exist_ok=True); (P / 'vo' / 'split_report.txt').write_text('\n'.join(rep) + '\n')
print('\n'.join(rep))
if fails and not a.force:
    print(f'\n{len(fails)} failure(s): no clips written. Fix the take, or give the right times with --cuts.'); sys.exit(1)
if uncertain and not a.force:
    print('\nAMBIGUOUS: no clips written (exit 3). Do not guess: re-generate the take from vo_paste.txt, or pick times by ear.'); sys.exit(3)

# ---------- write clips ----------
un = P / 'vo' / 'unused'
for f in raw.glob('vo_*.*'):
    if f.stem[3:].isdigit():
        un.mkdir(parents=True, exist_ok=True); shutil.move(str(f), str(un / f.name))
for k in range(N):
    a0, a1 = cuts[k], cuts[k + 1]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a0:.3f}', '-to', f'{a1:.3f}', '-i', str(src),
                    '-ac', '1', '-ar', '44100', str(raw / f'vo_{k + 1:02d}.wav')], check=True)
json.dump({'take': str(src.relative_to(P)), 'cuts': [round(c, 3) for c in cuts], 'status': status,
           'script_hash': file_hash(P / 'script.json')}, open(P / 'vo' / 'split.json', 'w'))
print(f'\nSPLIT OK: {N} clips → vo/raw/vo_01..{N:02d}.wav  ({len(warns)} warnings). Next: vo_prep.py')
