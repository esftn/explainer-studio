#!/usr/bin/env python3
"""finish.py (v0.6) — ONE command for the whole Finish chat. Nothing to remember, nothing to skip.

  CLOUD (after the preview is approved and the cover is chosen):
    python3 engine/tools/finish.py videoNN --slug Bridge_Metro --cover A --guard mac_fp.json --who "Finish ep20 …" [--render] [--out xfer]
  MAC (after unpack says VERIFIED):
    python3 _series/tools/finish.py videoNN --verify [--who "Finish ep20 …"]      (from the VIDEO GEN folder)

CLOUD steps, in order — it stops at the first thing a human must fix and says exactly what:
  1  preflight      stage = preview-approved, script/facts hash = approved one, captions_en.json + publish.txt exist
  2  render         audio.py + render.py when out/<slug>_reel_9x16.mp4 is missing (or --render)
  3  check + fix    check_final.py on the reel; audio longer than video → tpad clone fix, re-checked; length ≤ project.json max_len
  4  feed           4:5 cut = crop=1080:1350:0:285 from the un-baked reel, checked
  5  covers         out/_cover_<NAME>_9x16.png / _4x5.png → cover_reel_9x16.png / cover_feed_4x5.png
  6  bake           cover as frame 1 in both videos (skipped when the first frame already IS the cover, SSIM ≥ 0.95), verified
  7  captions       make_srt.py, then the pair is validated: equal cue counts, none past the end, overlaps clamped
  8  publish.txt    publint.py: no placeholders, all sections, title ≤ 70 — a FAIL stops here, before anything is delivered
  9  deliver        pack.py check --final, state approve cover + stage delivered, state_check --fix, tidy --apply,
                    docs/delivery.md written FROM the measurements, pack --set final (guarded) + the commit plan
MAC --verify: layout, sizes, first frame = cover, captions pair, publish lint, state_check --fix, tidy, tracker regenerated, lock released.
Exit 0 = done; 2 = a person must fix something (printed); 1 = a tool failed."""
import argparse, datetime as dt, json, pathlib, re, shutil, subprocess, sys
sys.dont_write_bytecode = True      # the Mac folder can't delete: no __pycache__ litter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import publint, state_check, series_tracker as st                      # noqa: E402

OK, STOP = 0, 2
FEED_CROP = 'crop=1080:1350:0:285'
ssim_min = 0.95


def say(tag, msg): print(f'{tag:<6} {msg}', flush=True)


def stop(msg, fixes=()):
    say('STOP', msg)
    for f in fixes: print('       · ' + f)
    sys.exit(STOP)


def run(cmd, check=True, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if check and r.returncode:
        print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(f'FAILED: {" ".join(str(c) for c in cmd[:4])}…')
    return r


def tool(name): return HERE / name


def jread(f, default=None):
    try: return json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
    except Exception: return default


def pj(P): return jread(P / 'project.json', {})


def probe(f):
    r = st.probe(f); return r or {}


def fix_av(f):
    """audio longer than video → hold the last frame (tpad clone); video longer than audio → pad the audio with silence."""
    p = probe(f); dv, da = p.get('v') or 0, p.get('a') or 0
    if abs(dv - da) < 0.1: return False
    tmp = f.with_suffix('.fix.mp4')
    if da > dv:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', f, '-vf', f'tpad=stop_mode=clone:stop_duration={da - dv + 0.04:.3f}', '-c:v', 'libx264', '-crf', '18',
               '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'copy', '-movflags', '+faststart', tmp]
    else:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', f, '-c:v', 'copy', '-af', f'apad=whole_dur={dv:.3f}', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', tmp]
    run(cmd); tmp.replace(f); say('FIX', f'{f.name}: audio {da:.2f} s / video {dv:.2f} s → made equal'); return True


def check_final(P, f):
    r = run([sys.executable, tool('check_final.py'), P, '--file', f.relative_to(P)], check=False)
    return r.returncode == 0, r.stdout


