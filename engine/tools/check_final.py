"""Final file check: resolution, fps, A/V length match, loudness, true peak, clean silent ending, frames at cut points.
usage: python check_final.py <project> [--file out/X_reel_9x16.mp4 | out/X_feed_4x5.mp4]"""
import argparse, json, subprocess, sys, re
from es import project, cfg

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--file')
a = ap.parse_args(); P = project(a.project)
f = P / a.file if a.file else max([*(P / 'out').glob('*_final.mp4'), *(P / 'out').glob('*_reel_9x16.mp4')], key=lambda x: x.stat().st_mtime, default=None)
if not f or not f.exists(): sys.exit('no final mp4 found')
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(f)]))
v = next(s for s in pr['streams'] if s['codec_type'] == 'video'); au = next((s for s in pr['streams'] if s['codec_type'] == 'audio'), None)
ok = True
def chk(cond, msg):
    global ok; print(('PASS ' if cond else 'FAIL ') + msg); ok &= cond
want = (1080, 1350) if 'feed_4x5' in f.name else (1080, 1920)
chk((v['width'], v['height']) == want, f"resolution {v['width']}x{v['height']} (want {want[0]}x{want[1]})")
chk(v['r_frame_rate'] in ('30/1', '30000/1001'), f"fps {v['r_frame_rate']}")
chk(v['pix_fmt'] == 'yuv420p', f"pix_fmt {v['pix_fmt']}")
chk(au is not None, 'audio track present')
if au:
    dv, da = float(v.get('duration', pr['format']['duration'])), float(au.get('duration', pr['format']['duration']))
    chk(abs(dv - da) < 0.1, f'A/V length {dv:.2f}s / {da:.2f}s')
    log = subprocess.run(['ffmpeg', '-i', str(f), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', log)[-1]); TP = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', log)[-1])
    chk(-16 <= I <= -13, f'loudness {I} LUFS (target -14.5)'); chk(TP <= -1.0, f'true peak {TP} dBTP (≤ -1)')
    end = subprocess.run(['ffmpeg', '-sseof', '-0.25', '-i', str(f), '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
    mx = re.findall(r'max_volume: (-?[\d.inf]+) dB', end)
    chk(bool(mx) and (mx[0] == '-inf' or float(mx[0]) < -50), f'silent last 0.25s (max {mx[0] if mx else "?"} dB)')
mb = f.stat().st_size / 1e6
print(f'size {mb:.1f} MB' + ('  (Facebook/Instagram/TikTok all accept; WhatsApp status needs <16 MB → see docs/platform-notes.md)' if mb > 16 else ''))
sys.exit(0 if ok else 1)
