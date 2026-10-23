"""Original score + synced SFX + VO mix, all synthesized in Python (no samples, no licences).
usage: python audio.py <project>            (needs cues.json + scenes.json from audit.py, vo/vo_NN.wav from vo_prep.py)
Config: audio_config.json (palette, moods, levels). Scene moods come from data-mood on each <section>.
Output: out/mix.wav (24-bit, master -14.5 LUFS, true peak ≤ -1.5 dBTP, clean silent ending), out/music_only.wav, out/audio_report.txt"""
import json, sys, pathlib
import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
import soundfile as sf
import pyloudnorm as pyln
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from es import project, cfg

P = project(sys.argv[1] if len(sys.argv) > 1 else None)
C = json.loads((P / 'audio_config.json').read_text())
L = C['levels']; G = C.get('sfx_gain', {})
if not (P / 'cues.json').exists(): sys.exit('run audit.py first (writes cues.json/scenes.json)')
cues = json.load(open(P / 'cues.json')); scenes = json.load(open(P / 'scenes.json'))
PC = cfg(P); VO_OFF = PC.get('voOffset', 0.3)
SR = 44100; rng = np.random.default_rng(C.get('seed', 7))
TOTAL = scenes[-1]['start'] + scenes[-1]['dur']; N = int(TOTAL * SR)
BEAT = 60 / C.get('bpm', 80); BAR = 4 * BEAT
mtof = lambda m: 440 * 2 ** ((m - 69) / 12)
report = []

# ---- mood timeline (data-mood carries forward) ----
moods, cur = [], 'intro'
for s in scenes:
    cur = s.get('mood') or cur; moods.append((s['start'], cur))
def mood_at(t):
    m = moods[0][1]
    for st, mo in moods:
        if t >= st - 1e-6: m = mo
    return m
end_scene = next((s for s, (_, mo) in zip(scenes, moods) if mo == 'end'), scenes[-1])
END_T = (TOTAL - C['end_chord_s']) if C.get('end_chord_s') else end_scene['start'] - 0.6   # end_chord_s: closing chord this many s before the end (rings through the hold)

# ---- DSP helpers ----
def env_adsr(n, a, d, s, r):
    a, d, r = int(a * SR), int(d * SR), int(r * SR); sus = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False), np.full(sus, s), np.linspace(s, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]
def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= buf.shape[0] or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    j = min(buf.shape[0], i + len(x)); x = x[: j - i] * gain
    buf[i:j, 0] += x * np.cos((pan + 1) * np.pi / 4) * 1.414; buf[i:j, 1] += x * np.sin((pan + 1) * np.pi / 4) * 1.414
def _f(kind, fc, order=2):
    return signal.butter(order, np.array(fc) / (SR / 2), kind)
def lp(x, fc, o=2): b, a = _f('low', fc, o); return signal.lfilter(b, a, x)
def hp(x, fc, o=2): b, a = _f('high', fc, o); return signal.lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = _f('band', [lo, min(hi, SR / 2 - 200)], o); return signal.lfilter(b, a, x)
def reverb_ir(sec=2.6, damp=3000, seed=1):
    r = np.random.default_rng(seed); n = int(sec * SR)
    ir = r.standard_normal((n, 2)) * np.exp(-np.arange(n) / SR * 3.2)[:, None]
    ir = np.stack([lp(ir[:, 0], damp), lp(ir[:, 1], damp)], 1); ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))[None, :] * 0.5
IR = reverb_ir()
def reverb(st, wet): return st + np.stack([signal.fftconvolve(st[:, c], IR[:, c])[: len(st)] for c in range(2)], 1) * wet
_cache = {}
def cached(key, fn):
    if key not in _cache: _cache[key] = fn()
    return _cache[key]

# ---- instruments ----
def pad_note(f, dur, amp, cutoff=1800):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for det in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (det / 12)
        for h, ha in ((1, 1), (2, .35), (3, .15), (4, .07)): x += ha * np.sin(2 * np.pi * ff * h * tt + rng.uniform(0, 6.28))
    return lp(x * env_adsr(n, min(1.2, dur * .4), .3, .85, min(1.4, dur * .45)) * amp, cutoff)
def pluck(f, amp, dec=1.6):
    n = int((dec + .2) * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt) + .42 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 2.2) + .18 * np.sin(2 * np.pi * 3.01 * f * tt) * np.exp(-tt * 4)
    return lp(x * np.minimum(1, tt / .006) * np.exp(-tt * (2.6 / dec)) * amp, 3500)