def clamp_srt(f):
    """overlapping cues → end the earlier cue 10 ms before the next one starts. Returns number fixed."""
    t = f.read_text(encoding='utf-8'); pat = re.compile(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)')
    ms = lambda s: (lambda h, m, x, y: ((int(h) * 60 + int(m)) * 60 + int(x)) * 1000 + int(y))(*re.split(r'[:,]', s))
    fm = lambda v: f'{v // 3600000:02d}:{v // 60000 % 60:02d}:{v // 1000 % 60:02d},{v % 1000:03d}'
    ms_ = list(pat.finditer(t)); n = 0; out = []; last = 0
    for i, m in enumerate(ms_):
        s, e = ms(m.group(1)), ms(m.group(2))
        if i + 1 < len(ms_):
            ns = ms(ms_[i + 1].group(1))
            if e > ns - 10: e = max(s + 200, ns - 10); n += 1
        out.append(t[last:m.start()]); out.append(f'{fm(s)} --> {fm(e)}'); last = m.end()
    out.append(t[last:]); f.write_text(''.join(out), encoding='utf-8'); return n


def captions_ok(P, dur, fix=True):
    a, b = P / 'out' / 'captions.bn_IN.srt', P / 'out' / 'captions.en_US.srt'; bad = []
    for f in (a, b):
        if not f.exists(): bad.append(f'{f.name} missing')
    if bad: return bad
    n = sum(clamp_srt(f) for f in (a, b)) if fix else 0
    if n: say('FIX', f'{n} overlapping caption cue(s) clamped')
    ca, cb = st.srt_cues(a), st.srt_cues(b)
    if len(ca) != len(cb): bad.append(f'bn has {len(ca)} cues, en has {len(cb)}')
    for nm, c in (('bn', ca), ('en', cb)):
        if not c: bad.append(f'{nm} captions empty'); continue
        if c[-1][1] > dur + 0.2: bad.append(f'{nm}: last cue ends {c[-1][1]:.2f} s, after the video ({dur:.2f} s)')
        if any(e <= s for s, e in c): bad.append(f'{nm}: a cue has zero/negative length')
    if len(ca) == len(cb) and any(abs(x[0] - y[0]) > 0.001 for x, y in zip(ca, cb)): bad.append('bn and en cue times differ')
    return bad


def cover_is_baked(video, cover):
    s = st.cover_ssim(video, cover); return s is not None and s >= ssim_min, s


def slugs(P, args):
    s = args.slug or pj(P).get('slug') or P.name
    return re.sub(r'[^A-Za-z0-9_]+', '_', s).strip('_') or P.name


def ep_no(P):
    S = jread(P / 'state.json', {}); e = S.get('ep') or re.sub(r'\D', '', P.name)
    return str(e).zfill(2)


