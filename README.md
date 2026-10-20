# Explainer Studio

Make industry-grade, Vox-style explainer shorts with Claude, Bangla first: brief → research → script →
voiceover → HTML animation (9:16 reels or 16:9 YouTube) → original music and SFX → a render gated by QA →
thumbnail and publish pack.

It is **two things in one repo**:
1. **A Claude plugin.** Five skills that walk Claude through every phase and stop at the right approval gates.
2. **An engine.** A deterministic HTML-to-video runtime plus Python tools for VO timing, music and SFX
   synthesis, QA, rendering and delivery checks.

## The pipeline

| Phase | Skill | What you approve | Tools |
|---|---|---|---|
| 0 Intake | `new-video` | brief (takeaway, angle, platform, voice, look) | `new_project.py` |
| 1–2 Research and script | `video-script` | **Gate 1** source ledger · **Gate 2** script + beat table + budget · the VO | `vo_prep.py` |
| 3–6 Build | `video-preview` | 3 style frames, then a half-size preview | `prep_photos.py` `font_test.py` `audit.py` `review.py` `audio.py` `render.py --preview` |
| 7 Final | `video-render` | **Gate 4**: sound-off, screen-off, facts, rights (you tick before publishing) | `audio.py` `render.py` `check_final.py` `make_srt.py` `thumbnail.py` `publish.py` `split_deliver.py` |

The rule behind the order: **approve cheap things before building expensive things.** `render.py` won't run
unless `audit.py` passed on the exact current timeline. The audit checks text inside the frame every 0.1 s,
missing images and fonts, VO coverage, visual density, source bands, the beat mix, and a licence row for
every image (monetised projects need `commercial=yes` on all of them).

AI images are illustration only (atmospheric COLLAGE beats). Maps, charts, documents and real people are
built by the engine or come from real sourced photos. See `docs/ai-visuals.md`.

## Install the plugin
- **Claude app:** open `explainer-studio.plugin` in a chat and accept it.
- **Claude Code:** `/plugin marketplace add esftn/explainer-studio`, then
  `/plugin install explainer-studio --marketplace esftn/explainer-studio`. Or copy `skills/` into `.claude/skills/`.

Then just ask: *“নতুন ভিডিও: … নিয়ে ৯০ সেকেন্ডের রিল বানাও”* or *“make an explainer about …”*.

## Engine setup (once per machine or session)
```bash
bash engine/tools/setup.sh      # ffmpeg + node required; installs playwright, numpy/scipy, rembg, Noto Bengali fonts
```

## Smoke test
```bash
python3 engine/tools/new_project.py /tmp/smoke --title "পরীক্ষা"
# add 2+ VO takes to /tmp/smoke/vo/raw/vo_01.mp3, vo_02.mp3 and a photo to /tmp/smoke/photos/
python3 engine/tools/vo_prep.py /tmp/smoke && python3 engine/tools/prep_photos.py /tmp/smoke
cp /tmp/smoke/img/p_01.jpg /tmp/smoke/img/hero.jpg
python3 engine/tools/audit.py /tmp/smoke && python3 engine/tools/audio.py /tmp/smoke
python3 engine/tools/render.py /tmp/smoke --name smoke && python3 engine/tools/check_final.py /tmp/smoke
```
For 16:9 add `--aspect 16:9` to `new_project.py`; after rendering also run `thumbnail.py` and `publish.py`.

Last verified on 2026-10-21 (v0.2.0):
- **16:9:** 7 scenes, 63 s, render 233 s on 3 workers. It came out at 1920×1080 with −14.6 LUFS and
  −1.4 dBTP, and the thumbnail and publish checks passed.
- **9:16:** a 4-scene, 37 s project passed QA, and its preview came out at 540×960.
- **Earlier (v0.1.0, 2026-10-19):** an 11-scene, 112 s project.

## What's inside
```
.claude-plugin/plugin.json   plugin manifest
skills/                      explainer-video (master rules) · new-video · video-script · video-preview · video-render
docs/                        PLAYBOOK · storytelling · bangla-localisation · design-system · ai-visuals · audio ·
                             qa-checklist · platform-notes · industry-research (with sources) · lessons-learned
templates/                   brief.md · fact-sheet.md (source ledger) · script.md (beat table) · licences.csv
engine/template/             engine.js (timeline, camera, animations, twos/shake, AUDIT, DENSITY) · engine.css ·
                             presets/ (vox-paper, dark-doc) · scenes/ (14 templates, 9:16) · scenes16/ (7, 16:9) ·
                             index16.html · thumbnail.html
engine/tools/                setup · new_project · font_test · paper · prep_photos · vo_prep · audio (bangla/cinematic
                             palettes) · audit · review · render · render_range · check_final · make_srt ·
                             thumbnail · publish · split_deliver
examples/hadi-ke/            the first video's script and reference scene file
```

## Scene authoring in 30 seconds
```html
<section class="scene" data-vo="3" data-type="PHOTO" data-mood="build" data-cam="0:1.08:0:0|7:1:-20:0">
  <div class="bgp"></div>
  <div class="cam">
    <div class="a ph ht sh" style="left:80px;top:300px;width:920px;height:700px" data-a="fade" data-t="0"><img src="img/p_04.jpg"></div>
    <div class="a h2" style="left:70px;top:1100px;width:940px" data-a="up" data-at="a0">১৯৯৩ সালে <span class="mk" data-a="mark" data-at="a1">ঝালকাঠিতে</span></div>
  </div>
  <div class="tag">০৩ শিকড়</div>
  <div class="src">সূত্র: প্রথম আলো, ২০২৫</div>
</section>
```
Photos (anything with an `<img>`) move with the camera. Text goes on a fixed layer automatically, so a zoom
can never crop it. `data-at="a1"` lands the highlight on the VO's first pause. The scene's length comes from
its VO clip.

## License
MIT for code and docs. Fonts are under SIL OFL (installed by `setup.sh`, not committed). Bring your own
licensed photos.
