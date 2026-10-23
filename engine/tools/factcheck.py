"""Facts gate (v0.6) — the checks that stop a wrong number from ever reaching the voiceover.
Used by script_check.py (run `python factcheck.py <project>` to see only this part).

What it checks
  A. SOURCE (every fact that is not marked "illustrative": true)
     · a real URL with a path (not a bare domain, not empty)
     · "quote": the exact sentence from the source that contains the number, "fetched": the date it was read
     · the number in the quote must match the fact's value (or a number in its claim) — units are compared as
       powers of ten, so  1.12 crore = 11,200,000 = 1.12 = "১.১২ কোটি"  all agree, 1.28 does not
     · a second source, or "official": true (primary government/agency dataset), or "single_source_note" (the
       sentence that goes into the pinned comment); otherwise the fact is single-source and the gate fails
     · the "source" text must not admit doubt (unverified, plan-stage, TBD …)
  B. SPOKEN NUMBERS (every number the voice says, found in the Bangla words of script.json)
     · spoken number ≈ a fact/math value of that scene (2 %)           → fine
     · spoken number within 25 % of a fact of that scene but not 2 %   → FAIL "close but different" (a mis-read
       figure: 1.28 spoken vs 1.12 sourced). "প্রায়/আনুমানিক" before the number allows 6 %.
     · a spoken number ≥ 20 (or with দশমিক) that matches no fact of the scene → WARN "not in facts.json"
     · a number phrase that cannot be parsed is ignored (never a false FAIL)
  C. SERIES (optional, ../_series/shared_facts.json): a fact whose "key" already exists with another value fails
     unless it has "supersedes": "<why>".   `--register` adds this episode's keys to the registry.
Strictness: rules.facts_gate (project.json). New projects (v0.6) have it true: A is a FAIL. Older projects: A is a
WARN so finished episodes can still be re-checked. B and C always run."""
import json, math, pathlib, re, sys
from urllib.parse import urlparse

# ---------------------------------------------------------------- Bangla number words
_U = {}
def _add(n, *words):
    for w in words: _U[w] = n
for n, ws in enumerate([('শূন্য',), ('এক',), ('দুই', 'দুটি', 'দুটো', 'দু'), ('তিন', 'তিনটি'), ('চার', 'চারটি'), ('পাঁচ', 'পাচ'), ('ছয়', 'ছয়টি'), ('সাত',), ('আট',), ('নয়', 'নয়টি'),
                         ('দশ',), ('এগারো', 'এগার'), ('বারো', 'বার'), ('তেরো', 'তের'), ('চৌদ্দ', 'চোদ্দ'), ('পনেরো', 'পনের'), ('ষোলো', 'ষোল'), ('সতেরো', 'সতের'), ('আঠারো', 'আঠার'),
                         ('ঊনিশ', 'উনিশ', 'ঊনিশ'), ('বিশ', 'কুড়ি'), ('একুশ',), ('বাইশ',), ('তেইশ',), ('চব্বিশ',), ('পঁচিশ', 'পচিশ'), ('ছাব্বিশ',), ('সাতাশ',), ('আটাশ', 'আঠাশ'),
                         ('ঊনত্রিশ', 'উনত্রিশ'), ('ত্রিশ',), ('একত্রিশ',), ('বত্রিশ',), ('তেত্রিশ',), ('চৌত্রিশ',), ('পঁয়ত্রিশ',), ('ছত্রিশ',), ('সাঁইত্রিশ', 'সাইত্রিশ'), ('আটত্রিশ',),
                         ('ঊনচল্লিশ', 'উনচল্লিশ'), ('চল্লিশ',), ('একচল্লিশ',), ('বিয়াল্লিশ',), ('তেতাল্লিশ',), ('চুয়াল্লিশ',), ('পঁয়তাল্লিশ',), ('ছেচল্লিশ',), ('সাতচল্লিশ',), ('আটচল্লিশ',),
                         ('ঊনপঞ্চাশ', 'উনপঞ্চাশ'), ('পঞ্চাশ',), ('একান্ন',), ('বায়ান্ন',), ('তিপ্পান্ন',), ('চুয়ান্ন',), ('পঞ্চান্ন',), ('ছাপ্পান্ন',), ('সাতান্ন',), ('আটান্ন',),
                         ('ঊনষাট', 'উনষাট'), ('ষাট',), ('একষট্টি',), ('বাষট্টি',), ('তেষট্টি',), ('চৌষট্টি',), ('পঁয়ষট্টি',), ('ছেষট্টি',), ('সাতষট্টি',), ('আটষট্টি',),
                         ('ঊনসত্তর', 'উনসত্তর'), ('সত্তর',), ('একাত্তর',), ('বাহাত্তর',), ('তিয়াত্তর',), ('চুয়াত্তর',), ('পঁচাত্তর',), ('ছিয়াত্তর',), ('সাতাত্তর',), ('আটাত্তর',),
                         ('ঊনআশি', 'উনআশি'), ('আশি',), ('একাশি',), ('বিরাশি',), ('তিরাশি',), ('চুরাশি',), ('পঁচাশি',), ('ছিয়াশি',), ('সাতাশি',), ('অষ্টাশি',),
                         ('ঊননব্বই', 'উননব্বই'), ('নব্বই',), ('একানব্বই',), ('বিরানব্বই',), ('তিরানব্বই',), ('চুরানব্বই',), ('পঁচানব্বই',), ('ছিয়ানব্বই',), ('সাতানব্বই',), ('আটানব্বই',), ('নিরানব্বই',)]):
    _add(n, *ws)
