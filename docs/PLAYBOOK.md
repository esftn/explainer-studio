# Explainer Studio — Production Playbook

The master rulebook for making industry-grade explainer videos with Claude (Bangla first, any language later).
Every rule here exists because skipping it cost a rebuild, a re-render or credits on a real project
(see `lessons-learned.md`). Detailed guidance lives in the other docs; this file is the spine.

---

## 0. Core principle

**Approve cheap things before building expensive things.**

| Cheap to change (approve first) | Expensive to change (build once) |
|---|---|
| Brief · source ledger · script + beat table · emotion map · style frames | Voiceover · AI clips · full layout · animation · render |

A video is "first-try ready" when nothing in the right column is built on an unapproved left column.

---

## 1. Roles

**The creator (user) provides** — the `/new-video` intake asks for all of it:
1. Topic, angle and *one-sentence takeaway* (if it can't be said in one sentence, it's not ready)
2. Audience (who, region, age, how much they already know) and purpose (inform / persuade / tribute / promote)
3. Platform(s) and length → see §6
4. Tone and register (e.g. informal চলিত, warm, serious) + 1–3 reference videos/screenshots
5. Photos/footage dropped in `photos/` (20–40 for a 2–3 min video), with credit/source notes if known
6. Voice: provider + paid account, or "I'll record it myself"; voice preference (gender, age, accent)
7. Brand: colours, handle/logo, end card, CTA
8. Rules: what must / must not appear; sensitivities (politics, religion, real people)
9. Materials to use (links, documents, transcripts). If Claude can't open one, it says so and asks for a paste.
10. Monetised or not (decides which licences are acceptable); AI illustrations allowed or not
11. Approvals: **brief → ledger → script → VO → style frames → preview → final QA**

**Claude does**: research + fact sheet with sources, script + emotion map, asset prep (resize, cutouts,
textures, font test), voiceover generation + timing, layout + animation, music + SFX, automated QA,
contact-sheet review, render, mastering, captions/SRT, cover, caption text, delivery.

---

## 2. Pipeline and gates

| # | Phase | Output | Gate |
|---|---|---|---|
| 0 | **Brief** | `brief.md` filled (template) + photo inventory | ✅ creator |
| 1 | **Research** | `fact-sheet.md` = source ledger: central question + thesis, F-numbered facts with source + confidence, counterpoints, hooks, visual opportunities | ✅ Gate 1 |
| 2 | **Script + beats** | `script.md` table: scene · beat type · VO line · on-screen text · template · asset · emotion · F-numbers; mix, budget, missing assets, licence warnings | ✅ Gate 2 |
| 3 | **Assets** | photos resized, contact sheet, cutouts, font test sheet, textures | auto-check |
| 4 | **Style frames** | 3 stills: hook · data/infographic scene · ending | ✅ creator |
| 5 | **Voiceover** | 1–3 long takes → split → trimmed, level-matched clips + anchors | ✅ creator listens |
| 6 | **Build + QA** | full timeline; `audit.py` (bounds, density, safe zone) passes; contact sheets reviewed by Claude; low-res preview MP4 | ✅ creator watches preview |
| 7 | **Final** | full-res render, audio master, `check_final.py`, cover/thumbnail, SRT, `publish.md` | ✅ Gate 4: creator ticks sound-off / screen-off / facts / rights before publishing |

Rules:
- Never generate VO before the script gate. Never render full-res before the preview gate.
- **Gates hold even in "do it all in one go" mode.** If the creator is away, continue with the most
  reasonable reading of cheap steps, state it at the top, and stop at the next gate. Never start a paid step
  (VO, AI clips) on an unapproved ledger and script, and never publish.
- **Use the creator's materials.** If a link or file can't be opened, say so and ask for a paste; never claim to have read it.
- Each gate message is short: what to check, what changes are cheap now, what becomes expensive after.

---

## 3. Story rules (details: `storytelling.md`)
- Hook in **0–3 s**: question, striking quote, shocking number or visual surprise. No title cards first.
- Open a loop early, close it last ("হু ইজ হাদি?" → "তাহলে, হাদি কে?").
- One idea per scene; a new visual beat every **2–3 s**; a pattern interrupt every 10–15 s.
- Arc: hook → context → rising stakes → turning point → consequence → answer/payoff → memorable last line/CTA.
- Facts carry the emotion; adjectives don't. Show numbers with comparisons.
- Sensitive topics: include the other side's stated position (e.g. a later clarification) and cite everything.

