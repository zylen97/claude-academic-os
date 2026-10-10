#!/usr/bin/env python3
"""Merge validated review batches into direction reports + screening summary.

Input : _review_runs/dispatch_plan.json and its filled batch files (all must be OK,
        see format_batches.py), _quota_result.json / literature_search_plan.md.
Output: direction{N}_report.md for every direction of the run,
        screening_summary_report.md (recomputed from all direction reports).

Per direction: WoS + OpenAlex share the international quota, CNKI has its own.
Within a track duplicates collapse first (lit_common unique-paper rule, best tier
kept), then tier caps apply in record order. Existing reports are only replaced
with --overwrite; the old copy is moved to _archive/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import format_batches as fb  # noqa: E402  (also puts the shared dir on sys.path)
import lit_common as lc  # noqa: E402
import dispatch_plan as dp  # noqa: E402

RANK = {t: i for i, t in enumerate(lc.TIERS)}
BOUNDARY = ("本阶段只做逐篇筛选与“疑似竞品”即时提示，不能据此判断是否存在直接竞品；"
            "正式竞品与创新性判断见 lit-pool 生成的 master_report.md。")


def collapse(papers: list[dict]) -> list[dict]:
    """One entry per unique paper: best tier wins, earliest record breaks ties."""
    out = []
    for group in lc.group_duplicates(papers):
        best = min(group, key=lambda i: (RANK[papers[i]["tier"]], i))
        p = dict(papers[best])
        p["_order"] = (RANK[p["tier"]], best)
        sus = [papers[i]["suspect"] for i in group if papers[i].get("suspect")]
        p["suspect"] = sus[0] if sus else ""
        out.append(p)
    return sorted(out, key=lambda p: p["_order"])


def select_track(papers: list[dict], caps: dict[str, int]) -> tuple[list[dict], list[dict]]:
    kept, dropped, used = [], [], {t: 0 for t in lc.TIERS}
    for p in collapse(papers):
        if used[p["tier"]] < caps[p["tier"]]:
            kept.append(p)
            used[p["tier"]] += 1
        else:
            dropped.append(p)
    return kept, dropped


def merge_direction(d: int, papers: list[dict], tracks: dict) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    intl = [p for p in papers if p["source_type"] in ("wos", "openalex")]
    cnki = [p for p in papers if p["source_type"] == "cnki"]
    for group, track in ((intl, "wos"), (cnki, "cnki")):
        if not group:
            continue
        cfg = tracks.get((d, track))
        if not cfg:
            raise ValueError(f"NO_QUOTA: D{d} has {track} records but no {track} quota")
        k, x = select_track(group, cfg["tiers"])
        kept += k
        dropped += x
    # a bilingual duplicate may survive two independently capped tracks
    final = collapse(kept)
    for t in lc.TIERS:
        rows = [p for p in final if p["tier"] == t]
        for i, p in enumerate(rows, 1):
            p["row"] = i
    return final, dropped


def render_report(d: int, name: str, papers: list[dict], dropped: list[dict], sources: list[dict]) -> str:
    counts = {t: sum(p["tier"] == t for p in papers) for t in lc.TIERS}
    src = "；".join(f"{s['source_file']} {s['record_count']}篇" for s in sources)
    retrieved = sum(s["record_count"] for s in sources)
    oa_drop = sum(p["source_type"] == "openalex" for p in dropped)
    lines = [f"# 方向{d}：{name} 文献筛选报告", "",
             f"> **日期**: {dt.date.today().isoformat()}",
             f"> **来源**: {src}",
             f"> **检索结果**: {retrieved}篇",
             f"> **最终入选**: {len(papers)}篇（核心 {counts['core']} / 重要 {counts['important']} / 备选 {counts['backup']}）",
             f"> **超出配额未入选**: {len(dropped)}篇" + (f"（其中 OpenAlex 补充 {oa_drop}篇）" if oa_drop else ""),
             ""]
    for t in lc.TIERS:
        lines += [f"## {lc.TIER_HEADINGS[t]}", "",
                  "| # | 作者 | 标题 | 年份 | 期刊 | 入选理由 |",
                  "|:--|:-----|:-----|:----:|:-----|:---------|"]
        for p in (p for p in papers if p["tier"] == t):
            lines.append(f"| {p['row']} | {lc.cell(p['author'])} | {lc.cell(p['title'])} | {p['year']} | "
                         f"{lc.cell(p['journal'])} | {lc.cell(p['reason'])} |")
        lines.append("")
    lines += ["## 疑似竞品（review 即时提示，未核实）", ""]
    sus = [p for p in papers if p.get("suspect")]
    if sus:
        lines += [f"- {p['tier']}:{p['row']} {lc.cell(p['author'])} ({p['year']}) {lc.cell(p['title'])} —— {lc.cell(p['suspect'])}"
                  for p in sus]
    else:
        lines.append("本方向未标出疑似竞品（不等于不存在竞品）。")
    lines += ["", "## 竞品判断边界", "", BOUNDARY, ""]
    records = [{"tier": p["tier"], "row": p["row"], "record_id": p["record_id"], "source_type": p["source_type"],
                "source_file": p["source_file"], "doi": p["doi"], "database_id": p["database_id"]} for p in papers]
    lines.append(f"{lc.RECORDS_PREFIX}{json.dumps(records, ensure_ascii=False)} -->")
    return "\n".join(lines) + "\n"


def render_summary(lit_dir: Path, plan_dirs: list[int], names: dict[int, str], budget: int) -> tuple[str, dict]:
    skipped = lc.skipped_directions(lit_dir, ("review",))
    reports = {d: p for d, p in lc.direction_reports(lit_dir).items() if d not in skipped}
    lines = ["# 文献筛选汇总报告", "", f"> **日期**: {dt.date.today().isoformat()}",
             "> **去重口径**: DOI、WoS UT、第一作者+年份+标题前80字符，任一相同即视为同一篇", "",
             "| 方向 | 名称 | 检索数 | 核心 | 重要 | 备选 | 入选合计 | 状态 |",
             "|:----:|:-----|:------:|:----:|:----:|:----:|:--------:|:-----|"]
    every, suspects = [], []
    for d in sorted(set(plan_dirs) | set(reports) | skipped):
        if d not in reports:
            lines.append(f"| D{d} | {names.get(d, f'方向{d}')} | — | — | — | — | — | {'用户确认跳过' if d in skipped else '无报告'} |")
            continue
        text = lc.read_text(reports[d])
        papers = lc.report_papers(reports[d])
        every += papers
        m = re.search(r"\*\*检索结果\*\*:\s*(\d+)", text)
        c = {t: sum(p["tier"] == t for p in papers) for t in lc.TIERS}
        status = "完成" if d in plan_dirs else "计划外"
        title = re.search(r"^#\s*方向\d+[：:]\s*(.+?)\s*文献筛选报告", text, re.M)
        lines.append(f"| D{d} | {title.group(1) if title else names.get(d, f'方向{d}')} | {m.group(1) if m else '?'} | "
                     f"{c['core']} | {c['important']} | {c['backup']} | {len(papers)} | {status} |")
        sec = re.search(r"^## 疑似竞品[^\n]*\n(.*?)(?=^## )", text, re.M | re.S)
        if sec:
            suspects += [f"- D{d} {ln[2:].strip()}" for ln in sec.group(1).splitlines() if ln.startswith("- ")]
    unique = len(lc.group_duplicates(every))
    lines += ["", f"- 各方向入选合计（含跨方向重复）: {len(every)}",
              f"- 跨方向重复: {len(every) - unique}",
              f"- 去重后独立文献: {unique}"]
    if budget:
        lines.append(f"- 预算: {budget}（{'超出，请检查配额' if len(every) > budget else '未超出'}）")
    lines += ["", "## 疑似竞品汇总（未核实）", ""]
    lines += suspects or ["各方向均未标出疑似竞品（不等于不存在竞品）。"]
    lines += ["", BOUNDARY, ""]
    return "\n".join(lines), {"occurrences": len(every), "unique": unique, "suspects": suspects}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace existing direction reports of this run (old copies go to _archive/)")
    ap.add_argument("--budget", type=int, default=None, help="default: total_budget in _quota_result.json")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    try:
        plan, results = fb.validate_all(lit_dir)
        bad = [f"{r['batch_id']}: {r['status']} {r['errors'][:2]}" for r in results if r["status"] != "OK"]
        if bad:
            raise ValueError("BATCHES_NOT_READY (run format_batches.py, redo these batches):\n  " + "\n  ".join(bad))
        cfg = dp.load_plan(lit_dir)
        run_dirs = [int(d) for d in plan["directions"]]
        names = dict(cfg["names"])
        names.update({int(k): v for k, v in plan.get("names", {}).items()})
        by_dir: dict[int, list[dict]] = defaultdict(list)
        for r in results:
            for p in r["included"]:
                by_dir[p["direction"]].append(p)
        data_errors = []
        for ps in by_dir.values():
            for p in ps:
                if not re.fullmatch(r"\d{4}", p["year"]):
                    data_errors.append(f"{p['record_id']}: RIS lacks a 4-digit year (PY/Y1)")
                if not p["author"]:
                    data_errors.append(f"{p['record_id']}: RIS lacks an author (AU)")
        if data_errors:
            raise ValueError("INCLUDED_RECORD_INCOMPLETE (fix the RIS record, then rerun dispatch):\n  " + "\n  ".join(data_errors[:20]))
        existing = [d for d in run_dirs if (lit_dir / f"direction{d}_report.md").exists()]
        if existing and not args.overwrite:
            raise ValueError(f"REPORT_EXISTS: {['direction%d_report.md' % d for d in existing]} — confirm with the user, then rerun with --overwrite (old copies are archived)")
        rendered, dropped_all = {}, {}
        for d in run_dirs:
            sources = [s for s in plan["sources"] if s["direction"] == d]
            final, dropped = merge_direction(d, by_dir.get(d, []), cfg["tracks"])
            rendered[d] = render_report(d, names.get(d, f"方向{d}"), final, dropped, sources)
            dropped_all[d] = (final, dropped)
        with tempfile.TemporaryDirectory(prefix=".review-stage-", dir=lit_dir) as tmp:
            for d, text in rendered.items():
                (Path(tmp) / f"direction{d}_report.md").write_text(text, encoding="utf-8")
            for d in rendered:
                target = lit_dir / f"direction{d}_report.md"
                if target.exists():
                    if target.read_text(encoding="utf-8") == rendered[d]:
                        continue
                    print(f"NOTICE: archived old {target.name} -> {lc.archive(target, lit_dir)}")
                os.replace(Path(tmp) / target.name, target)
        budget = args.budget if args.budget is not None else cfg["budget"]
        summary, stats = render_summary(lit_dir, cfg["directions"], cfg["names"], budget)
        dp.atomic_write(lit_dir / "screening_summary_report.md", summary)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, dp.PlanError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    print("=== MERGE SUMMARY ===")
    for d in run_dirs:
        final, dropped = dropped_all[d]
        c = {t: sum(p["tier"] == t for p in final) for t in lc.TIERS}
        oa = sum(p["source_type"] == "openalex" for p in dropped)
        print(f"D{d}: {len(final)} selected (core={c['core']}, important={c['important']}, backup={c['backup']}); "
              f"over quota {len(dropped)}" + (f" ⚠️ incl. {oa} OpenAlex supplement(s) dropped" if oa else ""))
    print(f"All reports: {stats['occurrences']} occurrences, {stats['unique']} unique papers")
    if budget and stats["occurrences"] > budget:
        print(f"⚠️ occurrences {stats['occurrences']} > budget {budget}")
    for s in stats["suspects"]:
        print(f"⚠️ 疑似竞品 {s[2:]}")
    print("=== VERIFY: PASS ===")


if __name__ == "__main__":
    main()
