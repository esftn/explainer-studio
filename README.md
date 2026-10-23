# Explainer Studio

Make industry-grade, Vox-style explainer shorts with Claude, Bangla first: brief → research → script →
voiceover → HTML animation → original music and SFX → a render gated by QA.

It is **two things in one repo**:
1. **A Claude plugin.** Five skills that walk Claude through every phase and stop at the right approval gates.
2. **An engine.** A deterministic HTML-to-video runtime plus Python tools for VO timing, music and SFX
   synthesis, QA, rendering and delivery checks.

## v0.7 — one front door, same steps in every chat

Start every chat with `python3 engine/tools/studio.py next videoNN` (or `_series/tools/studio.py` on the Mac): it prints the step card for the
episode's stage, the creator's rules and the report templates. Rules live in ONE file, `engine/studio/rules.json`.

| Command | What it does |
|---|---|
| `studio.py next [videoNN]` | step card + rules + report templates (no argument = series status) |
| `studio.py new videoNN --title … --ep NN` | project + Vox-style palette + music preset in one step |
| `studio.py look / music videoNN` | show or (re)assign the palette (`docs/look.md`) / music preset |
| `studio.py check videoNN --stage build\|final` | objective checks: typeface preset, palette, music unchanged, sound effects present, `data-mood`, ending, finals-only `out/` |
| `studio.py status [--write]` | every episode: stage, who is waiting, length, look, music → `_series/STATUS.md` |
| `studio.py close videoNN STAGE` | last command of every chat: state + status document (+ tracker when delivered) |

Rotation is by episode number: 12 palettes (contrast-checked, calm Vox / Johnny Harris style taken from episodes 1–5) and 5 original music presets; sound effects are proposed
automatically from the animations and thinned by `audio.py`. Details: `docs/CHANGES-v0.7.md`.

## The pipeline (v0.6 mechanics, still in force)

| Chat | Skill | You approve | Tools that check first |
|---|---|---|---|
| 1 Plan (1–3 episodes) | `new-video` → `video-script` | brief, then script; record one VO take from `vo_paste.txt` | `script_check.py` `state.py` `vo_text.py` |
| 2 Build (per episode) | `video-preview` | style frames, then preview + key-moment sheet | `vo_split.py` `vo_prep.py` `audit.py` `review.py --keys` |
| 3 Finish (1–3 episodes) | `video-render` | cover pick | **`finish.py`** (check_final + A/V fix, bake, captions pair, `publint.py`, pack) then `finish.py --verify` on the Mac |

**v0.6 — the studio works like a tool.** Three guards on top of the gates: **(1)** `guard.py` — a chat claims an episode (a second chat is refused) and
every push is checked against what was pulled, so one chat can no longer overwrite another's work; the episode tracker is *generated*
by `series_tracker.py` from the folders (notes live in the append-only `_series/issues.md`). **(2)** the facts gate in `script_check.py`
(`factcheck.py`): each number needs a real URL, the exact quote, a fetched date and a second source / official / single-source note; a spoken number
that is close to but not the sourced one fails (the "1.28 vs 1.12 crore" class of error). **(3)** `finish.py`: the whole Finish chat in one command
with a placeholder-proof `publish.txt` (`publint.py`), idempotent cover bake, captions-pair validation, and `finish.py --verify` on the Mac.
Mac-side copies of the tools: `videoNN/.studio/` and `VIDEO GEN/_series/tools/`.

The rule behind the order: **approve cheap things before building expensive things, and let the tools check
before you do.** Nothing can skip a gate: the VO text needs a passing, approved script; the split refuses a take
of an older text; `render.py` needs a full audit pass on the exact current timeline.

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
Last verified on 2026-10-19 with an 11-scene, 112 s project: QA pass; render 282 s on 3 workers;
−14.7 LUFS; −1.4 dBTP; silent ending.

## What's inside
```
.claude-plugin/plugin.json   plugin manifest
skills/                      explainer-video (master rules) · new-video · video-script · video-preview · video-render
docs/                        PLAYBOOK · storytelling · bangla-localisation · design-system · audio · qa-checklist ·
                             platform-notes · industry-research (with sources) · lessons-learned
templates/                   brief.md · fact-sheet.md · script.md · facts.json
engine/template/             engine.js (timeline, camera, animations, AUDIT, DENSITY) · engine.css ·
                             presets/ (vox-paper, dark-doc) · scenes/ (12 copy-paste scene templates)
engine/tools/                setup · new_project · state · script_check · vo_text · vo_split · vo_prep · font_test · paper ·
                             prep_photos · audio · audit (+ qa.js) · review (--keys) · render · render_range · check_final ·
                             make_srt · bake_cover · cover · pack (Mac transfers + layout) · split_deliver
examples/hadi-ke/            the first video's script and reference scene file
```

## Scene authoring in 30 seconds
```html
<section class="scene" data-vo="3" data-mood="build" data-cam="0:1.08:0:0|7:1:-20:0">
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

**v0.7 update:** `cover_check.py` (big, spoiler-free covers, designed by hand like episodes 1–5) and a reading-time check for on-screen text — see docs/CHANGES-v0.7.md.
