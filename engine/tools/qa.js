/* Explainer Studio QA probes — injected by audit.py / review.py after the page loads (works on older projects too).
 * QA_TARGETS()        every text-bearing element with its settle time, line boxes, colour and size
 * QA_COLLIDE(step)    text over text, text covered by a graphic, text straddling a graphic's edge
 * QA_KEYS()           key number elements (count/stamp/slam) not tied to a spoken word, data-say beyond scene end
 * Opt-outs: data-qa="ok" on an element (or ancestor) skips layout checks for it; data-zone="band" allows text
 * outside the 4:5 feed zone. */
(function () {
  const SC = [...document.querySelectorAll('.scene')];
  const TR = (window.PROJECT && window.PROJECT.transition) || 0.45;
  const st = document.createElement('style'); st.textContent = '*{pointer-events:auto!important}'; document.head.appendChild(st);
  let uid = 0;
  const id = (e) => e.dataset.qaId || (e.dataset.qaId = 'q' + (++uid));
  const ok = (e) => !!e.closest('[data-qa="ok"]');
  const hasText = (e) => !['STYLE', 'SCRIPT'].includes(e.tagName) && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
  function op(el, s) { let o = 1, p = el; while (p && p !== s) { const cs = getComputedStyle(p); if (cs.display === 'none' || cs.visibility === 'hidden') return 0; o *= +cs.opacity; p = p.parentElement; } return o; }
  function lines(e) {
    const out = [];
    [...e.childNodes].forEach((n) => {
      if (n.nodeType !== 3 || !n.textContent.trim()) return;
      const r = document.createRange(); r.selectNodeContents(n);
      [...r.getClientRects()].forEach((b) => { if (b.width > 2 && b.height > 2) out.push({ l: b.left, t: b.top, r: b.right, b: b.bottom }); });
    });
    return out;
  }
  // when has this element (and every animated ancestor) finished entering? local scene time
  function settle(e, s) {
    let t = TR + 0.05, out = Infinity, p = e;
    while (p && p !== s) {
      if (p.dataset && p.dataset.a) t = Math.max(t, (+p.dataset.t || 0) + (+(p.dataset.d || 0.7)) + 0.15);
      if (p.dataset && p.dataset.out) out = Math.min(out, +p.dataset.out);
      p = p.parentElement;
    }
    if (out < Infinity && t > out - 0.1) t = Math.max(TR + 0.05, out - 0.15);
    return Math.min(t, s._dur - 0.05);
  }
  // v0.7: when does an element start and stop being visible? (local scene time; reading time = end - start)
  function win(e, s) {
    let start = 0, end = s._dur, p = e;
    while (p && p !== s) {
      if (p.dataset && p.dataset.a) start = Math.max(start, +p.dataset.t || 0);
      if (p.dataset && p.dataset.out) end = Math.min(end, +p.dataset.out);
      p = p.parentElement;
    }
    return [start, end];
  }
  const textEls = (s) => [...s.querySelectorAll('*')].filter(hasText);

  window.QA_TARGETS = function () {
    const out = [];
    SC.forEach((s, i) => {
      textEls(s).forEach((e) => {
        const lt = settle(e, s); seek(s._start + lt);
        const o = op(e, s); if (o < 0.3) return;
        const cs = getComputedStyle(e), L = lines(e); if (!L.length) return;
        out.push({
          id: id(e), scene: i + 1, t: +(s._start + lt).toFixed(3), lt: +lt.toFixed(2), txt: e.textContent.trim().slice(0, 40),
          lines: L.map((b) => [Math.round(b.l), Math.round(b.t), Math.round(b.r), Math.round(b.b)]),
          color: cs.color, opacity: +o.toFixed(3), size: parseFloat(cs.fontSize),
          stroke: parseFloat(cs.webkitTextStrokeWidth || 0) >= 2 && cs.webkitTextStrokeColor !== cs.color ? cs.webkitTextStrokeColor : null,
          shadow: cs.textShadow && cs.textShadow !== 'none',
          src: !!e.closest('.src,.srcpill'), band: !!e.closest('[data-zone="band"]'), skip: ok(e),
          count: e.dataset.a === 'count' ? (e.dataset.to || null) : null,
          start: +win(e, s)[0].toFixed(2), end: +win(e, s)[1].toFixed(2), words: e.textContent.trim().split(/\s+/).filter(Boolean).length,
        });
      });
    });
    return out;
  };

  function paints(g) {
    if (['svg', 'IMG', 'CANVAS', 'img', 'canvas', 'VIDEO'].includes(g.tagName)) return true;
    const cs = getComputedStyle(g);
    const a = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return 0; const v = m[1].split(',').map(Number); return v.length > 3 ? v[3] : 1; };
    if (a(cs.backgroundColor) > 0.15 || cs.backgroundImage !== 'none') return true;
    if (parseFloat(cs.borderTopWidth) + parseFloat(cs.borderLeftWidth) > 1 && a(cs.borderTopColor) > 0.3) return true;
    return false;
  }
  const inter = (a, b) => ({ l: Math.max(a.l, b.l), t: Math.max(a.t, b.t), r: Math.min(a.r, b.r), b: Math.min(a.b, b.b) });
  const area = (x) => Math.max(0, x.r - x.l) * Math.max(0, x.b - x.t);

  window.QA_COLLIDE = function (step) {
    const res = [], seen = {}, FR = 1080 * 1920;
    SC.forEach((s, i) => {
      const T = []; for (let lt = TR + 0.05; lt < s._dur - 0.05; lt += step) T.push(lt);
      const texts = textEls(s);
      texts.forEach((e) => T.push(settle(e, s)));
      T.sort((a, b) => a - b);
      T.forEach((lt) => {
        seek(s._start + lt);
        const tv = texts.filter((e) => !ok(e) && op(e, s) > 0.5).map((e) => ({ e, L: lines(e) })).filter((x) => x.L.length);
        // text over text
        for (let a = 0; a < tv.length; a++) for (let b = a + 1; b < tv.length; b++) {
          if (tv[a].e.contains(tv[b].e) || tv[b].e.contains(tv[a].e)) continue;
          for (const la of tv[a].L) for (const lb of tv[b].L) {
            const x = inter(la, lb);
            if (x.r - x.l > 6 && x.b - x.t > 6) {
              const k = 'tt' + id(tv[a].e) + id(tv[b].e);
              if (!seen[k]) { seen[k] = 1; res.push({ kind: 'text-over-text', level: 'FAIL', scene: i + 1, t: +(s._start + lt).toFixed(2), a: tv[a].e.textContent.trim().slice(0, 30), b: tv[b].e.textContent.trim().slice(0, 30), box: [x.l, x.t, x.r, x.b].map(Math.round) }); }
            }
          }
        }
        // text vs graphics
        const gs = [...s.querySelectorAll('*')].filter((g) => !hasText(g) && !ok(g) && !g.closest('svg:not(:scope)') && paints(g) && op(g, s) > 0.4)
          .map((g) => ({ g, b: g.getBoundingClientRect() })).filter((x) => { const A = x.b.width * x.b.height; return A > 400 && A < 0.4 * FR; });
        tv.forEach(({ e, L }) => {
          gs.forEach(({ g, b }) => {
            if (g.contains(e) || e.contains(g)) return;
            const gb = { l: b.left, t: b.top, r: b.right, b: b.bottom };
            L.forEach((ln) => {
              const x = inter(ln, gb), A = area(x), LA = area(ln); if (A < 30 || LA === 0) return;
              // covered? sample the overlap: is the graphic painted on top of the text?
              let cov = 0, n = 0;
              for (let u = 1; u <= 3; u++) for (let v = 1; v <= 3; v++) {
                const px = x.l + (x.r - x.l) * u / 4, py = x.t + (x.b - x.t) * v / 4; n++;
                const top = document.elementsFromPoint(px, py).find((q) => q.closest('.scene') === s && op(q, s) > 0.2);
                if (top && (top === g || g.contains(top)) && !e.contains(top)) cov++;
              }
              const k = id(e) + '|' + id(g);
              if (cov >= 3) {
                if (!seen['c' + k]) { seen['c' + k] = 1; res.push({ kind: 'text-covered', level: 'FAIL', scene: i + 1, t: +(s._start + lt).toFixed(2), a: e.textContent.trim().slice(0, 30), b: g.tagName.toLowerCase() + (g.className && typeof g.className === 'string' ? '.' + g.className.split(' ')[0] : ''), box: [x.l, x.t, x.r, x.b].map(Math.round) }); }
              } else if (A / LA > 0.06 && A / LA < 0.9) {
                if (!seen['s' + k]) { seen['s' + k] = 1; res.push({ kind: 'text-touches-graphic', level: 'WARN', scene: i + 1, t: +(s._start + lt).toFixed(2), a: e.textContent.trim().slice(0, 30), b: g.tagName.toLowerCase() + (g.className && typeof g.className === 'string' ? '.' + g.className.split(' ')[0] : ''), box: [x.l, x.t, x.r, x.b].map(Math.round) }); }
              }
            });
          });
        });
      });
    });
    return res;
  };

  window.QA_KEYS = function () {
    const out = [];
    SC.forEach((s, i) => {
      s.querySelectorAll('[data-a="count"],[data-a="stamp"],[data-a="slam"]').forEach((e) => {
        if (ok(e)) return;
        if (!e.dataset.say && !e.dataset.at) out.push({ kind: 'untimed', scene: i + 1, txt: (e.textContent || '').trim().slice(0, 30) || e.dataset.to || e.dataset.a });
      });
      s.querySelectorAll('[data-say-t]').forEach((e) => {
        if (+e.dataset.sayT > s._dur - 0.3) out.push({ kind: 'say-late', scene: i + 1, txt: e.dataset.say });
      });
    });
    return out;
  };
})();
