#!/usr/bin/env python3
"""state_check.py — keeps every videoNN/state.json honest (tracker issue 8).

Run from the VIDEO GEN folder (copy in _series/ and _series/tools/ and in every videoNN/.studio/):
    python3 _series/tools/state_check.py            # check all episodes, exit 1 if anything is wrong
    python3 _series/tools/state_check.py 21         # check one episode
    python3 _series/tools/state_check.py 21 --fix   # apply the mechanical fixes (stage, open lines, duplicate log lines)
    python3 videoNN/.studio/state_check.py --fix    # inside a project folder: checks that project only
Every Finish chat MUST run it for its own episode (with --fix) as the last step before replying.
Checks:
  S1 state.json exists                       S4 title is the full Bangla video title (>=3 words)
  S2 stage matches the files (out/ complete => "delivered")   S5 no duplicate consecutive "stage X" log lines
  S3 delivered => "open" is empty (no stale 'waiting for…' notes)   S6 delivered => approved has preview + cover
"""
import json, re, sys, time
sys.dont_write_bytecode = True      # the Mac folder can't delete: no __pycache__ litter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root():
    """The VIDEO GEN folder = the nearest folder (from here or the cwd) that has video?? subfolders."""
    for start in (HERE, Path.cwd()):
        for c in [start, *start.parents]:
            if any(p.is_dir() for p in c.glob("video[0-9][0-9]")):
                return c
    return Path.cwd()


ROOT = find_root()
FINALS = ["*_reel_9x16.mp4", "*_feed_4x5.mp4", "cover_reel_9x16.png", "cover_feed_4x5.png",
          "captions.bn_IN.srt", "captions.en_US.srt", "publish.txt"]

def finals_complete(d):
    out = d / "out"
    return out.is_dir() and all(any(out.glob(p)) for p in FINALS)

def check(d, fix=False):
    msgs = []
    f = d / "state.json"
    if not f.exists():
        return ["S1 no state.json (create with state.py init, then set stage)"]
    s = json.loads(f.read_text(encoding="utf-8"))
    changed = False
    done = finals_complete(d)
    if done and s.get("stage") != "delivered":
        msgs.append(f"S2 out/ is complete but stage is '{s.get('stage')}' (should be 'delivered')")
        if fix:
            s["stage"] = "delivered"; s.setdefault("log", []).append(time.strftime("%Y-%m-%d %H:%M") + " stage delivered (state_check)"); changed = True
    if not done and s.get("stage") == "delivered":
        msgs.append("S2 stage is 'delivered' but out/ is missing finals (reel, feed, 2 covers, 2 SRT, publish.txt)")
    if s.get("stage") == "delivered" and s.get("open"):
        msgs.append(f"S3 stage delivered but {len(s['open'])} stale 'open' line(s): " + " | ".join(s["open"])[:120])
        if fix:
            s["open"] = []; s.setdefault("log", []).append(time.strftime("%Y-%m-%d %H:%M") + " note: open lines cleared at delivery (state_check)"); changed = True
    t = s.get("title", "")
    if not re.search(r"[ঀ-৿]", t) or len(t.split()) < 3:
        msgs.append(f"S4 title '{t}' is not the full Bangla video title (fix by hand: copy the title from publish.txt / script.json)")
    log = s.get("log", [])
    dedup, prev = [], None
    for line in log:
        k = line.split(" ", 2)[-1] if " stage " in line else None
        if k and k == prev:
            continue
        dedup.append(line); prev = k if k else prev
    if len(dedup) != len(log):
        msgs.append(f"S5 {len(log) - len(dedup)} duplicate 'stage' log line(s)")
        if fix:
            s["log"] = dedup; changed = True
    ap = s.get("approved", {})
    if s.get("stage") == "delivered" and not ("preview" in ap and "cover" in ap):
        msgs.append("S6 delivered but approved lacks preview and/or cover")
    if changed:
        f.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return msgs

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fix = "--fix" in sys.argv
    dirs = [d for d in sorted(ROOT.glob("video[0-9][0-9]")) if d.is_dir()]
    if args:
        dirs = [d for d in dirs if d.name in {f"video{int(a):02d}" for a in args if a.isdigit()}] or \
               [Path(a).resolve() for a in args if Path(a).is_dir()]
    elif HERE.name == ".studio":                      # run inside a project: that project only
        dirs = [HERE.parent]
    bad = 0
    for d in dirs:
        # skip planned-only folders (nothing but the VO take)
        if not (d / "state.json").exists() and not (d / "out").exists() and not (d / "index.html").exists():
            continue
        m = check(d, fix)
        print(("OK   " if not m else "FIX  ") + d.name)
        for x in m:
            print("       " + x)
        bad += bool(m)
    print(f"\n{bad} episode(s) need attention" if bad else "\nall state.json files consistent")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
