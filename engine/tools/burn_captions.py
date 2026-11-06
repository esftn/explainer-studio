"""Burn big on-screen captions into a finished video (v0.8.1). For Facebook (muted autoplay) and the "captions-on" A/B test.
The original video is never overwritten: writes <video>_captioned.mp4 next to it (or --out).

usage: python3 engine/tools/burn_captions.py <project> --video out/X_reel_9x16.mp4
            [--words docs/words.json | --srt out/captions.bn_IN.srt] [--out out/X_cap.mp4] [--max-words 3] [--y 1250] [--no-highlight]

--words  exact word timings: a JSON list of {"text", "start", "end"} (ElevenLabs Scribe "words"; entries with
         "type": "spacing" are skipped). Gives word-by-word captions with the spoken word highlighted.
--srt    fallback when no word timings exist (default out/captions.bn_IN.srt): each cue shown in chunks, no highlight.
Style: Tiro Bangla, white text with a heavy black outline, current word in the episode's brightest palette colour
(docs/look.json), on a dark box centred at y 1490 on 9:16 (low in the 4:5 key zone, above the Shorts title/UI); scaled for 4:5.
New builds keep a caption lane (y ~1430-1550) free of key text so the captions never cover a number.
Captions are skipped during the cover opening (project.json cover_hold) so they never sit on the cover title.
Shaping: libass + HarfBuzz render Bangla conjuncts correctly; the font is converted once from the engine's woff2 to TTF."""
import argparse, colorsys, json, pathlib, re, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('--video', required=True); ap.add_argument('--words'); ap.add_argument('--srt')
ap.add_argument('--out'); ap.add_argument('--max-words', type=int, default=3); ap.add_argument('--y', type=int)
ap.add_argument('--no-highlight', action='store_true'); ap.add_argument('--size', type=int, default=86)
a = ap.parse_args(); P = pathlib.Path(a.project).resolve(); V = (P / a.video).resolve()
if not V.exists(): sys.exit(f'missing {V}')
pj = json.loads((P / 'project.json').read_text()) if (P / 'project.json').exists() else {}
hold = float(pj.get('cover_hold', 0) or 0)
pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', str(V)]))
W, H = pr['streams'][0]['width'], pr['streams'][0]['height']
Y = a.y or (1490 if H >= 1900 else round(1490 - (1920 - H) / 2))   # 4:5 feed = centre crop of the 9:16 frame

# ---- font: TTF for libass (fontTools converts the engine's woff2 once)
ENG = pathlib.Path(__file__).resolve().parent.parent
cache = ENG / '.cache'; cache.mkdir(exist_ok=True); ttf = cache / 'TiroBangla-Regular.ttf'
if not ttf.exists():
    src = next(iter(sorted(P.glob('fonts/tiro-bangla/files/tiro-bangla-bengali-400-normal.woff2')) + sorted(ENG.glob('node_modules/@fontsource/tiro-bangla/files/tiro-bangla-bengali-400-normal.woff2'))), None)
    if not src: sys.exit('Tiro Bangla woff2 not found (project fonts/ or engine node_modules): run engine/tools/setup.sh')
    try: from fontTools.ttLib import TTFont
    except ImportError: sys.exit('pip install fonttools brotli   (needed once to convert the font)')
    f = TTFont(str(src)); f.flavor = None; f.save(str(ttf))

# ---- colours
def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
look = json.loads((P / 'docs' / 'look.json').read_text()) if (P / 'docs' / 'look.json').exists() else {'colors': {'c1': '#FFD23F'}}
def vivid(h):
    r, g, b = (x / 255 for x in hx(h)); _, l, s = colorsys.rgb_to_hls(r, g, b); return (l > .45) * 2 + s
hl = max((v for k, v in look['colors'].items() if k.startswith('c')), key=vivid)
ass_col = lambda h: '&H00%02X%02X%02X' % tuple(reversed(hx(h)))    # ASS is &HAABBGGRR

