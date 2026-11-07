#!/usr/bin/env python3
"""build_scenes.py (v0.10) — write index.html from a short scene plan (build.json) instead of typing 20–30 KB of HTML.

usage: python3 build_scenes.py videoNN            -> index.html (the <head> of the current index.html is kept)
       python3 build_scenes.py videoNN --check    only validate build.json (photos, say-words, fit), write nothing

build.json (see docs/cheatsheet.md for every block):
{
  "bands": "zigzag",               # top/bottom band style, must differ from the previous episode (list: BANDS below)
  "tex": "dots",                   # default background texture: dots|graph|bprint|none
  "css": "",                       # optional extra CSS (episode motif objects)
  "scenes": [                      # one per VO clip, in order (scene k = vo_k)
    {"photo": "garment_floor.jpg", "mood": "intro", "blocks": [ {"chip": "১ ডলার = ১২৩ টাকা"}, {"h2": "টাকার দাম কমলে"},
        {"blk": "রপ্তানি বাড়ে?"}, {"note": "সত্যিই?", "say": "সত্যিই"} ]},
    {"bg": 0, "mood": "build", "src": "সূত্র: বাংলাদেশ ব্যাংক", "blocks": [ {"h2": "২০২১: ১ ডলার = **৮৬ টাকা**", "say": "দুই"},
        {"num": 123, "from": 86, "post": " টাকা", "say": "একশো"} ]}
  ]
}
Timing: every block takes "say" (spoken word[#n][+/-s]) or "t" (seconds); without either it lands on the first word of its
text that is spoken in the scene, else it is spread evenly through the scene. The last scene lasts VO + end_hold.
Colours come only from docs/look.json (theme index "bg": 0..5 = the rows of docs/look.md)."""
import argparse, html, json, pathlib, re, sys, unicodedata

sys.dont_write_bytecode = True
MOODS = ['intro', 'build', 'drive', 'somber', 'elegy', 'answer', 'end']
BANDS = ['zigzag', 'coupon', 'stripes', 'dots', 'checker', 'ruler', 'scallop', 'tape', 'bars', 'plus']
SAFE_TOP, SAFE_H, W = 300, 1100, 960
SIZES = {'h0': 176, 'h1': 118, 'h2': 80, 'h3': 58, 'b': 48}
E = lambda s: html.escape(str(s), quote=False)
WHOOSH = ' data-sfx="whoosh"'


# ------------------------------------------------------------------ helpers
def jl(f, d=None):
    try: return json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
    except Exception: return d


def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= .03928 else ((v / 255 + .055) / 1.055) ** 2.4
    r, g, b = hx(h); return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def ratio(a, b): la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + .05) / (lb + .05)


def best_fg(bg, cands): return max(list(cands) + ['#FFFFFF', '#000000'], key=lambda c: ratio(bg, c))


def norm(w): return re.sub(r'[^\wঀ-৿]', '', unicodedata.normalize('NFC', w)).strip()


def load_vo(P):
    t = (P / 'vo.js').read_text(encoding='utf-8') if (P / 'vo.js').exists() else ''
    return json.loads(t[t.index('{'):t.rindex('}') + 1]) if '{' in t else {'durs': [], 'words': []}