def kick():
    n = int(.35 * SR); tt = np.arange(n) / SR; f = 48 + 60 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 11)
def ks_string(f, dur, bright=0.5, decay=0.996, seed=0):
    """Karplus-Strong plucked string (dotara/ektara), via lfilter so it's fast."""
    Ld = int(round(SR / f)); n = int(dur * SR)
    exc = np.zeros(n); r = np.random.default_rng(seed)
    burst = r.uniform(-1, 1, Ld); burst = lp(burst, 1500 + 6000 * bright)
    exc[:Ld] = burst
    a = np.zeros(Ld + 2); a[0] = 1; a[Ld] = -0.5 * decay; a[Ld + 1] = -0.5 * decay
    y = signal.lfilter([1.0], a, exc)
    y = hp(y, 60); y *= np.minimum(1, np.arange(n) / (0.002 * SR))
    return y / (np.abs(y).max() + 1e-9)
def tanpura(f, dur=4.5):
    """Additive tanpura note: harmonics bloom then fade one after another (jawari shimmer)."""
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for h in range(1, 22):
        peak = 0.25 + 0.11 * h; amp = 1 / h ** 0.9
        e = (tt / peak) * np.exp(1 - tt / peak)                    # each harmonic swells at its own time
        x += amp * e * np.sin(2 * np.pi * f * h * tt * (1 + 0.0004 * h) + rng.uniform(0, 6.28))
    x *= np.exp(-tt * 0.5) * np.minimum(1, tt / 0.01)
    return lp(x, 5200) / 6
def harmonium(f, dur, amp):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = sum((1 / h) * np.sin(2 * np.pi * f * h * tt + h) for h in range(1, 9))
    x *= 1 + 0.06 * np.sin(2 * np.pi * 5.2 * tt)                     # bellows wobble
    return lp(x * env_adsr(n, .35, .2, .9, min(.9, dur * .4)) * amp, 2400)
def bansuri(f, dur, amp):
    n = int(dur * SR); tt = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * tt) * np.clip((tt - 0.25) / 0.4, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = bp(rng.standard_normal(n), f * 0.8, f * 3.5) * 0.12
    return lp((tone + breath) * env_adsr(n, .09, .15, .8, min(.35, dur * .4)) * amp, 4500)
def tabla(kind):
    n = int(.6 * SR); tt = np.arange(n) / SR; sa = mtof(C.get('sa_midi', 50) + 12)
    if kind == 'ge':        # bayan: low, pitch glides up
        f = 85 + 30 * (1 - np.exp(-tt * 12)); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6) * .9
    if kind == 'na':        # dayan ringing stroke
        x = sum(a * np.sin(2 * np.pi * sa * m * tt) * np.exp(-tt * d) for m, a, d in ((1, 1, 9), (2, .5, 12), (3, .3, 15), (4, .2, 20)))
        return x * .5 + bp(rng.standard_normal(n), 2000, 7000) * np.exp(-tt * 90) * .2
    if kind == 'ti':        # closed stroke
        return bp(rng.standard_normal(n), 900, 4000) * np.exp(-tt * 70) * .6
    if kind == 'dha':
        return tabla('ge') + tabla('na')
    return np.zeros(n)

RAGA = {'bhupali': [0, 2, 4, 7, 9], 'yaman': [0, 2, 4, 6, 7, 9, 11], 'bhairavi': [0, 1, 3, 5, 7, 8, 10],
        'khamaj': [0, 2, 4, 5, 7, 9, 10], 'bhairav': [0, 1, 4, 5, 7, 8, 11]}
def raga_notes(name, lo, hi):
    sa = C.get('sa_midi', 50); out = []
    for o in range(-2, 4):
        for s in RAGA[name]:
            m = sa + 12 * o + s
            if lo <= m <= hi: out.append(m)
    return out

