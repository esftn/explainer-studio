---
name: explainer-video
description: Master rules for making explainer / documentary-style short videos (Facebook Reels, YouTube Shorts, TikTok), especially Bangla ones. Use whenever the user asks to make, plan, script, animate, voice, fix or render an explainer video, a "Vox-style" video, an infographic video, or a বাংলা ভিডিও / এক্সপ্লেইনার. Always start with studio.py next.
---

# Explainer Studio — conductor (v0.7)

You direct, research, write, design, animate and QA. The creator reviews scripts and videos himself; you make the process
identical in every chat, brief, and error-free. Perfection is not the goal: finished, consistent episodes are.

## First action of EVERY chat (no exceptions)
```bash
python3 engine/tools/studio.py next videoNN      # or on the Mac: python3 _series/tools/studio.py next videoNN
```
It prints this episode's stage, who is waiting, the **step card** to follow (numbered, with the exact commands), the creator's rules
and the report templates to use. **The card is the order of work. Do not improvise steps, skip a numbered step, or run a stage the
creator did not ask for.** With no episode it prints the series status.
Do NOT read `series-brief.md` or old chats at the start: the brief is an archive. Fetch only the section a card step needs
(Plan: "Shared figures"; Finish: "Cover log") with `project_search`.

## The flow (what the creator experiences)
1. **Titles in** (one or several; a batch of 6–9 is normal) → Plan: research → script → `script_check` PASS → he reviews the script.
2. On OK → ONE message with the VO paste text + the image list (REAL vs AI) → folders prepared (`studio.py new`: project, Vox-style
   palette, music preset) → "videoNN ready".
3. He drops images + the single VO take → new chat "Build episode NN" → preview (style frames and preview approved together).
4. "go ahead" → two covers → he picks → render, captions, publish text, bake, tidy, deliver → `studio.py close … delivered`
   writes the status document. He never tracks anything by hand.

## Look and sound are assigned, not chosen
- `studio.py look` gives the episode's Vox / Johnny Harris palette (rotated, 12 palettes from eps 1–5, contrast-checked themes). Build only from
  `docs/look.md`. `studio.py music` sets one of 5 original music presets (rotated by episode number). Sound effects are automatic
  (engine proposes them from the animations, `audio.py` thins them). Never swap the music, silence effects or pick colours by hand:
  `studio.py check --stage build` fails if you did.
- Typeface is always Tiro Bangla (preset `vox-money`).

## Reporting (the creator's time is the budget)
Use the report templates printed by `next`, nothing more: one line PASS/FAIL, then only what needs his decision. No list of passed
checks, no recap of approved items, no options he did not ask for. Add "time cut: …" only when a real saving exists.

## Safety mechanics kept from v0.6 (they prevent overwrites)
- **Claim before you touch** (Build/Finish): on the Mac `python3 _series/tools/guard.py claim videoNN --who "<Build|Finish> epNN <time>"`;
  REFUSED = another chat holds it: stop and tell the creator. After the pull in the cloud: `guard.py base videoNN`.
- **Never push over a changed Mac copy**: `guard.py fingerprint` on the Mac, then `pack.py pack … --guard mac_fp.json --who "…"`.
  Never `--force` without the creator's decision.
- **The tracker is generated** (`series_tracker.py`, run by `studio.py close … delivered`). Never edit `episode-tracker.md` by hand.
- **No number reaches the voice unverified**: `script_check.py` runs the facts gate (video-script §1).
- **Finish is one command**, `finish.py`; never report "delivered" before `finish.py --verify` printed DONE on the Mac.
- Mac tools live in `VIDEO GEN/_series/tools/` (copy `studio.py` + `rules.json` + the other seven files there after a plugin update; not into
  a `.studio/` another chat is using).
- Plugin or engine changes are made in a separate chat, never inside an episode chat.

## Kit location
Plugin root = two folders above this file: `docs/` (PLAYBOOK, design-system, audio), `templates/`, `engine/` (runtime, scene templates,
`tools/`, `studio/` = rules.json, palettes.json, music_bank.json). Copy `engine/` to the working directory if the plugin folder is
read-only; `bash engine/tools/setup.sh` once per session (`WITH_CUTOUTS=0` unless a cutout is needed).
Keep usage low: standard web search; grep a line instead of printing index.html; look at images only when needed; re-render only what changed.
