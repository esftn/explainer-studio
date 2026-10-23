"""Script gate: run BEFORE the creator sees a script, and again after every script edit.
usage: python script_check.py <project> [--today 2026-10-21]
Reads script.json (VO text per scene) and facts.json (every number the video uses). On PASS writes
.script_pass (hash of both files); vo_text.py refuses to make the VO text without it, so nothing reaches the
voiceover unchecked.

FAIL
  · facts.json missing, no "yardstick", or a fact without id/scenes/claim/date/role/chain/source/url
  · a "now" fact older than rules.now_max_months (default 12)        (series rule: Recency)
  · a fact used in a scene but marked "chain": false                  (series rule: Connection)
  · a "math" row that does not compute (expr vs expect, tol), or uses a number (>20) that is not a sourced
    fact — write calculations with fact keys, e.g. "13 * pinnacle_m"     (series rule: one measuring stick)
  · two facts with the same "key" but different values               (numbers must agree everywhere)
  · digits in the VO text (numbers are written as words for the voice)
  · estimated length over max_len (default 60 s)
  · the last scene does not end on a question with the CTA word (rules.ending_cta, default "কমেন্টে")
  · FACTS GATE (v0.6, see factcheck.py; rules.facts_gate, on for new projects): every non-illustrative fact needs a real
    source URL, an exact "quote" with the number (must match the value), a "fetched" date, and a second source or
    "official": true or a "single_source_note"; a number the voice says that is close to — but not — a fact of its
    scene (1.28 spoken, 1.12 sourced) fails; a key that disagrees with ../_series/shared_facts.json fails
WARN
  · a "now" fact older than 6 months (look for a newer figure) · a context fact older than 3 years
  · a scene that speaks about money/amounts but cites no fact or math row
  · length within 3 s of the limit
facts.json format: see templates/facts.json."""
import argparse, ast, datetime as dt, json, operator, re, sys
from es import project, cfg, load_script, strip_tags, speak_chars, norm_word, file_hash
import factcheck

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--today')
ap.add_argument('--register', action='store_true', help='on PASS, add this episode\'s fact keys to ../_series/shared_facts.json')
a = ap.parse_args(); P = project(a.project); C = cfg(P); R = C.get('rules', {})
today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
fails, warns = [], []
SC = load_script(P); N = len(SC)
if sorted(SC) != list(range(1, N + 1)): fails.append(f'script.json scenes must be numbered 1..N (got {sorted(SC)})')
for k, t in SC.items():
    if not strip_tags(t): fails.append(f'scene {k}: empty VO text')
    d = re.findall(r'[0-9০-৯]+', strip_tags(t))
    if d: fails.append(f"scene {k}: digits in the VO text ({', '.join(d[:3])}) — write numbers as words for the voice")

# ---------- length ----------
cps = C.get('vo', {}).get('chars_per_s', 12.5); tempo = C.get('vo', {}).get('tempo', 1.06)
pad = C.get('pad', 0.55); hold = C.get('end_hold', 3.0); max_len = C.get('max_len', 60)
vo_s = sum(speak_chars(t) for t in SC.values()) / cps / tempo
est = vo_s + pad * N + hold + C.get('voOffset', 0.3)
if max_len and est > max_len: fails.append(f'estimated length {est:.1f}s > {max_len}s — cut words before the creator sees it')
elif max_len and est > max_len - 3: warns.append(f'estimated length {est:.1f}s is close to the {max_len}s limit')

# ---------- ending ----------
cta = R.get('ending_cta', 'কমেন্টে')
if N:
    last = strip_tags(SC[N])
    q = re.split(r'(?<=[।!])\s+', last)
    if '?' not in last or (cta and cta not in last):
        fails.append(f'scene {N} (ending): must ask the viewer a question and include "{cta}" (series rule: Endings)')

# ---------- facts ----------
ff = P / 'facts.json'
cited = set()
if not ff.exists():
    fails.append('facts.json missing — every number the video uses needs a row (see templates/facts.json)')
    F = {}
else:
    try: F = json.loads(ff.read_text())
    except json.JSONDecodeError as e: fails.append(f'facts.json is not valid JSON: {e}'); F = {}
if F and not F.get('yardstick'): fails.append('facts.json: no "yardstick" — name the one measuring stick every comparison uses')


def when(s):
    s = str(s)
    for fmt, n in (('%Y-%m-%d', 10), ('%Y-%m', 7), ('%Y', 4)):
        try: return dt.datetime.strptime(s[:n], fmt).date()
        except ValueError: pass
    return None


def months(d):
    return (today.year - d.year) * 12 + today.month - d.month


