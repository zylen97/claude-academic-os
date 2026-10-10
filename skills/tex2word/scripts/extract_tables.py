#!/usr/bin/env python3
"""Extract each table region from a compiled PDF as a tight 300dpi PNG.

Usage: extract_tables.py <manuscript.pdf> <outdir>
Finds caption lines "Table N." / "Table X.Y." / "Table N (continued)" with
PyMuPDF, slices the page between consecutive captions, computes the tight
content bbox (text + rules) inside each slice, renders it at 300 dpi.
Outputs <outdir>/table_<N>.png (continued pages -> table_<N>_cont.png).
"""
import re
import sys
from pathlib import Path

import fitz

pdf = Path(sys.argv[1])
outdir = Path(sys.argv[2])
outdir.mkdir(parents=True, exist_ok=True)
CAP = re.compile(r"^Table\s+([0-9]+|[A-Z]\.[0-9]+)(\.|\s+\(continued\))")
PAD = 4  # pt

doc = fitz.open(pdf)
for page in doc:
    # get_text/get_drawings return UNROTATED coords; pixmap clip uses rotated
    # display coords -> transform everything into display space first.
    mat = page.rotation_matrix
    lines = []  # (display y0, text)
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            text = "".join(s["text"] for s in ln["spans"]).strip()
            if text:
                lines.append(((fitz.Rect(ln["bbox"]) * mat).y0, text))
    lines.sort()
    anchors = []
    for y, text in lines:
        m = CAP.match(text)
        if m:
            name = m.group(1) + ("_cont" if "continued" in m.group(2) else "")
            anchors.append((y, name))
    if not anchors:
        continue
    W, H = page.rect.width, page.rect.height  # page.rect is already display space
    # drop the page number: on rotated pages it sits rotated at the page edge
    words = [fitz.Rect(w[:4]) * mat for w in page.get_text("words")
             if not (w[4].isdigit() and ((fitz.Rect(w[:4]) * mat).x1 < 60
                                         or (fitz.Rect(w[:4]) * mat).x0 > W - 60))]
    rules = [d["rect"] * mat for d in page.get_drawings()]
    for i, (y, name) in enumerate(anchors):
        top = y - 2
        bot = (anchors[i + 1][0] - 4) if i + 1 < len(anchors) else H * 0.94
        # tight content bbox inside the band (text words + drawn rules)
        boxes = [r for r in words + rules if top <= r.y0 and r.y1 <= bot]
        if not boxes:
            continue
        clip = boxes[0]
        for r in boxes[1:]:
            clip |= r
        clip = fitz.Rect(clip.x0 - PAD, clip.y0 - PAD, clip.x1 + PAD, clip.y1 + PAD) & page.rect
        pix = page.get_pixmap(dpi=300, clip=clip)
        out = outdir / f"table_{name}.png"
        pix.save(out)
        print(f"p{page.number + 1}: {out.name} {pix.width}x{pix.height}")
