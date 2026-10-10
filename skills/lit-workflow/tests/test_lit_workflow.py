"""lit-workflow 单元测试：lit_status.py 与 openalex_to_ris.py（两侧布局通用，不联网）。

运行：python3 -m unittest discover -s <skill>/tests -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts" if (SKILL_ROOT / "scripts").is_dir() else SKILL_ROOT
sys.path.insert(0, str(SCRIPTS))

import lit_status  # noqa: E402
import openalex_to_ris  # noqa: E402


def rec(title: str) -> str:
    return f"TY  - JOUR\nTI  - {title}\nAB  - line one\n   continued\nER  - \n\n"


PLAN = """# P01 文献检索方案

## 方向表

| # | 方向 | 功能标签 | 优先级 | 配额 | 输入文件 |
|:--|:-----|:---------|:------:|:----:|:---------|
| 1 | 供应链韧性 | LR | P1 | WoS 60 + CNKI 20 | direction1_wos.ris, direction1_cnki.enw |
| 2 | 演化博弈 | METHOD | P2 | WoS 40 | direction2_wos.ris |
"""

QUOTA = {"directions": [
    {"id": 1, "name": "供应链韧性", "wos_quota": 60, "cnki_quota": 20, "quota": 80},
    {"id": 2, "name": "演化博弈", "wos_quota": 40, "cnki_quota": 0, "quota": 40},
]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.lit = self.root / "structure" / "2_literature"
        self.lit.mkdir(parents=True)
        (self.lit / "literature_search_plan.md").write_text(PLAN, encoding="utf-8")
        (self.lit / "_quota_result.json").write_text(json.dumps(QUOTA, ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel: str, text: str, age: float = 0.0) -> Path:
        p = self.lit / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        if age:
            t = time.time() - age
            os.utime(p, (t, t))
        return p

    def scan(self):
        return lit_status.scan(self.root)


class InputStage(Base):
    def test_missing_inputs_and_pending_cnki_block_review(self):
        self.write("direction1_wos.ris", rec("A"))
        self.write("direction1_cnki.enw", "%0 Journal Article\n%T 标题\n")
        st = self.scan()
        msgs = " ".join(st.blockers["review"])
        self.assertIn("D1 CNKI 尚未转换", msgs)
        self.assertIn("D2 缺少输入文件 direction2_wos.ris", msgs)
        self.assertEqual(1, len(st.conversions))
        self.assertIn("direction1_cnki.ris", st.conversions[0])
        names = {(r["direction"], r["source"]): r for r in st.rows}
        self.assertEqual("待转换", names[(1, "cnki")]["input"])
        self.assertEqual("供应链韧性", names[(1, "wos")]["name"])

    def test_broken_ris_blocks_and_bad_names_only_remind(self):
        self.write("direction1_wos.ris", "TY  - JOUR\nTI  - x\n")
        self.write("direction1_cnki.ris", rec("中文"))
        self.write("direction2_wos.ris", rec("B"))
        self.write("2-演化博弈.ris", rec("legacy"))
        st = self.scan()
        self.assertTrue(any("TY count 1 != ER count 0" in m for m in st.blockers["review"]))
        self.assertTrue(any("2-演化博弈.ris" in m for m in st.reminders))
        self.assertFalse(any("2-演化博弈" in m for m in st.blockers["review"]))

    def test_ready_for_review_and_screen_suggestion(self):
        self.write("direction1_wos.ris", rec("A") * 100)
        self.write("direction1_cnki.ris", rec("中文"))
        self.write("direction2_wos.ris", rec("B"))
        st = self.scan()
        self.assertEqual([], st.blockers["review"])
        self.assertEqual("review", st.current)
        row = next(r for r in st.rows if (r["direction"], r["source"]) == (1, "wos"))
        self.assertIn("建议筛选", row["note"])
        self.assertEqual("未筛选", row["screen"])
        # 输入阶段不应把 tag/pool 的"尚未运行"渲染成阻断
        lit_status.write_status(self.root, st)
        text = (self.lit / "lit_status.md").read_text(encoding="utf-8")
        self.assertNotIn("尚无 review 报告", text)


class LogsAndMarks(Base):
    def setUp(self):
        super().setUp()
        self.write("direction1_wos.ris", rec("A") * 3)
        self.write("direction1_cnki.ris", rec("中文"))
        self.write("direction2_wos.ris", rec("B"))

    def test_record_screen_survives_rescan_and_detects_mismatch(self):
        lit_status.record_screen(self.lit, direction=1, source="wos", method="XR≤2区+LLM",
                                 before=10, after=3, run_dir=self.lit / "_screen_runs" / "r1",
                                 backup=self.lit / "_screen_runs" / "original" / "direction1_wos.ris")
        lit_status.write_status(self.root)
        text = (self.lit / "lit_status.md").read_text(encoding="utf-8")
        self.assertIn("D1/wos：XR≤2区+LLM，10 → 3（运行目录 _screen_runs/r1", text)
        row = next(r for r in self.scan().rows if (r["direction"], r["source"]) == (1, "wos"))
        self.assertTrue(row["screen"].startswith("XR≤2区+LLM 10→3"))
        self.assertNotIn("⚠️", row["screen"])
        self.write("direction1_wos.ris", rec("A") * 5)
        row = next(r for r in self.scan().rows if (r["direction"], r["source"]) == (1, "wos"))
        self.assertIn("⚠️", row["screen"])
        d2 = next(r for r in self.scan().rows if r["direction"] == 2)
        self.assertEqual("未筛选", d2["screen"])

    def test_failed_review_blocks_pool_until_skipped(self):
        self.write("direction1_report.md", "| 1 | a |\n| 2 | b |\n", age=10)
        lit_status.mark(self.lit, direction=2, stage="review", state="FAILED", note="worker 超时")
        st = self.scan()
        self.assertEqual([], st.blockers["tag"])  # 规格：FAILED 只在 pool 前阻断
        self.assertTrue(any("D2 review FAILED" in m for m in st.blockers["pool"]))
        self.write("tagged_reports/direction1_report.md", "| 1 | a | LR |\n")
        st = self.scan()
        self.assertEqual("pool", st.current)
        lit_status.mark(self.lit, direction=2, stage="review", state="SKIPPED", note="用户确认跳过")
        st = self.scan()
        self.assertEqual([], st.blockers["pool"])
        row = next(r for r in st.rows if r["direction"] == 2)
        self.assertEqual(("跳过（用户确认）", "跳过"), (row["review"], row["tag"]))
        lit_status.mark(self.lit, direction=2, stage="review", state="CLEARED")
        self.assertTrue(any("D2 尚无 tag 副本" in m for m in self.scan().blockers["pool"]))

    def test_upstream_newer_is_only_a_warning(self):
        self.write("direction1_report.md", "| 1 | a |\n", age=100)
        self.write("direction2_report.md", "| 1 | b |\n", age=100)
        self.write("tagged_reports/direction1_report.md", "| 1 | a | LR |\n", age=200)
        self.write("tagged_reports/direction2_report.md", "| 1 | b | LR |\n", age=50)
        st = self.scan()
        row = next(r for r in st.rows if (r["direction"], r["source"]) == (1, "wos"))
        self.assertIn("⚠️", row["review"])  # 输入比 review 新
        self.assertIn("⚠️", row["tag"])     # review 比 tag 新
        self.assertEqual([], st.blockers["pool"])


class FinalCheck(Base):
    def test_judge_and_orphan_keys_block_final(self):
        for d in (1, 2):
            self.write(f"direction{d}_wos.ris", rec("A"))
            self.write(f"direction{d}_report.md", "| 1 | a |\n")
            self.write(f"tagged_reports/direction{d}_report.md", "| 1 | a | LR |\n")
        self.write("direction1_cnki.ris", rec("中文"))
        for g in lit_status.POOL_GROUPS:
            self.write(f"citation_pool/{g}.md", "| 分级 | 作者 | 年份 | key |\n| 核心 | A | 2020 | smith2020a |\n")
        self.write("citation_pool/master.bib", "@article{smith2020a,\n title={x}\n}\n")
        self.write("literature_manifest.json", json.dumps({"papers": [
            {"citation_key": "smith2020a", "directions": [1, 2]}]}))
        self.write("master_report.md", "# 总报告\n")
        self.write("method_landscape.md", "# 方法\n")
        st = self.scan()
        self.assertEqual([], st.blockers["final"])
        self.assertEqual("done", st.current)
        self.assertEqual("1 篇", next(r for r in st.rows if r["direction"] == 2)["pool"])
        self.write("master_report.md", "# 总报告\n<!-- JUDGE: 待判断 -->\n")
        self.write("literature_manifest.json", json.dumps({"papers": [
            {"citation_key": "smith2020a", "directions": [1, 2]},
            {"citation_key": "ghost2021b", "directions": [1]}]}))
        st = self.scan()
        msgs = " ".join(st.blockers["final"])
        self.assertIn("1 处 JUDGE 占位符", msgs)
        self.assertIn("ghost2021b", msgs)
        self.assertNotEqual("done", st.current)

    def test_report_rows_counted_with_shared_parser(self):
        self.write("direction1_wos.ris", rec("A"))
        self.write("direction1_report.md", "## 核心文献（Core）\n\n| # | 作者 | 标题 | 年份 | 期刊 | 理由 |\n|:--|\n"
                   "| 1 | S | T1 | 2024 | J | R |\n| 2 | S | T2 | 2024 | J | R |\n\n## 竞品判断边界\n| 3 | x | x | x | x | x |\n")
        row = next(r for r in self.scan().rows if r["direction"] == 1)
        self.assertTrue(row["review"].startswith("2 篇"))

    def test_cli_check_exit_codes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lit_status.main(["--project-root", str(self.root), "--check", "review", "--no-write"])
        self.assertEqual(2, code)
        self.assertIn("CHECK review: BLOCKED", out.getvalue())
        self.assertFalse((self.lit / "lit_status.md").exists())


WORK = {
    "id": "https://openalex.org/W123",
    "doi": "https://doi.org/10.1000/ABC.1",
    "title": "A study\nof things",
    "publication_year": 2021,
    "type": "article",
    "authorships": [{"author": {"display_name": "Jane Q Doe"}}, {"author": {"display_name": "Li, Wei"}}],
    "primary_location": {"source": {"display_name": "Journal of Tests", "issn": ["1234-5678"]}},
    "biblio": {"volume": "3", "issue": "2", "first_page": "10", "last_page": "20"},
    "abstract_inverted_index": {"Hello": [0], "world": [1]},
    "keywords": [{"display_name": "testing"}],
}


class OpenAlexToRis(Base):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = openalex_to_ris.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_json_to_ris_fields_and_append_dedup(self):
        src = self.root / "works.json"
        src.write_text(json.dumps({"results": [WORK]}), encoding="utf-8")
        code, out, err = self.run_main("--direction", "3", "--json", str(src), "--lit-dir", str(self.lit))
        self.assertEqual(0, code, err)
        text = (self.lit / "direction3_openalex.ris").read_text(encoding="utf-8")
        for line in ("TY  - JOUR", "TI  - A study of things", "AU  - Doe, Jane Q", "AU  - Li, Wei",
                     "PY  - 2021", "DO  - 10.1000/abc.1", "JO  - Journal of Tests", "AB  - Hello world",
                     "SN  - 1234-5678", "ER  - "):
            self.assertIn(line, text)
        code, _, err = self.run_main("--direction", "3", "--json", str(src), "--lit-dir", str(self.lit))
        self.assertEqual(1, code)
        self.assertIn("已存在", err)
        w2 = dict(WORK, doi="10.1000/xyz.2", id="https://openalex.org/W456")
        src.write_text(json.dumps([WORK, w2]), encoding="utf-8")
        code, out, _ = self.run_main("--direction", "3", "--json", str(src), "--lit-dir", str(self.lit), "--append")
        self.assertEqual(0, code)
        self.assertIn("新增 1，跳过重复 1", out)
        self.assertEqual(2, openalex_to_ris.lit_common.check_ris(self.lit / "direction3_openalex.ris")[0])

    def test_missing_required_fields_writes_nothing(self):
        src = self.root / "bad.json"
        src.write_text(json.dumps(dict(WORK, doi=None, authorships=[])), encoding="utf-8")
        code, _, err = self.run_main("--direction", "1", "--json", str(src), "--lit-dir", str(self.lit))
        self.assertEqual(1, code)
        self.assertIn("缺少作者", err)
        self.assertIn("缺少 DOI", err)
        self.assertFalse((self.lit / "direction1_openalex.ris").exists())

    def test_replace_archives_old_file(self):
        src = self.root / "w.json"
        src.write_text(json.dumps(WORK), encoding="utf-8")
        self.run_main("--direction", "1", "--json", str(src), "--lit-dir", str(self.lit))
        code, out, _ = self.run_main("--direction", "1", "--json", str(src), "--lit-dir", str(self.lit), "--replace")
        self.assertEqual(0, code)
        self.assertTrue(list((self.lit / "_archive").rglob("direction1_openalex.ris")))

    def test_doi_mode_sends_key_and_mailto(self):
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(url, timeout=30):
            seen["url"] = url
            return Resp(json.dumps(WORK).encode())

        with mock.patch.dict(os.environ, {"OPENALEX_API_KEY": "KEY123", "OPENALEX_MAILTO": "me@x.org"}), \
                mock.patch.object(openalex_to_ris.urllib.request, "urlopen", side_effect=fake_urlopen):
            code, out, err = self.run_main("--direction", "2", "--doi", "https://doi.org/10.1000/abc.1",
                                           "--lit-dir", str(self.lit))
        self.assertEqual(0, code, err)
        self.assertIn("api_key=KEY123", seen["url"])
        self.assertIn("mailto=me%40x.org", seen["url"])
        self.assertNotIn("KEY123", out + err)


if __name__ == "__main__":
    unittest.main()