music = np.zeros((N, 2)); nbars = int(np.ceil(END_T / BAR))
pal = C.get('palette', 'bangla')
if pal == 'cinematic':
    # v0.7: chord set, pattern, kick moods and closing chord are configurable so five music presets sound different (studio/music_bank.json)
    PROGS = {
        'dm':   [(50, [62, 65, 69]), (46, [62, 65, 70]), (41, [60, 65, 69]), (48, [60, 64, 67]),
                 (50, [62, 65, 69]), (43, [62, 67, 70]), (46, [62, 65, 70]), (45, [61, 64, 69])],
        'am':   [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [60, 64, 67]), (43, [59, 62, 67]),
                 (45, [57, 60, 64]), (41, [57, 60, 65]), (48, [60, 64, 67]), (40, [56, 59, 64])],
        'cmaj': [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]),
                 (48, [60, 64, 67]), (43, [59, 62, 67]), (41, [57, 60, 65]), (43, [59, 62, 67])]}
    PROG = PROGS.get(C.get('prog', 'dm'), PROGS['dm'])
    pattern = C.get('pattern', [0, 2, 1, 2, 0, 2, 1, 2])
    KICK = set(C.get('kick_moods', ['drive']))
    END_NOTES = C.get('end_notes', [50, 57, 62, 65, 69, 76]); END_PLUCK = C.get('end_pluck', [74, 81])
    for k in range(nbars):
        t0 = k * BAR; mo = mood_at(t0); root, tri = PROG[k % 8]
        amp = {'intro': .05, 'drive': .06, 'somber': .06, 'elegy': .062}.get(mo, .055)
        for i, m in enumerate(tri): place(music, pad_note(mtof(m), BAR + 1.3, amp), t0 - .2, pan=(-.35, 0, .35)[i])
        if mo != 'intro':
            n = int(BAR * SR); tt = np.arange(n) / SR; fb = mtof(root - 12 if root > 45 else root)
            bass = (np.sin(2 * np.pi * fb * tt) + .2 * np.sin(4 * np.pi * fb * tt)) * env_adsr(n, .08, .6, .6, .9) * (.11 if mo in ('somber', 'elegy') else .09)
            place(music, lp(bass, 400), t0)
        notes = [m + 12 for m in tri]
        if mo == 'intro':
            for j in (0, 4): place(music, pluck(mtof(notes[[0, 2][j // 4]]), .05, 2.2), t0 + j * BEAT / 2, pan=.2)
        elif mo in ('build', 'drive'):
            for j, idx in enumerate(pattern):
                place(music, pluck(mtof(notes[idx]), (.045 if mo == 'build' else .052) * (1 if j % 4 == 0 else .7)), t0 + j * BEAT / 2, pan=-.25 + .25 * idx)
            if mo in KICK:
                for j in (0, 2): place(music, kick(), t0 + j * BEAT, .10)
        elif mo in ('somber', 'elegy'):
            for j in (0, 3): place(music, pluck(mtof(notes[0] if j == 0 else notes[2]), .055, 2.6), t0 + j * BEAT, pan=-.1)
        elif mo == 'answer':
            for j, idx in enumerate([0, 1, 2, 1]): place(music, pluck(mtof(notes[idx] + (12 if j == 2 else 0)), .045, 2.2), t0 + j * BEAT, pan=.15)
    for i, m in enumerate(END_NOTES): place(music, pad_note(mtof(m), 7.5, .05 if m > 55 else .07), END_T, pan=-.4 + .16 * i)
    for i, m in enumerate(END_PLUCK): place(music, pluck(mtof(m), .05, 3.5), END_T + .05 + i * .35, pan=.2 * (1 if i else -1))
else:
    sa = C.get('sa_midi', 50); MO = C['moods']
    # tanpura: Pa – Sa' – Sa' – Sa cycle, one string every BEAT, continuous to the end chord
    cyc = [sa - 5, sa + 12, sa + 12, sa]; t = 0.0; k = 0
    while t < END_T + 2:
        m = cyc[k % 4]; place(music, cached(('tan', m), lambda: tanpura(mtof(m))), t, .5, pan=(-.3, .1, .3, -.1)[k % 4]); t += BEAT * 1.25; k += 1
    phrase_gap = 0
    for b in range(nbars):
        t0 = b * BAR; mo = mood_at(t0); spec = MO.get(mo, MO.get('intro')); lay = spec['layers']; rg = spec['raga']
        minor = 3 in RAGA[rg] and 4 not in RAGA[rg]
        if 'harmonium' in lay:
            for i, m in enumerate([sa + 12, sa + 12 + (3 if minor else 4), sa + 19]):
                place(music, harmonium(mtof(m), BAR + .6, .035), t0 - .1, pan=(-.3, 0, .3)[i])
        if 'dotara' in lay:
            pool = raga_notes(rg, sa + 12, sa + 24); pat = [sa + 12, sa + 19, sa + 24, sa + 19]
            for j in range(8):
                m = pat[j % 4] if j % 2 == 0 or rng.random() < .6 else int(rng.choice(pool))
                x = cached(('ks', m), lambda: ks_string(mtof(m), 1.6, .55, .994, seed=m))
                place(music, x, t0 + j * BEAT / 2 + rng.uniform(-.008, .008), (.06 if j % 4 == 0 else .04) * rng.uniform(.9, 1.05), pan=.25)
        if 'tabla' in lay:
            theka = ['dha', 'ge', 'na', 'ti', 'na', 'ka', 'dhi', 'na']        # keherwa
            for j, bol in enumerate(theka):
                bol = {'ka': 'ti', 'dhi': 'dha'}.get(bol, bol)
                place(music, cached(('tb', bol), lambda: tabla(bol)), t0 + j * BEAT / 2, .09 if j in (0, 6) else .06, pan=-.15)
        if 'bansuri' in lay and phrase_gap <= 0:
            pool = raga_notes(rg, sa + 19, sa + 31); idx = int(len(pool) * .4); tt = t0 + BEAT * .5
            for _ in range(int(rng.integers(4, 7))):
                d = float(rng.choice([.5, 1, 1, 1.5, 2])) * BEAT
                place(music, bansuri(mtof(pool[idx]), d + .25, .05), tt, pan=.15); tt += d
                idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2]), 0, len(pool) - 1))
            place(music, bansuri(mtof(sa + 24), BEAT * 2.5, .045), tt, pan=.15)        # resolve to Sa
            phrase_gap = 2
        else:
            phrase_gap -= 1
    # ending: Sa–Pa–Sa' bloom + dotara Sa, clean decay
    for i, m in enumerate([sa, sa + 7, sa + 12, sa + 19, sa + 24]): place(music, harmonium(mtof(m), 6.5, .03), END_T, pan=-.3 + .15 * i)
    place(music, ks_string(mtof(sa + 24), 4, .5, .998), END_T + .05, .07, .2)
    place(music, tanpura(mtof(sa), 6.5), END_T, .55)
music = reverb(music, .3); music = np.stack([hp(music[:, c], 35) for c in range(2)], 1)

# ---- SFX ----
sfx = np.zeros((N, 2))
def s_click():
    n = int(.05 * SR); tt = np.arange(n) / SR
    return bp(rng.standard_normal(n), 1500, 6000) * np.exp(-tt * 260) * .5 + np.sin(2 * np.pi * 2300 * tt) * np.exp(-tt * 180) * .35
def s_tick(p=1.0):
    n = int(.03 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 3100 * p * tt) * np.exp(-tt * 300) * .4 + bp(rng.standard_normal(n), 3000, 9000) * np.exp(-tt * 500) * .15
def s_whoosh(dur=.55, lo=300, hi=4000):
    n = int(dur * SR); tt = np.arange(n) / SR; noise = rng.standard_normal(n)
    bands = [bp(noise, f * .7, f * 1.4) for f in np.geomspace(lo, hi, 6)]; pos = (tt / dur) * (len(bands) - 1)
    x = sum(bnd * np.clip(1 - np.abs(pos - i), 0, 1) for i, bnd in enumerate(bands))
    return x * np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.6 * .5
def s_impact():
    n = int(1.2 * SR); tt = np.arange(n) / SR; f = 42 + 50 * np.exp(-tt * 9)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2) * .9 + lp(rng.standard_normal(n), 900) * np.exp(-tt * 28) * .5
            + np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 6) * .2)
