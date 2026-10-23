#!/usr/bin/env python3
"""publish.txt lint (v0.6) — a publish.txt may not leave Finish with an unfinished line in it.
  publint.py <publish.txt | project> [--facts facts.json] [--strict]       exit 1 on any FAIL
FAIL: a placeholder ("[…]" text, "নিজে যোগ করুন", "যাচাইয়ের অপেক্ষা", TODO/TBD…), a missing TITLE / DESCRIPTION /
      HASHTAGS / PINNED COMMENT / PHOTO CREDITS section, an empty section, a title over 70 characters.
WARN: hashtag count different from the "(N)" in its label, no comment call-to-action in the description, digits in
      the description body (the answer lives in the pinned comment), a fact with a single_source_note whose caveat
      does not appear anywhere in the text. --strict turns warnings into failures.
Used by finish.py and series_tracker.py; also runnable on its own."""
import json, pathlib, re, sys

SECTIONS = ['TITLE', 'ALT TITLE', 'DESCRIPTION', 'HASHTAGS', 'PINNED COMMENT', 'PHOTO CREDITS']
REQUIRED = ['TITLE', 'DESCRIPTION', 'HASHTAGS', 'PINNED COMMENT', 'PHOTO CREDITS']
HDR = re.compile(r'^(ALT TITLE|TITLE|DESCRIPTION|HASHTAGS|PINNED COMMENT|PHOTO CREDITS)\b[^\n]*$')
PLACEHOLDERS = [
    (r'\[[^\]\n]{2,}\]', 'text in [square brackets] (a placeholder?)'),
    (r'নিজে যোগ', '"নিজে যোগ…" (to be added by hand)'),
    (r'যোগ করুন', '"যোগ করুন" (to be added)'),
    (r'যাচাইয়ের অপেক্ষা', '"যাচাইয়ের অপেক্ষা…" (waiting for verification)'),
    (r'যাচাই বাকি', '"যাচাই বাকি" (verification pending)'),
    (r'\b(TODO|TBD|FIXME|XXX|PLACEHOLDER|lorem ipsum)\b', 'TODO/TBD marker'),
    (r'\{\{|\}\}|<<|>>', 'template braces'),
]
CAVEAT_WORDS = ['একটি সূত্র', 'একটি সংবাদ', 'একটি রিপোর্ট', 'একক সূত্র', 'সীমাবদ্ধতা', 'নির্ভর', 'অনুমান', 'নিশ্চিত নয়', 'প্রমাণিত নয়']


def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = HDR.match(line.strip()) if line and not line[0].isspace() else None
        if m: cur = m.group(1); out.setdefault(cur, []); out[cur].append(line.strip()); continue
        if cur: out[cur].append(line)
    return {k: '\n'.join(v[1:]).strip() for k, v in out.items()}, {k: v[0] for k, v in out.items()}


def lint(path, facts=None, strict=False):
    p = pathlib.Path(path)
    if p.is_dir(): p = p / 'out' / 'publish.txt'
    fails, warns = [], []
    if not p.exists(): return [f'{p} does not exist'], []
    text = p.read_text(encoding='utf-8')
    sec, hdr = sections(text)
    for r in REQUIRED:
        if r not in sec: fails.append(f'section {r} is missing')
        elif not sec[r].strip(): fails.append(f'section {r} is empty')
    for pat, why in PLACEHOLDERS:
        for m in re.finditer(pat, text):
            ln = text.count('\n', 0, m.start()) + 1
            fails.append(f'line {ln}: placeholder — {why}: "{m.group(0)[:50]}"')
    t = sec.get('TITLE', '')
    title = next((l.strip() for l in t.splitlines() if l.strip() and not l.strip().lower().startswith('alt')), '')
    if title and len(title) > 70: fails.append(f'title is {len(title)} characters (max 70)')
    for h, lab in (('HASHTAGS', None),):
        for line in sec.get(h, '').splitlines():
            m = re.match(r'^(YouTube|Facebook)\s*(?:\((\d+)\))?\s*:\s*(.*)$', line.strip())
            if m and m.group(2):
                n = len(re.findall(r'#\S+', m.group(3)))
                if n != int(m.group(2)): warns.append(f'{m.group(1)}: label says {m.group(2)} hashtags, found {n}')
    d = sec.get('DESCRIPTION', '')
    if d and 'কমেন্ট' not in d: warns.append('description has no comment call-to-action ("কমেন্টে …")')
    if d and re.search(r'[0-9০-৯]', re.sub(r'#\S+', '', d)): warns.append('digits in the description (the answer/numbers belong in the pinned comment)')
    if facts:
        try:
            F = json.loads(pathlib.Path(facts).read_text(encoding='utf-8'))
            notes = [f for f in F.get('facts', []) if f.get('single_source_note') and not f.get('illustrative')]
            if notes and not any(w in text for w in CAVEAT_WORDS):
                warns.append(f'{len(notes)} fact(s) rest on a single source (single_source_note) but the text carries no caveat (e.g. "সীমাবদ্ধতা: … একটি সূত্রের ওপর নির্ভর")')
        except Exception: pass
    if strict: fails += warns; warns = []
    return fails, warns


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    facts = sys.argv[sys.argv.index('--facts') + 1] if '--facts' in sys.argv else None
    if facts and facts in args: args.remove(facts)
    if not args: sys.exit(__doc__)
    f, w = lint(args[0], facts, '--strict' in sys.argv)
    for x in f: print('FAIL', x)
    for x in w: print('WARN', x)
    print('PUBLISH.TXT OK' if not f else f'PUBLISH.TXT: {len(f)} problem(s)')
    sys.exit(1 if f else 0)
