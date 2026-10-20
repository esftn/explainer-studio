# Audio Guide

## Targets
| Item | Target |
|---|---|
| Master loudness | −14 LUFS integrated (±0.5) |
| True peak | ≤ −1.5 dBTP (4× oversampled check) |
| VO clips | each level-matched to −17.5 LUFS, bus to −16 LUFS |
| Music bed | −23 LUFS pre-duck, ducked ~8 dB under speech (sidechain from VO) |
| SFX | −21 LUFS (gated), placed on visual hits, never on key words |
| Ending | music resolves on a final chord; fade over last ~4.5 s; last 0.25 s digital silence |

## Music (`tools/audio.py`)
- Original, synthesised in Python → no copyright claims.
- Sections are driven by `audio_config.json` (scene index → mood). Moods: intro, build, drive, tense, somber, elegy, resolve.
- Palettes: `cinematic` (pad, felt-piano arpeggio, soft kick) and `bangla` (tanpura drone, dotara pluck, bansuri, tabla).
- Final chord lands under the credits; clean tail.

## SFX vocabulary (cue types from `data-sfx`)
click · tick · whoosh · trans (scene change) · impact (big number/headline, ducks music ~3.5 dB) · stamp · tone (highlight accent tuned to the current chord) · bell (rickshaw-style bell) · paper (rustle)
- Burst thinning: same-type cues closer than 70 ms are merged.
- Whoosh peaks land on the entrance (start 0.18 s early).

## Voiceover
- Trim leading/trailing silence, optional tempo 1.03–1.06, high-pass 70 Hz, per-clip loudness match.
- Place at scene start + 0.3 s. Scene duration = VO length + 0.55 s (gives breath + transition).
- Lock scene durations after the preview gate so a re-recorded clip only needs a remix (no re-render) if it's ≤ the old length.
