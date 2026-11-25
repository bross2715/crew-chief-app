# Crew Chief HQ

NASCAR 26 setups, laps and coaching for Southpaw (Car 21).

Live app: https://bross2715.github.io/crew-chief-app/
Install it: open the link on your phone, then Add to Home Screen.

## How it updates
The page loads `data.json` each time it opens. A push that changes `data.json` is live on GitHub Pages in about a minute.
No rebuild is needed for data changes.

## Files
- `data.json`: tracks, laps, setups, race logs and the coach file. The only file that changes after a session.
- `maps.json`: track outlines. Rarely changes.
- `source/template.html`: the app code. After editing it run `python3 source/build.py` and push `index.html`.
- `source/build.py`: writes `index.html` (Pages) and `dist/artifact.html` (single file with data embedded, for the claude.ai artifact).
- `manifest.webmanifest`, `sw.js`, icons: make it installable.

## Rules
Never invent racing data. Tag laps verified, reported, recalled, approx or unknown. League race hub numbers are verified.
Coaching notes, track files and Grokbot feedback live in the private repo `crew-chief-hq` and are not published here.
This repo is public. Keep anything private out of `data.json`.
