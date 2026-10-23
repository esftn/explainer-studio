# Cover design (v0.7.1): hand-made per topic, like episodes 1–5

A cover is the video's poster: it decides whether the Reel gets tapped. Design every cover by hand for its topic; never a frame from the video,
never a template. The model is **episodes 1–5**, which the creator liked. Later covers (clock face, speech bubbles, form card) and the v0.7 template
covers were rejected as generic, too contrasty or cheap. Finished covers are never redone.

## 1. What made covers 1–5 work (copy this, not the pictures)
| Ep | Background | Hero | Title |
|---|---|---|---|
| 01 | mustard paper, dot texture | note stack running out of frame next to a real building cutout and a tiny door (scale) | cream-on-ink lines, last line on a red block "কত উঁচু?" |
| 02 | full-bleed photo of dollar bricks (top) and taka notes (bottom), berry paper between | taped paper receipt "১০০ কোটি ডলার × রেট = ?" | mint block "১ বিলিয়ন ডলার", mint tag "টাকায় কত?" |
| 03 | vermilion, newsprint strip at the top | real soybean-oil bottle cutout + big green up-arrow "ডলার" + price tag | cream text, black-on-cream block "বাজারে কী হয়?" |
| 04 | risograph indigo, grain, halftone photo at the top, halftone fade at the bottom | drawn bazaar bag with hatched top (the shrinking part) | cream line + mustard block "কম কিনি কেন?", small note "একই ব্যাগ, একই বেতন… ?" |
| 05 | raw concrete texture | real key-handover photo in a frame + fanned calendar pages ending in "?" | navy + orange blocks "কত বছরের আয়?" |

The recipe:
- **Calm colours** from the episode palette (`docs/look.md`, rebuilt from these covers): paper/cream, one strong background, one accent. Never neon, never two loud colours fighting.
- **Real things:** a photo, a real product cutout, or a detailed drawn object (a stack of notes, a bag with hatching). Not flat clip-art icons.
- **Texture:** paper grain, dots, halftone, newsprint, concrete. A photo or texture may bleed from the top or bottom edge as part of the picture. **No separate flat bars.**
- **Title:** two lines, the question word on a solid block; cream/paper or the accent; soft shadow, not a heavy black outline.
- **One small hook note** (taped paper / tag) with the setup fact that makes the question irresistible.
- **One device that points at the mystery:** "?", an arrow, a scale comparison, a "= ?" on a receipt.

## 2. Hard rules (checked by `cover_check.py`)
- Title ≥ 140 px (aim 150–170), ≤ 7 words, ≤ 3 lines, inside y 440–1500 (profile-grid square). All text inside the 4:5 zone (y 285–1635); other text ≥ 44 px.
- ≤ 4 text elements (title counts as one). Contrast: title ≥ 3:1, small text ≥ 4.5:1.
- Hero (mark it `data-cv="hero"`) ≥ 25 % of the 4:5 zone (aim 35–50 %). Title block `data-cv="title"`, notes `data-cv="note"`, "?"/arrows `data-cv="mark"`.
- Colours only from the episode palette (soft tints of them are allowed).
- **No spoiler:** the cover asks, the video answers. A number the script says only in its second half FAILs; add other forbidden words to `project.json` → `"cover_spoilers"`. Titles must make sense alone (no vague "আশ্চর্য", "ভয়ংকর").

## 3. Process
1. Read the brief, the script's hook, `docs/look.md` and the last 3 rows of the series cover log (don't repeat their colour or idea).
2. Write two one-line concepts that differ in idea (hero · background · title), not just colour.
3. Build each as `cover_<name>.html` in the project (fonts: `<link rel="stylesheet" href="fonts/tiro-bangla/400.css">`; Tiro Bangla, thicken with `-webkit-text-stroke`, never faux bold). Real photos from `images/` (cut out with rembg when useful).
4. `python3 engine/tools/cover.py videoNN cover_<name>.html` → 9:16, 4:5 and a review sheet; then `python3 engine/tools/cover_check.py videoNN cover_<name>.html` must print `COVER PASS`.
5. **Look at the sheet** (thumbnail tile must still read; colours calm; nothing cheap-looking). Compare it side by side with covers 1–5 if unsure.
6. Send both sheets; creator picks. `finish.py … --cover <name>` puts the pick in `out/` and bakes it; the other goes to `drafts/`.
7. Add a cover-log row (palette, hero, title) to the series brief.

## 4. Fixed facts
1080×1920; Bangla digits; consistent spelling with the video; no fake logos, no other creators' faces, no AI banknotes or AI images of real landmarks;
real photos credited in the post. Remind the creator to pick the cover in Facebook's upload screen.
