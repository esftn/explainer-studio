"""Prepare voiceover clips and lock scene timing to them.
usage: python vo_prep.py <project> [--tempo 1.06] [--only 3 5]
Input : vo/raw/vo_NN.(mp3|wav|m4a)   (NN = scene's data-vo number)
Output: vo/vo_NN.wav (trimmed, tempo, mono 44.1k), vo.js (durations + pause anchors), vo/report.txt
Anchors are the END of each internal pause ≥ pause_min s, i.e. when the next phrase starts — use data-at="aK"
in the HTML so a highlight lands exactly as the word is spoken."""
import argparse, json, pathlib, re, subprocess, sys
from es import project, cfg

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--tempo', type=float)
ap.add_argument('--only', nargs='*', type=int)
a = ap.parse_args(); P = project(a.project); C = cfg(P).get('vo', {})
tempo = a.tempo or C.get('tempo', 1.0); tdb = C.get('trim_db', -45); pmin = C.get('pause_min', 0.22)
raw = sorted(f for f in (P / 'vo' / 'raw').glob('vo_*.*') if f.suffix.lower() in ('.mp3', '.wav', '.m4a', '.flac', '.ogg'))
if not raw: sys.exit('no clips in vo/raw/ (name them vo_01.mp3, vo_02.mp3 …)')


def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)]))


durs, anchors, rep = {}, {}, []
old = {}
vj = P / 'vo.js'
if vj.exists():
    m = re.search(r'window\.VO=(\{.*\});', vj.read_text(), re.S)
    if m:
        try:
            j = json.loads(m.group(1).replace('durs:', '"durs":').replace('anchors:', '"anchors":'))
            for i, d in enumerate(j.get('durs', [])):
                if d is not None: old[i] = (d, j['anchors'][i])
        except Exception:
            pass
for f in raw:
    n = int(re.findall(r'\d+', f.stem)[0])
    if a.only and n not in a.only:
        if n in old: durs[n], anchors[n] = old[n]
        continue
    out = P / 'vo' / f'vo_{n:02d}.wav'
    trim = (f'silenceremove=start_periods=1:start_threshold={tdb}dB:start_silence=0.05,'
            f'areverse,silenceremove=start_periods=1:start_threshold={tdb}dB:start_silence=0.12,areverse')
    flt = trim + (f',atempo={tempo}' if abs(tempo - 1) > 1e-3 else '') + ',highpass=f=70'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(f), '-af', flt, '-ac', '1', '-ar', '44100', str(out)], check=True)
    d = dur(out)
    log = subprocess.run(['ffmpeg', '-i', str(out), '-af', f'silencedetect=noise=-38dB:d={pmin}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    ends = [round(e, 3) for e in ends if 0.2 < e < d - 0.15]
    durs[n], anchors[n] = round(d, 3), ends
    words = 0
    sc = P / 'script.json'
    if sc.exists():
        words = len(json.loads(sc.read_text()).get(str(n), '').split())
    wps = words / d if words else 0
    flag = '  <-- fast' if wps > 3.2 else ('  <-- slow' if wps and wps < 1.6 else '')
    rep.append(f'vo_{n:02d}: {d:6.2f}s  pauses→anchors a1..: {ends}  words/s {wps:.2f}{flag}')
mx = max(durs)
D = [durs.get(i) for i in range(mx + 1)]; A = [anchors.get(i, []) for i in range(mx + 1)]
vj.write_text('window.VO=' + json.dumps({'durs': D, 'anchors': A}) + ';\n')
tot = sum(d for d in D if d) + 0.55 * len(durs)
rep.append(f'total VO {sum(d for d in D if d):.1f}s → video ≈ {tot:.1f}s')
(P / 'vo' / 'report.txt').write_text('\n'.join(rep) + '\n'); print('\n'.join(rep))
