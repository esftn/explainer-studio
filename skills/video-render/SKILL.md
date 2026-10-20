---
name: video-render
description: Final audio master, full-resolution render, verification, captions, thumbnail, publish pack (titles, description, sources, chapters) and the final QA gate for an explainer video. Use when the preview is approved, or the user asks to render, export, finalize, make captions/SRT, a thumbnail, titles/description, or deliver/send/publish the video.
---

# Final render, publish pack and Gate 4

## Read
`../../docs/audio.md`, `../../docs/qa-checklist.md` (Gate 4 and delivery), `../../docs/platform-notes.md` (publishing rules).

## 1. Gate check
`audit.py` must have passed on the current timeline; the render refuses otherwise. Editing `licences.csv`
also needs a re-audit. If any scene changed since the preview, re-run `audit.py` and `review.py --scene N`
for those scenes first.

## 2. Audio
```bash
python3 engine/tools/audio.py <project>
```
Read `out/audio_report.txt` and confirm:
- master ≈ −14.5 LUFS
- true peak ≤ −1.5 dBTP
- no WARN about VO running past a scene

## 3. Render and verify
```bash
python3 engine/tools/render.py <project> --workers 2 --cover 1.5 --name <Slug>
python3 engine/tools/check_final.py <project>
python3 engine/tools/make_srt.py <project>
```
`check_final.py` must PASS on: the project's resolution (1080×1920 or 1920×1080), 30 fps, A/V length,
loudness, peak and the silent ending. To fix one scene later, use `render_range.py <project> --scene N`
(only if durations are unchanged).

## 4. Thumbnail and publish pack
```bash
python3 engine/tools/thumbnail.py <project>     # edit thumbnail.html first: hero subject, ≤ 2 text blocks of ≤ 3 words
python3 engine/tools/publish.py <project>       # out/publish.md + out/screen_off.m4a
```
- **Thumbnail:** look at `out/thumbnail_200.png`. If it can't be read in one second at feed size, fix it.
- **`publish.md`:** write in it:
  - 3 titles of ≤ 60 characters, using the hook's words
  - a hook line plus 2–3 lines of context, with no promise the video doesn't keep
  - 3–5 hashtags (Bangla and English)
  - one "next time" note
- **Check:** run `publish.py <project> --check` until it passes.
- **Chapters (16:9):** publish.py writes them from the scene tags. Fix any warning (YouTube needs ≥ 3, the
  first at 0:00, each ≥ 10 s).
- **AI assets:** the Disclosure section says whether to tick YouTube's altered/synthetic setting.

## 5. Delivery and Gate 4
- **Send** with SendUserFile:
  - `<Slug>_final.mp4`
  - `<Slug>_cover.png` (9:16) or `thumbnail.png` (16:9)
  - `captions.srt`
  - `publish.md`
  - `screen_off.m4a`
- **Files on the creator's computer:** through the bridge, files over ~25 MB must be split.
  1. Run `split_deliver.py <file>`.
  2. Commit the parts.
  3. Join them with `cat` on the device.
  4. Verify the md5.
- **Project zip:** zip the project (without `fonts/`, `node_modules` or `out/seg_*`) for future edits.
- **Gate 4:** ask the creator to tick the checklist in `publish.md` before publishing:
  - sound off (watch muted on a phone)
  - screen off (listen to `screen_off.m4a` only)
  - facts, rights and AI honesty

  You never publish.
- **Finish with:** what was delivered, its length, and one next step (e.g. the other aspect ratio, or a 4:5 feed cut).
