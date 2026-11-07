---
name: video-render
description: Final audio master, full-resolution render, verification, cover and delivery package for an explainer video. Use when the preview is approved, or the user asks to render, export, finalize, or deliver/send the video.
---

# Finish (v0.10) — same chat as Build, Mac shell only, cover baked right away

Runs straight after "go ahead" in the Build chat (keep the claim; no new chat). Every command:
`cd "$HOME/mnt/VIDEO GEN" && bash _series/es.sh <tool> …` with `device_bash`. Follow the FINISH card from `studio next videoNN`.

1. **Cover** — `cover_series … --render` → COVER PASS; look at `out/_cover_A_sheet.jpg` once. Do NOT wait for an OK:
   it is baked right away; the creator may ask for another afterwards (then cover_series again + the same finish command).
   Layout rules: full-bleed real photo, chip, one white line, one bright question block (one line, ≥ 140 px; too-wide blocks move
   their first words into the line automatically), no answer, no dark base.
2. **publish.txt** — same layout as the previous episode's `out/publish.txt`; title ≤ 45 chars, a question, no answer;
   description 3 short lines + follow line + sources, no figures; 3 YouTube hashtags + Facebook set; pinned comment holds the
   answer and the single-source notes; photo credits without placeholders.
3. **`finish videoNN --local --slug <Slug> --who '<claim label>'`** — renders (resumable; run the same command again while it
   prints RESUME), checks loudness/AV, bakes the cover (frame 1, thumbnail, 1.6 s opening), lints publish.txt, sets state,
   tidies, regenerates the tracker, updates titles_descriptions.md and releases the claim. Only DONE means delivered.
   If script/facts changed during Build it re-runs script_check itself (a FAIL there is the only stop).
4. `studio check videoNN --stage final` → STUDIO PASS; `studio close videoNN delivered --note '<caveat>'`.
5. Stage + send the reel and cover; report with the 'delivered' template (it names the baked cover).

Refused deletes in the Mac folder are moved to `VIDEO GEN/_to_delete/_trash/` automatically; tell the creator to empty `_to_delete/`.
Old cloud technique (pack/guard pushes, --verify): `docs/legacy-cloud-finish.md` — only if a step needs it.