# ------------------------------------------------------------------ CLOUD
def cloud(a):
    P = pathlib.Path(a.project).resolve(); out = P / 'out'; slug = slugs(P, a); S = jread(P / 'state.json', {}); C = pj(P)
    reel, feed = out / f'{slug}_reel_9x16.mp4', out / f'{slug}_feed_4x5.mp4'
    cr, cf = out / 'cover_reel_9x16.png', out / 'cover_feed_4x5.png'
    say('1/9', 'preflight')
    problems = []
    if S.get('stage') not in ('preview-approved', 'delivered'):
        problems.append(f"state.json stage is '{S.get('stage')}', not preview-approved — the creator has not approved the preview (state.py approve preview)")
    if 'preview' not in (S.get('approved') or {}): problems.append('preview approval is not recorded in state.json')
    sp = jread(P / '.script_pass', {});
    try:
        from es import file_hash
        if sp.get('hash') != file_hash(P / 'script.json', P / 'facts.json'): problems.append('script.json / facts.json changed since script_check PASS — run script_check.py and get the script re-approved')
    except Exception as e: problems.append(f'cannot verify script hash: {e}')
    if not (P / 'docs' / 'captions_en.json').exists(): problems.append('docs/captions_en.json missing — translate docs/captions_bn_cues.json (run make_srt.py first)')
    if not (out / 'publish.txt').exists(): problems.append('out/publish.txt missing — write it from templates/publish.md')
    if not (cr.exists() and cf.exists()) and not a.cover: problems.append('no cover: pass --cover <NAME> (the chosen out/_cover_<NAME>_9x16.png / _4x5.png)')
    base = P / '.studio_base.json'
    if base.exists() and not a.guard and not a.no_guard: problems.append('this folder was pulled with the push guard: run `guard.py fingerprint` on the Mac, stage the file and pass --guard <file> (or --no-guard if the creator said so)')
    if problems: stop('preflight failed', problems)

    say('2/9', 'render')
    if a.render or not (reel.exists() or (out / f'{slug}_final.mp4').exists()):
        run([sys.executable, tool('audio.py'), P]); r = run([sys.executable, tool('render.py'), P, '--workers', '2', '--name', slug]); print(r.stdout.strip().splitlines()[-1])
    if not reel.exists() and (out / f'{slug}_final.mp4').exists(): shutil.move(str(out / f'{slug}_final.mp4'), reel)
    if not reel.exists(): stop(f'{reel.name} missing after render')
    nocover = P / 'drafts' / (reel.stem + '_nocover.mp4')
    src = nocover if nocover.exists() else reel                       # un-baked source for the feed cut

    say('3/9', 'check + A/V fix')
    if not nocover.exists(): fix_av(reel)
    ok, txt = check_final(P, src if nocover.exists() else reel)
    if not ok: print(txt); stop('check_final failed on the reel (loudness / peak / size / silence) — re-run audio.py or fix the cause')
    dur = probe(reel).get('v') or 0; mx = C.get('max_len', 60)
    if dur > mx + 0.05 - (1 / 30 if nocover.exists() else 0) and not a.allow_long: stop(f'reel is {dur:.2f} s, over max_len = {mx} s (project.json)', ['cut it in Build, or ask the creator to waive: rerun with --allow-long'])
    say('OK', f'reel {dur:.2f} s')

    say('4/9', 'feed 4:5')
    if not feed.exists():
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', FEED_CROP, '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30',
             '-c:a', 'copy', '-movflags', '+faststart', feed])
        fix_av(feed)
    if not (P / 'drafts' / (feed.stem + '_nocover.mp4')).exists():
        ok, txt = check_final(P, feed)
        if not ok: print(txt); stop('check_final failed on the feed cut')

    say('5/9', 'covers')
    if a.cover:
        c9 = next(iter(sorted(out.glob(f'_cover_{a.cover}_9x16.png')) or sorted(out.glob(f'_cover_*{a.cover}*_9x16.png'))), None)
        if not c9: stop(f'no cover candidate named {a.cover}', [f'looked for out/_cover_{a.cover}_9x16.png (make it with cover.py)'])
        c4 = pathlib.Path(str(c9).replace('_9x16.png', '_4x5.png'))
        if not c4.exists(): stop(f'{c4.name} missing next to {c9.name}')
        shutil.copy2(c9, cr); shutil.copy2(c4, cf); say('OK', f'cover {c9.name} → cover_reel_9x16.png, cover_feed_4x5.png')

    say('6/9', 'bake cover as frame 1')
    for v, cvr in ((reel, cr), (feed, cf)):
        baked, s = cover_is_baked(v, cvr)
        if baked: say('OK', f'{v.name} already starts with the cover (SSIM {s:.2f}) — not baked twice'); continue
        run([sys.executable, tool('bake_cover.py'), P, '--video', v.relative_to(P), '--cover', cvr.relative_to(P)])
        baked, s = cover_is_baked(v, cvr)
        if not baked: stop(f'{v.name}: after baking, frame 1 is not the cover (SSIM {s})')
        pr = probe(v)
        if abs((pr.get('v') or 0) - (pr.get('a') or 0)) > 0.1: fix_av(v)
        say('OK', f'{v.name} baked (SSIM {s:.2f})')
    dur = probe(reel).get('v') or dur

    say('7/9', 'captions')
    have = (out / 'captions.bn_IN.srt').exists() and (out / 'captions.en_US.srt').exists()
    if a.rebuild_captions or not have:
        r = run([sys.executable, tool('make_srt.py'), P], check=False)
        if r.returncode: print(r.stdout, r.stderr); stop('make_srt failed', ['docs/captions_en.json must have exactly one line per Bangla cue (docs/captions_bn_cues.json)'])
    else: say('OK', 'captions already exist — kept as they are (--rebuild-captions to regenerate)')
    bad = captions_ok(P, dur)
    en = jread(P / 'docs' / 'captions_en.json', [])
    if en and len(en) != len(st.srt_cues(out / 'captions.en_US.srt')): bad.append(f'docs/captions_en.json has {len(en)} lines, out/captions.en_US.srt has {len(st.srt_cues(out / "captions.en_US.srt"))} cues — rebuild with --rebuild-captions')
    if bad: stop('captions are not a valid pair', bad)
    say('OK', f"{len(st.srt_cues(out / 'captions.bn_IN.srt'))} cues in both languages")

    say('8/9', 'publish.txt')
    f, w = publint.lint(out / 'publish.txt', P / 'facts.json')
    for x in w: say('WARN', x)
    if f: stop('publish.txt is not finished', f)
    say('OK', 'no placeholders, all sections present')

    say('9/9', 'deliver')
    if 'cover' not in (S.get('approved') or {}): run([sys.executable, tool('state.py'), P, 'approve', 'cover', '--note', a.cover or 'cover chosen'])
    if jread(P / 'state.json', {}).get('stage') != 'delivered': run([sys.executable, tool('state.py'), P, 'stage', 'delivered'])
    run([sys.executable, tool('state_check.py'), P, '--fix'], check=False)
    run([sys.executable, tool('tidy.py'), P, '--apply'])
    rpt = write_delivery(P, slug, reel, feed, a)
    r = run([sys.executable, tool('pack.py'), 'check', P, '--final', '--working'], check=False); print(r.stdout.strip())
    if r.returncode: stop('pack check failed', r.stdout.splitlines())
    xfer = pathlib.Path(a.out or '/tmp/xfer').resolve(); name = f'final{ep_no(P)}'
    cmd = [sys.executable, tool('pack.py'), 'pack', P, '--set', 'final', '--no-images', '--out', xfer, '--name', name]
    if a.guard: cmd += ['--guard', a.guard, '--who', a.who or '']
    if a.force: cmd += ['--force']
    r = run(cmd, check=False); print(r.stdout.strip())
    if r.returncode: stop('push guard refused — nothing was packed', r.stdout.splitlines())
    parts = sorted(xfer.glob(f'{name}.part_*')) + [xfer / f'{name}.manifest.json']
    batches, cur, size = [], [], 0
    for p in parts:
        if cur and size + p.stat().st_size > 90e6: batches.append(cur); cur, size = [], 0
        cur.append(p); size += p.stat().st_size
    batches.append(cur)
    print(f'\nCOMMIT PLAN — {len(parts)} files in {len(batches)} commit call(s) (≤ 90 MB each), destination videoNN/_to_delete/ on the Mac:')
    for i, b in enumerate(batches, 1): print(f'  call {i}: ' + ', '.join(f'{p.name} ({p.stat().st_size / 1e6:.1f} MB)' for p in b))
    print(f'THEN on the Mac, from the VIDEO GEN folder:\n  python3 _series/tools/pack.py unpack {P.name}/_to_delete --name {name} --into {P.name}   → must print VERIFIED\n  python3 _series/tools/finish.py {P.name} --verify' + (f' --who "{a.who}"' if a.who else '') + '   → must print DONE')
    print(f'\nREPORT {rpt.relative_to(P)} written. Reply to the creator with: length, folder, cover letter, the single-source caveats, and "empty _to_delete/".')


