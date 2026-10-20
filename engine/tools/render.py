"""Render the video (frames → H.264) and mux the audio mix. Refuses to run unless audit.py passed on THIS timeline.
usage: python render.py <project> [--workers 2] [--crf 18] [--silent] [--cover 2.0] [--name Hadi_Ke_v4]
       python render.py <project> --preview      (15 fps, half size, ~4x faster: for the creator's preview gate)
Output: out/<name>_final.mp4 (+ out/<name>_cover.png) or out/<name>_preview.mp4."""
import argparse, json, subprocess, sys, pathlib, time
from es import project, cfg, timeline_hash, page, size, FPS, TOOLS


def worker(P, a, b, out, crf, fps=FPS, scale=None):
    with page(P) as pg:
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', str(fps), '-c:v', 'mjpeg', '-i', '-',
                               '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-r', str(fps)]
                              + (['-vf', f'scale={scale}:-2'] if scale else []) + [str(out)],
                              stdin=subprocess.PIPE)
        for n in range(a, b):
            pg.evaluate(f'seek({n / fps})'); ff.stdin.write(pg.screenshot(type='jpeg', quality=93))
            if (n - a) % 300 == 0: print(f'  [{out.name}] {n}/{b}', flush=True)
        ff.stdin.close(); ff.wait()
        if ff.returncode: sys.exit(f'ffmpeg failed on {out}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--crf', type=int, default=18); ap.add_argument('--silent', action='store_true')
    ap.add_argument('--cover', type=float); ap.add_argument('--name'); ap.add_argument('--force', action='store_true')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--_w', nargs=3, type=int, help=argparse.SUPPRESS)
    a = ap.parse_args(); P = project(a.project); O = P / 'out'; O.mkdir(exist_ok=True)
    if a._w:
        worker(P, a._w[0], a._w[1], O / f'seg_{a._w[2]}.mp4', a.crf, 15 if a.preview else FPS, size(P)[0] // 2 if a.preview else None); sys.exit()
    qa = P / '.qa_pass'
    if not a.force:
        if not qa.exists(): sys.exit('BLOCKED: run audit.py first (no .qa_pass).')
        q = json.loads(qa.read_text())
        if q['hash'] != timeline_hash(P): sys.exit('BLOCKED: timeline changed since the last audit — re-run audit.py.')
    mix = O / 'mix.wav'
    if not a.silent and not mix.exists(): sys.exit('BLOCKED: out/mix.wav missing — run audio.py (or pass --silent for a preview).')
    if not a.silent and mix.stat().st_mtime < qa.stat().st_mtime - 1:
        sys.exit('BLOCKED: mix.wav is older than the last audit — re-run audio.py so SFX match the timeline.')
    name = a.name or cfg(P).get('slug') or P.name
    with page(P) as pg: total = pg.evaluate('TOTAL')
    fps = 15 if a.preview else FPS; crf = 26 if a.preview else a.crf
    N = int(round(total * fps)); per = (N + a.workers - 1) // a.workers; t0 = time.time()
    procs = [subprocess.Popen([sys.executable, str(TOOLS / 'render.py'), str(P), '--crf', str(crf)] + (['--preview'] if a.preview else []) + ['--_w', str(w * per), str(min(N, (w + 1) * per)), str(w)])
             for w in range(a.workers)]
    if any(p.wait() for p in procs): sys.exit('a render worker failed')
    lst = O / 'list.txt'; lst.write_text(''.join(f"file 'seg_{w}.mp4'\n" for w in range(a.workers)))
    video = O / 'video_only.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(video)], check=True)
    final = O / f'{name}_{"preview" if a.preview else "final"}.mp4'
    if a.silent:
        video.replace(final)
    else:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(mix), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                        '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-shortest', str(final)], check=True)
        video.unlink()
    for w in range(a.workers): (O / f'seg_{w}.mp4').unlink(missing_ok=True)
    lst.unlink(missing_ok=True)
    if a.cover is not None:
        with page(P) as pg:
            pg.evaluate(f'seek({a.cover})'); pg.screenshot(path=str(O / f'{name}_cover.png'))
    # verify
    pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,nb_frames:format=duration', '-of', 'json', str(final)]))
    print(f'rendered {final} in {time.time() - t0:.0f}s  duration {float(pr["format"]["duration"]):.2f}s (timeline {total:.2f}s)')
    print('next: check_final.py → thumbnail.py → publish.py (Gate 4 checklist)')
