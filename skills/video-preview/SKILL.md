---
name: video-preview
description: Build the animated explainer from an approved script and VO — split the take, assets, style frames, scenes, QA audit, key-moment review and a low-res preview. Use when the user asks to build, design, animate, lay out, preview, fix a scene, or when text is cut off, empty space, wrong font, or timing issues are reported.
---

# Build (v0.10) — Mac shell only, scenes from build.json

Everything runs with `device_bash` in the VIDEO GEN folder: `cd "$HOME/mnt/VIDEO GEN" && bash _series/es.sh <tool> …`.
The episode is never copied to the cloud (no pack, pull, push, fingerprint). The only cloud steps: looking at an image
(`device_stage_files` → Read) and sending the preview (`device_stage_files` → SendUserFile).

1. `bash _series/es.sh studio next videoNN` prints the card, the build.json cheat sheet, the rules and the report templates.
   **That output is the whole instruction.** Do not open engine.js/engine.css, tool sources, the tracker, the build plan,
   old notes or other skills. `bash _series/es.sh studio words videoNN` gives the spoken words, photos and theme rows.
2. Write `videoNN/build.json` in one heredoc; `build_scenes` makes index.html. Fix problems in build.json with small patches
   and re-run `build_scenes` + `audit`. Never hand-write or hand-patch index.html (the `html`/`css` keys cover motif objects).
3. Look at images at most three times: the photo sheet, `out/keys_one.jpg`, and later the cover sheet.
4. VO cuts: `vo_split` writes best-estimate clips by itself when the take has no clear pauses; never ask for a new take.
5. Report with the 'preview' template only. On "go ahead" go straight on with the Finish card (video-render) in this chat.

If `bash _series/es.sh version` differs from this plugin's version: in the cloud run `bash <plugin>/engine/tools/mac/make_kit.sh`,
commit the two files it names into `_series/mac_render/` and `_series/es.sh`, and move the older kit to `_to_delete/`.
Old cloud technique (pull/push, hand-built HTML): `docs/legacy-cloud-build.md` — only if a step needs it.
