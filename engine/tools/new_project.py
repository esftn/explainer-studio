"""Create a new video project from the template.
usage: python new_project.py <folder> --title "হাদি কে?" [--ep 04] [--preset vox-money|vox-paper|dark-doc] [--lang bn|en]
       [--palette bangla|cinematic] [--max-len 60]
Layout = the series layout: out/ (finals only) docs/ drafts/ vo/raw vo/unused img/ images/ + working files at the top."""
import argparse, json, pathlib, shutil, subprocess, sys
from es import ENGINE, TOOLS

ap = argparse.ArgumentParser()
ap.add_argument('folder'); ap.add_argument('--title', default='Untitled')
ap.add_argument('--preset', default='vox-paper'); ap.add_argument('--lang', default='bn')
ap.add_argument('--palette', default='bangla', choices=['bangla', 'cinematic'])
ap.add_argument('--max-len', type=float, default=60)
ap.add_argument('--ep'); ap.add_argument('--slug')
a = ap.parse_args()

P = pathlib.Path(a.folder).resolve()
if (P / 'index.html').exists(): sys.exit(f'{P} already has a project — refusing to overwrite.')
# an existing videoNN folder (with the creator's images/) is fine: the project is created inside it
T = ENGINE / 'template'
if not (T / 'presets' / f'{a.preset}.css').exists(): sys.exit(f'unknown preset {a.preset}')
for d in ('img', 'photos', 'images', 'vo/raw', 'vo/unused', 'out', 'docs', 'drafts', '.studio', 'engine/presets', 'engine/scenes', 'fonts'):
    (P / d).mkdir(parents=True, exist_ok=True)
for f in ('engine.js', 'engine.css'): shutil.copy(T / f, P / 'engine' / f)
for f in (T / 'presets').glob('*.css'): shutil.copy(f, P / 'engine' / 'presets' / f.name)
for f in (T / 'scenes').glob('*.html'): shutil.copy(f, P / 'engine' / 'scenes' / f.name)

fs = ENGINE / 'node_modules' / '@fontsource'
for fam in ('noto-sans-bengali', 'noto-serif-bengali', 'tiro-bangla'):
    if not (fs / fam).exists(): sys.exit(f'missing font {fam} — run engine/tools/setup.sh first')
    shutil.copytree(fs / fam, P / 'fonts' / fam, dirs_exist_ok=True)

proj = {'title': a.title, 'lang': a.lang, 'preset': a.preset, 'voOffset': 0.3, 'pad': 0.55, 'transition': 0.45,
        'max_len': a.max_len, 'end_hold': 3.0, 'sayLead': 0.25, 'feed_zone': [285, 1635],
        'rules': {'ending_cta': 'কমেন্টে', 'now_max_months': 12, 'facts_gate': True},
        'vo': {'tempo': 1.06, 'trim_db': -45, 'pause_min': 0.22, 'scene_break': '[pause]', 'scene_break_min': 0.45, 'chars_per_s': 12.5}}
(P / 'project.json').write_text(json.dumps(proj, ensure_ascii=False, indent=2))
html = (T / 'index.html').read_text()
html = html.replace('{{LANG}}', a.lang).replace('{{TITLE}}', a.title).replace('{{PRESET}}', a.preset)
html = html.replace('{{HOOK}}', a.title).replace('{{PROJECT_JSON}}', json.dumps({k: proj[k] for k in ('lang', 'voOffset', 'pad', 'transition', 'sayLead')}))
(P / 'index.html').write_text(html)
(P / 'vo.js').write_text('window.VO={durs:[],anchors:[]};\n')
shutil.copy(TOOLS / 'audio_config.example.json', P / 'audio_config.json')
cfg = json.loads((P / 'audio_config.json').read_text()); cfg['palette'] = a.palette
(P / 'audio_config.json').write_text(json.dumps(cfg, indent=2))
for name in ('brief.md', 'script.md', 'fact-sheet.md'):
    src = ENGINE.parent / 'templates' / name
    if src.exists() and not (P / 'docs' / name).exists(): shutil.copy(src, P / 'docs' / name)
if not (P / 'facts.json').exists(): shutil.copy(ENGINE.parent / 'templates' / 'facts.json', P / 'facts.json')
MAC_TOOLS = ('pack.py', 'guard.py', 'state_check.py', 'publint.py', 'series_tracker.py', 'finish.py', 'tidy.py', 'studio.py')   # what a project (and VIDEO GEN/_series/tools) carries so the Mac side can verify without the cloud
for _t in MAC_TOOLS:
    if (TOOLS / _t).exists(): shutil.copy(TOOLS / _t, P / '.studio' / _t)
subprocess.run([sys.executable, str(TOOLS / 'state.py'), str(P), 'init', '--title', a.title] + (['--ep', a.ep] if a.ep else [])
               + ['--slug', a.slug or P.name], check=True, capture_output=True)
subprocess.run([sys.executable, str(TOOLS / 'paper.py'), str(P)], check=True)
print(f'project ready: {P}\nnext: python3 engine/tools/studio.py next {P.name}   (step card for this stage)')
