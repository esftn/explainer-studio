# QA Checklist (run before preview and before final render)

Automated (`tools/audit.py` → writes `.qa_pass` only if all pass; `render.py` refuses without a fresh pass):
- [ ] **Bounds** — no visible text outside 0–1080 × 0–1795 at any 0.1 s step (transitions excluded)
- [ ] **Source band** — no content text overlapping the bottom band
- [ ] **Density** — no stretch > 1.5 s with < 55% of the content area occupied
- [ ] **Assets** — every `<img>` loads; no fallback fonts (document.fonts check)
- [ ] **Length** — total ≤ platform limit set in `project.json`
- [ ] **Licences** — every image used has a row in `licences.csv`; on a monetised project nothing is `commercial=no`
  or `?` (unknown → warning on non-monetised projects)
- [ ] **Beat mix** — no more than 3 COLLAGE (AI) beats in a row; mix printed by type

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

Gate 4: the creator's final check (in `out/publish.md`; tick before publishing):
- [ ] **Sound off:** watch the whole video muted on a phone. Every number and label is readable and the story still makes sense.
- [ ] **Screen off:** listen to `out/screen_off.m4a` only. The narration makes sense without the pictures.
- [ ] **Facts:** every on-screen name, date, number, map and quote matches the ledger.
- [ ] **Rights:** every asset has a source and licence; the music and SFX are original (synthesised by `audio.py`).
- [ ] **AI honesty:** AI visuals are illustration only; recreated documents are labelled; YouTube's altered/synthetic setting is ticked if any realistic AI visual is used.

Delivery:
- [ ] Frame count = round(total × 30)
- [ ] md5 of the copy on the creator's computer matches the render
- [ ] Cover, caption text, `.srt`, project zip delivered
- [ ] `publish.md`: 3 title options ≤ 60 characters, description with the source list, chapters (long form), thumbnail (16:9)
