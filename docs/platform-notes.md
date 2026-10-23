# Platform & Environment Notes (Claude cloud workspace)

- **Network allowlist**: the workspace (and a linked computer's shell) can usually reach only package registries and GitHub. Wikimedia, news sites, ElevenLabs storage etc. are blocked unless allowed in claude.ai **Settings → Capabilities**. Ask the creator to drop photos into `photos/` instead of scraping.
- **Built-in browser pane** (on the creator's computer) can reach sites; its downloads land in the creator's Downloads folder (sometimes as hidden temp files while in progress). Use small batches; long `fetch` loops time out at ~45 s per call.
- **ElevenLabs MCP**: generations return signed URLs that expire in ~2 h; the storage host blocks cross-origin fetch, so download by opening the first URL in the browser pane and fetching the rest from that origin. Free tier can be disabled for "unusual activity" (bursts, VPN) — use a paid plan and 1–3 long takes.
- **Freepik MCP**: images, background removal, TTS (different voice catalogue), music/SFX generation — a backup provider.
- **Transfers to the creator's computer**: ≤ 30 MB per file. Split large files into ≤ 14 MB parts; gzip the first part of an MP4 (its header can be altered in transit); rejoin with `cat` and verify md5.
- **Compute**: 2 CPUs; full-res Playwright render ≈ 1 frame / 0.2–0.25 s per worker → ~9–10 min per worker for 2,650 frames. Use `render_range.py` to re-render only changed scenes.
- **Context hygiene**: big tool outputs (e.g. ElevenLabs status ~70 KB) get saved to files — parse with python/jq, don't read whole.
- **Claude Motion** (Anthropic, beta, Oct 2026): code-driven animated explainers with MP4 export, Team/Enterprise only, visuals without audio — an alternative front-end when available; this engine covers VO + music + SFX end to end.
