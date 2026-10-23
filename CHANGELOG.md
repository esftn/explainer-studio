# Changelog

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
