#!/usr/bin/env python3
"""Unit tests for the review -> tag -> pool stage scripts (Academic OS Lite §3).

Identical on Claude (~/.claude/skills) and Codex (~/.codex/skills): script paths
are resolved relative to this file. Run: python3 -m unittest <this file>
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]


def _find(*cands: str) -> Path:
    for c in cands:
        if (SKILLS / c).is_file():
            return SKILLS / c
    raise FileNotFoundError(cands)


DISPATCH = _find("shared/dispatch_plan.py", "_academic-shared/scripts/dispatch_plan.py")
FORMAT = _find("lit-review/format_batches.py")
MERGE = _find("lit-review/merge_screening.py")
CNKI = _find("lit-review/cnki_enw_to_ris.py")
INSERT = _find("lit-tag/insert_tags.py", "lit-tag/scripts/insert_tags.py")
AGG = _find("lit-tag/tag_aggregate.py", "lit-tag/scripts/tag_aggregate.py")
PREP = _find("lit-pool/pool_prepare.py")
FMT_POOL = _find("lit-pool/format_pool_agents.py")
POOL_MERGE = _find("lit-pool/pool_merge.py")
RIS2BIB = _find("lit-pool/ris2bib.py")
REPORT = _find("lit-pool/generate_master_report.py")
FINAL = _find("lit-pool/finalize_pool.py")
STATUS = _find("lit-workflow/lit_status.py", "lit-workflow/scripts/lit_status.py")


def ris(title: str, author: str, year: int, abstract: str = "", journal: str = "TEST JOURNAL",
        doi: str = "", extra: str = "") -> str:
    return ("TY  - JOUR\n" f"AU  - {author}\n" f"TI  - {title}\n" + extra + f"PY  - {year}\n" f"T2  - {journal}\n"
            + (f"AB  - {abstract}\n" if abstract else "") + (f"DO  - {doi}\n" if doi else "") + "ER  - \n\n")


def fill_review(lit: Path, decisions: dict[str, tuple]) -> None:
    """decisions: record_id -> (decision, tier, reason, evidence[, suspect]); others -> exclude."""
    for f in sorted((lit / "_review_runs").glob("d*_b*.md")):
        out, cur = [], None
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^### (\S+)", line)
            if m:
                cur = m.group(1)
            if cur and line.startswith("- ") and line.endswith(": "):
                dec = decisions.get(cur, ("exclude", "", "无关", "仅凭标题"))
                vals = {"决定": dec[0], "级别": dec[1], "理由": dec[2], "证据": dec[3],
                        "疑似竞品": dec[4] if len(dec) > 4 else ""}
                name = line[2:-2]
                if name in vals:
                    line = f"- {name}: {vals[name]}"
            out.append(line)
        f.write_text("\n".join(out) + "\n", encoding="utf-8")


def fill_tags(lit: Path, tags_by_title: dict[str, str], default: str = "LR") -> None:
    for f in sorted((lit / "_tag_runs").glob("d*_tags.md")):
        text = f.read_text(encoding="utf-8")
        meta = json.loads(text.splitlines()[0][len("<!-- lit-tags: "):-4])
        titles = {(r["tier"], r["row"]): r["title"] for r in meta["refs"]}

        def sub(m: re.Match) -> str:
            t = titles[(m.group(1), int(m.group(2)))]
            return f"{m.group(1)}:{m.group(2)} → {tags_by_title.get(t, default)}"
        f.write_text(re.sub(r"^(core|important|backup):(\d+) → *$", sub, text, flags=re.M), encoding="utf-8")


def fill_pool(lit: Path) -> None:
    for f in sorted((lit / "_pool_runs").glob("pool_agent*_raw.md")):
        text = f.read_text(encoding="utf-8")
        f.write_text(re.sub(r"^- 引用场景: *$", "- 引用场景: 可支撑相关论点", text, flags=re.M), encoding="utf-8")


class LitStagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.lit = Path(self.tmp.name) / "zy99_latexfile" / "structure" / "2_literature"
        self.lit.mkdir(parents=True)
        (self.lit / "literature_search_plan.md").write_text("# Plan\n\n## 方向1：Alpha\n\n## 方向2：Beta\n", encoding="utf-8")
        quota = {"total_budget": 6, "directions": [
            {"id": 1, "name": "Alpha", "wos_quota": 3, "wos_tiers": {"core": 1, "important": 1, "backup": 1},
             "cnki_quota": 1, "cnki_tiers": {"core": 1, "important": 0, "backup": 0}},
            {"id": 2, "name": "Beta", "wos_quota": 2, "wos_tiers": {"core": 1, "important": 1, "backup": 0}, "cnki_quota": 0}]}
        (self.lit / "_quota_result.json").write_text(json.dumps(quota), encoding="utf-8")
        (self.lit / "direction1_wos.ris").write_text(
            ris("Alpha first paper on coordination", "Smith, Jane", 2024, "Uses a longitudinal panel to identify coordination effects.",
                doi="10.1234/same", extra="   with a continued title\n")
            + ris("Alpha second paper", "Jones, Lee", 2023, "Reports simulation evidence on reliability and transfers.")
            + ris("Alpha third paper", "Brown, Kim", 2022, "A survey of grid operators."), encoding="utf-8")
        (self.lit / "direction1_openalex.ris").write_text(
            ris("Alpha first paper: an extended title variant", "Jane Smith", 2024, "Uses a longitudinal panel.",
                doi="https://doi.org/10.1234/SAME"), encoding="utf-8")
        (self.lit / "direction1_cnki.ris").write_text(
            ris("纵向信息共享平台研究", "张三", 2022, "基于演化博弈分析信息共享平台对合作稳定性的影响。", "管理科学"), encoding="utf-8")
        (self.lit / "direction2_wos.ris").write_text(
            ris("Alpha first paper on coordination with a continued title", "Smith, Jane", 2024, "Panel evidence.",
                doi="10.1234/same") + ris("Beta method origin", "Snijders, Tom", 2001, "Defines the stochastic actor-oriented model."),
            encoding="utf-8")
        self.decisions = {
            "D1-wos-1": ("include", "核心", "协调效应面板，方法先例", "longitudinal panel", "研究问题高度重叠"),
            "D1-wos-2": ("include", "重要", "可靠性仿真证据", "simulation evidence"),
            "D1-wos-3": ("exclude", "", "调查对象不符", "survey of grid operators"),
            "D1-openalex-1": ("include", "核心", "同一论文的 OpenAlex 记录", "longitudinal panel"),
            "D1-cnki-1": ("include", "核心", "信息共享平台演化博弈", "演化博弈分析"),
            "D2-wos-1": ("include", "重要", "方向2中的同一论文", "Panel evidence"),
            "D2-wos-2": ("include", "核心", "方法原始文献", "stochastic actor-oriented model"),
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cmd(self, *args, expect: int = 0) -> subprocess.CompletedProcess:
        r = subprocess.run([sys.executable, *map(str, args)], text=True, capture_output=True)
        self.assertEqual(r.returncode, expect, r.stdout + r.stderr)
        return r

    # -- helpers ---------------------------------------------------------------
    def review(self) -> None:
        self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit)
        fill_review(self.lit, self.decisions)
        self.run_cmd(FORMAT, "--lit-dir", self.lit)
        self.run_cmd(MERGE, "--lit-dir", self.lit)

    def tag(self, tags: dict | None = None) -> None:
        self.run_cmd(DISPATCH, "--mode", "report", "--lit-dir", self.lit)
        fill_tags(self.lit, tags or {"Beta method origin": "METHOD-基础+LR"})
        self.run_cmd(INSERT, "--lit-dir", self.lit, "--rq-count", 2)
        self.run_cmd(AGG, "--lit-dir", self.lit, "--rq-count", 2)

    def pool(self) -> None:
        self.run_cmd(PREP, "--lit-dir", self.lit)
        fill_pool(self.lit)
        self.run_cmd(FMT_POOL, "--lit-dir", self.lit)
        self.run_cmd(POOL_MERGE, "--lit-dir", self.lit)
        self.run_cmd(RIS2BIB, "--lit-dir", self.lit)
        self.run_cmd(REPORT, "--lit-dir", self.lit, "--idea-file", self.lit / "none.md")
        rep = self.lit / "master_report.md"
        rep.write_text(re.sub(r"<!-- JUDGE[^>]*-->", "已判断", rep.read_text(encoding="utf-8")), encoding="utf-8")
        (self.lit / "method_landscape.md").write_text("# 方法论综述\n", encoding="utf-8")

    # -- tests -------------------------------------------------------------------
    def test_full_pipeline(self) -> None:
        self.review()
        d1 = (self.lit / "direction1_report.md").read_text(encoding="utf-8")
        self.assertIn("Alpha first paper on coordination with a continued title", d1)  # RIS continuation kept
        self.assertNotIn("extended title variant", d1)  # same DOI -> one paper
        self.assertIn("研究问题高度重叠", d1)  # suspected competitor surfaced
        self.assertIn("跨方向重复: 1", (self.lit / "screening_summary_report.md").read_text(encoding="utf-8"))
        self.tag({"Alpha first paper on coordination with a continued title": "LR+COMP+GAP-RQ1",
                  "Beta method origin": "METHOD-基础", "纵向信息共享平台研究": "BG+DISC-RQ2"})
        self.assertEqual(d1, (self.lit / "direction1_report.md").read_text(encoding="utf-8"))  # review report immutable
        self.assertIn("功能标签", (self.lit / "tagged_reports/direction1_report.md").read_text(encoding="utf-8"))
        self.assertIn("去重后独立文献**: 4篇", (self.lit / "tag_report.md").read_text(encoding="utf-8"))
        self.pool()
        self.run_cmd(FINAL, "--lit-dir", self.lit)
        self.run_cmd(FINAL, "--lit-dir", self.lit, "--check-only")
        man = json.loads((self.lit / "literature_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(man["count"], 4)
        smith = next(p for p in man["papers"] if p["author"] == "Smith")
        self.assertEqual(smith["directions"], [1, 2])
        self.assertIn("COMP", smith["pools"])
        bib = (self.lit / "citation_pool/master.bib").read_text(encoding="utf-8")
        self.assertEqual(sorted(re.findall(r"^@\w+\{([^,]+),", bib, re.M)), sorted(p["citation_key"] for p in man["papers"]))
        self.assertTrue((self.lit / "_quota_result.json").exists())

    def test_dispatch_blocks_and_reminders(self) -> None:
        (self.lit / "5-old-topic.ris").write_text(ris("x", "A, B", 2020), encoding="utf-8")
        r = self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit)
        self.assertIn("NONCONFORMING_RIS_IGNORED", r.stdout)  # reminder only
        (self.lit / "direction2_wos.ris").rename(self.lit / "direction2_openalex.ris")
        r = self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit, expect=1)
        self.assertIn("direction2_wos.ris", r.stderr)  # OpenAlex never replaces a required WoS track
        (self.lit / "direction2_openalex.ris").rename(self.lit / "direction2_wos.ris")
        with (self.lit / "direction2_wos.ris").open("a", encoding="utf-8") as f:
            f.write("TY  - JOUR\nTI  - broken\n")
        r = self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit, expect=1)
        self.assertIn("TY count 3 != ER count 2", r.stderr)

    def test_batch_validation_and_retry_semantics(self) -> None:
        self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit)
        r = self.run_cmd(FORMAT, "--lit-dir", self.lit, "--json", expect=1)
        self.assertEqual({v["status"] for v in json.loads(r.stdout).values()}, {"EMPTY"})
        bad = dict(self.decisions, **{"D1-wos-2": ("include", "", "缺级别", "simulation evidence"),
                                      "D2-wos-2": ("include", "核心", "证据不在摘要", "not in abstract")})
        fill_review(self.lit, bad)
        r = self.run_cmd(FORMAT, "--lit-dir", self.lit, expect=1)
        self.assertIn("d1_wos_b1: INVALID", r.stdout)
        self.assertIn("d2_wos_b1: OK", r.stdout)  # evidence mismatch is a reminder only
        self.assertIn("证据 not found verbatim", r.stdout)
        self.run_cmd(MERGE, "--lit-dir", self.lit, expect=1)  # never merges a partial worker set
        batch = self.lit / "_review_runs/d1_cnki_b1.md"
        batch.write_text(batch.read_text(encoding="utf-8").split("### D1-cnki-1")[0], encoding="utf-8")
        r = self.run_cmd(FORMAT, "--lit-dir", self.lit, expect=1)
        self.assertIn("record blocks differ from chunk", r.stdout)

    def test_plans_are_separate_and_required(self) -> None:
        self.review()
        review_plan = (self.lit / "_review_runs/dispatch_plan.json").read_text(encoding="utf-8")
        self.run_cmd(INSERT, "--lit-dir", self.lit, "--rq-count", 2, expect=1)  # no tag plan -> error, no fallback
        self.run_cmd(DISPATCH, "--mode", "report", "--lit-dir", self.lit)
        self.assertEqual(review_plan, (self.lit / "_review_runs/dispatch_plan.json").read_text(encoding="utf-8"))
        (self.lit / "_review_runs/dispatch_plan.json").unlink()
        self.run_cmd(FORMAT, "--lit-dir", self.lit, expect=1)

    def test_overwrite_requires_flag_and_archives(self) -> None:
        self.review()
        b = self.lit / "_review_runs/d1_wos_b1.md"
        b.write_text(b.read_text(encoding="utf-8").replace("- 级别: 重要", "- 级别: 备选"), encoding="utf-8")
        r = self.run_cmd(MERGE, "--lit-dir", self.lit, expect=1)
        self.assertIn("REPORT_EXISTS", r.stderr)
        self.run_cmd(MERGE, "--lit-dir", self.lit, "--overwrite")
        archived = list((self.lit / "_archive").rglob("direction1_report.md"))
        self.assertEqual(len(archived), 1)

    def test_stale_batch_is_archived_and_tags_carry_over(self) -> None:
        self.review()
        self.tag({"Alpha second paper": "DISC-RQ1"})
        src = self.lit / "direction1_wos.ris"
        src.write_text(src.read_text(encoding="utf-8").replace("Alpha third paper", "Alpha third paper revised"), encoding="utf-8")
        self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit, "--directions", "1")
        self.assertTrue(list((self.lit / "_archive").rglob("d1_wos_b1.md")))
        fill_review(self.lit, dict(self.decisions, **{"D1-wos-3": ("include", "备选", "修订后入选", "survey of grid operators")}))
        self.run_cmd(MERGE, "--lit-dir", self.lit, "--overwrite")
        r = self.run_cmd(AGG, "--lit-dir", self.lit, "--rq-count", 2, expect=1)
        self.assertIn("TAGGED_COPY_STALE: D1", r.stdout)
        self.run_cmd(PREP, "--lit-dir", self.lit, expect=1)
        self.run_cmd(DISPATCH, "--mode", "report", "--lit-dir", self.lit, "--directions", "1")
        t = (self.lit / "_tag_runs/d1_b1_tags.md").read_text(encoding="utf-8")
        self.assertRegex(t, r"important:1 → DISC-RQ1")  # carried over by title
        self.assertRegex(t, r"backup:1 → *\n")  # new paper still to fill
        fill_tags(self.lit, {})
        self.run_cmd(INSERT, "--lit-dir", self.lit, "--rq-count", 2)
        self.run_cmd(AGG, "--lit-dir", self.lit, "--rq-count", 2)

    def test_invalid_tag_and_pool_gates(self) -> None:
        self.review()
        self.run_cmd(DISPATCH, "--mode", "report", "--lit-dir", self.lit)
        fill_tags(self.lit, {"Alpha second paper": "DISC-RQ3"})
        r = self.run_cmd(INSERT, "--lit-dir", self.lit, "--rq-count", 2, expect=1)
        self.assertIn("DISC-RQ3", r.stdout)
        self.assertFalse((self.lit / "tagged_reports").exists())  # transactional
        for f in (self.lit / "_tag_runs").glob("*_tags.md"):
            f.write_text(f.read_text(encoding="utf-8").replace("DISC-RQ3", "DISC-RQ2"), encoding="utf-8")
        self.run_cmd(INSERT, "--lit-dir", self.lit, "--rq-count", 2)
        self.run_cmd(AGG, "--lit-dir", self.lit, "--rq-count", 2)
        self.pool()
        rep = self.lit / "master_report.md"
        rep.write_text(rep.read_text(encoding="utf-8") + "\n<!-- JUDGE: 未填 -->\n", encoding="utf-8")
        r = self.run_cmd(FINAL, "--lit-dir", self.lit, expect=1)
        self.assertIn("JUDGE_PENDING", r.stdout)
        rep.write_text(rep.read_text(encoding="utf-8").replace("<!-- JUDGE: 未填 -->", ""), encoding="utf-8")
        self.run_cmd(FINAL, "--lit-dir", self.lit)
        bib = self.lit / "citation_pool/master.bib"
        text = bib.read_text(encoding="utf-8")
        first_key = re.search(r"^@\w+\{([^,]+),", text, re.M).group(1)
        bib.write_text(re.sub(r"@\w+\{" + re.escape(first_key) + r",.*?\n\}\n*", "", text, flags=re.S), encoding="utf-8")
        r = self.run_cmd(FINAL, "--lit-dir", self.lit, "--check-only", expect=1)
        self.assertIn("KEYS_NOT_IN_MASTER_BIB", r.stdout)

    def test_citation_keys_are_reused_on_refresh(self) -> None:
        self.review()
        self.tag()
        self.pool()
        self.run_cmd(FINAL, "--lit-dir", self.lit)
        man = json.loads((self.lit / "literature_manifest.json").read_text(encoding="utf-8"))
        smith_key = next(p["citation_key"] for p in man["papers"] if p["author"] == "Smith")
        man["papers"] = [dict(p, citation_key="smith2024keep") if p["author"] == "Smith" else p for p in man["papers"]]
        (self.lit / "literature_manifest.json").write_text(json.dumps(man), encoding="utf-8")
        self.run_cmd(PREP, "--lit-dir", self.lit, expect=1)  # 'smith2024keep' fails the key pattern
        man["papers"] = [dict(p, citation_key="smith2024k") if p["author"] == "Smith" else p for p in man["papers"]]
        (self.lit / "literature_manifest.json").write_text(json.dumps(man), encoding="utf-8")
        self.run_cmd(PREP, "--lit-dir", self.lit)
        prep = json.loads((self.lit / "_pool_runs/pool_prepare.json").read_text(encoding="utf-8"))
        self.assertIn("smith2024k", {p["citation_key"] for p in prep["papers"]})
        self.assertNotEqual(smith_key, "smith2024k")
        self.assertTrue(list((self.lit / "_archive").rglob("pool_prepare.json")))  # plan changed -> archived
        raw = "".join(f.read_text(encoding="utf-8") for f in (self.lit / "_pool_runs").glob("pool_agent*_raw.md"))
        self.assertIn("可支撑相关论点", raw)  # scenes carried over for unchanged (label, paper) pairs

    def test_user_confirmed_skip_is_excluded(self) -> None:
        root = self.lit.parents[1]
        self.run_cmd(DISPATCH, "--mode", "ris", "--lit-dir", self.lit)
        fill_review(self.lit, {k: v for k, v in self.decisions.items() if k.startswith("D1")})
        for f in (self.lit / "_review_runs").glob("d2_*.md"):  # D2 worker failed twice: batch left unfilled
            f.write_text(f.read_text(encoding="utf-8").replace("- 决定: exclude", "- 决定: "), encoding="utf-8")
        self.run_cmd(MERGE, "--lit-dir", self.lit, expect=1)
        self.run_cmd(STATUS, "mark", "--project-root", root, "--direction", 2, "--stage", "review", "--state", "FAILED", "--note", "两次失败")
        self.run_cmd(MERGE, "--lit-dir", self.lit, expect=1)  # FAILED alone does not unblock
        self.run_cmd(STATUS, "mark", "--project-root", root, "--direction", 2, "--stage", "review", "--state", "SKIPPED", "--note", "用户确认跳过")
        self.run_cmd(MERGE, "--lit-dir", self.lit)
        self.assertFalse((self.lit / "direction2_report.md").exists())
        self.assertIn("用户确认跳过", (self.lit / "screening_summary_report.md").read_text(encoding="utf-8"))
        self.tag()
        self.pool()
        self.run_cmd(FINAL, "--lit-dir", self.lit)
        man = json.loads((self.lit / "literature_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(all(p["directions"] == [1] for p in man["papers"]))
        r = self.run_cmd(STATUS, "--project-root", root, "--check", "final")
        self.assertNotIn("D2 尚无", r.stdout)

    def test_cnki_converter_requires_direction_output_and_nonzero_input(self) -> None:
        enw = self.lit / "direction2_cnki.enw"
        enw.write_text("", encoding="utf-8")
        self.run_cmd(CNKI, "--input", enw, "--output", self.lit / "direction2_cnki.ris", expect=1)
        enw.write_text("%0 Journal Article\n%A 张三\n%T 平台研究\n%J 管理科学\n%D 2022\n%X 摘要。\n", encoding="utf-8")
        self.run_cmd(CNKI, "--input", enw, "--output", self.lit / "cnki_combined.ris", expect=1)
        self.run_cmd(CNKI, "--input", enw, "--output", self.lit / "direction2_cnki.ris")
        text = (self.lit / "direction2_cnki.ris").read_text(encoding="utf-8")
        self.assertEqual((text.count("TY  - "), text.count("ER  - ")), (1, 1))
        self.run_cmd(CNKI, "--input", enw, "--output", self.lit / "direction2_cnki.ris", expect=1)  # no silent overwrite


if __name__ == "__main__":
    unittest.main()
