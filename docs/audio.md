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

## Music (`tools/audio.py`) — v0.7: five rotating presets
- Original, synthesised in Python → no copyright claims.
- `engine/studio/music_bank.json` holds 5 presets: `tanpura-bansuri` (calm), `dotara-drive` (rhythmic), `harmonium-warm`, `felt-piano-minor` (D minor), `cinematic-pulse` (A minor, energetic). `studio.py music` assigns `preset[(ep-1) % 5]` and writes `audio_config.json` (with `music_id`). Never edit that file by hand; `studio.py check` fails if the music was swapped.
- Sections come from `data-mood` on each scene (intro, build, drive, somber, elegy, answer, end; it carries forward). Every video needs `intro` first and `end` last.
- Engines: `bangla` (tanpura drone, dotara, bansuri, harmonium, tabla; raga per mood) and `cinematic` (pads, felt-piano arpeggio, bass, kick; chord set `prog`: dm | am | cmaj).
- Final chord lands under the closing line and rings through the hold; the last line is never faded.

## Automatic sound effects (v0.7)
The engine proposes a cue for every animated element that has no `data-sfx`: slam→impact, stamp→stamp, pop→pop, count/mark→tick, growx/drawy/draw→whoosh, strike→click, photo/cutout entrances→paper; every scene change gets `trans`. `audio.py` thins them (`auto_sfx` in audio_config: ≤3 per scene, ≤1–2 per type, ≥0.6 s apart, 80 % gain) so they are present on every episode but never busy. Hand-placed `data-sfx` cues are always kept; `data-sfx="none"` silences one element; `project.json` `autoSfx:false` turns the proposals off (then `studio.py check` fails: effects are required).

## SFX vocabulary (cue types from `data-sfx`)
click · tick · whoosh · trans (scene change) · impact (big number/headline, ducks music ~3.5 dB) · stamp · tone (highlight accent tuned to the current chord) · bell (rickshaw-style bell) · paper (rustle)
- Burst thinning: same-type cues closer than 70 ms are merged.
- Whoosh peaks land on the entrance (start 0.18 s early).

## Voiceover
- Trim leading/trailing silence, optional tempo 1.03–1.06, high-pass 70 Hz, per-clip loudness match.
- Place at scene start + 0.3 s. Scene duration = VO length + 0.55 s (gives breath + transition).
- Lock scene durations after the preview gate so a re-recorded clip only needs a remix (no re-render) if it's ≤ the old length.
