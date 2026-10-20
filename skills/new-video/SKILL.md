---
name: new-video
description: Start a new explainer video project and collect everything needed from the creator up front. Use when the user says "new video", "make a video about…", "start an explainer", "নতুন ভিডিও", or gives a topic for a video without a brief yet.
---

# New video — intake and brief

Goal: one short round of questions, then a filled `brief.md` the creator approves. Ask only what you
cannot infer; never ask about things the engine decides (layout, animation, SFX timing).

## 1. Read
`../../docs/PLAYBOOK.md` §1 (roles) and §11 (getting started), and `../../templates/brief.md`.

## 2. Fill in what you already know
From the request and the conversation: topic, angle, language, platform, tone. Run a quick web search to
scope the topic (2–4 searches) so your questions are informed (e.g. "two sources disagree on the date").
Open every link or file the creator gave. List any that wouldn't open and ask for the text.

## 3. Ask about the gaps in ONE AskUserQuestion call (max 4 questions; skip any already answered)
Priority order:
1. **Central question and takeaway:** the question the video answers and the one sentence viewers should
   remember. Offer 2–3 angles you found.
2. **Format and platform:** Short 9:16 (Facebook Reels ≤ 90 s, recommended for Bangladesh; Shorts ≤ 2:59) ·
   Long 16:9 YouTube (chapters of 45–90 s) · both.
3. **Voice:** own recording (best for monetisation) · ElevenLabs (paid plan? the free tier blocks generation
   and has no commercial licence) · Gemini TTS (free; lists Bangla) · text only. Character: Dhaka-standard,
   male or female.
4. **Look and sound:** VOX (paper collage, vox-paper) · HARRIS (maps and archival photos, dark-doc) · MIX;
   music bangla-folk or cinematic. Mention whether AI illustrations are allowed for symbolic beats.

Then, in plain text, ask two quick yes/no questions (the creator can answer in one line):
- **Monetised?** If yes, every asset needs a commercial-use licence.
- **First video?** If yes, suggest a 60-second pilot first.

Also list what they should drop into `photos/`: 20–40 images for 2–3 minutes, including a hero photo, with
the source and licence for each if known. Add brand items (handle, end card, CTA) and any sources, notes or
transcripts to use. Photos from the creator save the most time and credits; scraping is the last resort
(small batches through the browser pane, never hammering a site).

## 4. Create the project
```bash
python3 engine/tools/new_project.py <slug> --title "<title>" --aspect 9:16 --preset vox-paper --palette bangla [--monetized]
```
For 16:9 use `--aspect 16:9`. For both, create `<slug>-916` and `<slug>-169`; the second reuses the first
one's `vo/raw/` and `photos/`. Write the answers into `<slug>/brief.md` and copy the creator's photos into
`<slug>/photos/`.

## 5. Gate
Send the brief as a short summary: central question, takeaway, angle, audience, format and aspect, voice,
look, whether it's monetised, and what's missing. Say what is still cheap to change. Wait for approval,
then hand off to `video-script`.
