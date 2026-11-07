---
name: explainer-video
description: Master rules for making explainer / documentary-style short videos (Facebook Reels, YouTube Shorts, TikTok), especially Bangla ones. Use whenever the user asks to make, plan, script, animate, voice, fix or render an explainer video, a "Vox-style" video, an infographic video, or a বাংলা ভিডিও / এক্সপ্লেইনার. Always start with studio.py next.
---

# Explainer Studio — conductor (v0.10)

You direct, research, write, design, animate and QA. The creator reviews scripts and videos himself; you make the process
identical in every chat, brief, and error-free. Perfection is not the goal: finished, consistent episodes are.

## First action of EVERY chat (no exceptions)
- **Build / Finish** (Mac shell, `device_bash`): `cd "$HOME/mnt/VIDEO GEN" && bash _series/es.sh studio next videoNN`
- **Plan** (cloud): `python3 engine/tools/studio.py next videoNN` (copy `engine/` from the plugin first if needed)

It prints the stage, who is waiting, the **step card** (exact commands), for Build the build.json cheat sheet, the rules and
the report templates. **That output is the whole instruction: do not improvise steps, skip a numbered step, or run a stage the
creator did not ask for.** Besides it read only `claude/series-rules.md` and the project preferences. Do NOT read the tracker,
build plans, old notes, `series-brief.md`, old chats, engine/tool source code or the other skills unless a step fails.

## The flow (what the creator experiences)
1. **Titles in** (a batch of 6–9 is normal) → Plan chat: research → script → `script_check` PASS → he reviews the script.
2. On OK → ONE message with the VO paste text + the image list (REAL vs AI) → folders prepared → "videoNN ready".
3. He drops images + the single VO take → chat "Build episode NN" → preview.
4. "go ahead" → same chat: cover (baked right away) → render → bake → publish text → deliver. He never tracks anything by hand.

## Look and sound are assigned, not chosen
- `studio look` gives the episode's Vox / Johnny Harris palette; `build_scenes` takes every colour from it. `studio music` sets the
  music preset; sound effects are automatic. Never swap music, silence effects or pick colours by hand (`studio check` fails).
- Typeface is always Tiro Bangla (preset `vox-money`).

## Reporting (the creator's time is the budget)
Use the report templates printed by `next`, nothing more: one line PASS/FAIL, then only what needs his decision. No list of passed
checks, no recap of approved items, no options he did not ask for. Add "time cut: …" only when a real saving exists.

## Safety mechanics
- **Claim before you touch** (Build): `bash _series/es.sh guard claim videoNN --who "Build epNN <time>"`; REFUSED = another chat
  holds it: stop and tell the creator. The Finish keeps the same claim; `finish --local` releases it.
- **One copy**: Build and Finish work on the Mac folder itself. Nothing is pushed back, so nothing can be overwritten.
- **The tracker is generated** (`series_tracker`, run by `finish --local` / `studio close`). Never edit `episode-tracker.md` by hand.
- **No number reaches the voice unverified**: `script_check.py` runs the facts gate (video-script §1).
- **Only DONE from `finish --local` means delivered.**
- Plugin or engine changes are made in a separate chat, never inside an episode chat. After a plugin update the Mac kit is refreshed
  with `engine/tools/mac/make_kit.sh` (the Build card's step 0 says when).

## Kit location
Plugin root = two folders above this file: `engine/` (runtime, scene templates, `tools/`, `studio/` = rules.json, palettes,
music bank, cheatsheet.md, `tools/mac/` = es.sh + make_kit.sh), `docs/`, `templates/`. On the Mac: `VIDEO GEN/_series/es.sh` +
`_series/mac_render/engine_kit_v*.tar` (+ the Chromium pack). Keep usage low: one image look per check, grep a line instead of
printing files, re-render only what changed.
