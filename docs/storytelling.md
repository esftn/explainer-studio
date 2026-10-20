# Storytelling & Voiceover Guide

## 1. Hooks (first 0–3 s) — pick by audience awareness
| Hook | Use when | Bangla example shape |
|---|---|---|
| Direct question | audience half-knows the topic | “হু ইজ হাদি?” / “এই টাকাটা আসলে কোথায় যায়?” |
| Striking quote | a public statement sparked the topic | quote card + speaker name |
| Shocking number | scale is the story | “২০ বার।” on a colour block |
| Relatable micro-story | emotional/consumer topics | “রিকশাওয়ালা রহিম ভাই রোজ…” |
| Visual surprise | crowded feed | full-bleed photo + one word |
| Provocative claim | myth-busting | “আমরা যা জানি, তার অর্ধেক ভুল।” |

Rules: lead with the viewer's question, not the creator's brand; open a loop and close it at the end;
fix the hook before polishing anything else.

## 2. Story arcs that work for explainers
1. **Question → answer** (loop): hook question → evidence beats → the answer restated with new meaning.
2. **Then → now → why**: past state, present state, the cause.
3. **Person → system**: one person's story widens to the bigger issue.
4. **Myth → fact → so what**.
5. **Timeline with a turning point**: steady beats, one dramatic turn, consequence, reflection.
6. **Zoom levels**: one home → a village → a nation (good for data/infographics).

Every arc: hook → context → stakes rise → turn → consequence → payoff → last line / CTA.

### Central question
Every video answers **one central question**, with a provisional answer (thesis) in one sentence. Both are
written into `fact-sheet.md` (the source ledger) before the script exists. If a scene doesn't serve the
question, cut it.

### Short format (≤ 90 s)
Cold open → why it matters → one mechanism or reveal → payoff / cliffhanger.

### Long format (YouTube 16:9, 3–12 min, Johnny Harris depth)
Plan the chapter arc first (one line per chapter), using this spine across the whole video:
1. **The question**: cold open plus the central question.
2. **The stakes**: why it matters, and to whom.
3. **The mechanism**: how it works (the Vox explainer layer, built from maps, charts and diagrams).
4. **Evidence and reveals**: what the sources show, in the order that builds tension.
5. **The counterpoint**: the strongest opposing evidence or explanation, stated fairly.
6. **The payoff**: the answer, with new meaning, plus the cliffhanger or last line.

Chapters run 45–90 s each. Each chapter gets a mini cold open and a hand-off line into the next one. The
chapter tags (`.tag`) become YouTube chapters in `publish.md`.

### Script rules that carry over from the research
- **Cold open:** the first 2–3 sentences (about 20–25 words, about 8 s) land on a precise date, a place or
  name, and one small concrete detail. *“২০২৫ সালের ১২ ডিসেম্বর, দুপুর। পল্টনের এক রিকশায়…”*
- **Explain, don't just narrate:** at least one sentence every 30 s answers *why* or *so what* (cause,
  consequence, scale, comparison).
- **One idea per sentence, ending cleanly.** Sentences become visual beats, so each one should suggest
  something the viewer can see.
- **Counterpoint:** include the strongest counterpoint or unknown from the ledger whenever it affects the
  thesis. Phrase uncertainty honestly (“পুলিশের দাবি…”, “এখনও জানা যায়নি…”).
- **No fabricated suspense,** no unsupported causal claims, no clickbait the video doesn't pay off.
- **Endings: pick one pattern.**

  | Pattern | Shape |
  |---|---|
  | Unresolved object | the thing still sitting there |
  | Dated forward jump | “২০২৬ সালের মার্চে, রায় আসবে।” |
  | Missing piece | the one fact nobody has |
  | Quiet contradiction | two true things that don't fit together |
  | Price line | what it cost, in one number |

  The last line is 12 words or fewer and ends on a noun, a name, a date or a short statement.
- **Creator note:** after the script, add one line suggesting where the creator could add a personal
  insight, opinion or on-camera moment (don't write it for them). Human perspective is what keeps AI-assisted
  videos original and monetisable.
- **Fact check:** under the script, map every factual sentence to its ledger numbers (F1, F2…).

## 3. Pacing & retention
- New visual beat every 2–3 s; pattern interrupt (colour/scene/sound change, a number slam, a question) every 10–15 s.
- Remove dead air: every beat either advances the idea or resets attention.
- One idea and one payoff per video; the takeaway must fit in one sentence.
- Short-form: 45–90 s is the sweet spot; ≤2:59 for Shorts/Reels limits.
- End on a line that sticks, a question to comment on, or a loop back to the hook.

## 4. Writing for the ear (Bangla)
- 8–12 words per sentence; one idea per sentence; verbs early.
- Spoken চলিত, not সাধু or bookish phrasing. Prefer everyday words (“শুরু করি”, not “আরম্ভ করা যাক”).
- Address the viewer as **আপনি** (respectful default for Bangladesh); “আমরা/চলুন” builds togetherness.
- Numbers in the VO script as words (“উনিশশো তিরানব্বই”), on screen as Bangla digits (১৯৯৩).
- English loanwords: keep only common ones; test TTS pronunciation first.
- Proverbs and short poetry lines (public-domain poets such as Tagore) add local colour — sparingly, ≤1 per video.

## 5. Emotion map (VO direction)
| Beat type | Delivery | ElevenLabs v3/v4 tag (if used) |
|---|---|---|
| Facts, dates, process | neutral, clear | none |
| Personal details, warmth | warm | `[warmly]` |
| Stakes rising | slightly faster, tense | `[nervous]` sparingly |
| Peak loss/injustice (max 2–3 per video) | slow, low | `[sad]` / `[slowly]` |
| Reveal / number | pause before, punch on the number | `…` or `[pause]` |
| Closing line | slow, deliberate | `[slowly]` |
Never tag every line — over-acting sounds fake. A poet or teacher description is a *fact* beat, not a sad one.

## 6. VO production rules
- Approve the script first; then generate in 1–3 long takes with identical settings.
- Voice options, in order of trust: **own voice** (best for authenticity and monetisation; one take per
  chapter, keep the best of 2–3) · **ElevenLabs** (paid plan for commercial use; Dhaka-standard voice) ·
  **Gemini TTS** in Google AI Studio (free tier; `gemini-3.8-flash-tts` lists Bangla; direct the style in
  plain words, e.g. "calm, clear documentary narrator, steady pace". Check the commercial terms and test one
  line for pronunciation first).
- Test one short line for pronunciation/voice fit before the full run.
- Pace ≈1.05× for social; trim leading/trailing silence; level-match each clip (−17.5 LUFS) before mixing.
- Timing: use silence anchors (`vo_prep.py`) or word timestamps (ElevenLabs Scribe supports Bengali STT; its forced-alignment endpoint does not list Bengali) to place highlights on the spoken word.
- Leave 0.6–1 s of near-silence after the heaviest line; let music swell slightly there.

## 7. Screen vs voice
**Two-way test** (done again at the final QA gate):
- **Sound off:** muted, the visuals alone still tell the story, and every number and label is readable on a phone.
- **Screen off:** audio alone, no line depends on a visual to be understood ("as you can see here…" is banned).

The voice tells the story; the screen shows **key word, number, quote, name, place or date** — never the full sentence.
Burned captions (optional) = short phrases, max 2 lines, above the bottom UI.
