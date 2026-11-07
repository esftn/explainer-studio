# Changelog

## 0.10.0 — 2026-11-07  (efficiency release: ep 34–36 used ~90–100 tool calls each)
- **Mac shell only for Build + Finish:** `engine/tools/mac/es.sh` (→ `VIDEO GEN/_series/es.sh`) runs any tool on the episode folder
  itself with the local Chromium kit; `make_kit.sh` builds `engine_kit_v<ver>-<hash>.tar` for `_series/mac_render/`. No pull/push,
  pack parts, fingerprints or push guard. `sitecustomize.py` turns refused deletes in the Mac folder into moves to
  `_to_delete/_trash/`; render chunks/segments go to the VM's own scratch (`ES_SCRATCH`), not the Mac folder.
- **`finish.py --local`:** render (resumable: same command again on RESUME), check, cover (newest `_cover_*` in out/ or drafts/),
  bake, publish lint, state, tidy, tracker, titles_descriptions.md, lock release — one command, DONE or a clear STOP. A
  script/facts change after approval re-runs script_check instead of stopping.
- **`build_scenes.py` + `build.json`:** scenes come from a ~3 KB plan (blocks: text, blk, num, chip, note, card, tags, bars,
  share, chain, vs, strike, photo, grid, row, html) instead of 20–30 KB of hand-written HTML. Colours from docs/look.json with
  contrast-picked text, 10 band styles (warns if the previous episode used the same), say-word timing from vo.js, and early
  warnings for unknown say words, text landing too late to read, over-full scenes and unknown moods.
- **Cheat sheet** (`engine/studio/cheatsheet.md`) printed with the Build card; **`studio words videoNN`** lists the spoken words
  per clip, photos, theme rows and the previous bands. Skills cut to the card + rules (video-preview/video-render ~2 KB each;
  the old cloud technique moved to docs/legacy-cloud-*.md).
- **`vo_split`:** no clear scene pauses → writes the best-estimate cuts itself (BEST-ESTIMATE, exit 0); `--strict` = old stop.
- **One look per check:** `review.py --one` → `out/keys_one.jpg` (one frame per scene + every flagged moment).
- **Cover baked right away** (creator decision 7 Nov 2026): no cover-OK wait; the 'delivered' report names the baked cover.
  `cover_series` moves a too-wide question block's first words into the white line instead of failing.
- Fixes: `studio close` clears stage-waiting open notes; key-sheet labels render Bangla; Python 3.10 compatible (Mac shell).

## 0.9.2 — 2026-11-07
- **Finish runs in the Build chat:** after "go ahead" on the preview, Claude approves the preview, keeps the claim (re-claim with the
  same label, `--stage finish`) and goes straight on to cover → finish → deliver in the same chat. No more "open a new chat: Finish
  episode NN". Changed: build card step 8, finish card header, `preview` report, rules, video-preview §5, video-render §0,
  explainer-video flow, state.py next-step text, tracker rules line, PLAYBOOK. Plan still runs in its own chat.

## 0.9.1 — 2026-11-07
- **sync_engine.py (new):** brings every episode's own engine copy (`videoNN/engine/`: engine.js, engine.css, presets, scene templates)
  up to the plugin's template in one command (`sync_engine.py <series root> --apply`); replaced files go to `_to_delete/engine_before_<v>/`;
  delivered episodes skipped unless `--include-delivered`. `studio.py next` now prints ENGINE OUT OF DATE with the fix command.

## 0.9.0 — 2026-11-07
- **Deliverables cut to 9:16 only:** `finish.py` now makes the 9:16 reel, its 9:16 cover and `publish.txt` — no 4:5 feed cut, no 4:5 cover,
  no `captions.bn_IN.srt` / `captions.en_US.srt` and no English caption translation (7 steps instead of 9). `cover.py` writes only the 9:16
  PNG (the review sheet still previews the feed crop). Finals checks (studio, state_check, pack, tidy, series_tracker) require 3 files;
  the old 4:5/SRT files in earlier episodes stay allowed in out/, never required. The y 285–1635 text zone stays as the safe zone.
- **titles_doc.py (new):** copies an episode's publish.txt (title, alt, full description, YouTube + Facebook hashtags, pinned comment)
  into `titles_descriptions.md` in the series root, replacing that episode's section or inserting it in order; `finish.py --verify` runs it.

## 0.8.2 — 2026-11-07
- **words_import.py (new):** exact word timings from an ElevenLabs Speech to Text export (`docs/words.json`). Aligns the script to the
  transcript and writes `words_norm.json`, `words_script.json` (the script's own spelling with real times, for `burn_captions.py --words`)
  and `words_cuts.json`; prints the scene cuts for `vo_split.py --cuts` (`--apply` runs it). Scribe picks which pause is the boundary,
  ffmpeg silencedetect picks where: Scribe word ends run into pauses or stop early (video37: up to 1.3 s), so raw Scribe midpoints
  would cut speech. Tested on video37: 102 words, all 9 scenes placed, every cut inside a real pause of 0.45–0.92 s.

## 0.8.1 — 2026-11-07
- **render_resume.py:** full render in 10 s chunks, resumable across runs (for shells that stop a command after ~3 min, e.g. the Mac shell). Tested on the Mac shell (ARM64, Sparticuz Chromium via ES_CHROME): video33 59.5 s in 2 runs / ~157 s, check_final all PASS.
- **Palettes:** the 12-set bank rebuilt in an energetic Vox register (vox-yellow, electric-teal, tomato-red, money-lime, cobalt-pop,
  hot-pink, charcoal-orange, sky-lemon, saffron-grape, coral-lime, violet-lemon, jungle-gold); families unchanged so rotation works;
  all themes ≥ 4.6:1 text contrast. Episodes that already have docs/look.json keep it until `studio.py look --set/--family` is re-run.
- **burn_captions.py (new):** big Bangla captions burned into a copy of the video (`*_captioned.mp4`) on a dark box at y 1490
  (4:5 scaled), skipped during the cover opening; word-by-word highlight when exact word timings exist (`--words`, ElevenLabs
  Scribe format), SRT chunks otherwise. libass + HarfBuzz shape Bangla; the font is converted once from woff2 (fonttools).
- **Scene templates:** `opener-loud` (scene 1), `share-bar` (who-gets-what split), `chain-cards` (answer chain); caption-lane rule.
- **ES_CHROME** env var: use a given Chrome/Chromium binary (render/cover tools) where Playwright's own browser is unavailable.
- Skills/PLAYBOOK read `claude/series-rules.md` (short current rules) instead of the 85 KB brief; rules.json 0.8.1 (topic test,
  caption lane, templates).

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