## 4. Voiceover rules
- Script for the ear: 8–12 word sentences, spoken register, numbers written as words for TTS.
- **Emotion map**: neutral for facts, warm for personal details, grave only at 2–3 peaks, strong close.
- Generate in **1–3 long takes** (same voice/model/settings) — never 17 bursts (rate limits, account flags).
- Pauses before reveals; ~0.6–1 s silence after the heaviest line.
- Test pronunciation of names/English words with one short take before the full run.
- Visual highlights land within ±0.3 s of the spoken word (use pause anchors / word timestamps).

## 5. Design rules (details: `design-system.md`)
- **Layers**: photo/camera layer (zooms/pans) · fixed text layer (never zoomed) · source band (always on top).
- **Safe area** (9:16, 1080×1920): text x 56–1024, y 150–1790 · (16:9, 1920×1080): x 64–1856, y 60–1020; bottom band = sources; keep key text out of the bottom 20% of Reels UI when sources aren't used.
- Entrances: slide ≤40 px, scale ≤1.15, fade. Nothing starts off-screen.
- **Density**: ≥55–60% of the frame occupied at all times; no stretch >1.5 s that is mostly empty.
- Every scene: ≥1 photo/graphic + 1 key text + 1 highlight; numbers as heroes with a comparison.
- Text on photos always sits on a strip/band.
- Motif words used ≤2× (open + close).
- Fonts tested on digits + conjuncts before design (Bangla: Noto Sans Bengali / Noto Serif Bengali; **not** Hind Siliguri for numerals).

## 6. Platform targets
| Platform | Ratio | Length | Notes |
|---|---|---|---|
| Facebook Reels / feed (≈79% of BD social share) | 9:16 (feed also 4:5) | ≤ 90 s ideal; ≤ 3 min | burned-in Bangla captions or SRT; many watch muted |
| YouTube Shorts | 9:16 | ≤ 2:59 | hook in 1–2 s; loopable ending helps |
| TikTok | 9:16 | 30–90 s sweet spot | captions above bottom UI |
| YouTube long-form | 16:9 | 6–12 min | chapters, slower pacing, more context |

## 7. Audio targets (details: `audio.md`)
- Master −14 LUFS integrated, true peak ≤ −1.5 dBTP; clean silent last 0.25 s.
- VO ≈ 12–15 dB above the ducked music bed; music ducks ~8 dB under speech.
- SFX on visual hits (click/whoosh/impact/stamp/tone), never on top of key words.
- Local palettes available (Bangla folk-inspired: tanpura drone, dotara pluck, bansuri, tabla) — see `bangla-localisation.md`.

## 8. QA before every render (`qa-checklist.md`)
`audit.py` must pass (text bounds every 0.1 s, source-band overlap, density) — `render.py` refuses to run otherwise.
Then: contact sheet every 1.5 s reviewed, spelling/consistency pass, sync spot-check, length, loudness, md5 on delivery.

## 9. AI visuals (details: `ai-visuals.md`)
- AI is illustration, never evidence. Maps, charts, documents, quotes and real people come from the engine or
  real sourced photos; AI only does atmospheric COLLAGE beats (≤ 40% in MIX; never > 3 in a row).
- No Bangla text inside AI images; all words go on the engine's text layer.
- Every asset (photo, AI image, clip) has a row in `licences.csv`; `audit.py` checks it.

## 10. One folder per video
If a file isn't in the project folder, it isn't in the video: `brief.md`, `fact-sheet.md`, `script.md`,
`script.json`, `licences.csv`, `photos/`, `img/`, `vo/`, `index.html`, `out/` (video, cover, thumbnail,
`captions.srt`, `publish.md`). That keeps facts, assets and licences traceable.

## 11. Getting started (first month)
1. **Week 1:** set up (`setup.sh`, `font_test.py`), pick a look, and make one 60-second **pilot** on a topic you know well.
2. **Week 2:** note the slowest step of the pilot and fix it, then make a second 60–90 s video.
3. **Week 3:** try one long-form chapter (16:9) to test depth.
4. **Week 4:** lock what worked (presets, palettes, scene templates) and set a cadence from the real time and credits used.

## 12. Efficiency rules
- Creator supplies photos → zero scraping. If scraping is unavoidable: small batches, browser-pane only.
- Review at low cost (contact sheets, low-res preview); render full-res once; re-render only changed ranges.
- Keep tool outputs compact (jq/grep), avoid reading big JSON or many single frames into context.
- Start every project from this engine; add new scene types/presets back to the repo when they prove useful.