# ------------------------------------------------------------------ CSS
def theme_css(look):
    C = look['colors']; ink = C.get('ink', '#111111'); paper = C.get('paper', '#FFFFFF')
    out = []
    for i, t in enumerate(look['themes']):
        bg, tx, hl, pop = t['bg'], t['text'], t['highlight'], t['pop']
        fgs = [bg, tx, ink, paper]
        card = paper if bg.lower() != paper.lower() else '#FFFFFF'
        out.append(f".th{i}{{--bgc:{bg};--ink:{tx};--accent:{hl};--accent2:{pop};--shadow:{ink};--note:{hl};"
                   f"--blk-bg:{hl};--blk-fg:{best_fg(hl, fgs)};--chip-bg:{pop};--chip-fg:{best_fg(pop, fgs)};"
                   f"--card-bg:{card};--card-fg:{best_fg(card, [ink, tx, '#111111'])};--note-fg:{best_fg(hl, fgs)}}}")
    # photo scenes: light text on a dark wash, the palette's two brightest accents for block + chip
    acc = sorted([v for k, v in C.items() if k.startswith('c')], key=lambda h: -lum(h) * (max(hx(h)) - min(hx(h)) + 40))
    b1, b2 = (acc + ['#FFC400', '#FF5A4E'])[:2]
    out.append(f".thp{{--bgc:#111;--ink:#FFFFFF;--accent:{b1};--accent2:{b2};--shadow:#000;--note:{b1};--blk-bg:{b1};"
               f"--blk-fg:{best_fg(b1, [ink, '#111111', '#FFFFFF'])};--chip-bg:{b2};--chip-fg:{best_fg(b2, [ink, '#111111', '#FFFFFF'])};"
               f"--card-bg:{paper};--card-fg:{best_fg(paper, [ink, '#111111'])};--note-fg:{best_fg(b1, [ink, '#111111', '#FFFFFF'])}}}")
    return '\n'.join(out)


def band_css(kind, look):
    C = look['colors']; c = [C.get(k) for k in ('c1', 'c2', 'c3', 'c4') if C.get(k)] + ['#FFC400', '#FF5A4E', '#1F3FD8', '#2EE6A8']
    ink = C.get('ink', '#111111'); paper = C.get('paper', '#FFFFFF'); a, b = c[0], c[1]
    base = '.band{position:absolute;left:-40px;width:1160px;height:104px;z-index:2;pointer-events:none}.band.t{top:118px}.band.b{top:1792px}\n'
    bg = {
        'zigzag': f"background:linear-gradient(135deg,{a} 25%,transparent 25%) -26px 0/52px 52px,linear-gradient(225deg,{a} 25%,transparent 25%) -26px 0/52px 52px,"
                  f"linear-gradient(315deg,{a} 25%,transparent 25%) 0 0/52px 52px,linear-gradient(45deg,{a} 25%,{b} 25%) 0 0/52px 52px",
        'coupon': f"background:radial-gradient(circle,var(--bgc) 15px,transparent 16px) 0 50%/96px 104px repeat-x,{a};border-top:5px dashed {ink};border-bottom:5px dashed {ink}",
        'stripes': f"background:repeating-linear-gradient(-45deg,{a} 0 26px,{b} 26px 52px)",
        'dots': f"background:radial-gradient({ink} 9px,transparent 10px) 0 0/44px 44px,{a}",
        'checker': f"background:conic-gradient({ink} 25%,{a} 0 50%,{ink} 0 75%,{a} 0) 0 0/52px 52px",
        'ruler': f"background:repeating-linear-gradient(90deg,{ink} 0 5px,transparent 5px 40px) 0 0/100% 46%  no-repeat,"
                 f"repeating-linear-gradient(90deg,{ink} 0 7px,transparent 7px 200px) 0 0/100% 80% no-repeat,{a}",
        'scallop': f"background:radial-gradient(circle at 50% 0,{a} 30px,transparent 31px) 0 0/64px 104px,radial-gradient(circle at 50% 100%,{b} 30px,transparent 31px) 32px 0/64px 104px",
        'tape': f"background:repeating-linear-gradient(90deg,{a} 0 120px,{b} 120px 240px);opacity:.92;transform:rotate(-1.4deg);"
                f"border-top:6px dotted {paper};border-bottom:6px dotted {paper}",
        'bars': f"background:linear-gradient(0deg,{a} 30%,transparent 30%) 0 100%/34px 100%,linear-gradient(0deg,{b} 55%,transparent 55%) 34px 100%/68px 100%,"
                f"linear-gradient(0deg,{ink} 80%,transparent 80%) 0 100%/102px 100%",
        'plus': f"background:linear-gradient({ink},{ink}) 50% 50%/30px 8px no-repeat,linear-gradient({ink},{ink}) 50% 50%/8px 30px no-repeat;"
                f"background-size:30px 8px,8px 30px;background-repeat:space;background-color:{a}",
    }[kind]
    return base + f'.band{{{bg}}}\n.band.b{{transform:rotate(1.2deg)}}.band.t{{transform:rotate(-1.2deg)}}\n'


