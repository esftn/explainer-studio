# Changelog

## 0.8.0 — 2026-11-07
From the TakaTheoryBD channel review (24 Shorts, YouTube Studio data): viewers decide in the first 1–2 s, leave at 30–40 s whatever the
length, and swiped away during the 3 s silent end hold; dark covers and small framed photos underperformed.
- **Cover opening:** `bake_cover.py --hold` (default project.json `cover_hold` 1.6): the cover fills the first 1.6 s with a slow push-in and
  fades into scene 1 while the first VO line plays (still frame 1 + embedded thumbnail as before).
- **Ending 1 s:** `end_hold` 1.0 in new projects, `studio.py check` accepts 0.8–1.4 s; closing chord 2.4 s before the end, end fade 0.6 s;
  the last scene's visual fade-out is 0.25 s.
- **Series cover:** new `cover_series.py` (full-bleed photo, chip, white line, one bright question block, faces below the title, palette's
  two brightest colours, auto-shrinks the block to one line); ONE cover per episode (report and cards updated). `docs/cover-design.md` §0.
- **Hook + length:** script target 85–100 words (~40–45 s); `script_check.py` warns above 110 words and when scene 1 is longer than 16 words;
  scene 1 must be loud (big question + large photo).
- **Titles:** `publint.py` warns above 45 characters (the title shows over the Short in the feed).
- rules.json 0.8.0 (always-rules, plan/build/finish cards, cover report; duplicate build step 6 removed).

## 0.7.2 — 2026-10-24
Catches the repo up from 0.2.0 to the plugin in use (0.3–0.7.2 were installed as .plugin files only).
- 0.5–0.6: Facebook 4:5 zone, captions bn/en, publish.txt, guard/pack/finish transfer tools, facts gate.
- 0.7: studio.py (step cards, look/music rotation, objective checks, automatic status), 5 rotating music presets, automatic SFX, palette bank.
- 0.7.1: reading-time check and bigger minimum text in audit.py; data-say lands 0.25 s early (sayLead); cover_check.py (size, zones, palette, spoilers).
- 0.7.2: palettes rebuilt from episodes 1–5 (12 calm sets); cover template tool removed, covers hand-designed (docs/cover-design.md); no top/bottom bars.
- Dropped since 0.2 (removed in later plugin versions): 16:9 scene set, thumbnail.py, publish.py, docs/ai-visuals.md.
Details: docs/CHANGES-v0.7.md.

## 0.2.0 — 2026-10-21
Learnings from the "Vox / Johnny Harris-style videos with AI" research merged in.
- **Source ledger** replaces the fact sheet: central question + thesis, F-numbered facts with confidence,
  chronology, counterpoints, hook options, visual opportunities.
- **Gates** (ledger, script + beats + budget, final QA) hold even in "do it all" mode; the creator's materials
  are used or reported as unreadable.
- **Beat types** (PHOTO, MAP, CHART, DOCUMENT, TEXT, TIMELINE, COLLAGE) route each scene to the engine or to
  AI illustration; mix rules; `audit.py` prints the mix.
- **AI visuals guide** (`docs/ai-visuals.md`): illustration never evidence, no Bangla text in AI images, style
  block + closer, rules for real people and children, Flow template, credit budget.
- **Long-form**: 16:9 1920×1080 support across the engine and tools, `scenes16/` templates, chapter spine,
  chapters in the publish pack.
- **Licence ledger** (`licences.csv`): rows written by `prep_photos.py`, checked by `audit.py` (blocks
  non-commercial assets on monetised projects).
- **New tools**: `thumbnail.py` (1280×720, ≤ 2 text blocks of ≤ 3 words, 200 px preview) and `publish.py`
  (titles, description, sources, credits, chapters, disclosure, Gate 4 checklist, `screen_off.m4a`).
- **New scenes**: `document-clip` (labelled recreation) and `collage-parallax`; engine `data-twos` (stop-motion
  cadence) and `data-shake`.
- **Storytelling**: cold-open rule, why/so-what every 30 s, five ending patterns, creator note, the sound-off
  and screen-off test. Gemini TTS added as a free Bangla voice option.

## 0.1.0 — 2026-10-19
First release: plugin (5 skills), playbook docs, HTML-to-video engine with QA-gated render, VO timing,
synthesised music/SFX, delivery checks.