_MULT = {'হাজার': 1e3, 'লাখ': 1e5, 'লক্ষ': 1e5, 'কোটি': 1e7, 'মিলিয়ন': 1e6, 'বিলিয়ন': 1e9, 'ট্রিলিয়ন': 1e12}
_HUND = ('শো', 'শ', 'শত')
_FRAC = {'দেড়': 1.5, 'দেড': 1.5, 'আড়াই': 2.5, 'আড়াইশো': 250}
_APPROX = ('প্রায়', 'আনুমানিক', 'প্রায়', 'কমবেশি', 'সাড়ে', 'অন্তত')
_DEC = 'দশমিক'
PUNCT = ',।?!—–…;:"\'“”‘’()|.'


def _tok(w):
    return ''.join(ch for ch in w if ch not in PUNCT and ch not in '‌‍').strip()


def bn_numbers(text):
    """Number phrases spoken in Bangla words → [{'value', 'text', 'approx', 'decimal'}]. Unknown words end a phrase."""
    toks = [_tok(w) for w in re.sub(r'\[[^\]]*\]', ' ', text).split()]
    out, i = [], 0
    while i < len(toks):
        w = toks[i]
        start = i
        total, cur, seen, used_mult, dec, last_mult = 0.0, 0.0, False, False, False, 0.0
        j = i
        # 'সাড়ে X' / 'দেড়' / 'আড়াই'
        plus = 0.0
        if toks[j] == 'সাড়ে' and j + 1 < len(toks) and (toks[j + 1] in _U):
            plus = 0.5; j += 1
        elif toks[j] in _FRAC and toks[j] != 'আড়াইশো':
            cur = _FRAC[toks[j]]; seen = True; j += 1
        while j < len(toks):
            t = toks[j]
            if t in _U and not dec:
                cur += _U[t]; seen = True
            elif t in _U and dec:
                break
            elif t == _DEC and seen:
                # decimal part: single digit words follow
                frac, k, digs = '', j + 1, 0
                while k < len(toks) and toks[k] in _U and _U[toks[k]] <= 9:
                    frac += str(_U[toks[k]]); k += 1; digs += 1
                if not digs: break
                base = total + cur
                value = float(f'{int(base)}.{frac}') if base == int(base) else base + float('0.' + frac)
                # a multiplier may still follow (ছয় দশমিক পাঁচ কোটি)
                if k < len(toks) and toks[k] in _MULT:
                    value *= _MULT[toks[k]]; k += 1
                out.append({'value': value + plus, 'text': ' '.join(toks[start:k]), 'approx': _appr(toks, start), 'decimal': True})
                j = k; seen = False; total = cur = 0; start = -1
                break
            elif t in _MULT and (seen or total):
                m = _MULT[t]
                if plus and cur: cur += plus; plus = 0.0
                if m > last_mult:                       # ascending (পনেরো হাজার কোটি): multiplies everything so far
                    total = (total + cur) * m if (total + cur) else m
                else:                                   # descending (এক কোটি আঠাশ লাখ): adds
                    total += (cur or 1) * m
                cur = 0; last_mult = m; seen = True; used_mult = True
            elif any(t.endswith(h) and t[:-len(h)] in _U for h in _HUND) and not dec:
                h = next(h for h in _HUND if t.endswith(h) and t[:-len(h)] in _U)
                cur = (cur + _U[t[:-len(h)]]) * 100 if cur and cur < 10 else _U[t[:-len(h)]] * 100 + (cur if cur >= 100 else 0); seen = True
            elif t in _HUND and seen:
                cur = (cur or 1) * 100
            else:
                break
            j += 1
        if start == -1:
            i = j; continue
        if seen:
            out.append({'value': total + cur + plus, 'text': ' '.join(toks[start:j]), 'approx': _appr(toks, start), 'decimal': False})
            i = j
        else:
            i += 1
    return out


