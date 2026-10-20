/* Explainer Studio runtime — deterministic, seekable timeline for HTML→video.
 * Scenes: <section class="scene" data-vo="3" data-dur="auto|9.5" data-cam="t:scale:x:y|...">
 * Elements: data-a (anim) data-t (start s) | data-at="a2" (VO pause anchor #2) data-d data-out data-sfx data-layer
 * Generators: <div data-gen="icons|ticks" ...> (see below)
 * Exposes: seek(t), TOTAL, CUES, SCENES, AUDIT(step), DENSITY(step)
 */
(function () {
  const VO = window.VO || { durs: [], anchors: [] };          // written by tools/vo_prep.py into vo.js
  const CFG = Object.assign({ voOffset: 0.3, pad: 0.55, transition: 0.45, safeBottom: 1795, width: 1080, height: 1920 }, window.PROJECT || {});
  const TR = CFG.transition;
  const BN = '০১২৩৪৫৬৭৮৯';
  const digits = (n) => (CFG.lang === 'en' ? String(n) : String(n).replace(/\d/g, (d) => BN[d]));
  const cl = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
  const eo = (p) => 1 - Math.pow(1 - cl(p), 3);
  const eio = (p) => { p = cl(p); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
  const eb = (p) => { p = cl(p); const c = 1.70158, c3 = c + 1; return 1 + c3 * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };
  let seed = 7; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };

  const scenes = [...document.querySelectorAll('.scene')];

  // ---- durations from VO ----
  let acc = 0;
  scenes.forEach((s, i) => {
    const vi = s.dataset.vo !== undefined ? +s.dataset.vo : null;
    let d = s.dataset.dur;
    if ((!d || d === 'auto') && vi !== null && VO.durs[vi] != null) d = VO.durs[vi] + CFG.pad;
    if ((!d || d === 'auto') && vi !== null) console.warn('scene', i + 1, 'has data-vo', vi, 'but no VO duration — run vo_prep.py');
    s._voMiss = vi !== null && (!d || d === 'auto'); s._dur = +d || 5; s._start = acc; s._vo = vi; acc += s._dur;
  });

  // ---- torn edges ----
  document.querySelectorAll('.torn').forEach((el) => {
    const pts = [], n = 26;
    for (let i = 0; i <= n; i++) pts.push(`${(i / n * 100).toFixed(2)}% ${(rnd() * 3.5).toFixed(2)}%`);
    for (let i = n; i >= 0; i--) pts.push(`${(i / n * 100).toFixed(2)}% ${(100 - rnd() * 3.5).toFixed(2)}%`);
    el.style.clipPath = `polygon(${pts.join(',')})`;
  });

  // ---- generators ----
  const ICONS = {
    person: (c) => `<svg class="ico" viewBox="0 0 40 64" width="100%"><circle cx="20" cy="12" r="11" fill="${c}"/><path d="M3 64V38a17 17 0 0 1 34 0v26z" fill="${c}"/></svg>`,
    phone: (c) => `<svg class="ico" viewBox="0 0 60 96" width="100%"><rect x="3" y="3" width="54" height="90" rx="10" fill="${c}"/><rect x="10" y="14" width="40" height="62" rx="3" fill="rgba(0,0,0,.75)"/><path d="M22 40l16 16M38 40L22 56" stroke="#ffc93c" stroke-width="5" stroke-linecap="round"/></svg>`,
    house: (c) => `<svg class="ico" viewBox="0 0 60 56" width="100%"><path d="M30 2L2 26h8v28h40V26h8z" fill="${c}"/></svg>`,
    dot: (c) => `<svg class="ico" viewBox="0 0 10 10" width="100%"><circle cx="5" cy="5" r="5" fill="${c}"/></svg>`,
    doc: (c) => `<svg class="ico" viewBox="0 0 48 60" width="100%"><path d="M2 2h30l14 14v42H2z" fill="${c}"/><path d="M10 26h28M10 34h28M10 42h20" stroke="rgba(255,255,255,.7)" stroke-width="3"/></svg>`,
  };
  document.querySelectorAll('[data-gen]').forEach((g) => {
    const kind = g.dataset.gen, n = +g.dataset.n || 10, t0 = +g.dataset.t0 || 0, step = +g.dataset.step || 0.08;
    const color = g.dataset.color || 'var(--ink)', hl = (g.dataset.hl || '').split(',').filter(Boolean).map(Number);
    const hlColor = g.dataset.hlcolor || 'var(--red)', every = +g.dataset.sfxEvery || 3;
    for (let i = 0; i < n; i++) {
      const d = document.createElement('div');
      if (kind === 'ticks') {
        const x = n > 1 ? (i / (n - 1)) * 96 + 2 : 50;
        d.style.cssText = `position:absolute;left:${x}%;top:${g.dataset.top || 30}px;width:10px;height:${g.dataset.h || 88}px;margin-left:-5px;background:${hl.includes(i) ? hlColor : (g.dataset.color || 'var(--red)')};border-radius:3px`;
      } else {
        d.style.width = (g.dataset.size || 60) + 'px';
        d.innerHTML = (ICONS[g.dataset.icon || 'person'])(hl.includes(i) ? hlColor : color);
      }
      d.dataset.a = 'pop'; d.dataset.t = (t0 + i * step).toFixed(3); d.dataset.d = g.dataset.d || '0.28';
      if (i % every === 0) d.dataset.sfx = g.dataset.sfx || 'tick';
      g.appendChild(d);
    }
  });

  // ---- layer split: photos stay in .cam (camera moves), everything else goes to fixed .fix ----
  scenes.forEach((s) => {
    const c = s.querySelector('.cam'); if (!c) return;
    const fx = document.createElement('div'); fx.className = 'fix ' + [...c.classList].filter((k) => k !== 'cam').join(' ');
    [...c.children].forEach((el) => {
      const lay = el.dataset.layer || (el.tagName === 'IMG' || el.querySelector('img') ? 'cam' : 'fix');
      if (lay === 'fix') fx.appendChild(el);
    });
    c.after(fx);
  });

  // ---- resolve VO anchors: data-at="a2[+0.2]" -> data-t ----
  scenes.forEach((s) => {
    const anc = s._vo !== null ? (VO.anchors[s._vo] || []) : [];
    s.querySelectorAll('[data-at]').forEach((e) => {
      const m = e.dataset.at.match(/^a(\d+)([+-][\d.]+)?$/); if (!m) return;
      const k = +m[1]; const base = k === 0 ? 0 : (anc[k - 1] !== undefined ? anc[k - 1] : null);
      if (base === null) { console.warn('missing anchor ' + e.dataset.at + ' in scene ' + (scenes.indexOf(s) + 1) + ' (vo_' + s._vo + ' has ' + anc.length + ' pauses) — use a smaller aN or data-t'); return; }
      e.dataset.t = (CFG.voOffset + base - 0.08 + (m[2] ? +m[2] : 0)).toFixed(3);
    });
    s._els = [...s.querySelectorAll('[data-a]')]; s._cam = s.querySelector('.cam');
    s._keys = (s.dataset.cam || '0:1:0:0').split('|').map((k) => k.split(':').map(Number));
    s._kb = [...s.querySelectorAll('[data-kb] img')];
  });

  function cam(s, lt) {
    const K = s._keys; if (lt <= K[0][0]) return K[0]; if (lt >= K[K.length - 1][0]) return K[K.length - 1];
    for (let i = 0; i < K.length - 1; i++) if (lt >= K[i][0] && lt <= K[i + 1][0]) {
      const p = eio((lt - K[i][0]) / (K[i + 1][0] - K[i][0])); return K[i].map((v, j) => v + (K[i + 1][j] - v) * p);
    }
    return K[0];
  }
  function applyEl(e, lt) {
    const a = e.dataset.a, t = +e.dataset.t || 0, d = +(e.dataset.d || 0.5);
    const r = (lt - t) / d, p = eo(r); let op = null;
    switch (a) {
      case 'up': op = p; e.style.transform = `translateY(${(1 - p) * 46}px)`; break;
      case 'left': op = p; e.style.transform = `translateX(${-(1 - p) * 34}px)`; break;
      case 'right': op = p; e.style.transform = `translateX(${(1 - p) * 34}px)`; break;
      case 'fade': op = p; break;
      case 'pop': { const q = eb(r); op = cl(r * 3); e.style.transform = `scale(${r <= 0 ? 0.001 : Math.max(0.001, q)})`; break; }
      case 'slam': { const q = cl(r / 0.9); const sc = q < 1 ? 1.14 - 0.14 * eb(q) : 1; op = cl(q * 3); e.style.transform = `scale(${sc})`; break; }
      case 'stamp': { const q = cl(r); const sc = q < 1 ? 1.25 - 0.25 * eo(q) : 1; op = cl(q * 2.5); e.style.transform = `scale(${sc})`; break; }
      case 'mark': e.style.setProperty('--m', p); break;
      case 'drawy': e.style.transform = `scaleY(${p})`; break;
      case 'growx': e.style.transform = `scaleX(${p})`; break;
      case 'strike': e.style.transform = `rotate(-4deg) scaleX(${p})`; break;
      case 'draw': e.style.strokeDasharray = '1'; e.style.strokeDashoffset = String(1 - p); break;
      case 'rot': { const f = +e.dataset.from, to = +e.dataset.to; e.style.transform = `rotate(${f + (to - f) * eio(r)}deg)`; break; }
      case 'count': { const f = +(e.dataset.from || 0); const v = f + (+e.dataset.to - f) * eo(r); const dec = +(e.dataset.dec || 0); e.textContent = digits(dec ? v.toFixed(dec) : Math.round(v)); break; }
    }
    if (e.dataset.out) { const o = +e.dataset.out; const q = cl((lt - o) / 0.35); if (op === null) op = 1; op *= 1 - q; }
    if (op !== null) e.style.opacity = op;
  }
  const TOTAL = acc;
  window.seek = function (t) {
    scenes.forEach((s, i) => {
      const lt = t - s._start, last = i === scenes.length - 1;
      const vis = lt >= 0 && lt < s._dur + (last ? 10 : TR);
      if (!vis) { s.style.display = 'none'; return; }
      s.style.display = 'block';
      let op = 1, tx = 0, rot = 0;
      if (i > 0 && lt < TR) { const p = eio(lt / TR); tx = (1 - p) * CFG.width; rot = (1 - p) * 3; }
      if (!last && lt >= s._dur) { const p = eio((lt - s._dur) / TR); tx = -p * 420; op = 1 - p * 0.6; }
      if (last && lt > s._dur - 1.1) op = Math.max(0, 1 - (lt - (s._dur - 1.1)) / 1.1);
      s.style.opacity = op; s.style.transform = `translateX(${tx}px) rotate(${rot}deg)`; s.style.zIndex = i;
      if (s._cam) { const c = cam(s, lt); s._cam.style.transform = `translate(${c[2]}px,${c[3]}px) scale(${c[1]})`; }
      s._els.forEach((e) => applyEl(e, lt));
      s._kb.forEach((im) => { im.style.transform = `scale(${1.02 + 0.08 * cl(lt / s._dur)})`; });
    });
  };
  window.TOTAL = TOTAL;
  window.SCENES = scenes.map((s) => ({ start: s._start, dur: s._dur, vo: s._vo, voMissing: !!s._voMiss, mood: s.dataset.mood || null }));
  window.CUES = (function () {
    const c = [];
    scenes.forEach((s, i) => {
      if (i > 0) c.push({ t: s._start - 0.05, type: 'trans' });
      s.querySelectorAll('[data-sfx]').forEach((e) => { const ty = e.dataset.sfx; if (ty && ty !== 'none') c.push({ t: s._start + (+e.dataset.t || 0), type: ty }); });
    });
    return c.sort((a, b) => a.t - b.t);
  })();

  // ---- QA helpers ----
  function visibleOpacity(el, s) { let o = 1, p = el; while (p && p !== s) { const cs = getComputedStyle(p); o *= +cs.opacity; if (cs.display === 'none') return 0; p = p.parentElement; } return o; }
  window.AUDIT = function (step) {
    const bad = [], seen = {};
    for (let t = 0; t < TOTAL; t += step) {
      seek(t);
      scenes.forEach((s, i) => {
        const lt = t - s._start; if (lt < TR || lt > s._dur - 0.02 || s.style.display === 'none') return;
        s.querySelectorAll('.fix *, .cam *').forEach((el) => {
          if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) return;
          if (visibleOpacity(el, s) < 0.08) return;
          const r = el.getBoundingClientRect();
          if (r.left < -1 || r.right > CFG.width + 1 || r.top < -1 || r.bottom > CFG.safeBottom) {
            const k = i + '|' + el.textContent.trim().slice(0, 24);
            if (!seen[k]) { seen[k] = 1; bad.push({ kind: 'bounds', scene: i + 1, t: +lt.toFixed(2), txt: el.textContent.trim().slice(0, 40), l: Math.round(r.left), r: Math.round(r.right), top: Math.round(r.top), b: Math.round(r.bottom) }); }
          }
        });
      });
    }
    return bad;
  };
  // Density: share of a 18x30 grid (content area y 150..1790) hit by a visible photo/graphic/text element.
  window.DENSITY = function (step) {
    const out = []; const xs = 18, ys = 30;
    for (let t = 0; t < TOTAL; t += step) {
      seek(t);
      const s = scenes.find((sc) => t >= sc._start + TR && t < sc._start + sc._dur - 0.05); if (!s) continue;
      let hit = 0, tot = 0;
      for (let yi = 0; yi < ys; yi++) for (let xi = 0; xi < xs; xi++) {
        const x = 40 + (xi + 0.5) * (1000 / xs), y = 150 + (yi + 0.5) * (1640 / ys); tot++;
        const els = document.elementsFromPoint(x, y);
        const e = els.find((el) => el.closest('.scene') === s && !el.matches('.scene,.cam,.fix,.bgp,.bgd') && visibleOpacity(el, s) > 0.3);
        if (e) hit++;
      }
      out.push({ t: +t.toFixed(2), scene: scenes.indexOf(s) + 1, fill: +(hit / tot).toFixed(2) });
    }
    return out;
  };
  seek(0);
})();