def s_stamp():
    n = int(.4 * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * 150 * tt) * np.exp(-tt * 22) * .8 + bp(rng.standard_normal(n), 400, 3500) * np.exp(-tt * 60) * .6
def s_tone():
    f = mtof(C.get('sa_midi', 50) + 31); n = int(1.6 * SR); tt = np.arange(n) / SR      # Pa, two octaves up — fits every raga
    x = np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 3) + .12 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6)
    return x * np.minimum(1, tt / .004) * np.exp(-tt * 2.6) * .32
def s_trans():
    x = s_whoosh(.6, 200, 2500) * .8; tt = np.arange(len(x)) / SR
    return x + np.sin(2 * np.pi * 70 * tt) * np.exp(-((tt - .45) ** 2) / .004) * .25
def s_bell():      # small brass ghanta / mandir bell: inharmonic partials, long ring
    f = mtof(C.get('sa_midi', 50) + 36); n = int(3 * SR); tt = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-tt * d) for m, a, d in ((1, 1, 1.4), (2.32, .6, 2.2), (4.25, .35, 3.5), (6.63, .2, 5), (.5, .25, 1.0)))
    return x * np.minimum(1, tt / .002) * .25
def s_paper():     # paper/newsprint rustle for cutouts and clippings
    n = int(.45 * SR); tt = np.arange(n) / SR; x = bp(rng.standard_normal(n), 1200, 8000)
    gr = (rng.random(n) < .004).astype(float); gr = np.convolve(gr, np.hanning(300), 'same')
    return x * (0.25 + gr) * np.sin(np.pi * tt / tt[-1]) * .5
