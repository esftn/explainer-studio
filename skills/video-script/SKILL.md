---
name: video-script
description: Research, fact-check and write the script and voiceover for an explainer video, then generate and time the VO. Use after the brief is approved, or when the user asks to research, write, rewrite or voice a video script, or fix VO tone/pronunciation.
---

# Research → fact sheet → script → voiceover

## Read
`../../docs/storytelling.md`, `../../docs/bangla-localisation.md` (Bangla), `../../templates/fact-sheet.md`,
`../../templates/script.md`, `../../docs/lessons-learned.md` (VO section).

## 1. Research → `fact-sheet.md`
- Search, don't recall: anything current or contested is looked up (WebSearch, standard mode, several
  queries in one turn). Two independent sources for contested facts; on conflict say less (year only).
- Every row: fact as it will be said · date · source title + URL · confidence. Quotes verbatim with who/where/when.
- Sensitive topics: include the other side's stated position or later clarification.

## 2. Script → `script.md` + `script.json`
- Arc: hook (0–3 s, no title card) → context → rising stakes → turning point → consequence → answer → last line.
- Open a loop in the hook and close it at the end. One idea per scene; a visual beat every 2–3 s.
- One row per scene: VO line · on-screen text · visual/infographic (pick a template from
  `../../engine/template/scenes/`) · photo · emotion tag · source.
- Bangla: চলিত register, BD vocabulary (পানি, গোসল…), 8–12-word sentences, আপনি unless the brief says তুমি.
  Write numbers as words in the VO text, Bangla digits on screen.
- Target ~2.3–2.8 words/s. Count: total words ÷ 2.5 ≈ seconds. Trim before the gate, not after VO.
- `script.json` = `{"1": "VO text of scene 1", ...}` (keys = scene numbers = `data-vo`).
- Gate: send the table; creator approves. Changes are free now and expensive after VO.

## 3. Voiceover (paid step — only after script approval)
- ElevenLabs MCP: `creative_create_flow` once, then `creative_generate_speech` per clip on that flow with the
  SAME voice_id, model and settings for all clips; poll `creative_get_flow_run_status`. Pick the voice with
  `creative_list_voices` (Dhaka-standard Bangla voice; avoid Kolkata/Hindi-accented ones). Test 1 short line
  with names/English words first.
- Delivery: neutral for facts; warm for personal moments; grave only at 2–3 peaks. Do not add emotion
  tags to factual scenes (v3 lesson: an emotional take on a factual scene sounded wrong).
- Download clips promptly (signed URLs expire in ~2 h) into `<project>/vo/raw/vo_NN.mp3`.
- On 429 wait and retry once; on "free tier disabled" stop and tell the creator — never burn retries.
- Own recording: one long take, then split at the scene breaks into vo_NN files.

## 4. Lock timing
```bash
python3 engine/tools/vo_prep.py <project>     # trims, tempo 1.06, writes vo.js + vo/report.txt
```
Read `vo/report.txt`: flag scenes with words/s > 3.2 (rushed) or < 1.6. Pause anchors (a1, a2…) are the
times the next phrase starts — use them for highlights. Gate: creator listens to the VO (send 1–2 clips or
the joined file).
