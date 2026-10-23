# QA Checklist (v0.5 — tools first, eyes on what they flag)

**Script gate** (`tools/script_check.py` → `.script_pass`; `vo_text.py` refuses without it + the creator's approval):
- [ ] Every number in `facts.json` with date, role (now/before/context), chain, source, URL
- [ ] "now" figures ≤ 12 months old (Recency) · no off-chain fact used (Connection)
- [ ] Every derived number is a `math` row written with fact keys and computes (one measuring stick)
- [ ] Same key = same value everywhere · VO has no digits · ending is a question with "কমেন্টে" · est. ≤ 60 s

**VO gate** (`tools/vo_split.py`):
- [ ] The take was recorded from the approved `vo_paste.txt` (hash match)
- [ ] Breaks CLEAN (scene pauses clearly longest); AMBIGUOUS (exit 3) = re-generate from vo_paste.txt, never guess
- [ ] No scene's speed off by more than ±45 % (FAIL = a phrase in the wrong scene; nothing written)

**Build gate** (`tools/audit.py` → `.qa_pass`; `render.py` refuses without a fresh full pass):
- [ ] Bounds: no text outside the frame / into the source band at any 0.1 s step
- [ ] 4:5 feed zone: all text inside y 285–1635 (except source line / `data-zone="band"`)
- [ ] No text on text, no text covered by a graphic; text touching a graphic edge checked on the sheet
- [ ] Contrast against what is actually behind each text (screenshot); size ≥ 30 px (running text ≥ 40 px)
- [ ] Reading time: each text on screen long enough to read (0.6 s + 0.33 s/word; labels/numbers ≥ 1.2 s)
- [ ] `studio.py check videoNN --stage build` PASS (palette, music, SFX, moods, ending)
- [ ] Key numbers tied to the spoken word (`data-say`), every `data-say` word found in its scene's VO
- [ ] On-screen numbers found in `facts.json` · density ≥ 55 % · assets/fonts load · length ≤ max_len

**Claude's eyes** (`tools/review.py --keys`): every flagged frame (red box) fixed or judged intended; the
highlighted spoken word under each cue frame matches the graphic; spelling of Bangla conjuncts and digits.

**Audio** (`tools/audio.py`): −14.5 ±0.5 LUFS, ≤ −1.5 dBTP; VO above music; ending holds ~3 s; silent last 0.25 s.

**Delivery** (`tools/check_final.py`, `tools/pack.py`):
- [ ] Reel 1080×1920 and feed 1080×1350 PASS · captions start on spoken words (`make_srt.py`)
- [ ] Cover hand-designed, `cover_check.py` COVER PASS (size, zones, palette, no spoiler), picked, baked into both videos (`bake_cover.py` PASS)
- [ ] `pack.py unpack` on the Mac prints VERIFIED · `pack.py check --final` prints LAYOUT OK (out/ = finals only)
