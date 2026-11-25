#!/usr/bin/env python3
"""Recolor the COTA track report from Grokbot sector data, one run at a time.

Usage (repo root):
  python3 source/recolor.py --sectors /path/to/cota-sectors-YYYY-MM-DD.json --run "2026-11-24 practice, clips 2-4"
Run it again with a new Grokbot sector file and a new --run label after each session.
Same label twice replaces that run, so it is safe to repeat.

Rule (all numbers come from the sector file, nothing is typed by hand):
  target sector time = Pro Line sector time scaled so the lap equals the field leader's qualifying lap
  gap % = your clean-lap average in the sector against that target
  green <= 1.5%, amber <= 4%, red > 4%. Any spin, off or cut in the sector caps it at amber.
"""
import json, argparse, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--sectors", required=True)
ap.add_argument("--run", required=True)
a = ap.parse_args()

PRO = {"S1": 12.40, "S2": 14.18, "S3": 9.09, "S4": 9.39, "S5": 17.18, "S6": 9.35, "S7": 23.13}  # Pro Line hot lap sectors
LEADER = 98.431  # field leader qualifying lap, seconds
GREEN, AMBER = 0.015, 0.04
scale = LEADER / sum(PRO.values())

d = json.loads((root / "data.json").read_text())
t = [x for x in d["tracks"] if "report" in x][0]
r = t["report"]
sj = json.loads(pathlib.Path(a.sectors).read_text())
summ = {s["id"]: s for s in sj["sector_summary"]}

new = {}
for s in r["sectors"]:
    q = summ[s["id"]]
    c = q["clean"]
    inc = q["incl_incidents_excl_traffic"]["n"] - c["n"]
    tgt = PRO[s["id"]] * scale
    gap = c["mean_s"] - tgt
    pct = c["mean_s"] / tgt - 1
    tier = "green" if pct <= GREEN else "amber" if pct <= AMBER else "red"
    if inc > 0 and tier == "green":
        tier = "amber"
    new[s["id"]] = dict(tier=tier, clean_mean=round(c["mean_s"], 3), std=round(c["std_s"], 3), n=c["n"],
                        incidents=inc, best_ever=q["best_ever_s"], target=round(tgt, 2), gap=round(gap, 2), pct=round(pct * 100, 1))

big = max(new, key=lambda k: new[k]["gap"])
for s in r["sectors"]:
    n = new[s["id"]]
    spread = "tight" if n["std"] <= 0.3 else "loose"
    s["tier"] = n["tier"]
    s["stats"] = n
    s["why"] = (f"{s['id']}: you average {n['clean_mean']:.2f} s on clean laps, target {n['target']:.2f} s, "
                f"{n['gap']:+.2f} s ({n['pct']:+.1f}%). Spread {n['std']:.2f} s ({spread}). "
                + (f"{n['incidents']} spin, off or cut lap(s) not counted. " if n["incidents"] else "")
                + ("Biggest gap on the lap." if s["id"] == big else ""))
    h = s.setdefault("hist", [])
    h[:] = [x for x in h if x["run"] != a.run] + [dict(run=a.run, tier=n["tier"], gap=n["gap"], pct=n["pct"])]

# spot chips follow their sector unless pinned (hand-set coach calls) or info-only (gray)
PIN = {"1", "5", "12"}
LBL = {"green": "Keep", "amber": "Small gain", "red": "Needs work"}
secs = {s["id"]: s for s in r["sectors"]}
for sp in r["spots"]:
    if sp["id"] in PIN or sp["tier"] == "gray" or sp.get("sec") not in secs:
        continue
    st = secs[sp["sec"]]["tier"]
    sp["tier"] = st
    sp["chip"] = "Biggest gain" if (sp["sec"] == big and st == "red") else LBL[st]

r["runs"] = [x["run"] for x in r["sectors"][0]["hist"]]
r["goal"] = f"Goal: every sector at or under {GREEN*100:.1f}% off the target (leader qualifying pace {LEADER}). Colors are recomputed from each run's clean laps."
d["updated"] = "2026-11-25"
(root / "data.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
for s in r["sectors"]:
    print(s["id"], s["tier"], s["stats"]["pct"], "%", s["stats"]["gap"], "s")
