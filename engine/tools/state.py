"""Episode state: what is approved, what is next. It is how a new chat picks up an episode without re-reading
the old one (read `state.py show` first, never old transcripts).
usage: python state.py <project> show
       python state.py <project> init --ep 04 --title "…" [--slug …]
       python state.py <project> approve brief|script|style|preview|cover [--note "…"]
       python state.py <project> stage <stage>            (vo-received, built, delivered, …)
       python state.py <project> note "decision or open item"    |   done "open item text"
Writes state.json (machine) + docs/state.md (readable). Approving the script stores the hash of script.json +
facts.json; vo_text.py refuses to make the VO text for any other version."""
import argparse, json, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from es import file_hash

STAGES = ['plan', 'brief-approved', 'script-approved', 'folders-ready', 'vo-received', 'style-approved', 'built', 'preview-approved', 'delivered']
NEXT = {'plan': 'Plan chat: approve the brief (new-video)',
        'brief-approved': 'Plan chat: research → facts.json → script → script_check PASS → creator approves (video-script)',
        'script-approved': 'Plan chat: send VO text + image list in one message, then prepare the folders (studio.py new …)',
        'folders-ready': 'Creator: drop images in images/ and the single VO take in vo/raw/vo_full.mp3, then open a chat: "Build episode NN"',
        'vo-received': 'Build chat: vo_split → vo_prep → style frames (video-preview)',
        'style-approved': 'Build chat: build all scenes → audit PASS → key-moment sheet → preview (video-preview)',
        'built': 'Creator: watch the preview + key-moment sheet, send timestamped notes or approve',
        'preview-approved': 'Finish chat: render, captions, covers, bake, deliver (video-render)',
        'delivered': 'Done. Post it; log the cover in the series brief.'}
ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('cmd')
ap.add_argument('arg', nargs='?'); ap.add_argument('--note'); ap.add_argument('--ep'); ap.add_argument('--title'); ap.add_argument('--slug')
a = ap.parse_args(); P = pathlib.Path(a.project).resolve(); F = P / 'state.json'
S = json.loads(F.read_text()) if F.exists() else {'ep': None, 'title': None, 'slug': None, 'stage': 'plan', 'approved': {}, 'open': [], 'log': []}
now = time.strftime('%Y-%m-%d %H:%M')


def log(m): S['log'].append(f'{now} {m}')


if a.cmd == 'init':
    S.update({k: v for k, v in (('ep', a.ep), ('title', a.title), ('slug', a.slug or P.name)) if v}); log('init')
elif a.cmd == 'approve':
    what = a.arg
    if what not in ('brief', 'script', 'style', 'preview', 'cover'): sys.exit('approve brief|script|style|preview|cover')
    rec = {'time': now}
    if a.note: rec['note'] = a.note
    if what == 'script':
        sp = P / '.script_pass'; cur = file_hash(P / 'script.json', P / 'facts.json')
        if not sp.exists() or json.loads(sp.read_text()).get('hash') != cur:
            sys.exit('BLOCKED: script_check.py must PASS on this exact script before it can be approved')
        rec['hash'] = cur
    S['approved'][what] = rec
    S['stage'] = {'brief': 'brief-approved', 'script': 'script-approved', 'style': 'style-approved',
                  'preview': 'preview-approved', 'cover': S['stage']}[what]
    log(f'approved {what}' + (f' — {a.note}' if a.note else ''))
elif a.cmd == 'stage':
    if a.arg not in STAGES: sys.exit(f'stage must be one of {STAGES}')
    S['stage'] = a.arg; log(f'stage {a.arg}')
elif a.cmd == 'note':
    S['open'].append(a.arg); log(f'note: {a.arg}')
elif a.cmd == 'done':
    S['open'] = [o for o in S['open'] if o != a.arg]; log(f'done: {a.arg}')
elif a.cmd != 'show':
    sys.exit('commands: show, init, approve, stage, note, done')
if a.cmd != 'show':
    F.write_text(json.dumps(S, ensure_ascii=False, indent=1))
    (P / 'docs').mkdir(exist_ok=True)
    md = [f"# Episode {S.get('ep') or '?'} — {S.get('title') or ''}", '', f"**Stage:** {S['stage']}  ", f"**Next:** {NEXT[S['stage']]}", '',
          '## Approved'] + [f"- {k}: {v['time']}" + (f" — {v['note']}" if v.get('note') else '') for k, v in S['approved'].items()] + \
         ['', '## Open items'] + [f'- {o}' for o in S['open']] + ['', '## Log'] + [f'- {l}' for l in S['log'][-15:]]
    (P / 'docs' / 'state.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print(f"ep {S.get('ep')} · {S.get('title')} · stage: {S['stage']}\nnext: {NEXT[S['stage']]}")
if S['approved']: print('approved: ' + ', '.join(f"{k} ({v['time']})" for k, v in S['approved'].items()))
if S['open']: print('open: ' + ' | '.join(S['open']))