def used_mult_after(total):
    return False


def _appr(toks, start):
    return start > 0 and toks[start - 1] in _APPROX


# ---------------------------------------------------------------- numbers inside quotes / claims (digits)
_BN = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
_SCALE = {'thousand': 1e3, 'k': 1e3, 'lakh': 1e5, 'lac': 1e5, 'lakhs': 1e5, 'crore': 1e7, 'crores': 1e7, 'million': 1e6, 'mn': 1e6, 'm': 1e6,
          'billion': 1e9, 'bn': 1e9, 'trillion': 1e12, 'tn': 1e12, 'হাজার': 1e3, 'লাখ': 1e5, 'লক্ষ': 1e5, 'কোটি': 1e7, 'মিলিয়ন': 1e6, 'বিলিয়ন': 1e9, 'ট্রিলিয়ন': 1e12}
_NUM = re.compile(r'(?<![\w.])(\d[\d,]*(?:\.\d+)?|\.\d+)\s*(%|percent|per cent|শতাংশ|thousand|lakhs?|lac|crores?|million|billion|trillion|bn|mn|tn|k|m|হাজার|লাখ|লক্ষ|কোটি|মিলিয়ন|বিলিয়ন|ট্রিলিয়ন)?(?![\w])', re.I)


def digit_numbers(text):
    """All numbers written with digits (ASCII or Bangla), with an optional scale word → list of floats (value×scale and raw)."""
    t = (text or '').translate(_BN)
    vals = []
    for m in _NUM.finditer(t):
        try: raw = float(m.group(1).replace(',', ''))
        except ValueError: continue
        sc = (m.group(2) or '').lower()
        vals.append(raw * _SCALE.get(sc, 1.0) if sc not in ('%', 'percent', 'per cent', 'শতাংশ') else raw)
        vals.append(raw)
    # Indian-grouped phrases like "1 crore 28 lakh" → combine adjacent scaled numbers
    comb = re.findall(r'(\d[\d,]*(?:\.\d+)?)\s*(crore|কোটি|lakh|লাখ|thousand|হাজার)\s*(?:and\s*)?(\d[\d,]*(?:\.\d+)?)\s*(lakh|লাখ|thousand|হাজার)', t, re.I)
    for a_, s1, b_, s2 in comb:
        vals.append(float(a_.replace(',', '')) * _SCALE[s1.lower()] + float(b_.replace(',', '')) * _SCALE[s2.lower()])
    return vals


def sig_digits(v):
    """significant digits of a spoken number: 100 → 1, 18 → 2, 12,800,000 → 3 (decimals counted as written)."""
    t = f'{abs(v):.10g}'
    if 'e' in t: t = f'{abs(v):.0f}'
    t = t.replace('.', '').lstrip('0').rstrip('0')
    return max(len(t), 1)


def mant(x):
    """mantissa in [1,10) — compares numbers across powers of ten (units: crore vs absolute vs percent)."""
    x = abs(float(x))
    if x == 0: return 0.0
    return x / 10 ** math.floor(math.log10(x))


