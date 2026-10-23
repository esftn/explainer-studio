# Explainer Studio — Production Playbook

The master rulebook for making industry-grade explainer videos with Claude (Bangla first, any language later).
Every rule here exists because skipping it cost a rebuild, a re-render or credits on a real project
(see `lessons-learned.md`). Detailed guidance lives in the other docs; this file is the spine.

---

## 0. Core principle

**Approve cheap things before building expensive things.**

| Cheap to change (approve first) | Expensive to change (build once) |
|---|---|
| Title · facts · script · emotion map · image list | Voiceover · full layout · animation · render |

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
9. Three approvals (v0.7): **script → preview (look included) → cover pick**. A title alone is enough to start; no brief gate.

**Claude does**: research + fact sheet with sources, script + emotion map, asset prep (resize, cutouts,
textures, font test), voiceover generation + timing, layout + animation, music + SFX, automated QA,
contact-sheet review, render, mastering, captions/SRT, cover, caption text, delivery.

---

## 2. Pipeline and gates (v0.7: every chat starts with `studio.py next`; v0.6 claim/guard, facts gate, one-command Finish)

| # | Phase | Output | Tool gate | Creator |
|---|---|---|---|---|
| 0 | **Title** (Chat 1, batch 1–3 episodes) | `studio.py new` → project, palette (`docs/look.md`), music preset; Claude writes `docs/brief.md` itself | — | gives the title |
| 1 | **Research** | `facts.json` (+ `docs/fact-sheet.md`) — each fact: URL, exact quote, fetched date, second source/official/single-source note | `script_check.py` + facts gate (`factcheck.py`) | — |
| 2 | **Script** | `script.json` + `docs/script.md` (with the spoken word each graphic lands on) | `script_check.py` PASS | ✅ script → `state.py approve script` |
| 2b | **Image list** (after script approval) | table: filename · scene · REAL or AI · Gemini prompt (AI rows) | — | creator makes/finds images |
| 3 | **VO text** | `vo/vo_paste.txt` (one take, scene-break lines, 2–3 tags) | `vo_text.py` (needs approval) | records one take → `vo/raw/vo_full.mp3` |
| 4 | **Split + timing** (Chat 2) | `vo/raw/vo_NN.wav`, `vo.js` (durations, anchors, word times) | `vo_split.py` + `vo_prep.py` | — |
| 5 | **Look** | assigned palette + motif (`studio.py look`); Claude checks its own stills, no separate gate | `studio.py check --stage build` | — |
| 6 | **Build + QA** | full timeline with `data-say` cues (land 0.25 s early), auto SFX, rotating music; key-moment sheet; 540p preview | `audit.py` PASS (incl. text size + reading time), `review.py --keys`, `studio.py check` | ✅ preview |
| 7 | **Final** (Chat 3) | reel + feed, `captions.bn_IN.srt` + `captions.en_US.srt`, `publish.txt` | `finish.py` (render, check_final + A/V fix, captions pair, `publint.py`) | — |
| 8 | **Cover + delivery** | 2 hand-designed concepts (`cover-design.md`, `cover_check.py` PASS) → pick → bake; verified offline copy; tidy; `docs/delivery.md`; generated tracker | `finish.py` then `finish.py --verify` on the Mac | ✅ cover |

Rules:
- A tool FAIL is fixed before anything is sent to the creator.
- Never make VO text before the script is approved; never render full-res before the preview is approved.
- Each chat starts from `state.py show` + the series brief + the generated tracker and ends with one verified `pack.py` transfer.
- v0.6 hand-offs: a Build/Finish chat **claims** the episode (`guard.py claim`, refused = stop), pulls with `pack.py unpack` (saves the base), pushes only with
  `--guard <Mac fingerprint>` (refused if the Mac copy changed since the pull), and releases at the end. The tracker is generated
  (`series_tracker.py --write`), never hand-edited; notes go to `_series/issues.md` (append-only). Finish ends with `finish.py --verify` = DONE on the Mac.
- If the creator is away, continue with the most reasonable reading, state it at the top, and stop before any paid/irreversible step.

---|---|---|---|
| 0 | **Brief** | `brief.md` filled (template) + photo inventory | ✅ creator |
| 1 | **Research** | `fact-sheet.md`: every fact → date → source URL; conflicts flagged | ✅ creator |
| 2 | **Script** | `script.md` table: scene · VO line · on-screen text · visual/infographic · emotion tag · photo · source | ✅ creator |
| 3 | **Assets** | photos resized, contact sheet, cutouts, font test sheet, textures | auto-check |
| 4 | **Look** | palette assigned by `studio.py look`; approved with the preview | — |
| 5 | **Voiceover** | 1–3 long takes → split → trimmed, level-matched clips + anchors | ✅ creator listens |
| 6 | **Build + QA** | full timeline; `audit.py` (bounds, density, safe zone) passes; contact sheets reviewed by Claude; low-res preview MP4 | ✅ creator watches preview |
| 7 | **Final** | full-res render (parallel, per-range), audio master, caption, SRT, delivery with md5 check | — |
| 8 | **Cover** | 2–3 designed cover concepts per `cover-design.md` (episode palette, real photo/cutout hero, question title without the answer; `cover_check.py` PASS) | ✅ creator picks |

Rules:
- Never generate VO before the script gate. Never render full-res before the preview gate.
- If the creator is away, continue with the most reasonable reading, state it at the top, and stop before any paid/irreversible step (VO credits, publishing).
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
- **4:5 feed zone**: key content inside y 285–1635; top/bottom bands = bleed, never empty. No chapter chips on screen.
- **Safe area** (1080×1920): text x 56–1024, y 150–1790; bottom band = sources; keep key text out of the bottom 20% of Reels UI when sources aren't used.
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

## 9. Efficiency rules
- Creator supplies photos → zero scraping. If scraping is unavoidable: small batches, browser-pane only.
- Review at low cost (contact sheets, low-res preview); render full-res once; re-render only changed ranges.
- Keep tool outputs compact (jq/grep), avoid reading big JSON or many single frames into context.
- Start every project from this engine; add new scene types/presets back to the repo when they prove useful.
