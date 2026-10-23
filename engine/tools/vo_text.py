"""Make the ready-to-paste voiceover text for a manual ElevenLabs take (one take, whole script).
usage: python vo_text.py <project> [--marker "[pause]"]

Reads  script.json (approved words) and optional vo_tags.json ({"1": "[curious] same words with tags/…", ...}).
Writes vo/vo_paste.txt  (scenes separated by a scene-break line that makes the voice pause clearly)
       vo/vo_paste.json (script hash + marker, so vo_split.py can prove the take matches the approved script)
Refuses to run unless script_check.py passed on the current script.json + facts.json, and (when state.json
exists) the creator approved exactly this version (state.py approve script).
Tagged lines must contain exactly the approved words: tags and punctuation may be added, words may not change.

Scene-break marker: a "[pause]" line between scenes. Tested with Rayhan / Eleven v4 (21 Oct 2026): "[pause]" gave
1.39 s, "[long pause]" 2.0 s, "... ..." 1.6 s, against ≤ 0.52 s for every pause inside a scene → the split is
CLEAN. A "— —" line did NOT work (0.46–0.49 s, same as sentence pauses); v3/v4 ignore SSML <break> tags.
Change it per project with project.json vo.scene_break."""
import argparse, json, re, sys
from es import project, cfg, load_script, strip_tags, norm_word, file_hash

ap = argparse.ArgumentParser(); ap.add_argument('project', nargs='?'); ap.add_argument('--marker')
a = ap.parse_args(); P = project(a.project); C = cfg(P).get('vo', {})
marker = a.marker or C.get('scene_break', '[pause]')
sp = P / '.script_pass'
cur = file_hash(P / 'script.json', P / 'facts.json')
if not sp.exists() or json.loads(sp.read_text()).get('hash') != cur:
    sys.exit('BLOCKED: run script_check.py first — it must PASS on the current script.json and facts.json')
st = P / 'state.json'
if st.exists():
    ap_ = json.loads(st.read_text()).get('approved', {}).get('script', {})
    if ap_.get('hash') != cur:
        sys.exit('BLOCKED: the creator has not approved THIS version of the script (state.py approve script after their OK)')
SC = load_script(P)
tags = {}
tf = P / 'vo_tags.json'
if tf.exists():
    tags = {int(k): v for k, v in json.loads(tf.read_text()).items() if str(k).isdigit()}
bad = []
for k, t in tags.items():
    w1 = [norm_word(x) for x in strip_tags(SC.get(k, '')).split()]; w2 = [norm_word(x) for x in strip_tags(t).split()]
    if [x for x in w1 if x] != [x for x in w2 if x]: bad.append(k)
if bad: sys.exit(f'vo_tags.json scene(s) {bad}: words differ from script.json — tags and punctuation only')
n_tagged = sum(len(re.findall(r'\[[^\]]+\]', t)) for t in tags.values())
parts = [tags.get(k, SC[k]).strip() for k in sorted(SC)]
txt = f'\n\n{marker}\n\n'.join(parts) + '\n'
(P / 'vo').mkdir(exist_ok=True)
(P / 'vo' / 'vo_paste.txt').write_text(txt, encoding='utf-8')
json.dump({'script_hash': file_hash(P / 'script.json'), 'marker': marker, 'scenes': len(parts), 'chars': len(txt)},
          open(P / 'vo' / 'vo_paste.json', 'w'))
print(f'vo/vo_paste.txt: {len(parts)} scenes, {len(txt)} characters, {n_tagged} audio tags, scene break "{marker}"')
if n_tagged > 6: print(f'WARN {n_tagged} tags — house rule is 2–3 peaks; facts stay untagged')
