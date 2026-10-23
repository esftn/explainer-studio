#!/usr/bin/env python3
"""Episode lock + push guard (v0.6). Stops a second chat from overwriting an episode someone else is working on.
Pure standard library; runs on the Mac (where the truth lives) and in the cloud workspace. A copy sits in every
videoNN/.studio/ and in VIDEO GEN/_series/tools/.

  guard.py claim <videoNN> --who "Build ep21 (chat 2026-10-23 10:40)" [--stage build] [--hours 12] [--force]
        take the episode. Refuses (exit 3) when another chat holds a fresh lock. Run it on the Mac folder.
  guard.py release <videoNN> --who "<same label>"        (the folder can't delete: the lock is marked released)
  guard.py status <videoNN>                              who holds it, since when, last change of the sources, stage
  guard.py fingerprint <videoNN> [--out file.json]       hashes of every source file (what a build is made of)
  guard.py base <videoNN>                                save the fingerprint as .studio_base.json — run right after pulling
  guard.py check-push <local videoNN> --mac mac_fp.json [--who X] [--force]
        BEFORE pushing: the Mac copy must still be what you pulled (no other chat changed it) and the lock must be yours.
        Exit 2 = conflict (lists the files); nothing is pushed.

Typical build chat:
  Mac:    python3 _series/tools/guard.py claim video21 --who "Build ep21 …"            (refused → stop, tell the creator)
  pull → cloud:  python3 engine/tools/guard.py base video21
  … work …
  Mac:    python3 _series/tools/guard.py fingerprint video21 --out video21/_to_delete/mac_fp.json   → stage that file
  cloud:  python3 engine/tools/guard.py check-push video21 --mac mac_fp.json --who "Build ep21 …"  → push only on OK
  Mac:    python3 _series/tools/guard.py release video21 --who "Build ep21 …"
"""
import argparse, datetime as dt, hashlib, json, pathlib, socket, sys

SOURCES = ['project.json', 'index.html', 'scenes.json', 'cues.json', 'vo.js', 'facts.json', 'script.json', 'vo_tags.json', 'ext.js',
           'audio_config.json', 'cover_*.html', 'docs/*.md', 'docs/*.json']
SOURCE_DIRS = [('vo/raw', '*'), ('.studio', '*.py'), ('images', '*'), ('img', '*')]
LOCK = '.lock.json'
BASE = '.studio_base.json'


def sha(f):
    h = hashlib.sha256()
    with open(f, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''): h.update(b)
    return h.hexdigest()[:20]


def fingerprint(P, skip=()):
    P = pathlib.Path(P).resolve(); files = {}
    for pat in SOURCES:
        for f in sorted(P.glob(pat)):
            if f.is_file(): files[f.relative_to(P).as_posix()] = sha(f)
    for d, pat in SOURCE_DIRS:
        for f in sorted((P / d).glob(pat)) if (P / d).is_dir() else []:
            if f.is_file() and not f.name.startswith('.'): files[f.relative_to(P).as_posix()] = f'{f.stat().st_size}:{sha(f) if f.stat().st_size < 30_000_000 else "big"}'
    files = {k: v for k, v in files.items() if k.split('/')[0] not in skip}
    stage = None
    try: stage = json.loads((P / 'state.json').read_text()).get('stage')
    except Exception: pass
    return {'project': P.name, 'time': now(), 'stage': stage, 'skip': list(skip), 'lock': read_lock(P), 'files': files}


def now():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def age_h(t):
    try: return (dt.datetime.now(dt.timezone.utc) - dt.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)).total_seconds() / 3600
    except Exception: return 1e9


def read_lock(P):
    f = pathlib.Path(P) / LOCK
    try: return json.loads(f.read_text())
    except Exception: return None


def live(lock, hours):
    return bool(lock) and not lock.get('released') and age_h(lock.get('since', '')) < hours


def cmd_claim(a):
    P = pathlib.Path(a.project).resolve(); L = read_lock(P)
    if live(L, a.hours) and L['who'] != a.who and not a.force:
        print(f"REFUSED: {P.name} is held by \"{L['who']}\" ({L.get('stage', '?')}, since {L['since']}, {age_h(L['since']):.1f} h ago).")
        print('Do not build or push this episode. Ask the creator whether that chat is finished; then re-run with --force.')
        sys.exit(3)
    rec = {'who': a.who, 'stage': a.stage, 'since': now() if not (L and L.get('who') == a.who and not L.get('released')) else L['since'],
           'renewed': now(), 'host': socket.gethostname(), 'released': False}
    if L and L.get('who') != a.who and live(L, a.hours): rec['took_over_from'] = L['who']
    (P / LOCK).write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    print(f'CLAIMED {P.name} for "{a.who}"' + (f" (took over from \"{rec['took_over_from']}\")" if rec.get('took_over_from') else ''))


