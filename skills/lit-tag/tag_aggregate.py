#!/usr/bin/env python3
"""Aggregate tagged_reports/ into tag_report.md (unique-paper counts).

Blocking: tagged_reports/ does not mirror the review reports (missing / extra /
stale copy); a paper without a valid label. Adequacy against pool targets is
informational only. Counts use the shared unique-paper rule (lit_common):
DOI, WoS UT, or first author + year + title[:80]; duplicates merge their labels
and keep the best tier. Direction contributions are occurrence-based.
"""
from __future__ import annotations

import argparse
import datetime as dt
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

allowed_tags, split_tags = lc.allowed_labels, lc.split_labels

POOL_TARGETS = {"BG": 50, "LR": 150, "GAP": 75, "METHOD": 60, "DISC": 65}
RANK = {t: i for i, t in enumerate(lc.TIERS)}


tag_group = lc.label_group


def load_tagged(lit_dir: Path, rq_count: int) -> tuple[list[dict], list[str]]:
    """All tagged rows (occurrences) after the blocking consistency checks."""
    errors = lc.compare_tagged_to_review(lit_dir)
    allowed = allowed_tags(rq_count)
    rows: list[dict] = []
    for d, path in sorted(lc.active_tagged_reports(lit_dir).items()):
        for r in lc.report_papers(path):
            if r["ncols"] != 7:
                errors.append(f"TABLE_SCHEMA: {path.name} {r['tier']}:{r['row']} has {r['ncols']} columns, expected 7")
                continue
            labels = split_tags(r["tags"] or "")
            bad = [t for t in labels if t not in allowed]
            if not labels or bad:
                errors.append(f"TAG_INVALID: D{d} {r['tier']}:{r['row']} {r['tags']!r}")
                continue
            r["labels"] = labels
            rows.append(r)
    return rows, errors


def unique_papers(rows: list[dict]) -> list[dict]:
    out = []
    for group in lc.group_duplicates(rows):
        best = min(group, key=lambda i: (RANK[rows[i]["tier"]], i))
        p = dict(rows[best])
        p["labels"] = sorted({t for i in group for t in rows[i]["labels"]})
        p["occurrences"] = [rows[i] for i in group]
        p["directions"] = sorted({rows[i]["direction"] for i in group})
        out.append(p)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--rq-count", type=int, required=True)
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    try:
        rows, errors = load_tagged(lit_dir, args.rq_count)
    except (OSError, ValueError) as exc:
        errors, rows = [str(exc)], []
    if not rows and not errors:
        errors.append("NO_TAGGED_PAPERS: tagged_reports/ is empty")
    if errors:
        print("=== VERIFY: FAIL ===")
        for e in errors[:30]:
            print(f"  ❌ {e}")
        print("tag_report.md not written.")
        raise SystemExit(1)

    uniq = unique_papers(rows)
    tag_tier = defaultdict(lambda: defaultdict(int))
    group_n = defaultdict(int)
    for p in uniq:
        for t in p["labels"]:
            tag_tier[t][p["tier"]] += 1
        for g in {tag_group(t) for t in p["labels"]}:
            group_n[g] += 1
    dir_group = defaultdict(lambda: defaultdict(int))
    for r in rows:
        for g in {tag_group(t) for t in r["labels"]}:
            dir_group[r["direction"]][g] += 1

    L = ["# 标签统计报告", "",
         f"> **日期**: {dt.date.today().isoformat()}",
         f"> **RQ 数**: {args.rq_count}",
         f"> **去重后独立文献**: {len(uniq)}篇",
         f"> **方向内入选记录**: {len(rows)}条（方向贡献表按出现次数计）", "",
         "## 标签分布（按独立文献）", "",
         "| 标签 | 核心 | 重要 | 备选 | 合计 |", "|:-----|:----:|:----:|:----:|:----:|"]
    for t in sorted(tag_tier):
        c = tag_tier[t]
        L.append(f"| {t} | {c['core']} | {c['important']} | {c['backup']} | {sum(c.values())} |")
    L += ["", "## 均衡性预警", "", "| 标签组 | Pool目标 | 实际 | 达标率 | 状态 |", "|:-----|:-------:|:----:|:-----:|:----:|"]
    for g, target in POOL_TARGETS.items():
        n = group_n.get(g, 0)
        rate = round(n / target * 100, 1)
        L.append(f"| {g} | {target} | {n} | {rate}% | {'✅' if rate >= 80 else '⚠️' if rate >= 50 else '❌'} |")
    L.append(f"| COMP | — | {group_n.get('COMP', 0)} | — | {'⚠️ 当前语料未标出竞品（不等于不存在）' if not group_n.get('COMP') else '—'} |")
    groups = sorted({g for v in dir_group.values() for g in v})
    L += ["", "## 各方向标签贡献（按出现次数）", "",
          "| 方向 | " + " | ".join(groups) + " |", "|:-----|" + "|".join(":--:" for _ in groups) + "|"]
    for d in sorted(dir_group):
        L.append(f"| D{d} | " + " | ".join(str(dir_group[d].get(g, 0)) for g in groups) + " |")
    dp.atomic_write(lit_dir / "tag_report.md", "\n".join(L) + "\n")

    print("=== TAG AGGREGATE ===")
    print(f"Unique papers: {len(uniq)}; direction occurrences: {len(rows)}")
    for g, target in POOL_TARGETS.items():
        print(f"  {g}: {group_n.get(g, 0)}/{target}")
    print(f"  COMP: {group_n.get('COMP', 0)}")
    print("=== VERIFY: PASS ===")
    print(f"Report: {lit_dir / 'tag_report.md'}")


if __name__ == "__main__":
    main()
