# Explainer Studio

Make Vox / Johnny Harris-style explainer shorts with Claude, Bangla first (Facebook Reels, YouTube Shorts, TikTok):
title → research → script → voiceover → HTML animation → original music and sound effects → QA-gated render → cover → delivery.
Built for the series **বাংলা অর্থনীতি রিলস** (24+ episodes) and for making 6–9 videos in one sitting with the same steps every time.

**Current version: 0.7.2** — see [CHANGELOG.md](CHANGELOG.md) and [docs/CHANGES-v0.7.md](docs/CHANGES-v0.7.md).

It is **two things in one repo**:
1. **A Claude plugin** — five skills plus a "front door" tool (`studio.py`) that tells Claude the exact steps for the episode's stage.
2. **An engine** — a deterministic HTML-to-video runtime and Python tools for VO timing, music and SFX synthesis, QA, rendering and delivery.

## How a video gets made

| Chat | You do | Claude does | Checked by |
|---|---|---|---|
| **1 · Plan** (1–3 episodes) | give a title | research, facts with sources, script; then the VO text + image list in one message; prepares the folders | `script_check.py` (facts gate) · `state.py` |
| | approve the script, record one VO take, drop the images | | |
| **2 · Build** (per episode) | watch the preview, send notes | split VO, build scenes, auto sound effects, rotating music, audit, preview | `audit.py` · `review.py --keys` · `studio.py check` |
| **3 · Finish** (1–3 episodes) | pick cover A or B | two hand-designed covers, final render, captions (bn + en), `publish.txt`, bake cover, pack, tidy, status | `cover_check.py` · `finish.py` · `finish.py --verify` on the Mac |

Every chat starts with **`python3 engine/tools/studio.py next videoNN`**: it prints the step card for the episode's stage, the creator's rules
and the short report templates. All rules live in one file, `engine/studio/rules.json`. Reports to the creator are a few lines.

### studio.py
| Command | What it does |
|---|---|
| `studio.py next [videoNN]` | step card + rules + report templates (no argument = series status) |
| `studio.py new videoNN --title … --ep NN` | project + palette + music preset in one step |
| `studio.py look / music videoNN` | show or (re)assign the palette (`docs/look.md`) / music preset |
| `studio.py check videoNN --stage build\|final` | typeface preset, palette colours, music unchanged, sound effects present, `data-mood`, ending hold, finals-only `out/` |
| `studio.py status [--write]` | every episode: stage, who is waiting, length, look, music → `_series/STATUS.md` |
| `studio.py close videoNN STAGE` | last command of every chat: state + status document (+ tracker when delivered) |

## Look, sound, text, covers
- **Palettes:** 12 calm palettes taken from episodes 1–5 (mustard paper, vermilion and kraft, risograph indigo, berry and mint, concrete and orange, …),
  each with contrast-checked scene themes. Rotated by episode number, skipping a colour family used by the previous three episodes. Edit only `engine/studio/build_palettes.py`.
- **Music:** 5 original presets (tanpura-bansuri, dotara-drive, harmonium-warm, felt-piano-minor, cinematic-pulse) rotated by episode, mixed low under the VO.
- **Sound effects:** every animation proposes one (slam → impact, pop → pop, count → tick, photo → paper …); `audio.py` keeps at most 3 per scene, ≥ 0.6 s apart, quiet.
- **On-screen text:** ≥ 30 px (running text ≥ 40 px); lands 0.25 s *before* the spoken word; `audit.py` fails any text that is on screen too short to read
  (0.6 s + 0.33 s per word; numbers and labels ≥ 1.2 s).
- **Covers:** designed by hand per topic like episodes 1–5 — real photo or cutout, calm palette, big title (≥ 140 px) that asks without giving the answer,
  no top/bottom bars. `cover_check.py` gates size, crop zones, contrast, palette and spoilers. Guide: `docs/cover-design.md`.

