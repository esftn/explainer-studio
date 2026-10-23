# Bangla Explainer Video — Post-mortem & Playbook
*Project: "হাদি কে?" (v1 → v3), October 2026. Use this as the base for the master prompt.*

---

## 1. Where things went wrong (root causes)

| # | What happened | Root cause | Cost | Rule for next time |
|---|---|---|---|---|
| 1 | v1 (calm "নথি/dossier" tone, text-only, no photos, no voice) was largely rebuilt in v2 | Key creative decisions (tone, style reference, voiceover, photo sources) arrived after the first build | 1 full build + render wasted | **Lock a creative brief before any build** (see §3, Phase 0) |
| 2 | "১৯৯৩" looked broken everywhere | Hind Siliguri draws the digit ১ as a hook; the font was never tested on numerals | Full re-style | **Font test sheet before design**: digits ০–৯, conjuncts (ক্ষ, ষ্ট্র, জ্ঞ, ন্দ্র), ং ঃ ঁ, “quotes”, ৳, %, dates |
| 3 | Text cut by the frame during zooms (জানাজা, বিচার, ending) | The camera zoom scaled the whole scene, text included; "slam/stamp" entrances started at 1.45–1.9× size | User found it; full re-render | **Camera moves only the photo layer; text sits in a fixed, safe layer**; entrance scale ≤ 1.15; automated bounds check |
| 4 | Overuse of "নথি" | A concept motif was repeated in the header, title, stamp and ending | Revision round | A motif appears **at most 2×** (open and close) |
| 5 | Sources at the top, then moved to the bottom; text fighting the source line | Placement not agreed upfront | Revision | Sources always on a **bottom band with its own background**; content stays above y≈1790 |
| 6 | Poet scene voice sounded emotional and odd | Emotion tag (`[softly]`) chosen per line by feel, not by content type | Re-record failed (see #8) | **Emotion map**: facts neutral; emotion only at 2–3 peaks (death, ending) |
| 7 | Photos were hard to get (~25 tool calls) | The workspace and your Mac's shell are both on an allowlist; Wikimedia and hadiarchive blocked; my 210-photo grid flooded the hadiarchive server; browser downloads landed as hidden temp files | Big time and token cost | **You put the photos in the project folder**, or allow the domains first; if scraping, small batches only |
| 8 | ElevenLabs rate-limited, then the account was flagged ("unusual activity", free tier disabled) | 17 separate calls in a burst on a free account; signed links expire in 2h; extra download hops (CORS) | Clip 05 could not be redone | Free tier is risky for production: **paid tier**, no VPN, generate in **1–3 long takes**, not 17 bursts |
| 9 | 30 MB transfer limit; the MP4 header got corrupted in transit | Platform limits not known upfront | ~6 extra calls | Split into ≤14 MB pieces; **gzip the first piece**; verify the md5 on your Mac |
| 10 | Long empty stretches in scenes (half-blank screens for 3–5 s) | Elements timed only to VO words; no density rule | Revision | **Density rule**: ≥60% of the frame filled at all times, a new visual every 2–3 s |
| 11 | Review missed mid-animation problems | v2 review looked only at *end-state* frames of each scene | User found issues | Review **frames across time** (every 1–1.5 s) + automated audit before rendering |
| 12 | Each full render ≈ 20 min, done 3 times (+1 partial) | 2-CPU machine, render at full res for every check | Time | Low-res preview for review; **render per scene** so only changed scenes re-render |
| 13 | Lots of AI context burned | Huge tool outputs (ElevenLabs status ~70 KB each), many large images read | Tokens/credits | Ask tools for compact output; read contact sheets, not single frames |
| 14 | Photo rights unclear | Fan/memorial archives state no license; one image's CC BY-SA share-alike carried over from the original video | Risk | Record the source and license of every photo **while collecting it**; flag unknowns before use |

**What worked and should be kept:** facts researched with sources (caught 19 → 20 delays); VO first, then timing animations to measured VO pauses; Python sound design synced to animation cues; music ducking under VO; loudness mastering (−14 LUFS, −1.5 dBTP); rembg cutouts with a white sticker outline; the automated text-bounds audit; contact-sheet review; partial scene re-render; the reusable engine (index.html + render.py + audio2.py + audit.py + review.py).

---

## 2. How to get a video right on the first try

Error-free on the first try comes from **approving cheap things before building expensive things**.
Cheap to change: brief → facts → script → style frames. Expensive: VO → full layout → render.

### Pre-flight checklist (before anything is built)
- [ ] Topic, angle, purpose (inform / mobilise / tribute), audience
- [ ] Platform + length (Shorts/Reels ≤ 2:59; TikTok can be longer), 1080×1920, 30 fps
- [ ] Tone of voice and language register (e.g. informal চলিত, emotional but factual)
- [ ] Style reference (e.g. Vox editorial) + 1–3 reference videos/screenshots
- [ ] Voiceover: yes/no, provider, **paid account**, voice chosen by listening to 2–3 samples
- [ ] Photos supplied in `/source_photos` (or domains allowed), with source/credit notes
- [ ] Brand: colours, fonts, logo/handle, end card / CTA
- [ ] Rules: sources position, credits content, words to avoid, motif limits
- [ ] Sensitive topic? → balance requirements (e.g. include the other side's clarification)

---

## 3. Recommended production pipeline (with approval gates)

| Phase | Output | Gate (your approval) | Notes |
|---|---|---|---|
| **0. Brief** | Filled pre-flight checklist | ✅ | 5-minute questionnaire; prevents a v1 → v2 rebuild |
| **1. Research** | Fact sheet: each fact + date + source link | ✅ | Flag conflicts (e.g. birth date 1 Jan vs 30 Jun) |
| **2. Script** | Table per scene: VO line · on-screen text · visual · emotion tag · photo | ✅ | Spell-check pass here; read aloud for the ear |
| **3. Assets** | Photos sorted, cutouts made, font test sheet | — | Photos come from your folder |
| **4. Style frames** | 3 still frames (hook, data scene, ending) | ✅ | Locks the look before animating 17 scenes |
| **5. Voiceover** | 1–3 long takes → split by silence → durations | ✅ listen | Only after the script is approved, so no re-generation |
| **6. Build + QA** | Full timeline + automated QA + contact sheets + low-res preview MP4 | ✅ watch preview | QA list in §4 |
| **7. Final** | Full-res render (per scene, in parallel), audio master, cover, caption | — | One render only |

---

## 4. Automated QA (run before every render)
1. **Bounds:** no text outside the frame or inside the source band, every 0.1 s (`audit.py`)
2. **Overlap:** text doesn't sit on busy photos without a strip or band behind it
3. **Density:** no frame more than 40% empty for more than 1.5 s
4. **Fonts:** digits and conjuncts render (test sheet); no fallback fonts
5. **Spelling/consistency:** Bangla digits everywhere, consistent names (ঢাকা-৮, ইনকিলাব মঞ্চ)
6. **Sync:** each highlight lands within ±0.3 s of the spoken word
7. **Length:** ≤ platform limit; credits ≤ 5 s
8. **Audio:** −14 LUFS integrated, ≤ −1.5 dBTP, VO ≥ 12 dB above the music bed, clean silent ending
9. **Delivery:** md5 of the copy on your Mac matches the render

---

## 5. Using the voiceover to make the video more engaging
- **Hook in the first 2 s:** open on a question or a striking quote ("হু ইজ হাদি?"), not a title.
- **Write for the ear:** short sentences (8–12 words), one idea each; spoken Bangla, not bookish.
- **Emotion map, not emotion everywhere:** neutral for facts; warmth for personal details; gravity only at the 2–3 peak moments; a strong final line. Too many tags sound fake.
- **Pause before reveals:** "…" or `[pause]` before a key number or name, then show it on screen exactly as it's spoken.
- **Let silence land:** 0.6–1 s of near-silence after the heaviest line (the death, "বিশ বার!").
- **VO and screen complement each other:** the VO tells the story; the screen shows the **key word, number or quote**. Don't print every spoken word.
- **Numbers:** written as words for TTS ("উনিশশো তিরানব্বই"); shown as Bangla digits on screen.
- **English or foreign words:** test pronunciation (e.g. "হু ইজ হাদি", "ইউনিভার্সিটি অব স্কলার্স") before generating everything.
- **Pace:** ~1.05× speed suits social media; vary energy by section (build → somber → resolve).
- **Sound design under the VO:** duck the music about 8 dB under speech; effects on visual hits, never on top of key words.
- **End with a line that sticks, or a question/CTA** ("সেটা সরাবে কে?" / "শেয়ার করুন").
- **One voice throughout**; record all lines in one session (same model and settings) so the tone matches.

---

## 6. Design rules learned (style-independent)
- **Layer architecture:** background/photo layer (camera moves here) · text/graphics layer (fixed) · source band (always on top).
- **Safe area:** text x 56–1024 px, y 150–1790 px; bottom band reserved for sources.
- **Entrances:** slide ≤ 40 px, scale ≤ 1.15, fade; never start text off screen.
- **Transitions:** 0.4–0.5 s; text appears after the transition finishes.
- **Every scene:** at least 1 photo or graphic, 1 key text, 1 highlight/number; a new element every 2–3 s.
- **Numbers as heroes:** big digits on a colour block, counted up, with a comparison ("৩২ vs ৭২.৩").
- **Annotated comparisons** make abstract facts concrete (timeline ruler, life bar, 20 tick marks).
- **Photos:** consistent treatment (desaturated, halftone, torn edges, sticker cutouts).
- **Text on a photo** always gets a strip or band behind it.

---

## 7. Optimising time and AI credits

| Area | This project | Optimised |
|---|---|---|
| Creative direction | 3 versions (v1 dossier → v2 Vox → v3 fixes) | 1 brief + 3 style frames → 1 build |
| Photos | ~25 calls (blocked sites, scraping, temp files) | You drop 20–40 photos in a folder: **0 calls** |
| Voiceover | 17 calls + rate limits + account flag + browser download hops | 1–3 long takes on a paid account; split locally |
| Review | Full-res stills, found issues late | Automated audit + 1 contact sheet per 20 s + low-res preview |
| Rendering | 3 full renders × ~20 min | 1 final render, per-scene, parallel; re-render only changed scenes |
| Context | Huge tool outputs and many images | Compact queries; contact sheets only |
| Reuse | Built from scratch | **Start from the v3 project zip** (engine, audit, audio, render) |

Rough estimate: the next video of similar length should take **~40–50% of the tool calls** and **1 render instead of 3–4**, if Phases 0–2 are approved before building.

**Further savings:**
- Turn this playbook plus the v3 engine into a reusable **skill or template**, so each new video only needs the brief, script and photos.
- Keep a **library** of approved fonts, colour palettes, sound effects and the music engine.
- For a recurring series, keep a **fixed layout system** (6–8 scene templates: hook, quote, timeline, number, comparison, photo grid, ending, credits) and only swap content.

---

## 8. Platform and technical notes to remember
- Workspace and Mac shell: outbound sites blocked unless allowed in **Settings → Capabilities**; the built-in browser can reach sites but its downloads land in Downloads, sometimes as hidden temp files.
- Transfer to your Mac: ≤ 30 MB per file; split into 14 MB pieces, gzip the first piece of an MP4, verify the md5.
- ElevenLabs links expire in 2 h; download immediately. Free tier gets flagged by bursts or VPN.
- Freepik MCP: images, video, TTS (different voices from ElevenLabs), background removal; useful as a backup.
- Container: 2 CPUs. Full-res render ≈ 8–10 min per 90 s of video per worker.


---

## Video 01 of the economics series — "১ কোটি বনাম ১,০০০ কোটি" (Oct 2026)

| What happened | Rule now |
|---|---|
| Script mixed "650 floors" (3 m floors) with a 40-floor/152 m tower — numbers contradicted each other | One measuring stick per comparison; check every pair of numbers agrees |
| 4 takes × 4 variations burned credits and hit ElevenLabs concurrency/rate limits | One take per voiceover, whole script in one request; split by transcript word timings |
| Signed audio URLs blocked by the network allowlist | Ask the creator to allow `storage.googleapis.com` before the VO step |
| Chapter chips ("০১ প্রশ্ন") distracted from the main visuals | No `.tag` in videos |
| Uneven rule line above the source band | Source = plain text in the bottom band, no rule |
| Facebook feed shows Reels cropped to 4:5 | Key content in y 285–1635; bands carry bleed |
| Master fade (4.6 s) swallowed the last VO line; ending felt abrupt | Hold last scene ~3 s after VO; `end_chord_s` lands the closing chord on the CTA; `end_fade_s` 1 s |
| Default cover at 1.5 s was an empty frame; a frame grab is weak anyway | Design a dedicated cover per video (`cover-design.md`): question title, one hero element, topic palette |
| A real photo of the subject (Shanta Pinnacle) beat any drawn icon | Ask for a photo of the key object; cut it out and use it as the comparison unit |


---

## Process review after episodes 01–03 (Oct 2026) → plugin v0.4

| Where time went | Rule / tool now |
|---|---|
| Script fixes caught by the creator after the script was "done" (650 floors; stale 2022–23 inflation; off-chain remittance and wage lines; ending question added late) | `facts.json` + `script_check.py`: recency, connection, arithmetic with fact keys, ending CTA, no digits in VO — before the creator sees it |
| Script edited after the VO existed (ep. 02) → VO, split, timing, mix, render all again | `state.py approve script` stores the hash; `vo_text.py` and `vo_split.py` refuse any other version |
| Manual take split by guessing from small pauses; a phrase landed in the wrong scene (ep. 02, visuals late in scenes 8–9). Tested on the real ep. 03 take: its scene breaks (0.4–0.5 s) equal sentence pauses and natural speed varies −16 %…+24 % per scene, so pause/speed guesses got 1–5 of 8 cuts wrong | `vo_text.py` puts a "[pause]" line between scenes; `vo_split.py` cuts only when the scene pauses are clearly the longest (8/8 right on ep. 03 with real pauses), otherwise stops (AMBIGUOUS) and asks for a re-generated take |
| Visuals timed by hand to seconds | `data-say="word"`: the engine times the graphic to the spoken word (word times from `vo_prep.py`) |
| Creator found illegible numbers, overlaps, text touching bars | `audit.py`: contrast vs real background, text-on-text, covered text, edge touches, 4:5 zone, size; `review.py --keys` sheet with the spoken line under each frame |
| Captions drifted up to 0.8 s | `make_srt.py` starts each line on its first spoken word |
| Many tar → _to_delete → extract round trips; ep. 03 folder structure missing on the Mac | Mac skeleton at setup; `pack.py` one verified transfer per stage (decode check survives C2PA); `pack.py check --final` |
| One giant chat per episode (every turn re-reads everything) | Three chats (Plan batch / Build / Finish batch), `state.json` hand-off, plugin work in its own chat |
| Deferred: a per-episode theme library | Revisit once there are enough episodes to learn from (creator decision, Oct 2026) |
