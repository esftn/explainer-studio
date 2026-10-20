"""Patch a rendered video: re-render only frames [a,b) and splice them in (fast fix for one scene).
usage: python render_range.py <project> --scene 10            (re-render one whole scene)
       python render_range.py <project> --frames 2400 2700
Needs a fresh audit (.qa_pass) of the edited timeline. Scene timing must NOT have changed — if a duration
changed, do a full render.py instead (audio + every later frame would shift)."""
import argparse, json, subprocess, sys
from es import project, cfg, timeline_hash, page, FPS, TOOLS

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--scene', type=int)
ap.add_argument('--frames', nargs=2, type=int); ap.add_argument('--name')
a = ap.parse_args(); P = project(a.project); O = P / 'out'
q = P / '.qa_pass'
if not q.exists() or json.loads(q.read_text())['hash'] != timeline_hash(P): sys.exit('BLOCKED: run audit.py on the edited timeline first.')
name = a.name or cfg(P).get('slug') or P.name; final = O / f'{name}_final.mp4'
if not final.exists(): sys.exit(f'no {final} to patch — run render.py')
with page(P) as pg: S = pg.evaluate('SCENES'); total = pg.evaluate('TOTAL')
old = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(final)]))
if abs(old - total) > 0.15: sys.exit(f'timeline length changed ({old:.2f}s → {total:.2f}s): full render needed.')
if a.scene:
    s = S[a.scene - 1]; fa, fb = int(round(s['start'] * FPS)), int(round((s['start'] + s['dur'] + 0.45) * FPS))
else:
    fa, fb = a.frames
N = int(round(total * FPS)); fb = min(fb, N)
subprocess.run([sys.executable, str(TOOLS / 'render.py'), str(P), '--_w', str(fa), str(fb), '9'], check=True)
mid = O / 'seg_9.mp4'
enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-an']
parts = []
if fa > 0:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(final), '-frames:v', str(fa)] + enc + [str(O / 'pA.mp4')], check=True); parts.append('pA.mp4')
parts.append('seg_9.mp4')
if fb < N:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{fb / FPS:.4f}', '-i', str(final)] + enc + [str(O / 'pC.mp4')], check=True); parts.append('pC.mp4')
(O / 'plist.txt').write_text(''.join(f"file '{p}'\n" for p in parts))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(O / 'plist.txt'), '-c', 'copy', str(O / 'v.mp4')], check=True)
tmp = O / f'{name}_patched.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(O / 'v.mp4'), '-i', str(final), '-map', '0:v', '-map', '1:a?', '-c', 'copy',
                '-movflags', '+faststart', '-shortest', str(tmp)], check=True)
tmp.replace(final)
for f in ('pA.mp4', 'pC.mp4', 'seg_9.mp4', 'v.mp4', 'plist.txt'): (O / f).unlink(missing_ok=True)
print(f'patched frames {fa}..{fb} in {final}. Check the seams: review the frames at both cut points.')
