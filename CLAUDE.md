# Explainer Studio: notes for Claude

This repo is both a Claude plugin (`.claude-plugin/`, `skills/`) and the engine it drives (`engine/`).
- Start with `skills/explainer-video/SKILL.md` (every chat begins with `python3 engine/tools/studio.py next`), then `docs/PLAYBOOK.md`.
- Make video projects **outside** this repo, using `python3 engine/tools/new_project.py <folder> ...`.
- Engine changes: edit `engine/template/*`. Existing projects keep their own copy in `<project>/engine/`.
  After any engine change, run the smoke test from the README before committing.
- Never commit media, fonts (`node_modules/`), VO, or photos you have no licence for.