def write_delivery(P, slug, reel, feed, a):
    F = jread(P / 'facts.json', {}); S = jread(P / 'state.json', {}); A = jread(P / 'audio_config.json', {})
    pr, pf = probe(reel), probe(feed)
    log = run(['ffmpeg', '-i', reel, '-af', 'ebur128=peak=true', '-f', 'null', '-'], check=False).stderr
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', log); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', log)
    vo = (P / 'vo.js').read_text(encoding='utf-8') if (P / 'vo.js').exists() else ''
    C = pj(P); tempo = (C.get('vo') or {}).get('tempo')
    cm = re.search(r'^TITLE[^\n]*\n(.+)$', (P / 'out' / 'publish.txt').read_text(encoding='utf-8'), re.M)
    single = [f"{k}: {v.get('single_source_note')}" for k, v in (F.get('facts') or {}).items() if isinstance(v, dict) and v.get('single_source_note')] if isinstance(F.get('facts'), dict) else \
             [f"{x.get('id', '?')}: {x['single_source_note']}" for x in (F.get('facts') or []) if x.get('single_source_note')]
    L = [f"# Delivery — ep {ep_no(P)} · {S.get('title') or (cm.group(1) if cm else '')}", '',
         f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M UTC} by finish.py from the files (not typed).", '',
         f"- Title (publish.txt): {cm.group(1).strip() if cm else '?'}",
         f"- Reel: {reel.name} · {pr.get('w')}x{pr.get('h')} · {pr.get('v', 0):.2f} s · {reel.stat().st_size / 1e6:.1f} MB",
         f"- Feed: {feed.name} · {pf.get('w')}x{pf.get('h')} · {pf.get('v', 0):.2f} s · {feed.stat().st_size / 1e6:.1f} MB",
         f"- Loudness {I[-1] if I else '?'} LUFS · true peak {TP[-1] if TP else '?'} dBTP",
         f"- Cover: {(S.get('approved') or {}).get('cover', {}).get('note', '?')} (baked as frame 1 in both videos)",
         f"- Captions: {len(st.srt_cues(P / 'out' / 'captions.bn_IN.srt'))} cues bn_IN + en_US",
         f"- VO tempo {tempo or '?'} · pad {C.get('pad', '?')} · end hold {C.get('end_hold', '?')} s · voOffset {C.get('voOffset', '?')} (project.json)",
         f"- Rules: max_len {C.get('max_len', 60)} s · facts_gate {(C.get('rules') or {}).get('facts_gate', False)}",
         '', '## Single-source caveats (also in the pinned comment)'] + (['- ' + x for x in single] or ['- none']) + \
        ['', '## Next', '- Post; set the cover in the upload screen; empty videoNN/_to_delete/.']
    f = P / 'docs' / 'delivery.md'; f.write_text('\n'.join(L) + '\n', encoding='utf-8'); return f