BASE_CSS = """
.col{position:absolute;left:60px;top:300px;width:960px;height:1100px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px;text-align:center}
.col.top{justify-content:flex-start;top:320px}.col.left{align-items:flex-start;text-align:left}
.col>*{max-width:960px}
.row{display:flex;gap:36px;align-items:center;justify-content:center;width:960px}.row>*{flex:1}
.blkw .blk{display:inline-block;background:var(--blk-bg);color:var(--blk-fg);padding:0 30px 14px;transform:rotate(-1.4deg);box-shadow:10px 10px 0 var(--shadow)}
.chipx{display:inline-block;background:var(--chip-bg);color:var(--chip-fg);font:400 46px/1.25 var(--font-sans);-webkit-text-stroke:1px currentColor;padding:4px 26px 12px;box-shadow:8px 8px 0 var(--shadow);transform:rotate(-1.2deg)}
.cardx{background:var(--card-bg);color:var(--card-fg);border:5px solid var(--shadow);box-shadow:12px 12px 0 var(--shadow);padding:20px 34px 28px;min-width:520px}
.cardx .sub{font:400 44px/1.4 var(--font-sans);opacity:.85}
.notex{display:inline-block;background:var(--note);color:var(--note-fg);font:400 54px/1.3 var(--font-sans);-webkit-text-stroke:1.2px currentColor;padding:10px 30px 18px;transform:rotate(-3deg);box-shadow:8px 8px 0 var(--shadow)}
.tags{display:flex;flex-wrap:wrap;gap:24px 30px;justify-content:center}
.tags>span:nth-child(even){transform:rotate(1.6deg)}
.barsx{width:960px;text-align:left}.barsx .lbl{display:flex;justify-content:space-between;font:400 48px/1.3 var(--font-sans);-webkit-text-stroke:.6px currentColor;margin-top:18px}
.trk{position:relative;height:84px;margin-top:6px}.trk>i{position:absolute;top:0;bottom:0;transform-origin:left;display:block;box-shadow:6px 6px 0 var(--shadow)}
.legend{font:400 40px var(--font-sans);margin-top:16px}.legend i{display:inline-block;width:34px;height:34px;margin:0 10px 0 22px;vertical-align:middle}
.share{display:flex;width:960px;height:120px;box-shadow:8px 8px 0 var(--shadow)}.share>i{display:block;height:100%;transform-origin:left}
.sharel{display:flex;width:960px;font:400 42px/1.3 var(--font-sans)}.sharel>span{text-align:center}
.chain{display:flex;flex-direction:column;align-items:center;gap:6px}.chain .arw{font:400 64px/1 var(--font-sans);color:var(--accent2)}
.vs{display:flex;gap:30px;align-items:center;justify-content:center;width:980px}.vs .cardx{min-width:0;flex:1}.vs .mid{font:400 64px var(--font-sans);color:var(--accent2)}
.phb{background:center/cover no-repeat;border:10px solid var(--card-bg);box-shadow:12px 12px 0 var(--shadow);width:860px;height:480px;transform:rotate(-1.5deg)}
.cap{font:400 40px/1.3 var(--font-sans);margin-top:10px}
.strk{position:relative;display:inline-block;opacity:.6}.strk>i{position:absolute;left:-10px;right:-10px;top:52%;height:14px;background:var(--accent2);transform-origin:left;display:block}
.gridx{display:grid;gap:8px}.gridx>i{display:block;aspect-ratio:1;background:var(--ink);opacity:.25;border-radius:4px}.gridx>i.on{background:var(--accent2);opacity:1}
.wash{background:linear-gradient(rgba(0,0,0,.70),rgba(0,0,0,.32) 38%,rgba(0,0,0,.18) 60%,rgba(0,0,0,.78) 92%)}
.thp .col{color:#FFFFFF;text-shadow:0 4px 18px rgba(0,0,0,.75)}
.thp .col .cardx,.thp .col .blk,.thp .col .chipx,.thp .col .notex{text-shadow:none}
"""


