"""Prepare voiceover clips and lock scene timing to them.
usage: python vo_prep.py <project> [--tempo 1.06] [--only 3 5]
Input : vo/raw/vo_NN.(mp3|wav|m4a)   (NN = scene's data-vo number; made by vo_split.py from one take)
Output: vo/vo_NN.wav (trimmed, tempo, mono 44.1k), vo.js (durations, pause anchors, word times), vo/report.txt

Anchors are the END of each internal pause ≥ pause_min s (when the next phrase starts): data-at="aK".
Word times: each word of script.json gets an estimated start time. Pauses are matched to punctuation in the text,
and words in between are placed by spoken-character share. Use data-say="সাতশো" in the HTML so a graphic lands
on that spoken word; captions (make_srt.py) use the same times."""
import argparse, json, pathlib, re, subprocess, sys
from es import project, cfg, load_vo, strip_tags, speak_chars, BREAK_PUNCT

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--tempo', type=float)
ap.add_argument('--only', nargs='*', type=int)
a = ap.parse_args(); P = project(a.project); C = cfg(P).get('vo', {})
tempo = a.tempo or C.get('tempo', 1.0); tdb = C.get('trim_db', -45); pmin = C.get('pause_min', 0.22)
raw = sorted(f for f in (P / 'vo' / 'raw').glob('vo_*.*')
             if f.suffix.lower() in ('.mp3', '.wav', '.m4a', '.flac', '.ogg') and re.fullmatch(r'vo_\d+', f.stem))
if not raw: sys.exit('no clips in vo/raw/ — run vo_split.py on the take first (or name clips vo_01.mp3, vo_02.mp3 …)')
sc = P / 'script.json'
script = json.loads(sc.read_text()) if sc.exists() else {}


def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)]))


def word_times(text, d, sil):
    """sil: [(start, end)] internal silences. Returns [[word, t], ...] (t = clip time the word starts)."""
    toks = strip_tags(text).split()
    if not toks: return []
    ch = [max(speak_chars(t), 1) for t in toks]; tot = float(sum(ch))
    cf = [sum(ch[:i]) / tot for i in range(len(toks))]            # char fraction before each word
    speech = []; t0 = 0.0
    for s, e in sil:
        if s > t0: speech.append((t0, s))
        t0 = e
    if d > t0: speech.append((t0, d))
    stot = sum(e - s for s, e in speech) or d
    def s2t(f):                                                     # speech fraction → clip time
        need = f * stot
        for s, e in speech:
            if need <= e - s + 1e-9: return s + need
            need -= e - s
        return d
    pf = []
    for s, e in sil:                                                # speech fraction at each pause
        pf.append(sum(max(0, min(e2, s) - s2) for s2, e2 in speech) / stot)
    bnd = [i for i in range(1, len(toks)) if toks[i - 1][-1:] in BREAK_PUNCT]   # word index after punctuation
    # match punctuation boundaries to pauses, monotonic, nearest within tolerance
    knots = [(0.0, 0.0)]; j0 = 0; fixed = {}
    for i in bnd:
        best, bj = 0.12, None
        for j in range(j0, len(sil)):
            dd = abs(pf[j] - cf[i])
            if dd < best: best, bj = dd, j
        if bj is not None:
            knots.append((cf[i], pf[bj])); fixed[i] = sil[bj][1]; j0 = bj + 1
    knots.append((1.0, 1.0))
    out = []
    for i, t in enumerate(toks):
        if i in fixed: tt = fixed[i]
        else:
            f = cf[i]
            for (c0, p0), (c1, p1) in zip(knots, knots[1:]):
                if c0 <= f <= c1:
                    g = p0 + (p1 - p0) * ((f - c0) / (c1 - c0) if c1 > c0 else 0); break
            tt = s2t(g)
        out.append([t, round(tt, 3)])
    return out


old = load_vo(P)
durs, anchors, words, rep = {}, {}, {}, []
for f in raw:
    n = int(f.stem[3:])
    if a.only and n not in a.only:
        if n < len(old['durs']) and old['durs'][n] is not None:
            durs[n] = old['durs'][n]; anchors[n] = old['anchors'][n]
            words[n] = old['words'][n] if n < len(old['words']) else []
        continue
    out = P / 'vo' / f'vo_{n:02d}.wav'
    trim = (f'silenceremove=start_periods=1:start_threshold={tdb}dB:start_silence=0.05,'
            f'areverse,silenceremove=start_periods=1:start_threshold={tdb}dB:start_silence=0.12,areverse')
    flt = trim + (f',atempo={tempo}' if abs(tempo - 1) > 1e-3 else '') + ',highpass=f=70'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(f), '-af', flt, '-ac', '1', '-ar', '44100', str(out)], check=True)
    d = dur(out)
    log = subprocess.run(['ffmpeg', '-i', str(out), '-af', f'silencedetect=noise=-38dB:d={pmin}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', log)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    sil = [(max(s, 0), e) for s, e in zip(st, en) if 0.2 < e < d - 0.15]
    ends = [round(e, 3) for s, e in sil]
    durs[n], anchors[n] = round(d, 3), ends
    text = script.get(str(n), '')
    words[n] = word_times(text, d, sil) if text else []
    nw = len(strip_tags(text).split())
    wps = nw / d if nw else 0
    flag = '  <-- fast' if wps > 3.2 else ('  <-- slow' if wps and wps < 1.6 else '')
    rep.append(f'vo_{n:02d}: {d:6.2f}s  pauses→anchors a1..: {ends}  words/s {wps:.2f}{flag}')
mx = max(durs)
D = [durs.get(i) for i in range(mx + 1)]; A = [anchors.get(i, []) for i in range(mx + 1)]
Wd = [words.get(i, []) for i in range(mx + 1)]
(P / 'vo.js').write_text('window.VO=' + json.dumps({'durs': D, 'anchors': A, 'words': Wd}, ensure_ascii=False) + ';\n')
pad = cfg(P).get('pad', 0.55)
tot = sum(d for d in D if d) + pad * len(durs)
rep.append(f'total VO {sum(d for d in D if d):.1f}s → video ≈ {tot:.1f}s (+ ending hold)')
(P / 'vo' / 'report.txt').write_text('\n'.join(rep) + '\n'); print('\n'.join(rep))
