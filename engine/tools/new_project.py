"""Create a new video project from the template.
usage: python new_project.py <folder> --title "হাদি কে?" [--preset vox-paper|dark-doc] [--lang bn|en] [--palette bangla|cinematic]"""
import argparse, json, pathlib, shutil, subprocess, sys
from es import ENGINE, TOOLS

ap = argparse.ArgumentParser()
ap.add_argument('folder'); ap.add_argument('--title', default='Untitled')
ap.add_argument('--preset', default='vox-paper'); ap.add_argument('--lang', default='bn')
ap.add_argument('--palette', default='bangla', choices=['bangla', 'cinematic'])
a = ap.parse_args()

P = pathlib.Path(a.folder).resolve()
if (P / 'index.html').exists(): sys.exit(f'{P} already has a project — refusing to overwrite.')
T = ENGINE / 'template'
if not (T / 'presets' / f'{a.preset}.css').exists(): sys.exit(f'unknown preset {a.preset}')
for d in ('img', 'photos', 'vo/raw', 'out', 'engine/presets', 'engine/scenes', 'fonts'):
    (P / d).mkdir(parents=True, exist_ok=True)
for f in ('engine.js', 'engine.css'): shutil.copy(T / f, P / 'engine' / f)
for f in (T / 'presets').glob('*.css'): shutil.copy(f, P / 'engine' / 'presets' / f.name)
for f in (T / 'scenes').glob('*.html'): shutil.copy(f, P / 'engine' / 'scenes' / f.name)

fs = ENGINE / 'node_modules' / '@fontsource'
for fam in ('noto-sans-bengali', 'noto-serif-bengali'):
    if not (fs / fam).exists(): sys.exit(f'missing font {fam} — run engine/tools/setup.sh first')
    shutil.copytree(fs / fam, P / 'fonts' / fam, dirs_exist_ok=True)

proj = {'title': a.title, 'lang': a.lang, 'preset': a.preset, 'voOffset': 0.3, 'pad': 0.55, 'transition': 0.45,
        'vo': {'tempo': 1.06, 'trim_db': -45, 'pause_min': 0.22}}
(P / 'project.json').write_text(json.dumps(proj, ensure_ascii=False, indent=2))
html = (T / 'index.html').read_text()
html = html.replace('{{LANG}}', a.lang).replace('{{TITLE}}', a.title).replace('{{PRESET}}', a.preset)
html = html.replace('{{HOOK}}', a.title).replace('{{PROJECT_JSON}}', json.dumps({k: proj[k] for k in ('lang', 'voOffset', 'pad', 'transition')}))
(P / 'index.html').write_text(html)
(P / 'vo.js').write_text('window.VO={durs:[],anchors:[]};\n')
shutil.copy(TOOLS / 'audio_config.example.json', P / 'audio_config.json')
cfg = json.loads((P / 'audio_config.json').read_text()); cfg['palette'] = a.palette
(P / 'audio_config.json').write_text(json.dumps(cfg, indent=2))
for name in ('brief.md', 'script.md', 'fact-sheet.md'):
    src = ENGINE.parent / 'templates' / name
    if src.exists(): shutil.copy(src, P / name)
subprocess.run([sys.executable, str(TOOLS / 'paper.py'), str(P)], check=True)
print(f'project ready: {P}\nnext: fill brief.md → fact-sheet.md → script.md, put VO takes in vo/raw/, photos in photos/')
