# QA Checklist (run before preview and before final render)

Automated (`tools/audit.py` → writes `.qa_pass` only if all pass; `render.py` refuses without a fresh pass):
- [ ] **Bounds** — no visible text outside 0–1080 × 0–1795 at any 0.1 s step (transitions excluded)
- [ ] **Source band** — no content text overlapping the bottom band
- [ ] **Density** — no stretch > 1.5 s with < 55% of the content area occupied
- [ ] **Assets** — every `<img>` loads; no fallback fonts (document.fonts check)
- [ ] **Length** — total ≤ platform limit set in `project.json`

Claude review (contact sheets every 1.5 s, `tools/review.py`):
- [ ] Hook visible and readable in the first frame-second
- [ ] Every scene has photo/graphic + key text + highlight
- [ ] Text never on a busy photo without a strip
- [ ] Highlights/marks match the spoken word (check anchors)
- [ ] Spelling/consistency pass (names, places, digits, ঢাকা-৮ style hyphens)
- [ ] Sensitive-topic balance & sources present on every factual scene

Audio (`tools/audio.py` prints these):
- [ ] −14 ±0.5 LUFS, ≤ −1.5 dBTP, limiter touching < 2% of samples
- [ ] VO clearly above music; no SFX on key words; silent last 0.25 s

Delivery:
- [ ] Frame count = round(total × 30)
- [ ] md5 of the copy on the creator's computer matches the render
- [ ] Cover, caption text, `.srt`, project zip delivered
