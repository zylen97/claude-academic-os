#!/usr/bin/env python3
"""Preprocess a LaTeX manuscript for pandoc -> docx conversion.

Usage: preprocess.py <manuscript.tex> <output.tex> [<tables-png-dir>]
Reads <manuscript.aux> next to the input for true cross-reference numbers.
If <tables-png-dir> is given (PNGs from extract_tables.py), every table /
longtable environment is replaced by its PDF-rendered image.
Prints the extracted \\title{} text to stdout (for pandoc --metadata title=).
"""
import re
import struct
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
tables_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else None
tex = src.read_text(encoding="utf8")

# 0. Expand \input{...} so table/figure files can be transformed in one stream
tex = re.sub(r"\\input\{([^}]+)\}",
             lambda m: Path(m.group(1)).read_text(encoding="utf8")
             if Path(m.group(1)).exists() else m.group(0), tex)

# 1. Resolve \ref/\eqref from the .aux file (true LaTeX numbers, incl. appendix letters)
aux = src.with_suffix(".aux")
labels = {}
if aux.exists():
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux.read_text(encoding="utf8")):
        labels[m.group(1)] = m.group(2).replace("~", " ")
def sub_ref(m):
    return labels.get(m.group(2), m.group(2)).strip()
tex = re.sub(r"(~?)\\ref\{([^}]+)\}", lambda m: (" " if m.group(1) else "") + sub_ref(m), tex)
tex = re.sub(r"\\eqref\{([^}]+)\}", lambda m: "(" + labels.get(m.group(1), m.group(1)) + ")", tex)

# 2. Extract title for pandoc metadata; keep frontmatter otherwise (abstract parses fine)
title = ""
tm = re.search(r"\\title\{(.+?)\}\s*$", tex, flags=re.M)
if tm:
    title = tm.group(1)

# 3. Keywords env -> labeled plain paragraph
tex = re.sub(
    r"\\begin\{keyword\}(.*?)\\end\{keyword\}",
    lambda m: "\\textbf{Keywords:} " + " ; ".join(
        s.strip() for s in m.group(1).replace("\n", " ").split("\\sep")) ,
    tex, flags=re.S)

# 3.5 Optionally replace table/longtable envs with PDF-rendered images
TEXTWIDTH_PX = 1890  # PDF text width at 300 dpi (16 cm); used to keep relative table widths
def png_width(p):
    with open(p, "rb") as f:
        f.seek(16)
        return struct.unpack(">I", f.read(4))[0]
def table_to_image(m):
    lm = re.search(r"\\label\{([^}]+)\}", m.group(0))
    num = labels.get(lm.group(1)) if lm else None
    if not num or not tables_dir:
        return m.group(0)
    parts = []
    for suffix in ("", "_cont"):
        img = tables_dir / f"table_{num}{suffix}.png"
        if img.exists():
            w = min(1.0, png_width(img) / TEXTWIDTH_PX)
            parts.append("\\includegraphics[width=%.2f\\textwidth]{%s}" % (w, img.as_posix()))
    return "\n\n".join(parts) + "\n" if parts else m.group(0)
if tables_dir and tables_dir.exists():
    tex = re.sub(r"\\begin\{table\}.*?\\end\{table\}", table_to_image, tex, flags=re.S)
    tex = re.sub(r"\\begin\{longtable\}.*?\\end\{longtable\}", table_to_image, tex, flags=re.S)

# 3.6 Number figure captions to match the compiled PDF ("Figure N: ...")
def number_fig_caption(m):
    env = m.group(0)
    lm = re.search(r"\\label\{(fig:[^}]+)\}", env)
    num = labels.get(lm.group(1)) if lm else None
    if num:
        env = re.sub(r"\\caption\{", r"\\caption{Figure %s: " % num, env, count=1)
    return env
tex = re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", number_fig_caption, tex, flags=re.S)

# 4. Strip wrappers pandoc chokes on (tables inside them would be silently dropped)
tex = re.sub(r"\\begin\{adjustbox\}\{[^}]*\}\s*", "", tex)
tex = re.sub(r"\\end\{adjustbox\}\s*", "", tex)
tex = re.sub(r"\\begin\{(landscape|center)\}", "", tex)
tex = re.sub(r"\\end\{(landscape|center)\}", "", tex)
tex = re.sub(r"\\resizebox\{[^}]*\}\{[^}]*\}\{", "", tex)  # opening only; stray } is harmless in pandoc

# 5. Appendix sections -> unnumbered "Appendix X." headings (letters from aux order)
parts = tex.split("\\appendix", 1)
if len(parts) == 2:
    counter = [0]
    def appendix_section(m):
        counter[0] += 1
        return "\\section*{Appendix %s. %s}" % (chr(64 + counter[0]), m.group(1))
    parts[1] = re.sub(r"\\section\{([^}]+)\}", appendix_section, parts[1])
    tex = parts[0] + parts[1]

# 6. Sanitize citation keys with curly quotes (pandoc's bibtex parser rejects them)
tex = re.sub(r"\\cite([pt]?|alp|year)(\[[^]]*\])?\{([^}]*)\}",
             lambda m: m.group(0).replace("’", "'"), tex)

dst.write_text(tex, encoding="utf8")
print(title)
