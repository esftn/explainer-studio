---
name: video-render
description: Final audio master, full-resolution render, verification, captions, cover and delivery package for an explainer video. Use when the preview is approved, or the user asks to render, export, finalize, make captions/SRT, or deliver/send the video.
---

# Render → captions → cover → bake → deliver  (Chat 3 · Finish; 1–3 episodes per chat)

> **v0.7:** the order of work is the step card printed by `python3 engine/tools/studio.py next videoNN` (it wins over anything below that conflicts). This file is the technique reference for your current step; do not read it start to finish.

## 0. Start lean
Series brief (cover log!) + the generated tracker + `../../docs/audio.md`, `../../docs/cover-design.md`, `../../docs/platform-notes.md`.
**Claim the episode first** (`python3 _series/tools/guard.py claim videoNN --who "Finish epNN …"` on the Mac — REFUSED = stop; then `guard.py fingerprint videoNN --out videoNN/_to_delete/mac_fp.json` right before pushing). Pull each episode in one verified step
(see video-preview §0). `state.py videoNN show` must say `preview-approved`.

**v0.6: render/check (§1), bake (§3) and delivery (§4) are ONE command, `finish.py`.** Your own work in this chat is only the creative part:
the English caption lines (§2), `publish.txt` (§2) and the cover concepts (§3). Then:
```bash
python3 engine/tools/finish.py videoNN --slug <Slug> --cover <A|B|…> --guard mac_fp.json --who "Finish epNN <date time>" --out xfer
```
It runs, in order, and stops at the first thing a person must fix: preflight (stage, approved script hash, captions_en, publish.txt) →
render (if missing) → check_final + automatic A/V-length fix → 4:5 feed cut → covers → bake (skipped if frame 1 already is the cover) →
captions pair validation (equal cue counts, none past the end, overlaps clamped) → **publish.txt lint (no placeholder may remain)** →
state + tidy + `docs/delivery.md` (written from measurements) → guarded pack + the exact commit plan. Print the last lines to the creator only if it STOPs.

## 1. Gate check + render  (finish.py does this; the commands are for a manual re-run only)
`audit.py` full PASS on the current timeline (render refuses otherwise). Then:
```bash
python3 engine/tools/audio.py videoNN            # read out/audio_report.txt: ≈ −14.5 LUFS, ≤ −1.5 dBTP
python3 engine/tools/render.py videoNN --workers 2 --name <Slug>
python3 engine/tools/check_final.py videoNN      # must PASS
```
Rename/cut to the delivery names: `out/<Slug>_reel_9x16.mp4` and the 4:5 feed cut `out/<Slug>_feed_4x5.mp4`
(crop the 4:5 zone y 285–1635 → 1080×1350). Run `check_final.py videoNN --file out/<Slug>_feed_4x5.mp4` too.

## 2. Captions + publish text
Captions (Facebook only accepts `<name>.<lang>_<COUNTRY>.srt`; Bangla has no Bangladesh variant, so `bn_IN`):
```bash
python3 engine/tools/make_srt.py videoNN   # writes out/captions.bn_IN.srt + docs/captions_bn_cues.json
# translate docs/captions_bn_cues.json line by line → docs/captions_en.json (same length/order; natural short
# English, ≤2 lines per cue; every number/term checked against facts.json), then run make_srt.py again:
python3 engine/tools/make_srt.py videoNN   # also writes out/captions.en_US.srt with the same timings
```
`out/publish.txt` (replaces post_caption.txt; template `../../templates/publish.md`) for Facebook + YouTube:
- Title: Bangla, ≤70 chars, curiosity hook/question, plus one alternative.
- Description: a story, not a recap — hook, why it matters to an ordinary Bangladeshi viewer, a nudge to watch,
  a new comment question (not the video's), follow/subscribe line, sources as names. **No figures, no answer,
  no lines copied from the script.** YouTube: search words in the first 2 lines. Facebook: hook in line 1.
- Hashtags: 3 for YouTube, 5–8 for Facebook (Bangla + English topic tags, one series tag, nothing spammy).
- Pinned comment: the answer/data recap lives here. Photo credits line if real photos were used.
Re-read the description once against the script: any number or answer found there is removed.

## 3. Cover (designed per video)
**v0.7.1:** design each cover by hand as `cover_<name>.html` (cover-design.md), render with `cover.py`, then `python3 engine/tools/cover_check.py videoNN cover_<name>.html` must print `COVER PASS`; LOOK at the sheet before sending.

Follow `cover-design.md`: the episode's own palette (`docs/look.md`) — and different from the last three covers (cover log, grep that section only), one hero element, question title, quick
trend check, 2 concepts → `cover.py` review sheets → creator picks. Save `out/cover_reel_9x16.png` +
`out/cover_feed_4x5.png`; other concepts to `drafts/`. After confirmation `finish.py … --cover <NAME>` copies the chosen
`out/_cover_<NAME>_9x16.png/_4x5.png` into place, bakes both videos (once — it checks frame 1 first) and records `approve cover`.

## 4. Deliver (what finish.py prints at the end)
1. Commit the listed parts + manifest to `videoNN/_to_delete/` exactly as the COMMIT PLAN says (one call per batch). **After each commit
   call, check the file really arrived on the Mac** (the unpack in the next step does it: any missing part = FAIL).
2. On the Mac, from the VIDEO GEN folder: `python3 _series/tools/pack.py unpack videoNN/_to_delete --name finalNN --into videoNN` → must print VERIFIED.
3. On the Mac: `python3 _series/tools/finish.py videoNN --verify --who "Finish epNN …"` → must print `DONE` (layout, 7 finals, first frame = cover,
   captions pair, publish.txt clean, state.json consistent, folders tidied, `_series/episode-tracker.md` regenerated, lock released).
   Anything else: fix and repeat; do NOT tell the creator it is delivered.
3b. `python3 engine/tools/studio.py check videoNN --stage final` must print STUDIO PASS (finals only in out/, all 7 present, no placeholder).
3c. On the Mac, last command: `python3 _series/tools/studio.py close videoNN delivered --note "<single-source caveat>"` — writes state, `_series/STATUS.md` and regenerates the tracker. No hand-typed tracker or status.
4. Send the reel with SendUserFile. Remind the creator to set the cover in Facebook's upload screen and to empty `_to_delete/`.
5. Brief: append to `series-brief.md` (episode line, cover-log row, new shared figures, lessons) — or, if another chat owns the brief,
   `python3 _series/tools/series_tracker.py --note "epNN delivered: …"` and leave `docs/delivery.md` as the source.

Final message to the creator: what was delivered, the length, the folder, the cover letter, the single-source caveats (from
`docs/delivery.md`), and one next step. Nothing else.