# ---- timed chunks
def srt_cues(p):
    out = []
    for blk in re.split(r'\n\s*\n', p.read_text(encoding='utf-8').strip()):
        m = re.search(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', blk)
        if not m: continue
        g = [int(x) for x in m.groups()]; s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000; e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        txt = ' '.join(blk.split('\n')[2:]).strip()
        if txt: out.append((s, e, txt))
    return out
chunks = []          # (start, end, [words], [(ws, we)] or None)
if a.words:
    raw = json.loads((P / a.words).read_text(encoding='utf-8'))
    raw = raw.get('words', raw) if isinstance(raw, dict) else raw
    words = [(float(w['start']), float(w['end']), w['text'].strip()) for w in raw if w.get('type', 'word') == 'word' and w['text'].strip()]
    cur = []
    for i, w in enumerate(words):
        cur.append(w)
        gap = (words[i + 1][0] - w[1]) if i + 1 < len(words) else 9
        if len(cur) >= a.max_words or re.search(r'[।?!,:;—]$', w[2]) or gap > .35:
            chunks.append((cur[0][0], cur[-1][1], [x[2] for x in cur], [(x[0], x[1]) for x in cur])); cur = []
else:
    sp = (P / (a.srt or 'out/captions.bn_IN.srt'))
    if not sp.exists(): sys.exit(f'no --words and no SRT at {sp}')
    for s, e, txt in srt_cues(sp):
        ws = txt.split(); n = max(1, -(-len(ws) // a.max_words)); d = (e - s) / n
        for k in range(n):
            part = ws[k * a.max_words:(k + 1) * a.max_words]
            if part: chunks.append((s + k * d, s + (k + 1) * d, part, None))

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f'{h}:{m:02d}:{s:05.2f}'
esc = lambda s: s.replace('\\', '').replace('{', '(').replace('}', ')')
fs = round(a.size * (W / 1080))
lines = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 0', '', '[V4+ Styles]',
         'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
         f'Style: Cap,Tiro Bangla,{fs},&H00FFFFFF,&H00FFFFFF,&H28101010,&H28101010,0,0,0,0,100,100,0,0,3,{max(10, fs // 6)},0,5,60,60,0,1', '',
         '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
n_ev = 0
for s, e, ws, wt in chunks:
    if e <= hold + .05: continue
    s = max(s, hold + .05); e = e + .12
    pos = f'{{\\an5\\pos({W // 2},{Y})}}'
    if wt and not a.no_highlight:
        for i, (a0, a1) in enumerate(wt):
            b0 = max(a0, s) if i else s; b1 = wt[i + 1][0] if i + 1 < len(wt) else e
            if b1 <= b0: continue
            txt = ' '.join((f'{{\\c{ass_col(hl)}}}{esc(w)}{{\\c&H00FFFFFF&}}' if j == i else esc(w)) for j, w in enumerate(ws))
            lines.append(f'Dialogue: 0,{ts(b0)},{ts(b1)},Cap,,0,0,0,,{pos}{txt}'); n_ev += 1
    else:
        lines.append(f'Dialogue: 0,{ts(s)},{ts(e)},Cap,,0,0,0,,{pos}{esc(" ".join(ws))}'); n_ev += 1
assf = V.with_suffix('.captions.ass'); assf.write_text('\n'.join(lines) + '\n', encoding='utf-8')
out = (P / a.out).resolve() if a.out else V.with_name(V.stem + '_captioned.mp4')
q = lambda p: str(p).replace('\\', '/').replace(':', '\\:').replace("'", "\\'")
vf = f"ass='{q(assf)}':fontsdir='{q(cache)}'"
cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-map', '0:v:0', '-map', '0:a?', '-vf', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
       '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', str(out)]
subprocess.run(cmd, check=True)
assf.unlink(missing_ok=True)
print(f'wrote {out.name}: {n_ev} caption events ({"word timings" if a.words else "SRT chunks"}), highlight {hl}, y {Y}, cover opening {hold:.1f} s skipped')
