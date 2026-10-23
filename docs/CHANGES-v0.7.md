# Explainer Studio v0.7 — what changed and why

Creator request (24 Oct 2026): same steps in every chat, brief reports, Vox / Johnny Harris looks with matching palettes, sound effects with the
animation, 3–5 rotating background musics, and automatic status tracking — to make 6–9 videos in one sitting.

## Root causes found
1. **Same music on every episode.** `new_project.py` copied the same `audio_config.json` (palette bangla, seed 7, same moods) into every project.
2. **No sound effects.** Effects only played from hand-written `data-sfx` attributes; the build skill never mentioned them or `data-mood`, so generated scenes had none
   (only scene-change whooshes at −27 LUFS).
3. **No palette source.** Each episode invented its colours, which led to repeats (three tangerine covers) and low-contrast pairs.
4. **Rules lived in five skills + an 82 KB brief + project memory**, so each chat followed a different mix. The brief was loaded at the start of every chat.
5. **Status was typed by hand** (tracker/state drift, issues #6 and #8).

## Changes
- `engine/tools/studio.py` (new, python-only, also copied to `.studio/` and meant for `_series/tools/`): `next new look music check status close`.
- `engine/studio/rules.json`: the creator's rules, the 3 step cards (plan, build, finish) and the report templates — single source of truth.
- `engine/studio/music_bank.json`: 5 presets (3 Bangla-instrument, 2 cinematic) rotated by episode; `audio.py` gained configurable chord set (`prog` dm|am|cmaj),
  pattern, kick moods and closing chord for the cinematic engine.
- Automatic SFX: `engine.js` proposes a cue per animation (`auto:true`); `audio.py` thins them (≤3 per scene, per-type caps, ≥0.6 s apart, 80 % gain). `autoSfx:false` in project.json disables them (and `studio.py check` then fails).
- `engine/studio/palettes.json` (+ `build_palettes.py`): 14 Vox / Johnny Harris palettes with pre-validated scene themes (text ≥ 4.5:1), motif, rotation that skips the colour families of the previous three episodes.
- `state.py`: new stage `folders-ready` (after the script is approved and the folders are prepared).
- Skills: `explainer-video` is now a 55-line conductor; the four stage skills point to the step card, drop the brief gate and the separate style-frame gate, and add look/sound/check steps.
- No brief gate when only a title is given; one message for VO text + image list; style frames and preview approved together.

## After installing
1. Copy `engine/tools/studio.py` and `engine/studio/rules.json` into `VIDEO GEN/_series/tools/` (with the other seven tool files if they changed).
2. Run `python3 _series/tools/studio.py status --write` once: it creates `_series/STATUS.md` for episodes 1–24.
3. Existing projects (ep 22–24 …) keep their own copy of `engine.js` and `audio_config.json`; apply `studio.py music videoNN --again` only to episodes that have not been built yet.

## Update 24 Oct 2026 — covers and on-screen text
- **Covers:** `cover_make.py` builds Vox-style covers from `engine/studio/cover/cover-kit.css` (4 layouts, 10 vector objects, episode palette); `cover_check.py` FAILs title < 140 px, > 7 words, text outside the 4:5 zone / title outside y 440–1500, text < 44 px, > 4 text elements, contrast, hero < 25 % of the zone, > 2 off-palette colours, and **spoilers** (a number said only in the second half of the script). `docs/cover-design.md` rewritten.
- **In-video text:** `audit.py` FAILs text under 30 px (WARN < 40 for running text) and text that is on screen too short to read (0.6 s + 0.33 s per word, numbers/labels ≥ 1.2 s). `data-say` now lands 0.25 s *before* the spoken word in new projects (`sayLead` in project.json); earlier is fine, late is not.
- Existing projects keep their old engine.js; copy the new one only into episodes not yet built.

## v0.7.1 (24 Oct 2026) — creator review
- The cover template tool (`cover_make.py`, cover kit, clip-art vectors) was **removed**: its covers looked generic and too contrasty. Covers are designed by hand per topic like episodes 1–5 (`docs/cover-design.md` rewritten with what made those work). `cover_check.py` stays as the gate (size, zone, contrast, palette, spoilers).
- The palette bank was **rebuilt from the colours of episodes 1–5** (12 calm palettes: mustard paper, teal map, vermilion kraft, money green, risograph indigo, berry mint, concrete orange, blueprint sky, kraft stamp, coral sand, plum paper, forest gold). Episodes already started keep their docs/look.json; run `studio.py look videoNN --again` only for episodes not yet built.
- No top/bottom bars in covers or videos: one full-bleed background (colour, texture or photo).
