---
name: video-preview
description: Build the animated explainer from an approved script and VO — assets, style frames, scenes, QA audit, contact-sheet review and a low-res preview. Use when the user asks to design, animate, lay out, preview, fix a scene, or when text is cut off, empty space, wrong font, or timing issues are reported.
---

# Assets → style frames → build → audit → review → preview

## Read
`../../docs/design-system.md`, `../../docs/qa-checklist.md`, and each scene template you use.

## 1. Assets
```bash
python3 engine/tools/prep_photos.py <project>            # img/p_XX.jpg + img/_sheet_N.jpg
python3 engine/tools/prep_photos.py <project> --cut p_03 # sticker cutout (needs rembg)
python3 engine/tools/font_test.py <project>              # then LOOK at out/font_test.png
```
Choose photos by looking at the contact sheets: hero = the most expressive/inspirational face, not the first file.

## 2. Style frames (gate)
Build only the hook scene, one infographic scene and the ending in `index.html`; `review.py --times`
three stills; send them. Approve the look before building the rest.

## 3. Build
- One `<section class="scene" data-vo="N">` per VO clip; durations come from VO automatically.
- Start from `engine/scenes/*.html`; keep coordinates inside x 56–1024, y 150–1790.
- Time highlights with `data-at="aK"` (VO pause anchors) so the mark lands on the spoken word.
- Photos go inside `.cam` (camera-moved); text automatically lands on the fixed layer.
- `data-mood` on the scene where the music should change (intro/build/drive/somber/elegy/answer/end).
- `data-sfx` only on visual hits; ≤1 impact per ~10 s.

## 4. Audit (hard gate) and review (your eyes)
```bash
python3 engine/tools/audit.py <project>     # must print QA PASS; fix every FAIL, treat density WARNs seriously
python3 engine/tools/review.py <project> --step 1.5
```
Read EVERY `out/review_N.jpg`. Check: text fully visible, nothing overlapping, no empty stretches, spelling
(Bangla conjuncts, digits), photo crops (no cut heads), source band present, ending clean. Fix → re-audit →
re-review the changed scenes (`review.py --scene N`).

## 5. Preview (gate)
```bash
python3 engine/tools/audio.py <project>
python3 engine/tools/render.py <project> --preview      # 540x960, 15 fps, with audio
```
Send `out/<name>_preview.mp4`. Ask the creator for timestamped notes ("0:42 text too fast").