## Safety mechanics (from v0.6)
- `guard.py`: a chat claims an episode (a second chat is refused); every push is checked against what was pulled.
- Facts gate (`script_check.py` / `factcheck.py`): every number needs a URL, exact quote, fetch date and a second source or a single-source note.
- `finish.py`: the whole Finish step in one command (render, A/V check, feed cut, cover bake, captions pair, placeholder-proof `publish.txt`, pack); `finish.py --verify` on the Mac.
- The episode tracker and `_series/STATUS.md` are generated, never typed by hand. Mac-side tool copies: `videoNN/.studio/` and `VIDEO GEN/_series/tools/`.

## Install
- **Claude app:** open `explainer-studio.plugin` (a zip of this repo) in a chat and accept it.
- **Claude Code:** `/plugin marketplace add esftn/explainer-studio`, then `/plugin install explainer-studio@esftn-explainer-studio`.

Then ask: *“নতুন ভিডিও: <title>”* or *“make an explainer about …”*.

After updating, copy `engine/tools/studio.py` and `engine/studio/rules.json` into `VIDEO GEN/_series/tools/`. Episodes already built keep their own engine copy.

## Engine setup (once per machine or session)
```bash
bash engine/tools/setup.sh      # ffmpeg + node required; installs playwright, numpy/scipy, rembg, Bengali fonts
```

## Smoke test
```bash
python3 engine/tools/new_project.py /tmp/smoke --title "পরীক্ষা"
python3 engine/tools/studio.py next /tmp/smoke            # prints the PLAN card
# add 2+ VO takes to /tmp/smoke/vo/raw/vo_01.mp3, vo_02.mp3 and a photo to /tmp/smoke/photos/
python3 engine/tools/vo_prep.py /tmp/smoke && python3 engine/tools/prep_photos.py /tmp/smoke
python3 engine/tools/audit.py /tmp/smoke && python3 engine/tools/audio.py /tmp/smoke
python3 engine/tools/render.py /tmp/smoke --name smoke && python3 engine/tools/check_final.py /tmp/smoke
```

## What's inside
```
.claude-plugin/        plugin.json · marketplace.json
skills/                explainer-video (conductor) · new-video · video-script · video-preview · video-render
docs/                  PLAYBOOK · design-system · cover-design · audio · qa-checklist · storytelling · bangla-localisation ·
                       platform-notes · industry-research · lessons-learned · CHANGES-v0.7
templates/             brief.md · fact-sheet.md · script.md · facts.json
engine/studio/         rules.json (rules, step cards, reports) · palettes.json (+ build_palettes.py) · music_bank.json
engine/template/       engine.js (timeline, camera, animations, auto SFX cues, audit hooks) · engine.css · presets/ · scenes/
engine/tools/          studio · new_project · state · script_check · factcheck · vo_text · vo_split · vo_prep · prep_photos ·
                       audio · audit (+ qa.js) · review · render · render_range · check_final · make_srt · cover · cover_check ·
                       bake_cover · finish · guard · pack · publint · series_tracker · tidy · split_deliver · setup
examples/hadi-ke/      the first video's script and reference scene file
```

## Scene authoring in 30 seconds
```html
<section class="scene t-green" data-vo="3" data-mood="build">
  <div class="bgx dots"></div>
  <div class="a ph" style="left:80px;top:320px;width:920px;height:640px" data-a="fade" data-t="0"><img src="img/p_04.jpg"></div>
  <div class="a h2" style="left:70px;top:1020px;width:940px" data-a="up" data-say="১৯৯৩">১৯৯৩ সালে <span class="mk" data-a="mark" data-say="ঝালকাঠিতে">ঝালকাঠিতে</span></div>
  <div class="src">সূত্র: প্রথম আলো, ২০২৫</div>
</section>
```
`data-say` lands an element just before its word is spoken; the scene's length comes from its VO clip; key content stays inside the 4:5 feed zone (y 285–1635).
Each animation gets a matching sound effect automatically (`data-sfx` overrides it).

## License
MIT for code and docs. Fonts are SIL OFL (installed by `setup.sh`, not committed). Bring your own licensed photos.
