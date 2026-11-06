"""Bake the confirmed cover into a finished video (run only AFTER the creator approves the cover).
  1. the cover becomes frame 1 (1/30 s — invisible in playback; first-frame previews show the cover)
  2. the cover is embedded as the MP4 thumbnail (attached_pic) for galleries / file browsers
  3. (v0.8) cover opening: the cover also fills the first --hold seconds (default project.json cover_hold, else 1.6)
     with a slow push-in (zoom 1.0 -> 1.08) and fades into scene 1 over the last 0.15 s, while the first VO line plays.
     Channel data (7 Nov 2026): viewers swipe in the first 1-2 s when the video opens on a quiet scene. --hold 0 = old behaviour.
The audio is delayed by the same one frame (from out/mix.wav when present, so it is encoded only once).
usage: python bake_cover.py <project> --video out/X_reel_9x16.mp4 --cover out/cover_reel_9x16.png [--mix out/mix.wav] [--hold 1.6]
Writes the video in place (keeps a copy as drafts/<name>_nocover.mp4) and verifies the result."""
import argparse, json, pathlib, shutil, subprocess, sys

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--video', required=True)
ap.add_argument('--cover', required=True); ap.add_argument('--mix'); ap.add_argument('--fps', type=int, default=30); ap.add_argument('--hold', type=float)
a = ap.parse_args(); P = pathlib.Path(a.project).resolve()
vid = (P / a.video).resolve(); cov = (P / a.cover).resolve()
mix = (P / a.mix).resolve() if a.mix else (P / 'out' / 'mix.wav')
for f in (vid, cov):
    if not f.exists(): sys.exit(f'missing {f}')
probe = lambda f: json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(f)]))
pr = probe(vid); v = next(s for s in pr['streams'] if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic'))
W, H = v['width'], v['height']; fr = 1 / a.fps
pj = json.loads((P / 'project.json').read_text()) if (P / 'project.json').exists() else {}
hold = a.hold if a.hold is not None else float(pj.get('cover_hold', 1.6))
keep = P / 'drafts' / (vid.stem + '_nocover.mp4'); keep.parent.mkdir(exist_ok=True)
if not keep.exists(): shutil.copy2(vid, keep)
thumb = P / 'out' / f'_thumb_{W}x{H}.jpg'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(cov), '-vf', f'scale={W}:{H}', '-q:v', '2', str(thumb)], check=True)
aud = ['-i', str(mix)] if mix.exists() else ['-i', str(keep)]
amap = '2:a' if mix.exists() else '2:a:0'
tmp = vid.with_suffix('.baking.mp4')
fc = f'[0:v]scale={W}:{H},format=yuv420p,setsar=1,fps={a.fps}[c];[1:v:0]setsar=1,fps={a.fps}[v];[c][v]concat=n=2:v=1:a=0[v0];[{amap}]adelay={fr * 1000:.3f}:all=1[aa]'
hold_in = []
if hold > 0:   # cover opening: push-in over the first `hold` s, alpha fade into scene 1
    z = .08 / max(1, int(hold * a.fps))
    hold_in = ['-loop', '1', '-framerate', str(a.fps), '-t', f'{hold + .2:.2f}', '-i', str(cov)]
    fc += (f';[4:v]scale={W * 3}:-2,zoompan=z=\'1+{z:.5f}*on\':x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':d=1:s={W}x{H}:fps={a.fps},'
           f'format=yuva420p,fade=t=out:st={hold - .15:.2f}:d=0.15:alpha=1[cz];[v0][cz]overlay=enable=\'lt(t,{hold:.2f})\':eof_action=pass,format=yuv420p[vv]')
else:
    fc += ';[v0]null[vv]'
cmd = ['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', str(a.fps), '-t', f'{fr + 1e-6:.7f}', '-i', str(cov), '-i', str(keep), *aud, '-i', str(thumb), *hold_in,
       '-filter_complex', fc,
       '-map', '[vv]', '-map', '[aa]', '-map', '3:v', '-c:v:0', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(a.fps),
       '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-c:v:1', 'copy', '-disposition:v:1', 'attached_pic', '-movflags', '+faststart', str(tmp)]
subprocess.run(cmd, check=True); tmp.replace(vid); thumb.unlink(missing_ok=True)
# verify
pr = probe(vid); ss = pr['streams']
ok = any(s.get('disposition', {}).get('attached_pic') for s in ss)
main = next(s for s in ss if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic'))
print(('PASS' if ok else 'FAIL'), 'embedded thumbnail'); print('PASS' if (main['width'], main['height']) == (W, H) else 'FAIL', f'size {W}x{H}')
print(f"duration {float(pr['format']['duration']):.2f}s (original + 1 frame); cover opening {hold:.1f} s; original kept at {keep.relative_to(P)}")
if not ok: sys.exit(1)
