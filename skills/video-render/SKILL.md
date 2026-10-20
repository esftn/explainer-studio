---
name: video-render
description: Final audio master, full-resolution render, verification, captions, cover and delivery package for an explainer video. Use when the preview is approved, or the user asks to render, export, finalize, make captions/SRT, or deliver/send the video.
---

# Final render and delivery

## Read
`../../docs/audio.md`, `../../docs/qa-checklist.md` (delivery), `../../docs/platform-notes.md`.

## 1. Gate check
`audit.py` must have passed on the current timeline (render refuses otherwise). If any scene changed
since the preview, re-run `audit.py` and `review.py --scene N` for those scenes first.

## 2. Audio
```bash
python3 engine/tools/audio.py <project>
```
Read `out/audio_report.txt`: master ≈ −14.5 LUFS, true peak ≤ −1.5 dBTP, no WARN about VO running past a scene.

## 3. Render + verify
```bash
python3 engine/tools/render.py <project> --workers 2 --cover 1.5 --name <Slug>
python3 engine/tools/check_final.py <project>
python3 engine/tools/make_srt.py <project>
```
`check_final.py` must PASS (1080×1920, 30 fps, A/V length, loudness, peak, silent ending). Fixing one scene
later: `render_range.py <project> --scene N` (only if durations are unchanged).

## 4. Delivery package
- `<Slug>_final.mp4`, `<Slug>_cover.png`, `captions.srt`, `caption.txt` (post text: hook line, 2–3 lines of
  context, sources, 3–5 hashtags in Bangla + English; no clickbait the video doesn't deliver).
- Send with SendUserFile. To write to the creator's computer through the bridge, files over ~25 MB must be
  split: `split_deliver.py <file>` → commit parts → join with `cat` on the device → verify md5.
- Zip the project (without `node_modules`, `out/seg_*`) for future edits.
- Finish with: what was delivered, the length, and one next step (e.g. a 4:5 feed cut).
