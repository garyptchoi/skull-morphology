#!/usr/bin/env python3
from pathlib import Path
import html
import re
import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = [
    (DOCS / "START_HERE.md", "start-here.html", "Start here"),
    (DOCS / "REPRODUCE.md", "reproduce.html", "Reproduce"),
    (DOCS / "REFERENCE.md", "reference.html", "Script reference"),
    (ROOT / "data/README.md", "data.html", "Data sources"),
    (ROOT / "data/figure_inputs/README.md", "figure-inputs.html", "Figure inputs"),
    (ROOT / "1_remeshing/Remeshing/README.md", "remeshing.html", "Remeshing setup"),
]
LINKS = {
    "START_HERE.md": "start-here.html", "REPRODUCE.md": "reproduce.html",
    "REFERENCE.md": "reference.html", "../README.md": "index.html",
    "../data/README.md": "data.html", "../data/figure_inputs/README.md": "figure-inputs.html",
    "../1_remeshing/Remeshing/README.md": "remeshing.html",
}


def render(source, destination, title):
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "toc"])
    def rewrite(match):
        url = match.group(1)
        path, mark, anchor = url.partition("#")
        return 'href="' + LINKS.get(path, path) + (mark + anchor if mark else "") + '"'
    body = re.sub(r'href="([^"]+)"', rewrite, body)
    nav = ''.join(f'<a href="{file}"' + (' aria-current="page"' if file == destination else '') +
                  f'>{label}</a>' for file, label in [
                      ("index.html", "Project overview"), ("start-here.html", "Start here"),
                      ("reproduce.html", "Reproduce"), ("reference.html", "Script reference"),
                      ("data.html", "Data sources"), ("citation.html", "Citation")])
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Skull morphology</title><link rel="stylesheet" href="assets/site.css"></head>
<body><a class="skip" href="#main">Skip to content</a><div class="shell">
<header class="masthead"><a class="brand" href="index.html">skull / morphology<small>GEOMETRY · BIOLOGY · CODE</small></a>
<nav aria-label="Main navigation"><a href="index.html">Overview</a><a href="start-here.html">Start here</a><a class="repo-link" href="https://github.com/kaikwanlau/skull-morphology">GitHub ↗</a></nav></header>
<div class="article-layout"><aside class="article-nav" aria-label="Guide contents">{nav}</aside><main class="article" id="main">{body}</main></div>
<footer class="footer"><span>SKULL / MORPHOLOGY — RESEARCH GUIDE</span><a href="index.html">Back to the visual guide ↑</a></footer>
</div></body></html>'''
    (DOCS / destination).write_text(page, encoding="utf-8")


for source, destination, title in PAGES:
    render(source.read_text(encoding="utf-8"), destination, title)
readme = (ROOT / "README.md").read_text(encoding="utf-8")
citation = readme.split("## Cite this work\n", 1)[1].split("Code license:", 1)[0]
render("# Cite this work\n\n" + citation, "citation.html", "Citation")
print("Built 7 static guide pages in docs/.")
