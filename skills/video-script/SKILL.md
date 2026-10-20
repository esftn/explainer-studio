---
name: video-script
description: Research and fact-check an explainer video into a source ledger, write the script and beat table, then generate and time the voiceover. Use after the brief is approved, or when the user asks to research, fact-check, write, rewrite or voice a video script, plan long-form chapters, or fix VO tone/pronunciation.
---

# Source ledger → script + beat table → voiceover

## Read
`../../docs/storytelling.md`, `../../docs/bangla-localisation.md` (Bangla), `../../docs/ai-visuals.md` §1
and §5, `../../templates/fact-sheet.md`, `../../templates/script.md`, and `../../docs/lessons-learned.md` (VO section).

## 1. Research → `fact-sheet.md` (the source ledger) — GATE 1
- **Search, don't recall.** Look up anything current or contested (WebSearch, standard mode, several queries
  in one turn). Prefer primary sources (records, original reports, laws, original interviews) and use
  reputable journalism for context.
- Fill in every section:
  - **Central question and provisional answer:** one sentence each.
  - **F-numbered facts:** 10–20 for a short, 25–40 for a long video. Each gets a source (title,
    publisher, date, URL) and a confidence rating: CONFIRMED, SINGLE-SOURCE or DISPUTED.
  - **Chronology.**
  - **Counterpoints and unknowns,** with how the script will phrase each one.
  - **3 cold-open hooks,** each tied to an F-number.
  - **Visual opportunities by beat type,** with an asset lead and its licence.
- **Conflicting sources → say less** (e.g. the year only). Quotes are verbatim, with who said them, where and when.
- **No web search available?** Say so, and mark everything not from the creator's material UNVERIFIED.
- **Gate 1:** send a compact summary: the question, the thesis, the facts table, counterpoints and hooks.
  The creator corrects it and picks a hook.

## 2. Script → `script.md` + `script.json` — GATE 2
- **Short:** cold open → why it matters → one mechanism or reveal → payoff.
- **Long:** plan the chapter arc first (question → stakes → mechanism → evidence → counterpoint → payoff),
  then write one chapter at a time. Each chapter has a mini cold open and a hand-off line.
- **Cold open:** a date, a place or name, and one concrete detail in the first 2–3 sentences.
- **Beats:** one idea per sentence, with a why/so-what line every 30 s. Include the strongest counterpoint
  where it matters.
- **Ending:** pick one of the five ending patterns. The last line is ≤ 12 words.
- **One row per scene:** beat **Type** (PHOTO/MAP/CHART/DOCUMENT/TEXT/TIMELINE/COLLAGE), VO line,
  on-screen text, template (from `../../engine/template/scenes/` or `scenes16/`), asset, emotion tag, SFX and F-numbers.
- **Mix rules:** MIX means COLLAGE ≤ 40% and never more than 3 in a row. Prefer an accurate MAP, CHART,
  DOCUMENT or PHOTO over a generic COLLAGE.
- **Bangla:**
  - চলিত register with BD vocabulary (পানি, গোসল…).
  - 8–12-word sentences.
  - আপনি unless the brief says তুমি.
  - Numbers as words in the VO text; Bangla digits on screen.
- **Length:** aim for ~2.3–2.8 words/s; total words ÷ 2.5 ≈ seconds. Trim before the gate, not after the VO.
- **After the script:** a fact-check list (line → F-numbers) and one *creator note* suggesting where the
  creator could add their own insight or perspective (don't write it for them).
- **Summary:**
  - the beat mix
  - estimated length
  - **budget** (VO characters; AI images; Flow clips × 2 × ~20 credits, or 0 with engine parallax)
  - missing assets and licence warnings
- **Save** `script.json` as `{"1": "VO text of scene 1", ...}`. The keys are scene numbers, matching `data-vo`.
- **Gate 2:** send the table and summary; the creator approves the script and the budget. Changes are free
  now and expensive after the VO.

## 3. COLLAGE prompts (only if the script has COLLAGE beats and AI is allowed)
Write `collage-prompts.txt` following `../../docs/ai-visuals.md` §3: SCENE, then the verbatim STYLE BLOCK
for the look, then the verbatim CLOSER. No Bangla text in the images. Apply the recurring-subject law and the
rules for real people and children. Use a connected image tool if one is available (e.g. Freepik); otherwise
the creator pastes the prompts into Gemini (Nano Banana Pro) and drops the images into `photos/`. Every AI
image gets a `licences.csv` row with `ai=yes`.

## 4. Voiceover (paid step — only after Gate 2)
- **ElevenLabs MCP:**
  1. Call `creative_create_flow` once.
  2. Call `creative_generate_speech` per clip on that flow, with the SAME voice_id, model and settings for every clip.
  3. Poll `creative_get_flow_run_status`.
  4. Pick a Dhaka-standard Bangla voice with `creative_list_voices` (avoid Kolkata- or Hindi-accented
     ones). Test one short line containing names and English words first.
- **Gemini TTS (free):** give the creator a style line plus the script for Google AI Studio
  (`gemini-3.8-flash-tts` lists Bangla). Check the commercial terms.
- **Own recording:** one take per chapter, keeping the best of 2–3, then split at the scene breaks into vo_NN files.
- **Delivery:** neutral for facts, warm for personal moments, grave only at 2–3 peaks. Don't add emotion tags
  to factual scenes (v3 lesson).
- **Downloads:** fetch clips promptly (signed URLs expire after ~2 h) into `<project>/vo/raw/vo_NN.mp3`.
- **Errors:** on a 429, wait and retry once. On "free tier disabled", stop and tell the creator; never burn retries.

## 5. Lock timing
```bash
python3 engine/tools/vo_prep.py <project>     # trims, tempo 1.06, writes vo.js + vo/report.txt
```
Read `vo/report.txt` and flag scenes with words/s > 3.2 (rushed) or < 1.6. Pause anchors (a1, a2…) mark
where the next phrase starts; use them to time highlights. Gate: the creator listens to the VO (send 1–2 clips
or the joined file).
