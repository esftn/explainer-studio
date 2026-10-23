---
name: video-script
description: Research, fact-check and write the script and voiceover for an explainer video, then prepare the VO take and time it. Use after the brief is approved, or when the user asks to research, write, rewrite or voice a video script, or fix VO tone/pronunciation.
---

# Research → facts.json → script → checked → approved → VO text  (Chat 1 · Plan)

> **v0.7:** the order of work is the step card printed by `python3 engine/tools/studio.py next videoNN` (it wins over anything below that conflicts). This file is the technique reference for your current step; do not read it start to finish.

## Read
`../../docs/storytelling.md`, `../../docs/bangla-localisation.md`, `../../templates/facts.json`,
`../../templates/script.md`, and the series brief (rules: one measuring stick, Recency, Connection, Tone of
comparisons, Endings; shared figures — reuse them so episodes agree).

## 1. Research → `facts.json` (+ `docs/fact-sheet.md` for the creator)
- Search, don't recall (standard mode; several queries in one turn). Two sources for contested facts.
- One row per number the video says or shows: claim · date · source + URL · `role` · `chain` · `key`/`value`.
- **Facts gate (v0.6, `rules.facts_gate`, on for new projects).** Every fact that is not an invented example also needs:
  `url` (the exact page the number was read on, not the site front page) · `quote` (the exact sentence from that page, containing
  the number — copy it, don't paraphrase) · `fetched` (date read) · and one of `second_source {source,url,quote}` |
  `official: true` (agency dataset) | `single_source_note` (the caveat the pinned comment must carry). Invented examples
  are `illustrative: true` and need no source. `script_check.py` FAILS when the quote's number ≠ `value`, when a
  `second_source` disagrees, when `source` admits doubt ("unverified", "যাচাই বাকি"), and when the voice says a number that is *close to but not* the
  scene's fact (1.28 spoken, 1.12 sourced). If two sources differ, make one fact per source and decide which the voice uses —
  never ship "the sources conflict". `script_check.py --register` (after PASS) records the keys in `../_series/shared_facts.json`;
  the next episode that uses the same key with another value must say `"supersedes"` or fail.
  - `role: now` = anything the script presents as current → must be the latest release (≤12 months).
  - `chain: true` only if the fact sits on the yardstick or a link of the episode's chain. Side stats
    (national averages, wages…) are `false` — and then they must not be used.
  - Assumptions are facts too (3 m per floor, a bottle = 1 L), with a source.
- Every comparison or derived number gets a `math` row written with fact keys
  (`"13 * pinnacle_m"`, `"int(dollar_now) - round(dollar_before)"`), with how it rounds made explicit.

## 2. Script → `script.json` + `docs/script.md`
- Arc: hook (0–3 s) → stakes → turn → answer → closing question with "কমেন্টে লিখুন".
- One idea per scene; a visual beat every 2–3 s. Bangla চলিত, BD vocabulary, numbers as words in the VO,
  Bangla digits on screen. Frame yardsticks so the main number feels big.
- `script.json` = `{"1": "VO text", ...}`; `docs/script.md` = table: scene · VO · on-screen text · visual ·
  the spoken word each key graphic lands on (becomes `data-say`) · fact id.

- Length budget at script time: estimate VO seconds (≈ spoken chars ÷ 15 per s) and total = Σ VO + 8×pad + hold + 0.3;
  if it exceeds 60 s, say which lines to trim in the script message (do not wait for the build).

## 3. Gate 1 — the tool, then the creator
```bash
python3 engine/tools/script_check.py videoNN     # must print SCRIPT PASS; fix every FAIL first
```
Only then send the script table (and fact sheet summary) to the creator. Every later edit → re-run the
check before re-sending. On the creator's OK: `python3 engine/tools/state.py videoNN approve script`.

## 3b. Image list (right after the script is approved, before the VO text)
Send ONE short table: `#` · filename · scene · what it shows · **REAL or AI** · Gemini prompt (AI rows only).
- Count = what the story needs: a photo for each scene that needs one, reuse where possible; scenes drawn as
  graphics get none. No padding.
- **REAL PHOTO (never AI) — mark the row in bold:** banknotes/coins, real landmarks and buildings (Padma Bridge,
  Pinnacle…), logos, brands and packaging with text, named people, official documents/forms/signs, real products
  compared by brand, maps or charts of real data. Say where to get it (own photo, a scan, a source the creator can
  open — Wikimedia/bb.org.bd are blocked for Claude) and the minimum size (≥1,200 px).
- AI-ok rows: generic scenes (shop counter, rice sack, street, field, workshop, interiors, hands doing something).
- Gemini prompt rules — realistic, not AI-looking: "documentary / phone-camera photograph, natural available light,
  35–50 mm lens look, slight grain and imperfection, ordinary lived-in Bangladeshi setting, not staged, not
  cinematic, no retouching". Always end with: vertical 9:16, no text, no logos, no watermark, no banknotes.
  Keep faces, hands and crowds minimal or turned away (where AI errors show); no readable signs or labels;
  simple object counts; one clear subject.
- On arrival, make a contact sheet and check each image for garbled text, odd hands/faces/proportions and wrong
  context (not Bangladeshi, wrong objects); reject and re-prompt only the bad ones. Rename Gemini_Generated_*
  files to the table's filenames.
- The creator generates images while reviewing the VO text; the build starts when both are in.

## 4. VO text for the manual take (default while ElevenLabs is on the free plan)
- Peaks only: write `vo_tags.json` with 2–3 tagged scenes (`[curious]` hook, `…` + `[excited]` reveal,
  `[warmly]` question) — same words as script.json, tags/punctuation only (the tool rejects word changes).
- `python3 engine/tools/vo_text.py videoNN` → `vo/vo_paste.txt` (scene-break line `[pause]` between scenes).
- v0.7: send the VO text AND the image table (§3b) in ONE message (the plan card's report `vo_and_images`). Send the text in a code block (SendUserMessage) with the routine: ElevenLabs → Rayhan (eleven v4) → paste
  all → generate ONE take → download → save as `videoNN/vo/raw/vo_full.mp3` on the Mac.
- `state.py videoNN note "waiting for VO take"`. End of Chat 1 for this episode: push the project
  (`pack.py pack videoNN --set project --no-images` → commit parts to `videoNN/_to_delete/` → on the Mac
  `pack.py unpack … --into videoNN` must print VERIFIED) and tell the creator what to type in Chat 2:
  "Build episode NN" (the plugin's `video-preview`).
- Paid path (when the creator has credits): ElevenLabs connector, one `creative_generate_speech` call for
  vo_paste.txt, download it to `vo/raw/vo_full.mp3`, then the same split below. Never batch many calls.

## 5. Split and lock timing (start of Chat 2, see video-preview)
```bash
python3 engine/tools/vo_split.py videoNN    # cuts the one take at the scene breaks, validates every scene
python3 engine/tools/vo_prep.py videoNN     # trims, tempo, durations, pause anchors, word times → vo.js
```
`vo_split` exit 2 = no `vo_full.*`; it names the newest audio file — confirm it with the creator, then
`--file`. Exit 3 = AMBIGUOUS: the take has no clear scene pauses (was it pasted without the "[pause]" lines?).
Never guess: ask the creator to re-generate from vo_paste.txt; only if that's impossible, the creator listens to
the excerpts in `vo/check/` and you pass their picks with `--cuts`. FAIL = a phrase is in the wrong scene or the
take reads an older text: no clips are written. Proven on the real ep. 03 take: with clear scene pauses 8/8 cuts
right; without them, pause- and speed-based guesses got 1–5 of 8 wrong.
The `[pause]` marker is tested (1.39 s scene breaks vs ≤ 0.52 s inside scenes). If a take still comes back
AMBIGUOUS, check that the creator pasted vo_paste.txt unchanged; `[long pause]` (2.0 s) is the fallback marker.
