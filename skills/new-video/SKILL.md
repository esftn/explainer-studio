---
name: new-video
description: Start a new explainer video project and collect everything needed from the creator up front. Use when the user says "new video", "make a video about…", "start an explainer", "নতুন ভিডিও", or gives a topic for a video without a brief yet.
---

# New video(s) — intake, Mac folder, brief  (Chat 1 · Plan)

> **v0.7:** the order of work is the step card printed by `python3 engine/tools/studio.py next videoNN` (it wins over anything below that conflicts). This file is the technique reference for your current step; do not read it start to finish.

Goal: one short round of questions for up to 3 episodes, the episode folders ready on the Mac, and a brief per
episode the creator approves. Ask only what you cannot infer; never ask about what the engine decides.

## 1. Read
The project's series brief (`claude/series-brief.md`: house defaults, shared figures, cover log, lessons),
`../../docs/PLAYBOOK.md` §1 and `../../templates/brief.md`. Batch: if the creator gives several topics, handle
them together — shared research, one question round, briefs side by side.

## 2. Scope (quick, standard search mode)
2–4 searches per topic so the questions are informed (angles, the obvious yardstick, recent figures).

## 3. Ask the gaps in ONE AskUserQuestion call (max 4 questions across all episodes) — v0.7: when the title is clear, ask nothing and go on
Takeaway & angle (offer 2–3), yardstick, anything the series brief doesn't settle. The series brief already
fixes platform, length (≤60 s), voice, preset family and endings — don't re-ask them.
In plain text, list the photos to drop in `videoNN/images/` (hero object, places, people) — creator photos
beat scraping.

## 4. Create the folders
v0.7: in the cloud workspace use `python3 engine/tools/studio.py new videoNN --title "<title>" --ep NN` instead of `new_project.py` — it also assigns the episode's Vox-style palette and music preset. Do this AFTER the script is approved (state stage `folders-ready`).
**On the Mac** (series home `~/Documents/VIDEO GEN/videoNN`): the creator makes `videoNN/` (+ `images/`)
and connects it with "Add folder". Then create the standard skeleton there, so later they only drop files in:
```bash
# cloud: copy pack.py over (device_commit_files → videoNN/.studio/pack.py), then on the Mac (device_bash):
python3 "$HOME/mnt/videoNN/.studio/pack.py" skeleton "$HOME/mnt/videoNN"
```
`new_project.py` puts `pack.py guard.py state_check.py publint.py series_tracker.py finish.py tidy.py` into `videoNN/.studio/`; push that folder
with the project. A copy of the same seven files belongs in `VIDEO GEN/_series/tools/` (copy once when the plugin is updated).
**In the cloud workspace** (where all the work happens):
```bash
python3 engine/tools/new_project.py videoNN --title "<title>" --ep NN --preset vox-money --palette cinematic
```
This makes the same layout (out/ docs/ drafts/ vo/raw vo/unused img/ images/), `facts.json`, `state.json`.

## 5. Brief → gate
v0.7: if the creator gave only a title there is NO brief gate: write `docs/brief.md` for yourself, run `state.py videoNN approve brief --note 'title given'` and go straight to `video-script`. Ask for approval only of the script.
Write `docs/brief.md`. Send it as a short summary per episode (takeaway, angle, yardstick, chain, look idea,
photos needed). Say what is cheap to change now. On approval: `state.py videoNN approve brief`, then
`video-script` in the same chat.
