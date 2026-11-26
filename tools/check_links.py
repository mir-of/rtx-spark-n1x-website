# -*- coding: utf-8 -*-
"""Check local links and assets in the generated site."""
from pathlib import Path
from html.parser import HTMLParser
import re
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
pages = sorted(ROOT.glob("*.html"))
problems = []
anchors = {}

class IDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v:
                self.ids.add(v)

for p in pages:
    text = p.read_text(encoding="utf-8", errors="replace")
    parser = IDParser()
    parser.feed(text)
    anchors[p.name] = parser.ids

for p in pages:
    text = p.read_text(encoding="utf-8", errors="replace")
    # hrefs and srcs
    for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
            continue
        if raw.startswith("#"):
            target = p.name
            frag = raw[1:]
            if frag and frag not in anchors.get(target, set()):
                problems.append(f"{p.name}: missing anchor {raw}")
            continue
        parsed = urllib.parse.urlsplit(raw)
        path_part = urllib.parse.unquote(parsed.path)
        target = (p.parent / path_part).resolve()
        if not target.exists():
            problems.append(f"{p.name}: missing file {raw}")
            continue
        if parsed.fragment:
            if target.suffix.lower() == ".html":
                ids = anchors.get(target.name)
                if ids is None:
                    t = target.read_text(encoding="utf-8", errors="replace")
                    pp = IDParser(); pp.feed(t); ids = pp.ids
                    anchors[target.name] = ids
                if parsed.fragment not in ids:
                    problems.append(f"{p.name}: missing anchor {raw}")

print("pages:", len(pages))
for p in pages:
    print(" -", p.name, p.stat().st_size, "bytes")
print("problems:", len(problems))
for x in problems:
    print(" !", x)
