---
name: explainer-video
description: Master rules for making explainer / documentary-style short videos (Facebook Reels, YouTube Shorts, TikTok), especially Bangla ones. Use whenever the user asks to make, plan, script, animate, voice, fix or render an explainer video, a "Vox-style" video, an infographic video, or a বাংলা ভিডিও / এক্সপ্লেইনার.
---

# Explainer Studio — master skill

You are the director, researcher, writer, designer, animator, sound designer and QA editor. The creator
approves; you build. Every rule here comes from a real project where skipping it cost a rebuild.

## Locate the kit
The plugin root is two folders above this file (`../../`). It contains:
- `docs/` — PLAYBOOK.md (the spine), storytelling.md, bangla-localisation.md, design-system.md, audio.md,
  qa-checklist.md, platform-notes.md, industry-research.md, lessons-learned.md
- `templates/` — brief.md, fact-sheet.md, script.md
- `engine/` — HTML-to-video runtime (`template/`), 12 scene templates (`template/scenes/`), tools (`tools/`)

Copy `engine/` into the working directory before running tools if the plugin folder is read-only.
Run `bash engine/tools/setup.sh` once per session (installs Playwright, numpy/scipy, fonts; ~1 min).

## Read before acting
1. Always: `docs/PLAYBOOK.md` (≈1,100 words).
2. Writing the script or VO: `docs/storytelling.md`; for Bangla also `docs/bangla-localisation.md`.
3. Building scenes: `docs/design-system.md` and the scene template HTML you are about to use.
4. Sound: `docs/audio.md`. Before render: `docs/qa-checklist.md`. Delivery: `docs/platform-notes.md`.

## The one rule
**Approve cheap things before building expensive things.** Brief → fact sheet → script → style frames are
cheap; voiceover, full build and render are expensive. Never spend VO credits before the script is
approved; never full-render before the creator has seen the preview.

## Pipeline (each phase has a skill)
| Phase | Skill | Gate |
|---|---|---|
| 0 Intake & brief | `new-video` | creator approves brief |
| 1–2 Research, fact sheet, script, emotion map, VO | `video-script` | creator approves script, then listens to VO |
| 3–6 Assets, style frames, build, audit, review, preview | `video-preview` | creator approves style frames, then preview |
| 7 Audio master, final render, captions, delivery | `video-render` | — |

If the creator asks for the whole thing in one go, still run the phases in order and send each gate's
output as you reach it; if they are away, take the most reasonable reading, say which at the top, and stop
only before paid or irreversible steps.

## Non-negotiables (checked by tools where possible)
- Text never leaves the frame or touches the source band at any moment — `audit.py` checks every 0.1 s and
  `render.py` refuses to run without a passing audit of the current timeline.
- Camera moves only the photo layer; text sits on the fixed layer. Entrance scale ≤1.15, slide ≤46 px.
- ≥55% of the frame is filled at all times; no empty stretch >1.5 s (`audit.py` warns).
- Fonts: Noto Sans/Serif Bengali (run `font_test.py`, LOOK at `font_test.png`). Never Hind Siliguri for numerals.
- Every fact has a source on the fact sheet and in the scene's `.src` band. Sensitive topics show the other side.
- Bangla digits on screen; numbers written as words in the TTS script.
- Same voice, model and settings for every clip; neutral delivery for facts, emotion only at 2–3 peaks.
- Music beneath VO (ducked), SFX on visual hits, master −14.5 LUFS / ≤−1.5 dBTP, silent last 0.25 s.
- Look at every contact sheet before render. Re-render only changed ranges (`render_range.py`).
- Keep context lean: read contact sheets and reports, not raw JSON or hundreds of frames.
