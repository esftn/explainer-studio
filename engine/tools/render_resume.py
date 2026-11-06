"""Resumable full render in 10-second chunks (v0.8.1) — for shells that stop a command after a few minutes (the Mac shell: 3 min).
Run it again until it prints DONE; finished chunks are kept between runs (out/_chunks/), so nothing is rendered twice.
usage: python render_resume.py <project> [--workers 2] [--budget 140] [--crf 18] [--name Slug] [--preview] [--silent] [--force]
Same gates as render.py (fresh audit; out/mix.wav newer than the audit unless --silent). Output = render.py's:
out/<name>_final.mp4 (or _preview.mp4). If the timeline changes between runs, the chunks are discarded and it starts over."""
import argparse, json, shutil, subprocess, sys, time
from es import project, cfg, timeline_hash, page, FPS, TOOLS

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--workers', type=int, default=2)
ap.add_argument('--budget', type=float, default=140); ap.add_argument('--crf', type=int, default=18); ap.add_argument('--name')
ap.add_argument('--preview', action='store_true'); ap.add_argument('--silent', action='store_true'); ap.add_argument('--force', action='store_true')
a = ap.parse_args(); P = project(a.project); O = P / 'out'; O.mkdir(exist_ok=True); t0 = time.time()
qa = P / '.qa_pass'
if not a.force:
    if not qa.exists(): sys.exit('BLOCKED: run audit.py first (no .qa_pass).')
    if json.loads(qa.read_text())['hash'] != timeline_hash(P): sys.exit('BLOCKED: timeline changed since the last audit — re-run audit.py.')
mix = O / 'mix.wav'
if not a.silent and not mix.exists(): sys.exit('BLOCKED: out/mix.wav missing — run audio.py (or pass --silent).')
if not a.silent and qa.exists() and mix.stat().st_mtime < qa.stat().st_mtime - 1: sys.exit('BLOCKED: mix.wav is older than the last audit — re-run audio.py.')
fps = 15 if a.preview else FPS; crf = 26 if a.preview else a.crf
C = O / '_chunks'; C.mkdir(exist_ok=True); stamp = C / 'timeline.txt'
th = timeline_hash(P) + ('-preview' if a.preview else '') + f'-crf{crf}'
if not stamp.exists() or stamp.read_text() != th:
    shutil.rmtree(C); C.mkdir(); stamp.write_text(th)
with page(P) as pg: total = pg.evaluate('TOTAL')
N = int(round(total * fps)); step = 10 * fps; chunks = [(k, k * step, min(N, (k + 1) * step)) for k in range((N + step - 1) // step)]
done = lambda k: (C / f'c{k:03d}.mp4').exists()
batch_s = None
while True:
    todo = [c for c in chunks if not done(c[0])]
    if not todo: break
    if batch_s and time.time() - t0 + batch_s > a.budget:
        print(f'RESUME: {len(chunks) - len(todo)}/{len(chunks)} chunks done ({time.time() - t0:.0f} s) — run the same command again'); sys.exit(0)
    b0 = time.time(); procs = []
    for k, f0, f1 in todo[:a.workers]:
        procs.append((k, subprocess.Popen([sys.executable, str(TOOLS / 'render.py'), str(P), '--crf', str(crf)] + (['--preview'] if a.preview else [])
                                          + ['--_w', str(f0), str(f1), f'9{k:03d}'], stdout=subprocess.DEVNULL)))
    for k, p in procs:
        if p.wait(): sys.exit(f'chunk {k} failed')
        (O / f'seg_9{k:03d}.mp4').replace(C / f'c{k:03d}.mp4')
    batch_s = time.time() - b0
    print(f'  chunks {[k for k, _ in procs]} in {batch_s:.0f} s', flush=True)
lst = C / 'list.txt'; lst.write_text(''.join(f"file 'c{k:03d}.mp4'\n" for k, _, _ in chunks))
video = C / 'video_only.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(video)], check=True)
name = a.name or cfg(P).get('slug') or P.name
final = O / f'{name}_{"preview" if a.preview else "final"}.mp4'
if a.silent: video.replace(final)
else:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(mix), '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-shortest', str(final)], check=True)
shutil.rmtree(C)
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(final)]))
print(f'DONE: {final} — duration {float(pr["format"]["duration"]):.2f}s (timeline {total:.2f}s)')
print('next: python tools/check_final.py', P)