def s_pop():
    n = int(.08 * SR); tt = np.arange(n) / SR; f = 900 - 500 * tt / tt[-1]
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 60) * .5
SFX = {'click': (s_click, 0), 'tick': (lambda: s_tick(rng.uniform(.9, 1.12)), 0), 'whoosh': (s_whoosh, -.18), 'trans': (s_trans, -.2),
       'impact': (s_impact, 0), 'stamp': (s_stamp, .12), 'tone': (s_tone, 0), 'bell': (s_bell, 0), 'paper': (s_paper, -.05), 'pop': (s_pop, 0)}
# v0.7: the engine also emits AUTO cues (from data-a: slam→impact, stamp→stamp, pop→pop, …). They are thinned here so the track stays
# subtle: a per-scene cap, a per-type cap, a minimum gap to every other cue, and a lower gain than hand-placed data-sfx cues.
AS = {'enabled': True, 'max_per_scene': 3, 'min_gap_s': 0.6, 'gain_mult': 0.8,
      'priority': ['impact', 'stamp', 'pop', 'whoosh', 'paper', 'click', 'tick'],
      'type_cap': {'impact': 1, 'stamp': 2, 'pop': 2, 'whoosh': 1, 'paper': 1, 'click': 1, 'tick': 1}}
AS.update(C.get('auto_sfx', {}))
_hand = [c for c in cues if not c.get('auto')]; _auto = [c for c in cues if c.get('auto')]
_keep, _taken, _ps, _pt = [], [c['t'] for c in _hand], {}, {}
if AS['enabled']:
    _pri = {k: i for i, k in enumerate(AS['priority'])}
    def _scene_of(t):
        for i, s in enumerate(scenes):
            if s['start'] - 1e-6 <= t < s['start'] + s['dur']: return i
        return len(scenes) - 1
    for c in sorted(_auto, key=lambda c: (_pri.get(c['type'], 99), c['t'])):
        k = _scene_of(c['t']); tk = (k, c['type'])
        if _ps.get(k, 0) >= AS['max_per_scene'] or _pt.get(tk, 0) >= AS['type_cap'].get(c['type'], 1): continue
        if any(abs(c['t'] - x) < AS['min_gap_s'] for x in _taken): continue
        _keep.append(c); _taken.append(c['t']); _ps[k] = _ps.get(k, 0) + 1; _pt[tk] = _pt.get(tk, 0) + 1
cues = sorted(_hand + _keep, key=lambda c: c['t'])
report.append(f'sfx cues: {len(_hand)} placed by hand/transitions, {len(_keep)} automatic (of {len(_auto)} candidates)')
last, duck, used, unknown = {}, np.ones(N), {}, set()
for c in cues:
    t, ty = c['t'], c['type']
    if t < 0 or t >= TOTAL - .3: continue
    if ty not in SFX: unknown.add(ty); continue
    if ty in last and t - last[ty] < .07: continue
    last[ty] = t; used[ty] = used.get(ty, 0) + 1
    fn, off = SFX[ty]; pan = 0 if ty in ('whoosh', 'trans', 'impact', 'stamp') else rng.uniform(-.25, .25)
    place(sfx, fn(), t + off, G.get(ty, .3) * (AS['gain_mult'] if c.get('auto') else 1.0), pan)
    if ty == 'impact':
        i = int(t * SR); n = int(SR); d = 1 - L.get('impact_duck', .35) * np.exp(-np.arange(n) / SR * 3)
        duck[i:i + n] = np.minimum(duck[i:i + n], d[: len(duck[i:i + n])])
