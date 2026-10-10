#!/usr/bin/env python3
"""Write the master_report.md skeleton (data filled, judgments as <!-- JUDGE --> blocks).

Input : _pool_runs/pool_prepare.json, citation_pool/*.md + master.bib, tag_report.md,
        screening_summary_report.md, tagged_reports/, idea.md.
Blocking: pool files or master.bib disagree with the prepared corpus.
An existing master_report.md is moved to _archive/ first (its judgments can be
carried over by hand). Exit message: DATA PASS — JUDGMENT PENDING.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
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
from format_pool_agents import load_prepare  # noqa: E402
from pool_merge import pool_keys, pool_rows  # noqa: E402
from ris2bib import bib_keys  # noqa: E402


def expected_groups(papers: list[dict]) -> dict[str, set[str]]:
    exp = {g: set() for g in lc.POOL_FILES}
    for p in papers:
        for t in p["tags"]:
            exp[lc.label_group(t)].add(p["citation_key"])
    return exp


def cross_check(lit_dir: Path, papers: list[dict]) -> list[str]:
    errors = []
    pool = lit_dir / "citation_pool"
    for g, keys in expected_groups(papers).items():
        path = pool / f"{g}.md"
        if not path.exists():
            errors.append(f"POOL_FILE_MISSING: {g}.md")
        elif pool_keys(path) != keys:
            got = pool_keys(path)
            errors.append(f"POOL_KEYS_{g}: missing={sorted(keys - got)[:8]} extra={sorted(got - keys)[:8]}")
    bib = pool / "master.bib"
    want = {p["citation_key"] for p in papers}
    if not bib.exists():
        errors.append("MASTER_BIB_MISSING: run ris2bib.py")
    elif set(bib_keys(lc.read_text(bib))) != want:
        errors.append("MASTER_BIB_KEYS differ from the prepared corpus (rerun ris2bib.py)")
    return errors


def gaps_and_rqs(idea: Path) -> tuple[list[dict], list[str]]:
    if not idea.exists():
        return [], []
    text = lc.read_text(idea)
    gaps = [{"id": f"G{m.group(1)}", "desc": m.group(2).strip()} for m in re.finditer(
        r"^(?:#{2,6}\s*|[-*]\s*)?(?:\*\*)?(?:Research\s+)?Gap\s*(\d+)\s*(?:\*\*)?\s*[:：.-]\s*(.+)$", text, re.M | re.I)]
    rqs = [f"RQ{m.group(1)}: {m.group(2).strip()}" for m in re.finditer(
        r"^(?:#{2,6}\s*|[-*]\s*)?(?:\*\*)?RQ\s*(\d+)\s*(?:\*\*)?\s*[:：.-]\s*(.+)$", text, re.M | re.I)]
    return list({g["id"]: g for g in gaps}.values()), list(dict.fromkeys(rqs))


def adequacy(tag_report: Path) -> list[list[str]]:
    if not tag_report.exists():
        return []
    sec = re.search(r"^## 均衡性预警\s*\n(.*?)(?=^## |\Z)", lc.read_text(tag_report), re.M | re.S)
    return [c for c in (lc.split_row(l) for l in (sec.group(1).splitlines() if sec else []) if l.startswith("|"))
            if c and c[0] in ("BG", "LR", "GAP", "METHOD", "DISC", "COMP")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--idea-file", required=True, help="structure/0_global/idea.md")
    ap.add_argument("--project-id", default="")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    try:
        prep = load_prepare(lit_dir)
        papers = prep["papers"]
        errors = cross_check(lit_dir, papers)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        papers, errors = [], [str(exc)]
    if errors:
        print("=== VERIFY: FAIL ===")
        for e in errors:
            print(f"  ❌ {e}")
        raise SystemExit(1)

    pool = lit_dir / "citation_pool"
    tiers = {t: sum(p["tier"] == t for p in papers) for t in lc.TIERS}
    comp = pool_rows(lc.read_text(pool / "COMP.md"))
    method = [r for r in pool_rows(lc.read_text(pool / "METHOD.md")) if r[0] in ("核心", "重要")]
    bg = [f"{r[1]} ({r[2]}) {r[3]}" for r in pool_rows(lc.read_text(pool / "BG.md"))[:8]]
    gaps, rqs = gaps_and_rqs(Path(args.idea_file))
    summary = lit_dir / "screening_summary_report.md"
    retrieved = 0
    if summary.exists():
        for c in (lc.split_row(l) for l in lc.read_text(summary).splitlines() if re.match(r"^\|\s*D\d+\s*\|", l)):
            retrieved += int(c[2]) if len(c) > 2 and c[2].isdigit() else 0
    tagged = lc.active_tagged_reports(lit_dir)
    pid = args.project_id or lit_dir.resolve().parents[1].name.split("_")[0]

    L = [f"# 文献总报告 — {pid}", "",
         f"> **日期**: {dt.date.today().isoformat()}",
         f"> **方向数**: {len(tagged)}",
         f"> **检索记录**: {retrieved or '未记录'}；方向内入选 {prep['total_occurrences']} 条；去重后 {len(papers)} 篇"
         f"（核心 {tiers['core']} + 重要 {tiers['important']} + 备选 {tiers['backup']}）",
         "> **语料表**: `literature_manifest.json`（lit-pool 收尾时生成）", "", "---", "",
         "## 一、创新性判断：有没有人做过？", "", "### 竞品清单（COMP）", ""]
    if comp:
        L += ["| # | citation key | 作者 | 年份 | 分级 | 引用场景/关键差异 |", "|:--|:--|:--|:--:|:--:|:--|"]
        L += [f"| {i} | {r[3]} | {r[1]} | {r[2]} | {r[0]} | {r[4][:120]} |" for i, r in enumerate(comp, 1)]
    else:
        L.append("*当前语料未标出直接竞品；这不是不存在竞品的证明，判断中须说明残余检索风险。*")
    L += ["", "### 判断", "", "<!-- JUDGE: 竞品判断（含残余检索风险；可参考 screening_summary_report.md 的疑似竞品汇总） -->", "",
          "---", "", "## 二、Research Gap 分析", ""]
    if gaps:
        L += ["| Gap | 描述 | 评估 | 文献支撑 | 理由 |", "|:--|:--|:--:|:--|:--|"]
        L += [f"| {g['id']} | {lc.cell(g['desc'])[:100]} | <!-- JUDGE --> | <!-- JUDGE --> | <!-- JUDGE --> |" for g in gaps]
    else:
        hint = "；".join(rqs[:5]) or "未识别到 RQ"
        L.append(f"<!-- JUDGE: idea.md 未识别到编号 Gap；已识别：{lc.cell(hint)}。按 idea.md 原结构填写，禁止臆造。 -->")
    L += ["", "---", "", "## 三、方法论先例", ""]
    if method:
        L += ["| # | citation key | 作者 | 年份 | 分级 | 引用场景 |", "|:--|:--|:--|:--:|:--:|:--|"]
        L += [f"| {i} | {r[3]} | {r[1]} | {r[2]} | {r[0]} | {r[4][:100]} |" for i, r in enumerate(method[:20], 1)]
    else:
        L.append("*当前语料没有核心/重要级方法先例；这是方法论证与补检风险，不是脚本错误。*")
    L += ["", "### 结论", "", "<!-- JUDGE: 方法论结论（充分先例/部分先例/当前语料无强先例，并说明风险） -->", "",
          "---", "", "## 四、紧迫性与实践需求", ""]
    if bg:
        L.append(f"> **BG 素材**：{'；'.join(bg)}")
    L += ["", "<!-- JUDGE: 紧迫性（至少引用 2-3 篇 BG 文献，区分学术证据与政策/事件证据） -->", "",
          "---", "", "## 五、引用池充足性", "", "| 分级 | 数量 |", "|:--|:--:|"]
    L += [f"| {lc.TIER_CN[t]} | {tiers[t]} |" for t in lc.TIERS]
    L += ["", "| 标签组 | Pool目标 | 实际 | 达标率 | 状态 |", "|:--|:--:|:--:|:--:|:--:|"]
    L += ["| " + " | ".join(c[:5]) + " |" for c in adequacy(lit_dir / "tag_report.md")]
    L += ["", "---", "", "## 六、补检建议", "",
          "<!-- JUDGE: 依据薄弱标签、RQ 对话文献、竞品/方法残余风险给出补检建议（补检只能经 lit-workflow 的 OpenAlex→RIS→review 回流）；无需补检时说明理由 -->",
          "", "---", "", "## 综合评估", "", "### 可行性", "", "<!-- JUDGE: 可行性 -->", "",
          "### 核心发现", "", "<!-- JUDGE: 文献分析核心发现 3-5 条 -->", "",
          "### 对研究设计的建议", "", "<!-- JUDGE: 建议 2-3 条 -->", "",
          "### 文献分布", "", "| 方向 | 核心 | 重要 | 备选 | 小计 |", "|:--|:--:|:--:|:--:|:--:|"]
    occ = 0
    for d, path in sorted(tagged.items()):
        rows = lc.parse_report_rows(lc.read_text(path))
        c = {t: sum(r["tier"] == t for r in rows) for t in lc.TIERS}
        occ += len(rows)
        L.append(f"| D{d} | {c['core']} | {c['important']} | {c['backup']} | {len(rows)} |")
    L.append(f"| 各方向合计（含跨方向重复） | | | | {occ} |")
    L.append(f"| **去重后语料** | **{tiers['core']}** | **{tiers['important']}** | **{tiers['backup']}** | **{len(papers)}** |")
    text = "\n".join(L) + "\n"

    target = lit_dir / "master_report.md"
    if target.exists():
        print(f"NOTICE: previous master_report.md archived -> {lc.archive(target, lit_dir)} (carry judgments over if still valid)")
    dp.atomic_write(target, text)
    print("=== MASTER REPORT SKELETON ===")
    print(f"Papers: {len(papers)}; COMP: {len(comp)}; core/important METHOD: {len(method)}")
    if not comp:
        print("  ⚠️ COMP=0: residual competitor-search risk")
    if not method:
        print("  ⚠️ no core/important METHOD precedent: method-justification risk")
    print(f"Judgment placeholders: {text.count('<!-- JUDGE')}")
    print("=== VERIFY: DATA PASS — JUDGMENT PENDING ===")
    print(f"Output: {target}")


if __name__ == "__main__":
    main()
