"""Bake the confirmed cover into a finished video (run only AFTER the creator approves the cover).
  1. the cover becomes frame 1 (1/30 s — invisible in playback; first-frame previews show the cover)
  2. the cover is embedded as the MP4 thumbnail (attached_pic) for galleries / file browsers
The audio is delayed by the same one frame (from out/mix.wav when present, so it is encoded only once).
usage: python bake_cover.py <project> --video out/X_reel_9x16.mp4 --cover out/cover_reel_9x16.png [--mix out/mix.wav]
Writes the video in place (keeps a copy as drafts/<name>_nocover.mp4) and verifies the result."""
import argparse, json, pathlib, shutil, subprocess, sys

ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--video', required=True)
ap.add_argument('--cover', required=True); ap.add_argument('--mix'); ap.add_argument('--fps', type=int, default=30)
a = ap.parse_args(); P = pathlib.Path(a.project).resolve()
vid = (P / a.video).resolve(); cov = (P / a.cover).resolve()
mix = (P / a.mix).resolve() if a.mix else (P / 'out' / 'mix.wav')
for f in (vid, cov):
    if not f.exists(): sys.exit(f'missing {f}')
probe = lambda f: json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(f)]))
pr = probe(vid); v = next(s for s in pr['streams'] if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic'))
W, H = v['width'], v['height']; fr = 1 / a.fps
keep = P / 'drafts' / (vid.stem + '_nocover.mp4'); keep.parent.mkdir(exist_ok=True)
if not keep.exists(): shutil.copy2(vid, keep)
thumb = P / 'out' / f'_thumb_{W}x{H}.jpg'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(cov), '-vf', f'scale={W}:{H}', '-q:v', '2', str(thumb)], check=True)
aud = ['-i', str(mix)] if mix.exists() else ['-i', str(keep)]
amap = '2:a' if mix.exists() else '2:a:0'
tmp = vid.with_suffix('.baking.mp4')
cmd = ['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', str(a.fps), '-t', f'{fr + 1e-6:.7f}', '-i', str(cov), '-i', str(keep), *aud, '-i', str(thumb),
       '-filter_complex', f'[0:v]scale={W}:{H},format=yuv420p,setsar=1,fps={a.fps}[c];[1:v:0]setsar=1,fps={a.fps}[v];[c][v]concat=n=2:v=1:a=0[vv];[{amap}]adelay={fr * 1000:.3f}:all=1[aa]',
       '-map', '[vv]', '-map', '[aa]', '-map', '3:v', '-c:v:0', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(a.fps),
       '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-c:v:1', 'copy', '-disposition:v:1', 'attached_pic', '-movflags', '+faststart', str(tmp)]
subprocess.run(cmd, check=True); tmp.replace(vid); thumb.unlink(missing_ok=True)
# verify
pr = probe(vid); ss = pr['streams']
ok = any(s.get('disposition', {}).get('attached_pic') for s in ss)
main = next(s for s in ss if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic'))
print(('PASS' if ok else 'FAIL'), 'embedded thumbnail'); print('PASS' if (main['width'], main['height']) == (W, H) else 'FAIL', f'size {W}x{H}')
print(f"duration {float(pr['format']['duration']):.2f}s (original + 1 frame); original kept at {keep.relative_to(P)}")
if not ok: sys.exit(1)