# ------------------------------------------------------------------ MAC
def verify(a):
    P = pathlib.Path(a.project).resolve(); bad = []
    say('1/5', 'tidy'); print(run([sys.executable, HERE / 'tidy.py', P, '--apply'], check=False).stdout.strip())
    say('2/5', 'layout'); r = run([sys.executable, HERE / 'pack.py', 'check', P, '--final'], check=False); print(r.stdout.strip())
    if r.returncode: bad += [l[5:] for l in r.stdout.splitlines() if l.startswith('FAIL')]
    say('3/5', 'state'); run([sys.executable, HERE / 'state_check.py', P, '--fix'], check=False)
    bad += ['state.json: ' + x for x in state_check.check(P, fix=False)]
    say('4/5', 'files'); E = st.episode(P, True); bad += [x for x in E['problems'] if not x.startswith('state.json')]
    if E['dur'] is None: bad.append('no reel found')
    say('5/5', 'tracker + lock')
    root = next((c for c in [P, *P.parents] if (c / '_series' / 'tools' / 'series_tracker.py').exists()), None)
    if root: print(run([sys.executable, root / '_series' / 'tools' / 'series_tracker.py', '--root', root, '--write'], check=False).stdout.strip())
    if bad:
        for b in dict.fromkeys(bad): say('FAIL', b)
        stop('verification failed — do not tell the creator it is done', [])
    if a.who:
        import guard; guard.cmd_release(argparse.Namespace(project=str(P), who=a.who, force=True))
    say('DONE', f"{P.name}: reel {E['dur']:.2f} s, 7/7 finals, cover baked, captions {E['cues'][0]}/{E['cues'][1]}, publish.txt clean, state consistent")


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('project'); ap.add_argument('--slug'); ap.add_argument('--cover', help='chosen cover name, e.g. A (out/_cover_A_9x16.png)')
ap.add_argument('--render', action='store_true'); ap.add_argument('--out', help='transfer folder (default /tmp/xfer)')
ap.add_argument('--guard', help='Mac fingerprint json from guard.py'); ap.add_argument('--who'); ap.add_argument('--no-guard', action='store_true')
ap.add_argument('--force', action='store_true'); ap.add_argument('--rebuild-captions', action='store_true'); ap.add_argument('--allow-long', action='store_true', help='the creator waived the length limit')
ap.add_argument('--verify', action='store_true', help='MAC mode: verify an unpacked delivery, tidy, regenerate the tracker, release the lock')
a = ap.parse_args()
(verify if a.verify else cloud)(a)
