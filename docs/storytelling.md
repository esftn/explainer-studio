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
- Test one short line for pronunciation/voice fit before the full run.
- Pace ≈1.05× for social; trim leading/trailing silence; level-match each clip (−17.5 LUFS) before mixing.
- Timing: use silence anchors (`vo_prep.py`) or word timestamps (ElevenLabs Scribe supports Bengali STT; its forced-alignment endpoint does not list Bengali) to place highlights on the spoken word.
- Leave 0.6–1 s of near-silence after the heaviest line; let music swell slightly there.

## 7. Screen vs voice
The voice tells the story; the screen shows **key word, number, quote, name, place or date** — never the full sentence.
Burned captions (optional) = short phrases, max 2 lines, above the bottom UI.