sfx = reverb(sfx, .12)
if unknown: report.append(f'WARN unknown sfx types ignored: {sorted(unknown)}')
report.append('sfx used: ' + ', '.join(f'{k}×{v}' for k, v in sorted(used.items())))

# ---- VO ----
meter = pyln.Meter(SR); vo = np.zeros(N); placed = 0
for s in scenes:
    if s['vo'] is None: continue
    f = P / 'vo' / f'vo_{s["vo"]:02d}.wav'
    if not f.exists(): report.append(f'WARN missing {f.name}'); continue
    x, sr0 = sf.read(f)
    if x.ndim > 1: x = x.mean(1)
    if sr0 != SR: x = signal.resample_poly(x, SR, sr0)
    x = hp(x, 70); x *= 10 ** ((L['vo_clip_lufs'] - meter.integrated_loudness(x)) / 20)
    i = int((s['start'] + VO_OFF) * SR); j = min(N, i + len(x))
    if i + len(x) > int((s['start'] + s['dur'] + .3) * SR): report.append(f'WARN vo_{s["vo"]:02d} runs past its scene')
    vo[i:j] += x[: j - i]; placed += 1
if placed:
    vo *= 10 ** ((L['vo_bus_lufs'] - meter.integrated_loudness(np.stack([vo, vo], 1))) / 20)
    e = uniform_filter1d(maximum_filter1d(np.abs(vo), int(.04 * SR)), int(.04 * SR))
    e = np.clip(e / (np.percentile(e[e > 1e-4], 90) + 1e-9), 0, 1)
    rel = np.exp(-1 / (.35 * SR)); env = np.maximum(signal.lfilter([1 - rel], [1, -rel], e), uniform_filter1d(e, int(.02 * SR)))
    vduck = 1 - L.get('vo_duck', .6) * np.clip(env * 1.5, 0, 1)
else:
    vduck = np.ones(N); report.append('WARN no VO placed')
music *= 10 ** ((L['music_lufs'] - meter.integrated_loudness(music)) / 20)
sfx *= 10 ** ((L['sfx_lufs'] - meter.integrated_loudness(sfx)) / 20)
mix = music * (duck * vduck)[:, None] + sfx + np.stack([vo, vo], 1)

# ---- master ----
fade = np.ones(N); fi = int(.3 * SR); fade[:fi] = np.linspace(0, 1, fi)
fo0 = int((TOTAL - C.get('end_fade_s', 4.6)) * SR); fo1 = int((TOTAL - .25) * SR)
fade[fo0:fo1] = np.cos(np.linspace(0, np.pi / 2, fo1 - fo0)) ** 2; fade[fo1:] = 0
mix *= fade[:, None]
mix *= 10 ** ((L['master_lufs'] - meter.integrated_loudness(mix)) / 20)
thr = 10 ** (L['true_peak_db'] / 20)
os_ = signal.resample_poly(mix, 4, 1, axis=0)
pk = np.abs(os_).max(1)[: 4 * len(mix)].reshape(-1, 4).max(1)[: len(mix)]; w = int(.004 * SR)
g = uniform_filter1d(minimum_filter1d(np.minimum(1, thr / np.maximum(maximum_filter1d(pk, 2 * w + 1), 1e-9)), 2 * w + 1), w)
report.append(f'limiter: {(g < 10 ** (-1 / 20)).mean() * 100:.2f}% of samples reduced >1 dB')
mix *= g[:, None]; mix[fo1:] = 0
tp = 20 * np.log10(np.abs(signal.resample_poly(mix, 4, 1, axis=0)).max() + 1e-12)
lu = meter.integrated_loudness(mix)
report.append(f'master: {lu:.2f} LUFS, true peak {tp:.2f} dBTP, length {len(mix) / SR:.2f}s, palette {pal}, music {C.get("music_id", "default")}')
if tp > L['true_peak_db'] + .3: report.append('FAIL true peak above target')
(P / 'out').mkdir(exist_ok=True)
sf.write(P / 'out' / 'mix.wav', mix.astype(np.float32), SR, subtype='PCM_24')
sf.write(P / 'out' / 'music_only.wav', (music * fade[:, None]).astype(np.float32), SR, subtype='PCM_24')
(P / 'out' / 'audio_report.txt').write_text('\n'.join(report) + '\n'); print('\n'.join(report))
