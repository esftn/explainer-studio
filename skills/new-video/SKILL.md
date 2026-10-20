---
name: new-video
description: Start a new explainer video project and collect everything needed from the creator up front. Use when the user says "new video", "make a video about…", "start an explainer", "নতুন ভিডিও", or gives a topic for a video without a brief yet.
---

# New video — intake and brief

Goal: one short round of questions, then a filled `brief.md` the creator approves. Ask only what you
cannot infer; never ask about things the engine decides (layout, animation, SFX timing).

## 1. Read
`../../docs/PLAYBOOK.md` §1 (roles) and `../../templates/brief.md`.

## 2. Fill what you already know
From the request and conversation: topic, angle, language, platform, tone. Do a quick web search to
scope the topic (2–4 searches) so your questions are informed (e.g. "two sources disagree on the date").

## 3. Ask the gaps in ONE AskUserQuestion call (max 4 questions; skip any already answered)
Priority order:
1. **Takeaway & angle** — the one sentence viewers should remember; offer 2–3 angles you found.
2. **Platform & length** — Facebook Reels ≤90 s (recommended for Bangladesh), Shorts ≤2:59, both.
3. **Voice** — AI voice (which provider is connected? paid plan? — ElevenLabs free tier blocks
   generation) / own recording / text-only; voice character (Dhaka-standard male/female).
4. **Look & sound** — vox-paper (editorial collage) / dark-doc; music bangla-folk / cinematic.
Then in plain text, list what they should drop in `photos/` (20–40 images for 2–3 min, hero photo,
credits/licences if known) and brand items (handle, end card, CTA). Photos from the creator save the most
time and credits — scraping is the last resort (small batches, browser pane, never hammer a site).

## 4. Create the project
```bash
python3 engine/tools/new_project.py <slug> --title "<title>" --preset vox-paper --palette bangla
```
Write the answers into `<slug>/brief.md`. Copy the creator's photos into `<slug>/photos/`.

## 5. Gate
Send the brief as a short summary (takeaway, angle, audience, platform/length, voice, look, what's
missing). Say what is cheap to change now. Wait for approval, then hand off to `video-script`.
