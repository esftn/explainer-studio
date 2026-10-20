# Design System (style-independent rules + engine conventions)

## 1. Canvas & layers
- **9:16** 1080×1920 (Reels, Shorts, TikTok) or **16:9** 1920×1080 (YouTube long-form), 30 fps. Set with
  `new_project.py --aspect 16:9`; for both, make two projects that share `vo/` and `photos/`.
  Each `<section class="scene">` has:
  1. `.bgp`/`.bgd` texture background (paper / dark)
  2. `.cam` — **camera layer**: photos, cutouts, full-bleed images, decorative shapes (`data-layer="cam"`). Camera keyframes (`data-cam="t:scale:x:y|..."`) move only this layer.
  3. `.fix` — **text/graphics layer** (auto-created): every element without an `<img>` moves here unless `data-layer="cam"`. Never zoomed.
  4. `.tag` chapter chip (top-left) and `.src` source band (bottom, always on top, own background).
- Safe area for text: **9:16** x 56–1024, y 150–1790 (platform UI covers the bottom ~20% on Reels/TikTok;
  the source band lives there because it's low-priority text). **16:9** x 64–1856, y 60–1020 (source band
  below 1020; keep key text out of the bottom-right corner, where YouTube shows end-screen elements in the
  last 20 s).
- Scene attributes: `data-vo` (VO clip) · `data-mood` (music section) · `data-type` (beat type: PHOTO, MAP,
  CHART, DOCUMENT, TEXT, TIMELINE or COLLAGE; `audit.py` reports the mix) · `data-twos="12"` (stop-motion
  cadence: animations step at 12 fps) · `data-shake="2"` (subtle hand-held jitter of the photo layer, in px)
  · `data-density="off"` (skip the density check, e.g. a deliberate black pause).

## 2. Motion vocabulary (`data-a`)
| Anim | Use | Limits |
|---|---|---|
| `up`, `left`, `fade` | default text/photo entrances | slide ≤ 46/34 px |
| `pop` | icons, chips, dots | overshoot ≤ 1.1 |
| `slam` | big numbers/headlines | start scale ≤ 1.14 |
| `stamp` | rubber stamps | start scale ≤ 1.25 |
| `mark` | highlighter sweep behind words | on the spoken word ±0.3 s |
| `count` | number count-up (Bangla digits) | `data-from`, `data-to` |
| `growx`/`drawy`/`draw` | bars, lines, SVG paths | chart reveals |
| `rot` | clock hands, dials | `data-from`, `data-to` deg |
| `strike` | red strike-through | |
Timing attributes: `data-t` (start, s from scene start), `data-d` (duration), `data-out` (fade-out time), `data-sfx` (click|tick|whoosh|impact|stamp|tone|bell|paper).

## 3. Camera
- Purposeful only: push-in to focus, pull-out to reveal scale (crowds), pan to follow a path.
- Max scale 1.75 on photos; text never affected (layer split).
- Ken Burns on hero photos: `data-kb="1"` (1.02→1.10).

## 4. Transitions
- 0.45 s paper-slide (incoming from right, outgoing left + fade). Text entrances start after ≥0.3 s into a scene.

## 5. Scene templates (in `engine/template/scenes/`)
| Template | Purpose |
|---|---|
| `hook-quote` | big question strip + quote card + cutout on colour circle |
| `big-number` | hero number on colour block + label + supporting photo |
| `timeline-vertical` | dated steps with drawn line and dots |
| `comparison-bar` | annotated bars (e.g. 32 vs 72.3 life expectancy) with half-mark |
| `tick-timeline` | repeated events as ticks across a date axis (e.g. 20 deferrals) |
| `icon-grid` | N icons popping (people, phones, houses) with count |
| `photo-collage` | 4–6 polaroids + one headline strip |
| `map-pin` | stylised street/area map with pin and label |
| `calendar-clock` | date card + clock to a time |
| `split-portrait` | two portraits + linking phrase |
| `ending-mural` | full-bleed photo, dark gradient, 3 closing lines |
| `credits` | sources + photo credits |
| `document-clip` | recreated headline/report with a highlighted phrase, labelled **পুনর্নির্মিত** (recreation) |
| `collage-parallax` | AI or photo layers (plate, hero, supporting) entering back to front, then a living-poster hold |

16:9 versions live in `engine/template/scenes16/` (`hook-quote`, `big-number`, `comparison-bar`,
`map-pin`, `document-clip`, `collage-parallax`, `ending-mural`). Landscape layouts put the photo on one side
and text on the other, rather than stacking them.

**Beat types → templates.** PHOTO: `photo-collage`, `split-portrait`, `ending-mural` · MAP: `map-pin` ·
CHART: `big-number`, `comparison-bar`, `icon-grid`, `tick-timeline` · DOCUMENT: `document-clip` · TEXT:
`hook-quote` · TIMELINE: `timeline-vertical`, `calendar-clock` · COLLAGE: `collage-parallax` (rules in
`ai-visuals.md`). Reuse templates instead of building one-off scenes; add a scene type that proves useful back
to the repo.

## 6. Infographic rules
- Facts are drawn by the engine from the source ledger: maps from open data (Natural Earth is public domain,
  OpenStreetMap needs attribution), numbers from F-numbers. Never use an AI image for a map, chart or document.
- Disputed borders and names: check them, and say whose map it is.
- One number per screen as the hero; always give a comparison or unit (“২০ বার”, “৩২ বনাম ৭২.৩”).
- Annotate: arrows, half-marks, brackets, labels — explain the chart in the chart.
- Draw in the order the voice explains it.
- Icons > pie charts for counts under ~40.

## 7. Typography (Bangla)
- Headlines: Noto Sans Bengali 900; body: Noto Sans Bengali 500–700; quotes: Noto Serif Bengali 700.
- Run `tools/font_test.py` before design: digits ০–৯, conjuncts (ক্ষ ষ্ট্র জ্ঞ ন্দ্র ঙ্ক), ং ঃ ঁ, quotes “ ”, ‘ ’, ৳, %.
- Min sizes at 1080 px width: body 40 px, labels 28 px, sources 22 px.

## 8. Style presets (`engine/template/presets/`)
- `vox-paper.css` — cream paper, ink, yellow highlighter, red accent, halftone, torn strips, sticker cutouts.
- `dark-doc.css` — charcoal documentary, red/yellow accents.
Add new presets as CSS variable sets; layouts stay identical.

## 9. Density rule
At every moment ≥55% of the content area is occupied by photo/graphic/text; `audit.py` flags stretches >1.5 s below this. Fix by bringing the next photo in earlier or adding a supporting image.