def same(a, b, tol=0.02):
    ma, mb = mant(a), mant(b)
    if ma == 0 or mb == 0: return ma == mb
    # allow 9.99 vs 1.00 wrap-around
    return abs(ma - mb) <= tol * max(ma, mb) or abs(ma / 10 - mb) <= tol * mb or abs(mb / 10 - ma) <= tol * ma


def near(a, b, lo=0.02, hi=0.25):
    ma, mb = mant(a), mant(b)
    if ma == 0 or mb == 0: return False
    for x, y in ((ma, mb), (ma / 10, mb), (mb / 10, ma)):
        d = abs(x - y) / max(x, y)
        if lo < d <= hi: return True
    return False


# ---------------------------------------------------------------- the gate
DOUBT = re.compile(r'unverified|not verified|plan[- ]stage|tbd|to be confirmed|যাচাই বাকি|যাচাইয়ের অপেক্ষা|\?\?|placeholder|assumed|guess', re.I)


def fact_numbers(f, strict=False):
    """the figures a fact stands for: its value/screen/display; only a fact with none of those falls back to the numbers in its claim
    (the claim also holds small helper numbers like the '১' in '১ ডলার', which would let a wrong quote slip through)."""
    nums = []
    for k in ('value', 'screen', 'display'):
        v = f.get(k)
        if isinstance(v, bool): continue
        if isinstance(v, (int, float)): nums.append(float(v))
        elif isinstance(v, str): nums += digit_numbers(v)
    if not strict or not [n for n in nums if n]: nums += digit_numbers(f.get('claim', ''))
    return [n for n in nums if n]


