---
name: video-preview
description: Build the animated explainer from an approved script and VO — assets, licences, style frames, scenes (9:16 or 16:9), QA audit, contact-sheet review and a low-res preview. Use when the user asks to design, animate, lay out, preview, fix a scene, add AI/collage visuals, or when text is cut off, empty space, wrong font, or timing issues are reported.
---

# Assets → style frames → build → audit → review → preview

## Read
`../../docs/design-system.md`, `../../docs/ai-visuals.md` (for any COLLAGE beat), `../../docs/qa-checklist.md`,
and each scene template you use.

## 1. Assets and licences
```bash
python3 engine/tools/prep_photos.py <project>            # img/p_XX.jpg + img/_sheet_N.jpg + licences.csv rows ("?")
python3 engine/tools/prep_photos.py <project> --cut p_03 # sticker cutout / parallax layer (needs rembg)
python3 engine/tools/font_test.py <project>              # then LOOK at out/font_test.png
```
- **Choose photos by looking at the contact sheets.** The hero is the most expressive or inspirational face,
  not the first file.
- **Fill `licences.csv`** for every image you will use: `source, licence, commercial (yes/no), ai (yes/no)`.
  A cutout inherits its photo's row; any other new file (hero.jpg, collage layers) needs its own row.
  Non-commercial sources (Google Earth Studio, CapCut free assets, unclear web images) are `commercial=no`.

## 2. Style frames (gate)
Build only three scenes in `index.html`: the hook, one infographic scene and the ending. Run
`review.py --times` to get three stills and send them. The look must be approved before you build the rest.

## 3. Build
- **One section per clip:** `<section class="scene" data-vo="N" data-type="…">` per VO clip. Durations come
  from the VO automatically.
- **Start from templates:** `engine/scenes/*.html` (the project's copy, 9:16 or 16:9). Keep coordinates in the
  safe area: 9:16 x 56–1024, y 150–1790; 16:9 x 64–1856, y 60–1020.
- **Beat types:**
  - MAP: `map-pin`, with open-data outlines.
  - CHART: `big-number`, `comparison-bar`, `icon-grid`, `tick-timeline`.
  - DOCUMENT: `document-clip`, labelled পুনর্নির্মিত, quoting the real wording.
  - TEXT: `hook-quote`.
  - TIMELINE: `timeline-vertical`, `calendar-clock`.
  - PHOTO: `photo-collage`, `split-portrait`, `ending-mural`.
  - COLLAGE: `collage-parallax`, with layers entering back to front, `data-twos="12"` and `data-shake="2"`.
    Use a Flow clip only for 1–3 hero beats.
- **Timing:** time highlights with `data-at="aK"` (VO pause anchors) so the mark lands on the spoken word.
- **Layers:** photos go inside `.cam` (moved by the camera); text automatically lands on the fixed layer.
- **Music:** put `data-mood` on the scene where the music should change (intro/build/drive/somber/elegy/answer/end).
- **SFX:** use `data-sfx` only on visual hits, with at most 1 impact per ~10 s.

## 4. Audit (hard gate) and review (your eyes)
```bash
python3 engine/tools/audit.py <project>     # must print QA PASS; fix every FAIL, treat density/licence WARNs seriously
python3 engine/tools/review.py <project> --step 1.5
```
The audit also prints the beat mix and fails on missing licence rows. On monetised projects it also fails on
any image that isn't `commercial=yes`.

Read EVERY `out/review_N.jpg` and check:
- text fully visible, with nothing overlapping
- no empty stretches
- spelling (Bangla conjuncts, digits)
- photo crops (no cut-off heads)
- source band present
- the ending is clean
- **sound-off readability:** every number and label readable at phone size

Fix → re-audit → re-review the changed scenes (`review.py --scene N`).

## 5. Preview (gate)
```bash
python3 engine/tools/audio.py <project>
python3 engine/tools/render.py <project> --preview      # half size, 15 fps, with audio
```
Send `out/<name>_preview.mp4` and ask the creator for timestamped notes ("0:42 text too fast").
