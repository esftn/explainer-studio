# Design System (style-independent rules + engine conventions)

## 1. Canvas & layers
- 1080×1920, 30 fps. Each `<section class="scene">` has:
  1. `.bgp`/`.bgd` texture background (paper / dark)
  2. `.cam` — **camera layer**: photos, cutouts, full-bleed images, decorative shapes (`data-layer="cam"`). Camera keyframes (`data-cam="t:scale:x:y|..."`) move only this layer.
  3. `.fix` — **text/graphics layer** (auto-created): every element without an `<img>` moves here unless `data-layer="cam"`. Never zoomed.
  4. `.tag` chapter chip (top-left) and `.src` source band (bottom, always on top, own background).
- **4:5 feed zone: key content inside y 285–1635** (Facebook timeline previews/autoplays Reels as 4:5). Bands above/below carry bleed so the full 9:16 never looks empty.
- Safe area for text: x 56–1024, y 150–1790. Platform UI covers the bottom ~20% on Reels/TikTok; the source band lives there because it's low-priority text.

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

Easing (engine.js): expo-out for entrances (quick start, long soft settle, default 0.7 s), quart in-out for
bars/stacks/counts, gentle back-out (overshoot ≈4%) for pops. Scene change = colour wipe from the right with
slight parallax (0.5 s). Counts accept `data-fmt="in"` for Indian grouping (২,০০,০০,০০০).

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

## 6. Infographic rules
- One number per screen as the hero; always give a comparison or unit (“২০ বার”, “৩২ বনাম ৭২.৩”).
- Annotate: arrows, half-marks, brackets, labels — explain the chart in the chart.
- Draw in the order the voice explains it.
- Icons > pie charts for counts under ~40.

## 7. Typography (Bangla)
- `vox-money` preset: **Tiro Bangla** everywhere (one weight; thicken headlines with `-webkit-text-stroke`, never faux bold; avoid ৳, it renders like ট).
- Headlines: Noto Sans Bengali 900; body: Noto Sans Bengali 500–700; quotes: Noto Serif Bengali 700.
- Run `tools/font_test.py` before design: digits ০–৯, conjuncts (ক্ষ ষ্ট্র জ্ঞ ন্দ্র ঙ্ক), ং ঃ ঁ, quotes “ ”, ‘ ’, ৳, %.
- Min sizes at 1080 px width: running text 40 px, labels 34 px (audit FAILs < 30 px), sources 22 px.
- **Reading time (v0.7.1):** every text stays on screen ≥ 0.6 s + 0.33 s per word (numbers / 1–2 word labels ≥ 1.2 s), counted from 0.25 s after it starts to its `data-out` or scene end. `audit.py` FAILs shorter. Appearing early is fine; appearing late is not. `data-say` lands 0.25 s before the word (`sayLead` in project.json).

## 8a. Palettes (v0.7) — Vox / Johnny Harris look
Colours are NOT chosen per episode: `studio.py look` assigns one of 12 contrast-checked palettes (v0.7.1: rebuilt from the colours of episodes 1–5 — calm, printed-paper, no neon) from `engine/studio/palettes.json` (rotating by episode, skipping a family used by the last three episodes) and writes `docs/look.md` with ready-made scene themes (bg / text / highlight / pop) and a motif. Style = flat calm colour blocks, real paper/grain/halftone texture, cutout photos with a thin paper outline and soft shadow, no top/bottom bars, hand-made marks (arrows, circles, underlines, string, stamps, tape), 3–4 colours per scene, big bold type. Edit colours only in `engine/studio/build_palettes.py` (it re-validates contrast).

## 8. Style presets (`engine/template/presets/`)
- `vox-paper.css` — cream paper, ink, yellow highlighter, red accent, halftone, torn strips, sticker cutouts.
- `dark-doc.css` — charcoal documentary, red/yellow accents.
- `vox-money.css` — Vox "Your money, explained": per-scene colour themes (money green, graph paper, blueprint, sky, Vox yellow, teal map, ink) with matching textures; Tiro Bangla.
Add new presets as CSS variable sets; layouts stay identical.

## 9. Density rule
At every moment ≥55% of the content area is occupied by photo/graphic/text; `audit.py` flags stretches >1.5 s below this. Fix by bringing the next photo in earlier or adding a supporting image.
