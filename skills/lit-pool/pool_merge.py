#!/usr/bin/env python3
"""Assemble citation_pool/{BG,LR,GAP,METHOD,DISC,COMP}.md from formatted agents.

Input : _pool_runs/pool_prepare.json + _pool_runs/pool_agent{N}.md (format_pool_agents.py).
Blocking: a formatted file missing; the (label, key) pairs in the formatted files
differ from the planned assignments. All six files are always written (an empty
COMP or METHOD pool is a reported risk, not an error). A changed existing pool
file is moved to _archive/ before being replaced.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def _shared() -> None:
    for base in Path(__file__).resolve().parents:
        for cand in (base / "shared", base / "_academic-shared" / "scripts"):
            if (cand / "lit_common.py").is_file():
                sys.path.insert(0, str(cand))
                return
    raise SystemExit("ERROR: lit_common.py not found (shared scripts directory)")


_shared()
import lit_common as lc  # noqa: E402
import dispatch_plan as dp  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from format_pool_agents import POOL_DIR, TABLE_HEADER, load_prepare  # noqa: E402

FULL = {"BG": "Background", "LR": "Literature Review", "GAP": "Gap Support",
        "METHOD": "Methodology", "DISC": "Discussion", "COMP": "Competitor"}
CHAPTER = {"BG": "Introduction [主]", "LR": "Literature Review [主]", "GAP": "Introduction + Literature Review",
           "METHOD": "Methodology [主]", "DISC": "Discussion [主]", "COMP": "跨章节（创新性论证）"}
PREF = {"BG": "优先投稿年及前两年的高质量期刊", "LR": "优先高引经典 + 理论脉络文献",
        "GAP": "优先同主题不同视角的文献", "METHOD": "优先方法原始文献 + 应用先例",
        "DISC": "优先可对话的实证/模型结果", "COMP": "优先问题、对象、机制高度重叠的研究"}


def pool_rows(text: str) -> list[list[str]]:
    return [lc.split_row(l) for l in text.splitlines() if re.match(r"^\|\s*(核心|重要|备选)\s*\|", l)]


def pool_keys(path: Path) -> set[str]:
    return {r[3] for r in pool_rows(lc.read_text(path)) if len(r) >= 6} if path.exists() else set()


def read_formatted(lit_dir: Path, prep: dict) -> tuple[dict[str, list[str]], list[str]]:
    by_tag: dict[str, list[str]] = defaultdict(list)
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    expected = {(t, k) for a in prep["agents"] for t, k in a["assignments"]}
    for a in prep["agents"]:
        path = lit_dir / POOL_DIR / a["formatted_file"]
        if not path.exists():
            errors.append(f"FORMATTED_MISSING: {a['formatted_file']} (run format_pool_agents.py)")
            continue
        tag = None
        for line in lc.read_text(path).splitlines():
            h = re.match(r"^#\s+(\S+)\s*$", line)
            if h:
                tag = h.group(1)
                continue
            if tag and re.match(r"^\|\s*(核心|重要|备选)\s*\|", line):
                key = lc.split_row(line)[3]
                if (tag, key) in seen:
                    errors.append(f"DUPLICATE: {key}@{tag}")
                seen.add((tag, key))
                by_tag[tag].append(line)
    if not errors and seen != expected:
        errors.append(f"ASSIGNMENTS_DIFFER: missing={sorted(expected - seen)[:5]} extra={sorted(seen - expected)[:5]}")
    return by_tag, errors


def render(group: str, sections: dict[str, list[str]]) -> str:
    n = sum(len(v) for v in sections.values())
    out = [f"# {group} — {FULL[group]}（{n}条）", "",
           f"> **生成日期**: {dt.date.today().isoformat()}",
           f"> **引用偏好**: {PREF[group]}",
           f"> **服务章节**: {CHAPTER[group]}", ""]
    rank = {"核心": 0, "重要": 1, "备选": 2}

    def order(row: str) -> tuple:
        c = lc.split_row(row)
        return (rank.get(c[0], 3), -int(c[2]) if c[2].isdigit() else 0, c[3])

    if len(sections) > 1:
        for tag in sorted(sections):
            out += [f"## {tag}（{len(sections[tag])}条）", "", *TABLE_HEADER, *sorted(sections[tag], key=order), ""]
    else:
        rows = next(iter(sections.values()), [])
        out += [*TABLE_HEADER, *sorted(rows, key=order), ""]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    try:
        prep = load_prepare(lit_dir)
        by_tag, errors = read_formatted(lit_dir, prep)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        by_tag, errors = {}, [str(exc)]
    if errors:
        print("=== VERIFY: FAIL ===")
        for e in errors[:20]:
            print(f"  ❌ {e}")
        raise SystemExit(1)
    files: dict[str, dict[str, list[str]]] = {g: {} for g in lc.POOL_FILES}
    for tag, rows in by_tag.items():
        files[lc.label_group(tag)][tag] = rows
    pool_dir = lit_dir / "citation_pool"
    print("=== POOL MERGE ===")
    for group, sections in files.items():
        text = render(group, sections)
        target = pool_dir / f"{group}.md"
        if target.exists() and lc.read_text(target) != text:
            lc.archive(target, lit_dir)
        dp.atomic_write(target, text)
        n = sum(len(v) for v in sections.values())
        print(f"  {group}.md: {n}" + ("  ⚠️ empty — report as residual risk" if n == 0 and group in ("COMP", "METHOD") else ""))
    print("=== VERIFY: PASS ===")


if __name__ == "__main__":
    main()
