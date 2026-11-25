#!/usr/bin/env python3
"""Build Crew Chief HQ.

index.html : the GitHub Pages app. Loads data.json and maps.json when it opens,
                  so a push that changes data.json updates the app with no rebuild.
dist/artifact.html : single file with the data embedded, for publishing as a claude.ai artifact.
Run from the repo root: python3 source/build.py
"""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
tpl = (root / "source" / "template.html").read_text()
data = (root / "data.json").read_text()
maps = (root / "maps.json").read_text()
json.loads(data); json.loads(maps)  # fail loudly on bad JSON

pwa = ('<link rel="manifest" href="manifest.webmanifest">'
       '<meta name="theme-color" content="#070a0f">'
       '<meta name="apple-mobile-web-app-capable" content="yes">'
       '<meta name="mobile-web-app-capable" content="yes">'
       '<meta name="apple-mobile-web-app-title" content="Crew Chief">'
       '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
       '<link rel="apple-touch-icon" href="apple-touch-icon.png">'
       '<link rel="icon" href="icon-192.png">'
       '<meta property="og:title" content="Crew Chief HQ">'
       '<meta property="og:description" content="NASCAR 26 setups, laps and coaching for Southpaw">'
       '<meta property="og:image" content="https://bross2715.github.io/crew-chief-app/icon-512.png">'
       '<meta property="og:url" content="https://bross2715.github.io/crew-chief-app/">'
       '<meta name="twitter:card" content="summary">')

import base64
avatar_uri = "data:image/png;base64," + base64.b64encode((root / "avatar.png").read_bytes()).decode()
site = tpl.replace("__AVATAR__", "avatar.png").replace("__PWA__", pwa).replace("__EMBED__", "false").replace("__DATA__", "null").replace("__MAPS__", "null")
(root / "index.html").write_text(site)

art = tpl.replace("__AVATAR__", avatar_uri).replace("__PWA__", "").replace("__EMBED__", "true").replace("__DATA__", data).replace("__MAPS__", maps)
(root / "dist").mkdir(exist_ok=True)
(root / "dist" / "artifact.html").write_text(art)
print("built index.html and dist/artifact.html")
