# Build cheat sheet (v0.10) — everything needed to write build.json. Do NOT open engine.js / engine.css / tool sources.

`bash _series/es.sh build_scenes videoNN [--check]` turns `videoNN/build.json` into index.html (colours from docs/look.json,
bands, textures, timing from vo.js). Edit build.json and re-run; never hand-edit index.html.

## Top level
`{"bands": "<style>", "tex": "dots", "css": "", "scenes": [ … one per VO clip, in order … ]}`
- bands: zigzag · coupon · stripes · dots · checker · ruler · scallop · tape · bars · plus  (must differ from the previous episode)
- tex (scene background texture): dots · graph · bprint · none
- css: optional extra CSS for the episode's motif objects (use with "html" blocks); colours only from docs/look.md

## Scene keys
- `photo`: "file.jpg" (from img/) → full-bleed photo + dark wash, light text; `pos`: "50% 30%" (object-position)
- `bg`: 0–5 = row of the themes table in docs/look.md (no photo). Vary it scene to scene.
- `mood` (music): intro (scene 1) · build · drive · somber · elegy · answer · end (last scene)
- `src`: source line at the bottom ("সূত্র: …" / "উদাহরণ" / "অনুমান") — needed whenever the scene shows a number
- `align`: center (default; photo scenes default to top) · top · left
- `blocks`: the content, top to bottom, in a centred 960 px column inside the safe zone (y 300–1400)

## Blocks (every block also takes: "say": "word" | "t": seconds, "a": animation, "sfx": sound, "size": h0|h1|h2|h3|b)
Timing: "say" = the spoken word it lands on (exact word from the scene's VO; "word#2" = 2nd time; "word+0.3" = later).
No say/t → it lands on the first word of its own text that is spoken, else spread through the scene.
| block | example | note |
|---|---|---|
| h0…h3, b | `{"h2": "টাকার দাম **কমলে**"}` | text; `**x**` = marker highlight |
| blk | `{"blk": "রপ্তানি বাড়ে?"}` | the big highlighted block (≤ 9 chars → h0, else h1) |
| num | `{"num": 123, "from": 86, "post": " টাকা", "dec": 0}` | counting number in a block; `"box": false` = plain |
| chip | `{"chip": "১ ডলার = ১২৩ টাকা"}` | small label |
| note | `{"note": "সত্যিই?"}` | tilted sticky note |
| card | `{"card": ["≈ ৪.৫ বিলিয়ন ডলার", "গত অর্থবছরে শোধ"]}` | card: title + sub-lines |
| tags | `{"tags": ["মজুরি", "বিদ্যুৎ"], "says": ["মজুরি,", "বিদ্যুৎ,"]}` | chips popping one by one |
| bars | `{"bars": [{"l": "বাড়তি আয়", "n": "৩৭০ টাকা", "v": 370, "say": "বাড়তি"}, …], "max": 400, "legend": […]}` | horizontal bars; `"v": [a, b]` = stacked |
| share | `{"share": [["আমদানি", 60], ["দেশে", 40]], "says": ["…", "…"]}` | one split bar |
| chain | `{"chain": ["টাকা দুর্বল", "আমদানি দামি", "লাভ কম"]}` | cards with ↓ arrows |
| vs | `{"vs": ["শক্ত", "দুর্বল"], "mid": "নাকি"}` | two cards side by side |
| strike | `{"strike": ["৮৬০ টাকা", "১,২৩০ টাকা"], "say": "পান"}` | old value struck, new value slams |
| photo | `{"photo": "x.jpg", "h": 420, "cap": "…"}` | framed photo inside the column |
| grid | `{"grid": 120, "cols": 12, "on": 20}` | unit grid, `on` cells highlighted |
| row | `{"row": [{…}, {…}]}` | blocks side by side |
| gap | `{"gap": 40}` | vertical space |
| html | `{"html": "<div class='leaf' data-a='pop' data-say='…'></div>"}` | escape hatch for a motif object (style it in "css") |

Animations ("a"): up · fade · slam · pop · stamp · left · right · rot · draw · growx.  Sounds ("sfx"): impact · stamp · pop · whoosh ·
paper · click · tick · tone · bell · none. Blocks get a sensible default sound; don't add more.

## Rules the tools check
- `build_scenes --check` warns before the audit: unknown say words, text landing too late to read, over-full scenes, moods, repeated bands.
- `audit` FAIL = fix in build.json and re-run both. WARN = decide; most are fine.
- Scene 1 is loud from t = 0: `photo` + chip + h2 + blk with `"t": 0` (the 1.6 s cover opening fades into it).
- Last scene: mood "end"; it automatically lasts VO + end_hold.
