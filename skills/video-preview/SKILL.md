---
name: video-preview
description: Build the animated explainer from an approved script and VO — split the take, assets, style frames, scenes, QA audit, key-moment review and a low-res preview. Use when the user asks to build, design, animate, lay out, preview, fix a scene, or when text is cut off, empty space, wrong font, or timing issues are reported.
---

# Pull → split VO → style frames → build → audit → key moments → preview  (Chat 2 · Build)

> **v0.7:** the order of work is the step card printed by `python3 engine/tools/studio.py next videoNN` (it wins over anything below that conflicts). This file is the technique reference for your current step; do not read it start to finish.

## 0. Start the chat lean
1. Series brief + `../../docs/design-system.md`, `../../docs/qa-checklist.md` (not old chats).
2. Pull the episode in ONE step: on the Mac `python3 .studio/pack.py pack . --set project --out _to_delete
   --name pullNN` (device_bash in videoNN), stage the parts + manifest, then in the cloud
   `pack.py unpack <dir> --name pullNN --into videoNN` → VERIFIED (it also saves the push-guard base). `state.py videoNN show`.
   **Before the pull**, on the Mac (VIDEO GEN folder): `python3 _series/tools/guard.py claim videoNN --who "Build epNN <date time>"` — REFUSED means another chat holds the
   episode: stop and tell the creator. **Before every push**: `python3 _series/tools/guard.py fingerprint videoNN --out videoNN/_to_delete/mac_fp.json` on the Mac, stage it, then
   `pack.py pack … --guard mac_fp.json --who "Build epNN …"` (refuses if the Mac copy changed). Release at the end of the chat: `python3 _series/tools/guard.py release videoNN --who "…"`.
3. `vo_split.py` + `vo_prep.py` (see video-script §5). `state.py videoNN stage vo-received`.

## 1. Assets
`prep_photos.py` (contact sheets of the creator's `images/`), cutouts with rembg `isnet-general-use` for
objects. Check photos for garbled AI text/labels; relabel if needed. Real photo of the key subject > icon.

## 2. Look (assigned) + style frames (no separate gate)
`python3 engine/tools/studio.py look videoNN` prints this episode's Vox / Johnny Harris palette, 4–6 contrast-checked scene themes and a motif
(also in `docs/look.md`). Use ONLY those colours; one theme per scene, 3–4 colours per scene. Own style elements and own top/bottom bands: never
reuse an earlier episode's objects (series-brief cover log, grep only that section). Build the hook, one infographic scene and the ending, look at
`review.py --times` stills yourself, and send only the finished preview (style frames and preview are approved together). `state.py videoNN approve style` when the preview goes out.

## 3. Build
- One `<section class="scene" data-vo="N">` per VO clip; durations come from the VO.
- **`data-mood` on every scene** (first `intro`, last `end`, in between `build|drive|somber|elegy|answer`): it moves the music. **Sound effects are automatic** from the animations (slam→impact, stamp→stamp, pop→pop, count→tick, bars→whoosh, photos→paper, scene changes→trans); add `data-sfx="bell|tone|…"` only for a special hit, `data-sfx="none"` only to silence one element. Never edit `audio_config.json`; the music preset was assigned by `studio.py music`.
- **Tie every key graphic to the spoken word:** `data-say="সাতশো"` (several words = phrase; `#2` = second
  time it is said; `+0.1` = nudge). Use `data-at`/`data-t` only for things not tied to a word.
- 4:5 feed zone: all text inside y 285–1635 (audit FAILs outside; `data-zone="band"` only for deliberate
  band text); bleed fills the top/bottom bands. Source line plain text in the bottom band.
- Last scene `data-dur="<vo + 3>"` (ending hold). Grid children must not carry class "a" (only data-a).
- `data-qa="ok"` only for a deliberate overlap (e.g. a label meant to sit across a card edge) — say why in an
  HTML comment.

## 4. Audit (hard gate) → key-moment sheet (your eyes; the creator sees it only on request)
```bash
python3 engine/tools/audit.py videoNN --fast    # while iterating
python3 engine/tools/audit.py videoNN           # full: must print QA PASS
python3 engine/tools/review.py videoNN --keys   # out/keys_N.jpg
python3 engine/tools/audio.py videoNN           # then:
python3 engine/tools/studio.py check videoNN --stage build   # must print STUDIO PASS (palette, music, sound effects, moods, ending)
```
Fix every FAIL. For every WARN, look at its frame on the key-moment sheet (red box) and either fix it or
decide it is intended. Read each keys sheet: the highlighted word under each frame must be the word the
graphic belongs to. Look at full contact sheets (`review.py --scene N`) only for scenes you changed a lot.

## 5. Preview (gate)
```bash
python3 engine/tools/render.py videoNN --preview --name <Slug>   # then mv out/<Slug>_preview.mp4 drafts/
```
Send the preview (and the keys sheet only if the creator asked for it; Claude still reads it itself). Style frames and preview may be approved together. Push to the Mac in one step (`pack.py pack videoNN --set
preview` → `_to_delete/` → unpack VERIFIED), also push `--set project --no-images` so the Mac has the build.
`state.py videoNN stage built`. Ask for timestamped notes. Fixes → re-audit → re-preview only changed scenes
(`render_range.py` when durations are unchanged). On approval: `state.py videoNN approve preview` and tell the
creator to start Chat 3 ("Finish episode NN").