def cmd_release(a):
    P = pathlib.Path(a.project).resolve(); L = read_lock(P)
    if not L: print('no lock'); return
    if L.get('who') != a.who and not a.force and not L.get('released'):
        print(f"REFUSED: the lock belongs to \"{L['who']}\""); sys.exit(3)
    L['released'] = True; L['released_at'] = now()
    (P / LOCK).write_text(json.dumps(L, ensure_ascii=False, indent=1)); print(f'RELEASED {P.name}')


def cmd_status(a):
    P = pathlib.Path(a.project).resolve(); L = read_lock(P)
    fp = fingerprint(P)
    if not L: print(f'{P.name}: no lock')
    elif L.get('released'): print(f"{P.name}: free (last held by \"{L['who']}\", released {L.get('released_at')})")
    else: print(f"{P.name}: HELD by \"{L['who']}\" ({L.get('stage', '?')}) since {L['since']} — {age_h(L['since']):.1f} h ago")
    print(f"stage: {fp['stage']} · {len(fp['files'])} source files")
    newest = max(((P / r).stat().st_mtime, r) for r in fp['files']) if fp['files'] else None
    if newest: print('last change: ' + dt.datetime.fromtimestamp(newest[0], dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC') + f' ({newest[1]})')
    prev = sorted((P / 'drafts').glob('*_preview.mp4')) if (P / 'drafts').is_dir() else []
    if prev: print('previews: ' + ', '.join(f"{f.name} ({dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc):%m-%d %H:%M})" for f in prev))


def cmd_fingerprint(a):
    fp = fingerprint(a.project)
    txt = json.dumps(fp, ensure_ascii=False, indent=1)
    if a.out: pathlib.Path(a.out).write_text(txt); print(f'fingerprint of {fp["project"]}: {len(fp["files"])} files → {a.out}')
    else: print(txt)


def write_base(P, skip=()):
    P = pathlib.Path(P).resolve(); fp = fingerprint(P, skip)
    (P / BASE).write_text(json.dumps(fp, ensure_ascii=False, indent=1)); return fp


def cmd_base(a):
    fp = write_base(a.project, ['images', 'img'] if a.no_images else ())
    print(f'base saved: {len(fp["files"])} source files ({BASE})')


def check_push_data(P, mac, who=None):
    """-> list of problems (empty = safe to push). mac = the Mac-side fingerprint dict."""
    P = pathlib.Path(P).resolve(); bf = P / BASE
    if not bf.exists(): return [f'no {BASE}: this folder was not pulled with the guard']
    b = json.loads(bf.read_text()); base = b['files']; skip = set(b.get('skip') or [])
    mf = {k: v for k, v in mac['files'].items() if k.split('/')[0] not in skip}
    problems = []
    for k in sorted(set(base) | set(mf)):
        if base.get(k) != mf.get(k):
            problems.append(('changed on the Mac' if k in base and k in mf else 'added on the Mac' if k in mf else 'removed on the Mac') + f': {k}')
    lock = mac.get('lock')
    if lock and who and not lock.get('released') and lock.get('who') != who and age_h(lock.get('since', '')) < 12:
        problems.append(f"locked by \"{lock['who']}\"")
    return problems


def cmd_check_push(a):
    P = pathlib.Path(a.project).resolve()
    problems = check_push_data(P, json.loads(pathlib.Path(a.mac).read_text()), a.who)
    if problems and not a.force:
        print(f"REFUSED: pushing would overwrite someone else's work in {P.name}:")
        for p in problems[:25]: print('  · ' + p)
        if len(problems) > 25: print(f'  · … and {len(problems) - 25} more')
        print('Do NOT push. Pull the Mac copy again, merge what you need, or ask the creator which version wins.')
        sys.exit(2)
    print(f'OK to push {P.name}: the Mac copy is unchanged since the pull' + (' (FORCED)' if problems else ''))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    x = sp.add_parser('claim'); x.add_argument('project'); x.add_argument('--who', required=True); x.add_argument('--stage', default='build')
    x.add_argument('--hours', type=float, default=12); x.add_argument('--force', action='store_true')
    x = sp.add_parser('release'); x.add_argument('project'); x.add_argument('--who', required=True); x.add_argument('--force', action='store_true')
    x = sp.add_parser('status'); x.add_argument('project')
    x = sp.add_parser('fingerprint'); x.add_argument('project'); x.add_argument('--out')
    x = sp.add_parser('base'); x.add_argument('project'); x.add_argument('--no-images', action='store_true')
    x = sp.add_parser('check-push'); x.add_argument('project'); x.add_argument('--mac', required=True); x.add_argument('--who'); x.add_argument('--force', action='store_true')
    a = ap.parse_args()
    {'claim': cmd_claim, 'release': cmd_release, 'status': cmd_status, 'fingerprint': cmd_fingerprint, 'base': cmd_base, 'check-push': cmd_check_push}[a.cmd](a)


if __name__ == '__main__':
    main()