def check(P, SC, F, strict=None, today=None, series_path=None, register=False):
    """returns (fails, warns)"""
    fails, warns = [], []
    R = {}
    try: R = json.loads((P / 'project.json').read_text()).get('rules', {})
    except Exception: pass
    strict = R.get('facts_gate', False) if strict is None else strict
    bad = fails if strict else warns
    facts = F.get('facts', [])
    by_scene = {}
    for f in facts:
        for s in f.get('scenes') or []: by_scene.setdefault(s, []).append(f)
    for m in F.get('math', []):
        for s in m.get('scenes') or []:
            by_scene.setdefault(s, []).append({'id': m.get('id'), 'value': m.get('expect'), 'claim': m.get('claim', ''), 'screen': m.get('screen')})

    # ---- A. sources
    for f in facts:
        fid = f.get('id', '?')
        if f.get('illustrative'):
            continue
        url = f.get('url') or ''
        u = urlparse(url)
        if not (u.scheme in ('http', 'https') and u.netloc):
            bad.append(f'fact {fid}: no source URL — open the source and paste the exact page address')
        elif len([x for x in u.path.split('/') if x]) == 0 and not u.query:
            bad.append(f'fact {fid}: URL {url} is a bare site address — use the page the number was read on')
        if DOUBT.search(str(f.get('source', ''))):
            bad.append(f"fact {fid}: the source text admits doubt (\"{f.get('source')}\") — resolve it before the voice says it")
        q = f.get('quote')
        if not q:
            bad.append(f'fact {fid}: no "quote" — copy the exact sentence from the source that contains the number, and add "fetched": "YYYY-MM-DD"')
        else:
            qn = digit_numbers(q)
            targets = fact_numbers(f, strict=True)
            if targets and qn and not any(same(a, b) for a in qn for b in targets):
                fails.append(f"fact {fid}: the quote does not contain this number — quote has {sorted(set(round(x, 3) for x in qn))[:5]}, "
                             f"fact says {sorted(set(round(x, 3) for x in targets))[:4]} → one of them is wrong")
            elif targets and not qn:
                warns.append(f'fact {fid}: the quote contains no number I can read — check by eye')
        if q and not f.get('fetched'): bad.append(f'fact {fid}: "fetched" date missing')
        sec = f.get('second_source')
        if not (sec or f.get('official') or f.get('single_source_note')):
            bad.append(f'fact {fid}: single-source figure — add "second_source": {{"source","url","quote"}}, or "official": true (primary agency data), '
                       f'or "single_source_note": "<the caveat for the pinned comment>"')
        if isinstance(sec, dict):
            su = urlparse(sec.get('url') or '')
            if not (su.scheme and su.netloc and sec.get('quote')): bad.append(f'fact {fid}: second_source needs url + quote')
            elif sec.get('quote'):
                qn2 = digit_numbers(sec['quote']); tg = fact_numbers(f, strict=True)
                if tg and qn2 and not any(same(a, b, 0.05) for a in qn2 for b in tg):
                    fails.append(f'fact {fid}: the two sources disagree ({sorted(set(round(x, 3) for x in qn2))[:3]} vs {sorted(set(round(x, 3) for x in tg))[:3]}) — say which and why, or use the safer figure')

    # ---- B. spoken numbers
    for s, text in SC.items():
        known = []
        for f in by_scene.get(s, []): known += fact_numbers(f)
        for n in bn_numbers(text):
            v = n['value']
            if v == 0: continue
            sig = sig_digits(v)
            if any(same(v, k, 0.02) for k in known): continue
            if v < 10 and not n['decimal']: continue                  # a count (তিনটি, চার ভাগ), not a figure
            close = [k for k in known if near(v, k)]
            precise = sig >= 3 or n['decimal']
            if precise and close:
                if n['approx'] and any(same(v, k, 0.06) for k in close): continue
                fails.append(f"scene {s}: the voice says \"{n['text']}\" ({v:g}) but the scene's fact is {close[0]:g} — close but different: "
                             f"re-read the source and fix the script or the fact")
            elif not precise and close and any(near(v, k, 0.12, 0.30) for k in close):
                warns.append(f"scene {s}: \"{n['text']}\" is a rounded form of the fact ({close[0]:g}) but more than 12 % off — say \"প্রায়\" or round more carefully")
            elif sig >= 2 and (v >= 100 or n['decimal']) and not close and not (1900 <= v <= 2100) and v not in (100, 1000):
                warns.append(f"scene {s}: the voice says \"{n['text']}\" ({v:g}) — no fact/math row of this scene has it")

    # ---- C. series registry
    reg_f = pathlib.Path(series_path) if series_path else P.parent / '_series' / 'shared_facts.json'
    reg = {}
    if reg_f.exists():
        try: reg = json.loads(reg_f.read_text())
        except Exception: warns.append(f'{reg_f} is not valid JSON — ignored')
    for f in facts:
        k, v = f.get('key'), f.get('value')
        if k and isinstance(v, (int, float)) and k in reg and not f.get('supersedes'):
            old = reg[k]['value']
            if abs(old - v) > 0.01 * max(abs(old), abs(v), 1e-9):
                fails.append(f"fact {f.get('id')}: key '{k}' is {v:g} here but {old:g} in ep. {reg[k].get('ep', '?')} (series registry) — same figure, same number; "
                             f'fix one, or add "supersedes": "why" if the newer source replaces it')
    if register and reg_f.parent.exists():
        for f in facts:
            k, v = f.get('key'), f.get('value')
            if k and isinstance(v, (int, float)) and not f.get('illustrative'):
                reg[k] = {'value': v, 'ep': P.name, 'source': f.get('source', ''), 'date': f.get('date', '')}
        reg_f.write_text(json.dumps(reg, ensure_ascii=False, indent=1))
    return fails, warns


if __name__ == '__main__':
    import argparse
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    ap = argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--strict', action='store_true'); ap.add_argument('--register', action='store_true')
    a = ap.parse_args(); P = pathlib.Path(a.project).resolve()
    SC = {int(k): v for k, v in json.loads((P / 'script.json').read_text()).items() if str(k).isdigit()}
    F = json.loads((P / 'facts.json').read_text())
    fl, wl = check(P, SC, F, strict=True if a.strict else None, register=a.register)
    for w in wl: print('WARN ', w)
    for f in fl: print('FAIL ', f)
    print('FACTS PASS' if not fl else f'{len(fl)} failure(s)'); sys.exit(1 if fl else 0)