keys = {}
need = ('id', 'scenes', 'claim', 'date', 'role', 'chain', 'source', 'url')
for f in F.get('facts', []):
    fid = f.get('id', '?')
    miss = [k for k in need if (k not in f or f[k] in ('', None)) and not (k == 'url' and f.get('illustrative'))]
    if miss: fails.append(f'fact {fid}: missing {", ".join(miss)}'); continue
    sc = f['scenes'] or []
    for s in sc:
        if s not in SC: fails.append(f'fact {fid}: scene {s} does not exist')
        cited.add(s)
    d = when(f['date'])
    if not d: fails.append(f"fact {fid}: date '{f['date']}' not understood (use YYYY-MM-DD, YYYY-MM or YYYY)"); continue
    role = f['role']
    if role not in ('now', 'before', 'context'): fails.append(f"fact {fid}: role must be now / before / context, not '{role}'")
    if role == 'now':
        age = months(d)
        if age > R.get('now_max_months', 12): fails.append(f"fact {fid}: a 'now' figure from {f['date']} ({age} months old) — find the latest figure, or present it as 'before'")
        elif age > 6: warns.append(f"fact {fid}: 'now' figure is {age} months old — check for a newer release")
    if role == 'context' and months(d) > 36: warns.append(f"fact {fid}: context figure from {f['date']} is over 3 years old")
    if sc and f['chain'] is False:
        fails.append(f"fact {fid}: used in scene(s) {sc} but off the episode's chain/yardstick — cut it (series rule: Connection)")
    if f.get('key') is not None and f.get('value') is not None:
        keys.setdefault(f['key'], []).append((fid, float(f['value'])))
for k, v in keys.items():
    vals = [x[1] for x in v]
    if max(vals) - min(vals) > 0.01 * max(abs(x) for x in vals):
        fails.append(f"facts with key '{k}' disagree: " + ', '.join(f'{i}={x:g}' for i, x in v))

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}


VARS = {f['key']: float(f['value']) for f in F.get('facts', []) if f.get('key') and f.get('value') is not None}
FACTVALS = [float(f['value']) for f in F.get('facts', []) if f.get('value') is not None]


def calc(e):
    lits = []
    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Name):
            if n.id in VARS: return VARS[n.id]
            raise ValueError(f"'{n.id}' is not a fact key")
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): lits.append(n.value); return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('round', 'int', 'abs') and not n.keywords:
            args = [ev(x) for x in n.args]
            return {'round': lambda *x: round(*[x[0]] + [int(y) for y in x[1:]]), 'int': lambda x: int(x), 'abs': abs}[n.func.id](*args)
        raise ValueError('only fact keys, numbers, + - * / ** ( ), round(), int(), abs() are allowed')
    v = ev(ast.parse(str(e).replace('×', '*').replace('÷', '/'), mode='eval'))
    # every number in a calculation must trace to a sourced fact: big literals must be fact values (use their key)
    loose = [x for x in lits if abs(x) > 20 and not any(abs(x - y) <= 1e-6 * max(abs(y), 1) for y in FACTVALS)]
    return v, loose


for m in F.get('math', []):
    mid = m.get('id', '?')
    for s in m.get('scenes', []): cited.add(s)
    try:
        got, loose = calc(m['expr']); exp = float(m['expect']); tol = float(m.get('tol', 0.02))
        if loose: fails.append(f"math {mid}: number(s) {', '.join(f'{x:g}' for x in loose)} have no fact row — add them as facts and use their keys")
        if abs(got - exp) > tol * max(abs(exp), 1e-9):
            fails.append(f"math {mid} ({m.get('claim', '')}): {m['expr']} = {got:,.4g}, not {exp:,.4g} (±{tol:.0%}) — the numbers disagree")
    except Exception as e:
        fails.append(f"math {mid}: cannot compute '{m.get('expr')}' ({e})")

# ---------- facts gate (v0.6) ----------
if F:
    _f, _w = factcheck.check(P, SC, F, today=today)
    fails += _f; warns += _w

MONEY = ('টাকা', 'ডলার', 'শতাংশ', 'ভাগ', 'কোটি', 'লাখ', 'হাজার', 'মিলিয়ন', 'বিলিয়ন', 'গুণ')
for k, t in SC.items():
    w = [norm_word(x) for x in strip_tags(t).split()]
    if k != N and any(x.startswith(m) for x in w for m in MONEY) and k not in cited:
        warns.append(f'scene {k}: talks about amounts but no fact/math row cites it')

print(f'script: {N} scenes, ≈{vo_s:.1f}s VO → ≈{est:.1f}s video (limit {max_len}s); '
      f'facts: {len(F.get("facts", []))}, math: {len(F.get("math", []))}, yardstick: {F.get("yardstick", "—")}')
for w in warns: print('WARN ', w)
for f in fails: print('FAIL ', f)
sp = P / '.script_pass'
if fails:
    if sp.exists(): sp.unlink()
    print(f'\n{len(fails)} failure(s) — fix the script/facts before the creator sees them.'); sys.exit(1)
sp.write_text(json.dumps({'hash': file_hash(P / 'script.json', P / 'facts.json'), 'date': str(today), 'est': round(est, 1)}))
if a.register: factcheck.check(P, SC, F, register=True); print('registered fact keys in ../_series/shared_facts.json')
print(f'\nSCRIPT PASS ({len(warns)} warnings).')
