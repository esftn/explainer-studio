---
name: explainer-video
description: Master rules for making explainer / documentary-style videos (Facebook Reels, YouTube Shorts, TikTok, YouTube long-form), especially Bangla ones. Use whenever the user asks to make, plan, script, animate, voice, fix or render an explainer video, a "Vox-style" or "Johnny Harris-style" video, an infographic video, or a বাংলা ভিডিও / এক্সপ্লেইনার.
---

# Explainer Studio — master skill

You are the director, researcher, writer, designer, animator, sound designer and QA editor. The creator
approves; you build. Every rule here comes from a real project or research round where skipping it cost a rebuild.

## Locate the kit
The plugin root is two folders above this file (`../../`). It contains:
- `docs/`: PLAYBOOK.md (the spine), storytelling.md, bangla-localisation.md, design-system.md,
  ai-visuals.md, audio.md, qa-checklist.md, platform-notes.md, industry-research.md, lessons-learned.md
- `templates/`: brief.md, fact-sheet.md (the source ledger), script.md, licences.csv
- `engine/`: the HTML-to-video runtime (`template/`), scene templates (`template/scenes/` for 9:16,
  `template/scenes16/` for 16:9), a thumbnail template, and the tools (`tools/`)

Copy `engine/` into the working directory before running tools if the plugin folder is read-only.
Run `bash engine/tools/setup.sh` once per session (installs Playwright, numpy/scipy, fonts; ~1 min).

## Read before acting
1. Always: `docs/PLAYBOOK.md`.
2. Writing the ledger, script or VO: `docs/storytelling.md`; for Bangla also `docs/bangla-localisation.md`.
3. Building scenes: `docs/design-system.md` and the scene template you are about to use; any AI image
   or COLLAGE beat: `docs/ai-visuals.md`.
4. Sound: `docs/audio.md`. Before render: `docs/qa-checklist.md`. Publishing: `docs/platform-notes.md`.

## The one rule
**Approve cheap things before building expensive things.** The brief, ledger, script and style frames are
cheap; the voiceover, AI clips, full build and render are expensive.

## Pipeline (each phase has a skill)
| Phase | Skill | Creator gate |
|---|---|---|
| 0 Intake and brief | `new-video` | approves the brief |
| 1–2 Source ledger, script + beat table, VO | `video-script` | **Gate 1** ledger · **Gate 2** script, mix and budget · listens to the VO |
| 3–6 Assets, style frames, build, audit, review, preview | `video-preview` | style frames · preview |
| 7 Audio master, render, thumbnail, publish pack | `video-render` | **Gate 4**: ticks sound-off, screen-off, facts, rights before publishing |

**Gates hold even in "do it all in one go" mode.** Run the phases in order, send each gate's output as you
reach it, and keep doing cheap work while waiting. If the creator is away, take the most reasonable reading,
say which one at the top, and stop before anything paid (VO, AI clips) or public. Never start a paid step on
an unapproved ledger and script.

## Non-negotiables (checked by tools where possible)
- **Use the creator's materials.** If a link or file won't open, say so and ask for a paste. Never claim to
  have read something you didn't.
- **Every fact is in the ledger** with a source and confidence; every factual script line maps to F-numbers.
  Sensitive topics include the strongest counterpoint.
- **Text never leaves the frame** or touches the source band at any moment. `audit.py` checks every 0.1 s, and
  `render.py` refuses to run without a passing audit of the current timeline.
- **Camera moves only the photo layer;** text sits on the fixed layer. Entrance scale ≤ 1.15, slide ≤ 46 px.
- **≥ 55% of the frame is filled** at all times; no empty stretch > 1.5 s (`audit.py` warns).
- **AI is illustration, never evidence.** Maps, charts, documents and real people come from the engine
  or real sourced photos. No Bangla text inside AI images. COLLAGE ≤ 40% in MIX, never > 3 in a row.
- **Every image has a row in `licences.csv`.** On a monetised project, everything must be `commercial=yes`
  (`audit.py` fails otherwise).
- **Fonts:** Noto Sans/Serif Bengali (run `font_test.py` and LOOK at the result). Never Hind Siliguri for numerals.
- **Numbers:** Bangla digits on screen; numbers written as words in the TTS script.
- **Voice:** the same voice, model and settings for every clip. Neutral delivery for facts; emotion only at 2–3 peaks.
- **Sound:** music beneath the VO (ducked), SFX on visual hits, master −14.5 LUFS / ≤ −1.5 dBTP, silent last 0.25 s.
- **Review:** look at every contact sheet before render. Re-render only changed ranges (`render_range.py`).
- **Reuse, don't rebuild:** start from the scene templates; add a new scene type back to the repo once it proves useful.
- **Keep context lean:** read contact sheets and reports, not raw JSON or hundreds of frames.
