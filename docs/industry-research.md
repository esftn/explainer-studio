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
