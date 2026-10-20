# How others make explainer videos with Claude (research, Oct 2026)

## Landscape
- **Code-driven video is the dominant Claude workflow.** Claude writes HTML/React/Python that renders deterministically to frames, then ffmpeg encodes.
  - **Remotion** (React) + official `remotion-dev/skills`: compositions with `<Sequence>`, `interpolate()`, `spring()`; render via `npx remotion render`. Check Remotion's licence for commercial use.
  - **HyperFrames** (HeyGen, Apache-2.0): HTML + seekable animation (GSAP/CSS/Lottie) → headless Chrome frame capture → MP4; deterministic “same input, same frames”; skills like `/faceless-explainer`, catalog blocks for charts/captions/transitions. Same architecture as this engine.
  - **Manim** (3Blue1Brown-style math/technical) and **Motion Canvas** skills for diagrams.
  - **Claude Motion** (Anthropic beta, 8 Oct 2026): animated explainers from text/diagrams/images, editable as code, MP4 export; Team/Enterprise only; no audio.
- Curated index: `awesome-claude-video-skills` (180+ repos) — explainers, shorts, motion graphics, editing.

## Patterns the best pipelines share
1. **Script/beat map first** → storyboard → assets → voice → timing → visuals → captions/sound → render → QA.
2. **Human gates**: approve beat map; pick a style from a 3–4-theme bake-off (vox-director).
3. **Word-level sync**: TTS then ASR/forced alignment (faster-whisper, FireRedASR) so each motion beat anchors to an exact word (video-talkcraft: 20–40 ms median deviation).
4. **Automated QA**: stillness detection, SFX energy checks, frame triplets at animation anchors, loudness normalisation; loop render→review until pass.
5. **Design-language files**: per-screen element budgets, whitespace anchors, safe areas measured by code, not by eye.
6. **Vox-style collage** (vox-director): torn paper, cut-outs, tape, halftone, newspaper clippings, flat colour per beat, big cut-out headlines; “the look is born in the keyframe — downstream steps can't fix a weak poster”.
7. **Templates for repeatability**: the payoff is re-rendering saved compositions with new data/stories, not the first render.

## Common pitfalls reported
- Vague prompts (“make it longer”) instead of exact timings; mismatched durations; everything animating at frame 0.
- Linear, uneased motion looks mechanical.
- Render time underestimated (every frame is a browser screenshot).
- Generic output when brand/context isn't given.

## What this engine adopts
Script-first gates · style frames before full build · VO-anchored timing · layer-split camera · automated bounds/density QA · contact-sheet review · per-range re-render · original synthesised music/SFX · loudness mastering.
Planned upgrades: word-level timestamps via Scribe STT (Bengali supported) · burned karaoke captions option · stillness detector · 4:5 feed export.

## B. Vox / Johnny Harris-style pipelines with AI (second research round, Oct 2026)
Nine tutorials and one shared "engine" prompt showed three approaches: (1) a prompt engine that turns
script → 4-second beats → AI image prompts → image-to-video (Google Flow) → manual edit; (2) Claude Code +
Remotion, where every graphic is code; (3) fully automated API pipelines that pay per clip.

What we adopted:
- **Beat types route the work.** About half of a Vox video is information graphics (maps, charts,
  documents, timelines, quotes), and AI video is bad at those (garbled text, wrong geography). Build those in
  the engine; use AI only for atmospheric COLLAGE beats → `ai-visuals.md`.
- **Source ledger** with a central question, confidence levels, counterpoints, and fact numbers mapped to
  every scripted line → `templates/fact-sheet.md`.
- **Four creator gates** that hold even in "do it all" mode: facts, script/beats, preview, final QA.
- **Long-form spine:** question → stakes → mechanism → evidence → counterpoint → payoff, in chapters → `storytelling.md`.
- **Cold open, why/so-what lines, five ending patterns, and a creator note** for human perspective.
- **Final QA:** sound off and screen off, plus facts, rights and AI honesty → `qa-checklist.md`.
- **Licence ledger** for every asset; flags for non-commercial sources (Google Earth Studio, CapCut free,
  ElevenLabs free) → `licences.csv`, checked by `audit.py`.
- **Style lock for AI images:** a verbatim style block and closer, the recurring-subject law, a style
  reference image, and representation rules for real people and children.
- **Credit budget** before spending (Flow ≈ 20 credits per Fast clip, 1,000 a month on Google AI Pro).
- **Stop-motion "on twos" cadence** and a subtle shake → `data-twos`, `data-shake`.
- **Publish pack:** 3 titles ≤ 60 characters, a description with sources, chapters, and a thumbnail that reads at 200 px.
- **Pilot first:** one 60-second video before scaling; log the time and credits.

What we didn't adopt: switching to Remotion (this engine already does the same job, deterministically, with
audio). Kept as an option if a team needs React components; free for individuals and companies of up to 3
people.

Sources (round B):
- Mark Ai Guy, Vox style animation 100% free: https://www.youtube.com/watch?v=_TTaaIocYq4
- Mark Ai Guy, Vox style with Opus 5.5 + Higgsfield: https://www.youtube.com/watch?v=WoNgl4qpogk
- Mapal, How to make Vox style videos (After Effects): https://www.youtube.com/watch?v=F7A503llNBA
- MoSidd, Vox-style motion graphics with Claude Code & Remotion: https://www.youtube.com/watch?v=7wuYBfE131U
- Jacksons AI, Claude prompt for Vox style videos: https://www.youtube.com/watch?v=RaxX_Q7Apj0
- Koen, 100% automated Vox-style motion graphics: https://www.youtube.com/watch?v=TiycelzfzC0
- Rachit Singh, Vox style documentary with one prompt: https://www.youtube.com/watch?v=L7vi4PNTZ8E
- RandomAI, Vox-style motion graphics with Opus 5.5 & Remotion: https://www.youtube.com/watch?v=uIHJvUVaB34
- Remotion licence: https://www.remotion.dev/docs/pricing
- Gemini TTS (Bangla listed for gemini-3.8-flash-tts): https://ai.google.dev/gemini-api/docs/speech-generation
- Google Veo / Flow credits: https://diyai.io/ai-tools/video-generation/google-veo-pricing/
- YouTube inauthentic content: https://www.creatorhandbook.net/youtube-updates-monetization-policy-for-inauthentic-content/
- Google Earth Studio terms: https://geoawesomeness.com/google-earth-studio-create-geospatial-animations-zero-experience/

## Sources
- OpenReplay — Making Videos with Claude Code and Remotion: https://blog.openreplay.com/making-videos-claude-code-remotion/
- awesome-claude-video-skills: https://github.com/zhuyansen/awesome-claude-video-skills
- HyperFrames: https://github.com/heygen-com/hyperframes
- vox-director: https://github.com/Alisa0808/vox-director
- video-talkcraft: https://github.com/Vincentwei1021/video-talkcraft
- The Decoder — Claude Motion & Dashboards: https://the-decoder.com/claude-can-now-generate-animated-explainer-videos-and-live-data-dashboards-from-text-prompts/
- Brave Brand — animated explainers with Claude: https://www.bravebrand.com/learn/brave-ai-systems/how-to-make-animated-explainer-videos-with-claude
- Yans Media — explainer hook techniques: https://www.yansmedia.com/blog/explainer-video-hook-techniques
- ElevenLabs forced alignment docs: https://elevenlabs.io/docs/overview/capabilities/forced-alignment.md