# ------------------------------------------------------------------ blocks
class Scene:
    def __init__(self, k, spec, vo, P, look, warns, offset, lead):
        self.k, self.s, self.P, self.look, self.warns = k, spec, P, look, warns
        self.words = [(norm(w), t) for w, t in (vo['words'][k] if k < len(vo['words']) and vo['words'][k] else [])]
        durs = vo.get('durs') or []
        self.dur = (durs[k] if k < len(durs) and durs[k] else 5.0)
        self.off, self.lead, self.cursor, self.n_auto = offset, lead, -1.0, 0
        self.extra = 0.0; self.pad = float((jl(P / 'project.json', {}) or {}).get('pad', 0.55))
        self.h_est = 0

    # ---- timing
    def say_time(self, say):
        """clip time of a say spec, or None when it is not spoken in this scene."""
        m = re.match(r'^(.*?)(?:#(\d+))?([+-][\d.]+)?$', say); words = [norm(x) for x in m.group(1).split()]
        seq = [w for w, _ in self.words]
        hits = [i for i in range(len(seq)) if seq[i:i + len(words)] == words]
        n = int(m.group(2) or 1)
        return self.words[hits[n - 1]][1] + float(m.group(3) or 0) if len(hits) >= n else None

    def say_ok(self, say): return self.say_time(say) is not None

    def need(self, text, at):
        """v0.10: warn now (instead of an audit FAIL later) when text lands too late in the scene to be read."""
        txt = re.sub(r'\*\*|<[^>]+>', '', str(text)).strip()
        if not txt or at is None: return
        left = self.dur + self.pad + self.extra - at; need = 0.6 + 0.07 * len(txt)
        if left < need: self.warns.append(f'scene {self.k}: "{txt[:30]}" lands at {at:.1f}s of {self.dur:.1f}s — only {left:.1f}s to read (needs ~{need:.1f}s): tie it to an earlier word')

    def timing(self, b, text=''):
        if 't' in b:
            try: self.need(text, float(b['t']) - self.off); return f' data-t="{float(b["t"]):.2f}"'
            except (TypeError, ValueError): self.warns.append(f'scene {self.k}: "t" must be seconds, got {b["t"]!r}'); b = {k: v for k, v in b.items() if k != 't'}
        if 'say' in b:
            self.need(text, self.say_time(b['say']))
            if not self.say_ok(b['say']):
                self.warns.append(f'scene {self.k}: say "{b["say"]}" is not spoken here — words: ' + ' '.join(w for w, _ in self.words))
            return f' data-say="{E(b["say"])}"'
        toks = [norm(x) for x in re.split(r'\s+', re.sub(r'\*\*', '', text)) if norm(x)]
        for i, (w, t) in enumerate(self.words):                         # first word of the text that is spoken, after the last block
            if t > self.cursor and w in toks:
                self.cursor = t; n = sum(1 for ww, _ in self.words[:i + 1] if ww == w); self.need(text, t)
                return f' data-say="{E(w)}{"#" + str(n) if n > 1 else ""}"'
        self.n_auto += 1; t = round(min(self.dur * .75, max(self.cursor, 0) + .6 * self.n_auto + (0 if self.cursor >= 0 else .1)), 2)
        return f' data-t="{t:.2f}"'

    # ---- text with **marks**
    def rich(self, s):
        parts = re.split(r'\*\*(.+?)\*\*', str(s)); out = []
        for i, p in enumerate(parts):
            out.append(f'<span class="mk" data-a="mark" data-t="{{T}}">{E(p)}</span>' if i % 2 else E(p))
        return ''.join(out)

    def est(self, text, size, width=W):
        px = SIZES.get(size, 48); chars = len(re.sub(r'\*\*', '', str(text)))
        lines = max(1, -(-int(chars * px * .55) // width)); self.h_est += lines * px * 1.25 + 30
        if size in ('h0',) and lines > 1: self.warns.append(f'scene {self.k}: "{text}" wraps at h0 — use h1 or shorten')

    def block(self, b):
        T = lambda txt='': self.timing(b, txt)
        sfx = lambda s: f' data-sfx="{b.get("sfx", s)}"' if b.get('sfx', s) else ''
        for size in ('h0', 'h1', 'h2', 'h3', 'b'):
            if size in b:
                self.est(b[size], size); t = T(b[size]); inner = self.rich(b[size])
                tv = re.search(r'data-(?:t|say)="([^"]+)"', t).group(1)
                inner = inner.replace('data-t="{T}"', f'data-say="{tv}+0.4"' if 'data-say' in t else f'data-t="{float(tv) + .4:.2f}"')
                return f'<div class="{size}" data-a="{b.get("a", "up")}"{t}>{inner}</div>'
        if 'blk' in b:
            sz = b.get('size', 'h0' if len(b['blk']) <= 9 else 'h1'); self.est(b['blk'], sz)
            return f'<div class="{sz} blkw" data-a="{b.get("a", "slam")}"{T(b["blk"])}{sfx("impact")}><span class="blk">{E(b["blk"])}</span></div>'
        if 'num' in b:
            sz = b.get('size', 'h0'); n = b['num']; fr = b.get('from', 0); dec = b.get('dec', 0)
            self.est(f"{b.get('pre', '')}{n}{b.get('post', '')}", sz)
            cnt = f'<span data-a="count" data-from="{fr}" data-to="{n}"' + (f' data-dec="{dec}"' if dec else '') + (f' data-fmt="{b["fmt"]}"' if b.get('fmt') else '') + \
                  f' data-d="{b.get("d", 1.0)}"{{T}}{sfx("tick")}>{E(fr)}</span>'
            t = T(str(n)); cnt = cnt.replace('{T}', t)
            inner = f'{E(b.get("pre", ""))}{cnt}{E(b.get("post", ""))}'
            if b.get('box', True): inner = f'<span class="blk">{inner}</span>'
            return f'<div class="{sz} blkw" data-a="pop"{t}>{inner}</div>'
        if 'chip' in b:
            self.h_est += 90; return f'<div data-a="{b.get("a", "pop")}"{T(b["chip"])}><span class="chipx">{E(b["chip"])}</span></div>'
        if 'note' in b:
            self.h_est += 100; return f'<div data-a="pop"{T(b["note"])}{sfx("tone")}><span class="notex">{E(b["note"])}</span></div>'
        if 'card' in b:
            c = b['card'] if isinstance(b['card'], list) else [b['card']]; self.h_est += 220
            sub = ''.join(f'<div class="sub">{E(x)}</div>' for x in c[1:])
            head = self.rich(c[0]).replace(' data-t="{T}"', '').replace('data-a="mark"', '')
            return f'<div class="cardx" data-a="pop"{T(c[0])}{sfx("paper")}><div class="{b.get("size", "h2")}">{head}</div>{sub}</div>'
        if 'tags' in b:
            says = b.get('says') or [None] * len(b['tags']); self.h_est += 110 * (1 + len(b['tags']) // 3); out = []
            for i, (tg, sy) in enumerate(zip(b['tags'], says)):
                bb = {'say': sy} if sy else {}
                out.append(f'<span data-a="pop"{self.timing(bb, tg)}{sfx("pop") if i == 0 else ""}><span class="chipx">{E(tg)}</span></span>')
            return f'<div class="tags">{"".join(out)}</div>'
        if 'bars' in b:
            rows = b['bars']; mx = b.get('max') or max(sum(r['v']) if isinstance(r['v'], list) else r['v'] for r in rows)
            cols = ['var(--accent2)', 'var(--accent)', 'var(--ink)']; out = []; self.h_est += 170 * len(rows) + (60 if b.get('legend') else 0)
            for i, r in enumerate(rows):
                vs = r['v'] if isinstance(r['v'], list) else [r['v']]; x = 0; segs = []
                t = self.timing(r, f"{r.get('l', '')} {r.get('n', '')}")
                tv = re.search(r'data-(t|say)="([^"]+)"', t)
                for j, v in enumerate(vs):
                    w = 960 * v / mx; c = r.get('c') or cols[(j if len(vs) > 1 else i) % 3]
                    st = (f' data-say="{tv.group(2)}+{.35 * j:.2f}"' if tv.group(1) == 'say' else f' data-t="{float(tv.group(2)) + .35 * j:.2f}"')
                    segs.append(f'<i style="left:{x:.0f}px;width:{w:.0f}px;background:{c}" data-a="growx" data-d="{b.get("d", .8)}"{st}{sfx("whoosh") if j == 0 else ""}></i>'); x += w
                out.append(f'<div class="lbl"><span>{E(r.get("l", ""))}</span><span>{E(r.get("n", ""))}</span></div><div class="trk">{"".join(segs)}</div>')
            lg = ''
            if b.get('legend'): lg = '<div class="legend">' + ''.join(f'<i style="background:{cols[j % 3]}"></i>{E(n)}' for j, n in enumerate(b['legend'])) + '</div>'
            return f'<div class="barsx">{"".join(out)}{lg}</div>'
        if 'share' in b:
            cols = ['var(--accent2)', 'var(--accent)', 'var(--ink)', 'var(--card-bg)']; tot = sum(p for _, p in b['share']); segs, labs = [], []; self.h_est += 260
            for i, (lab, p) in enumerate(b['share']):
                t = self.timing({'say': b['says'][i]} if b.get('says') else {}, lab)
                segs.append(f'<i style="width:{100 * p / tot:.1f}%;background:{cols[i % 4]}" data-a="growx" data-d=".6"{t}{WHOOSH if i == 0 else ""}></i>')
                labs.append(f'<span style="width:{100 * p / tot:.1f}%" data-a="up"{t}>{E(lab)}</span>')
            return f'<div><div class="share">{"".join(segs)}</div><div class="sharel">{"".join(labs)}</div></div>'
        if 'chain' in b:
            out = []; self.h_est += 190 * len(b['chain'])
            for i, c in enumerate(b['chain']):
                if i: out.append('<div class="arw">↓</div>')
                out.append(f'<div class="cardx" data-a="pop"{self.timing({}, c)}{sfx("paper") if i == 0 else ""}><div class="h3">{E(c)}</div></div>')
            return f'<div class="chain">{"".join(out)}</div>'
        if 'vs' in b:
            a_, c_ = b['vs']; self.h_est += 260
            return (f'<div class="vs"><div class="cardx" data-a="pop"{self.timing({}, a_)}{sfx("pop")}><div class="h2">{E(a_)}</div></div>'
                    f'<div class="mid" data-a="pop"{self.timing({}, b.get("mid", ""))}>{E(b.get("mid", "নাকি"))}</div>'
                    f'<div class="cardx" data-a="pop"{self.timing({}, c_)}><div class="h2">{E(c_)}</div></div></div>')
        if 'strike' in b:
            old, new = b['strike']; self.h_est += 330
            tn = self.say_time(b['say']) if 'say' in b else None          # the old value shows ~2 s before it is struck
            t1 = self.timing({'say': b['say_old']} if b.get('say_old') else {'t': round(max(0.1, (tn if tn is not None else 2.0) - 2.2) + self.off, 2)}, old)
            t2 = self.timing(b, new)
            tv = re.search(r'data-(t|say)="([^"]+)"', t2)
            st = f' data-say="{tv.group(2)}-0.3"' if tv.group(1) == 'say' else f' data-t="{max(0, float(tv.group(2)) - .3):.2f}"'
            return (f'<div class="h1" data-a="up"{t1}><span class="strk">{E(old)}<i data-a="strike" data-d=".35"{st}></i></span></div>'
                    f'<div class="h0 blkw" data-a="slam"{t2}{sfx("impact")}><span class="blk">{E(new)}</span></div>')
        if 'photo' in b:
            f = self.img(b['photo']); h = b.get('h', 480); self.h_est += h + 40
            cap = f'<div class="cap">{E(b["cap"])}</div>' if b.get('cap') else ''
            pos = f';background-position:{b["pos"]}' if b.get('pos') else ''
            return f'<div data-a="pop"{T(b.get("cap", ""))}{sfx("paper")}><div class="phb" style="background-image:url({f});height:{h}px;width:{b.get("w", 860)}px{pos}"></div>{cap}</div>'
        if 'grid' in b:
            n = b['grid']; cols = b.get('cols', 12); on = b.get('on', 0); size = min(70, (900 - 8 * (cols - 1)) // cols)
            rows = -(-n // cols); self.h_est += rows * (size + 8) + 20; t = self.timing(b, b.get('label', ''))
            tv = re.search(r'data-(t|say)="([^"]+)"', t); cells = []
            for i in range(n):
                dt_ = 1.2 * i / max(1, n)
                st = f' data-say="{tv.group(2)}+{dt_:.2f}"' if tv.group(1) == 'say' else f' data-t="{float(tv.group(2)) + dt_:.2f}"'
                cells.append(f'<i class="{"on" if i < on else ""}" data-a="pop"{st}></i>')
            return f'<div class="gridx" style="grid-template-columns:repeat({cols},{size}px)" data-sfx="tick">{"".join(cells)}</div>'
        if 'row' in b:
            return f'<div class="row">{"".join(self.block(x) for x in b["row"])}</div>'
        if 'gap' in b:
            self.h_est += b['gap']; return f'<div style="height:{b["gap"]}px"></div>'
        if 'html' in b: return b['html']
        self.warns.append(f'scene {self.k}: unknown block {list(b)}'); return ''

    def img(self, name):
        for d in ('img', 'images'):
            if (self.P / d / name).exists(): return f'{d}/{name}'
        self.warns.append(f'scene {self.k}: photo {name} not found in img/ or images/'); return f'img/{name}'

    def html(self, last, end_hold, tex):
        self.extra = end_hold if last else 0.0; s = self.s; photo = s.get('photo'); th = 'thp' if photo else f'th{s.get("bg", (self.k - 1) % 6)}'
        mood = s.get('mood', 'build'); cam = s.get('cam') or (f'0:1.06:0:0|{self.dur:.1f}:1:0:0' if photo else f'0:1:0:0|{self.dur:.1f}:1.04:0:-20')
        dur = f' data-dur="{self.dur + end_hold:.2f}"' if last else ''
        bgx = f'<div class="bgx {s.get("tex", tex) if s.get("tex", tex) != "none" else ""}"></div>'
        layers = ''
        if photo:
            f = self.img(photo)
            layers = (f'<div class="a ph" style="left:0;top:0;width:1080px;height:1920px" data-kb="1" data-layer="cam"><img src="{f}"'
                      + (f' style="object-position:{s["pos"]}"' if s.get('pos') else '') + '></div>'
                      '<div class="a wash" style="left:0;top:0;width:1080px;height:1920px" data-layer="cam"></div>')
        body = '\n    '.join(self.block(b) for b in s.get('blocks', []))
        if self.h_est > SAFE_H + 40: self.warns.append(f'scene {self.k}: about {self.h_est:.0f} px of content for {SAFE_H} px — drop or shrink a block')
        al = ' '.join(x for x in ('top' if s.get('align') == 'top' or (photo and s.get('align') != 'center') else '', 'left' if s.get('align') == 'left' else '') if x)
        src = f'\n  <div class="src">{E(s["src"])}</div>' if s.get('src') else ''
        return (f'<!-- {self.k} -->\n<section class="scene {th}" data-vo="{self.k}" data-mood="{mood}"{dur} data-cam="{cam}">\n  {bgx}\n'
                f'  <div class="band t"></div><div class="band b"></div>\n  <div class="cam">\n    {layers}\n'
                f'    <div class="a col {al}">\n    {body}\n    </div>\n  </div>{src}\n</section>\n')


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('project'); ap.add_argument('--check', action='store_true'); ap.add_argument('--spec', default='build.json')
    a = ap.parse_args(); P = pathlib.Path(a.project).resolve()
    spec = jl(P / a.spec) or sys.exit(f'no {a.spec} in {P.name} (or it is not valid JSON) — write the scene plan first (docs/cheatsheet.md)')
    look = jl(P / 'docs' / 'look.json') or sys.exit('no docs/look.json — run studio.py look first')
    pj = jl(P / 'project.json', {}); vo = load_vo(P); warns = []
    n_vo = len([d for d in vo.get('durs', [])[1:] if d])
    sc = spec.get('scenes', [])
    if n_vo and len(sc) != n_vo: warns.append(f'{len(sc)} scenes in {a.spec} but {n_vo} VO clips — one scene per clip')
    band = spec.get('bands', 'zigzag')
    if band not in BANDS: sys.exit(f'bands must be one of {BANDS}')
    prev = jl(P.parent / f'video{int(re.sub(r"[^0-9]", "", P.name) or 1) - 1:02d}' / 'build.json', {})
    if prev.get('bands') == band: warns.append(f'bands "{band}" was used by the previous episode — pick another ({", ".join(b for b in BANDS if b != band)})')
    end_hold = float(pj.get('end_hold', 1.0)); off = float(pj.get('voOffset', .3)); lead = float(pj.get('sayLead', .25))
    secs = [Scene(i + 1, s, vo, P, look, warns, off, lead).html(i == len(sc) - 1, end_hold, spec.get('tex', 'dots')) for i, s in enumerate(sc)]
    for i, x in enumerate(sc):
        if x.get('mood', 'build') not in MOODS: warns.append(f'scene {i + 1}: mood "{x.get("mood")}" unknown — use one of {MOODS}')
    if sc and sc[0].get('mood', 'build') != 'intro': warns.append('scene 1 should have "mood": "intro"')
    if sc and sc[-1].get('mood', 'build') != 'end': warns.append('last scene should have "mood": "end"')
    for w in warns: print('WARN ' + w)
    if a.check: print(f'CHECK {"OK" if not warns else "see WARN lines"} ({len(sc)} scenes)'); return
    old = (P / 'index.html').read_text(encoding='utf-8') if (P / 'index.html').exists() else ''
    head = old.split('<style>')[0] if '<style>' in old else None
    if not head:
        tpl = pathlib.Path(__file__).resolve().parent.parent / 'template' / 'index.html'
        head = tpl.read_text(encoding='utf-8').split('<style>')[0].replace('{{LANG}}', pj.get('lang', 'bn')).replace('{{TITLE}}', pj.get('title', P.name)).replace('{{PRESET}}', pj.get('preset', 'vox-money'))
    proj = {k: pj[k] for k in ('lang', 'voOffset', 'pad', 'transition', 'sayLead') if k in pj}
    css = f"/* generated by build_scenes.py from build.json — edit build.json, not this file. look {look['id']}, bands {band} */\n" + \
          theme_css(look) + '\n' + band_css(band, look) + BASE_CSS + (spec.get('css') or '')
    out = (head + '<style>\n' + css + '\n</style>\n</head>\n<body>\n\n' + '\n'.join(secs) +
           f'\n<script>window.PROJECT = {json.dumps(proj, ensure_ascii=False)};</script>\n<script src="vo.js"></script>\n<script src="engine/engine.js"></script>\n</body>\n</html>\n')
    (P / 'index.html').write_text(out, encoding='utf-8')
    print(f'index.html written: {len(sc)} scenes, {len(out) // 1024} KB, bands {band}' + (f', {len(warns)} warning(s)' if warns else ''))


if __name__ == '__main__':
    main()
