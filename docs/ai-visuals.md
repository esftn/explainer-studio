# AI Visuals: when, how, and the rules

AI images and clips are **illustration, never evidence**. They're for atmosphere: an idea, a mood, a symbolic
object. Facts are shown with real photos or with graphics built in the engine.

## 1. Route every beat to the cheapest tool that does it best

| Beat type | Built with | Never with |
|---|---|---|
| **PHOTO**: a real person, place or event | sourced photo + camera move / cutout / halftone | AI image |
| **MAP**: place, route, border, distance | engine (`map-pin` + SVG, open data) | AI image (wrong geography) |
| **CHART**: number, comparison, trend, scale | engine (`big-number`, `comparison-bar`, `icon-grid`, `tick-timeline`) | AI image (made-up numbers) |
| **DOCUMENT**: headline, report, letter, record | engine `document-clip`, labelled **পুনর্নির্মিত / recreation** | AI image, or a fake that looks genuine |
| **TEXT**: quote, term, one striking number | engine (`hook-quote`, kinetic type) | AI image |
| **TIMELINE**: a run of dates | engine (`timeline-vertical`, `tick-timeline`) | AI image |
| **COLLAGE**: atmosphere, symbol, an idea with no photo | AI image (Gemini Nano Banana Pro, Freepik…) → animated in the engine | presenting it as a real photo |

Mix rules (the `Type` column in `script.md`; `audit.py` reports the mix):
- **VOX** look: COLLAGE 40–60% of beats. **HARRIS** look: MAP + PHOTO ≥ 40%, COLLAGE ≤ 30%.
  **MIX** (default): COLLAGE ≤ 40%.
- Never more than 3 COLLAGE beats in a row.
- Prefer an accurate MAP, CHART, DOCUMENT or PHOTO over a generic COLLAGE whenever it explains more.
- The first beat (hook) and the last beat (payoff) are the strongest visuals.

## 2. Hard rules
1. **No Bangla text inside AI images.** Generators render Bangla script badly (broken conjuncts, wrong
   letters). Leave space instead and put all words on the engine's text layer, using the tested fonts.
   Latin text in an AI image: at most one 1–4 word label, and check it letter by letter.
2. **Real people:** never generate a realistic or recognisable face of a real person. Use their real,
   sourced photo, or a symbolic figure: a halftone cutout in generic clothing, face turned away or a black
   bar across the eyes.
3. **Children:** never depict a child's face. Use symbols such as small shoes by a door, an empty swing,
   a school bag on a step, or a blank silhouette.
4. **Never as evidence:** an AI image is never shown as a photo of a specific real event, place or
   document, and never carries data (no AI maps, charts or "documents").
5. **Recurring subject law:** a figure, object or place that comes back is described with identical
   wording every time (same shawl, same briefcase, same censor bar), so the set reads as one film.
6. **Ledger:** every AI asset gets a row in `licences.csv` with `ai=yes` and the tool used. If an asset
   looks realistic, tick YouTube's altered/synthetic content setting when publishing.
7. **Tragedy restraint:** no gore and no suffering close-ups. Tension lives in objects, places,
   documents and time.

## 3. Image prompt recipe (COLLAGE beats only)
Think first, without writing it down: what is the beat's core idea (not its literal words)? Pick one hero
element (about 70% of the visual weight), 2–3 supporting elements at most, and a background that serves
the story. Leave generous empty space where the engine will put the Bangla text.

Each prompt is one block of prose: **SCENE** (the composition) + **STYLE BLOCK** (verbatim) + **CLOSER**
(verbatim).

**STYLE BLOCK, vox-paper** (matches `presets/vox-paper.css`):
> hand-cut documentary paper collage on aged cream newsprint, black and white halftone photograph cutouts
> with rough scissor-cut edges, torn paper edges, masking tape fragments, rubber stamp marks, red string
> and brass pins where the story needs connections, desaturated archival palette of cream, ink black and
> halftone gray with ONE hot red accent (#e2333f) and a warm yellow secondary (#ffc93c), visible print grain
> and paper fibre, matte, flat even documentary lighting with soft cutout drop shadows; vary the paper tones
> between scraps so the collage reads as assembled from many real paper sources.

**STYLE BLOCK, dark-doc / HARRIS**:
> documentary mixed-media collage of textured archival photographs, old paper maps and field notebooks,
> halftone print texture, film grain, subtle dust, torn photo edges with white borders, hand-drawn marker
> circles and arrows in one red, warm desaturated sepia and slate palette with one red accent, matte paper
> surfaces, soft natural documentary lighting with gentle layered shadows.

**CLOSER**:
> Every element must appear physically hand-cut and layered from real paper, with visible cutout edges,
> halftone texture and soft shadow separation between layers. Clean, minimal, editorial composition with
> generous empty space. NOT digital illustration, NOT cartoon, NOT 3D render, NOT glossy, no gradients,
> no clutter, no watermark, no logos, no text. [9:16 or 16:9], ultra-detailed.

Consistency: generate the first image, approve it, then attach it as the **style reference** for every
following image. Fix wrong details with an edit instead of a full regeneration.

Delivery for the creator to paste into Gemini in bulk: one `collage-prompts.txt`, one self-contained block
per prompt, separated by a blank line, with no numbers or headers. List the beat numbers underneath.

## 4. Animating COLLAGE beats

**Default: engine parallax (zero credits).**
1. Cut the image into layers: `prep_photos.py --cut` (rembg) for the hero, or ask the image tool for
   separate transparent PNGs (background plate, hero, each supporting element).
2. Stack them in the scene's `.cam`, back to front, with staggered entrances (`data-a="up|pop|left"`, 0.3–0.5 s
   apart) and `data-sfx="paper"` on the hero.
3. Add `data-twos="12"` on the scene for the stop-motion "animated on twos" cadence, and optionally
   `data-shake="2"` for a hand-held paper feel.
4. Then hold it as a "living poster": a slow camera push of no more than 1.08.

**Flow / Veo (costs credits).** Use it only for 1–3 hero beats per video. Template (D = 4, 6 or 8 s):
> Transform the provided image into a D-second editorial paper-collage animation. Preserve the final
> composition exactly. The image is the FINISHED frame the animation builds toward. Stop-motion cadence,
> 2–3 frame holds, every element moves as a rigid paper piece. CAMERA LOCKED: no zoom, pan, tilt, shake,
> cuts or morphing. First 75%: open on the empty background plate; elements enter one by one, back to
> front, each landing with a tiny bounce and a real shadow; nothing moves again after it lands. Final 25%:
> everything holds, only paper corners lift slightly and shadows breathe. AUDIO: none (the engine adds
> sound). Never reveal a recognisable face of a real person or any child's face.

## 5. Credit budget (estimate it before spending)
- **Flow:** clips × 2 (one retake) × about 20 credits on Veo Fast (about 10 on Lite; Quality ≈ 100). On
  Google AI Pro's 1,000 credits a month, 6 hero clips per short ≈ 240 credits ≈ 4 shorts a month.
  Parallax in the engine costs 0.
- **Images:** Nano Banana Pro on Google AI Pro ≈ 100 images a day, but the cap varies at peak times.
- **Voice:** ElevenLabs bills roughly per character of script on most models. Check the balance before
  the run, and remember that the free tier has no commercial licence and can be disabled.
- Put the estimate in the script table's summary; the creator approves it at the script gate.

Sources: research chat "Vox-style animated videos with AI" (Oct 2026), and `industry-research.md` §B.
