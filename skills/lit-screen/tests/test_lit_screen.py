"""lit-screen 单元测试（Claude 平铺布局与 Codex scripts/ 布局通用）。

运行：python3 -m unittest discover -s <skill>/tests -v
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts" if (SKILL_ROOT / "scripts").is_dir() else SKILL_ROOT
sys.path.insert(0, str(SCRIPTS))

import finalize_screen  # noqa: E402
import screen_llm  # noqa: E402
import screen_xr  # noqa: E402

XR = {
    "1111-1111": {"journal": "J1", "zone_num": 1, "zone_str": "1 区", "top": "", "category": "", "warning": ""},
    "3333-3333": {"journal": "J3", "zone_num": 3, "zone_str": "3 区", "top": "", "category": "", "warning": ""},
}


def rec(title: str, *, abstract: str = "abstract", issn: str = "", cont: bool = False) -> str:
    sn = f"SN  - {issn}\r\n" if issn else ""
    more = "      continued abstract line\r\n" if cont else ""
    return f"TY  - JOUR\r\nTI  - {title}\r\nAB  - {abstract}\r\n{more}{sn}ER  - \r\n\r\n"


def fake_llm(index, title, abstract, direction, api_key):
    if title.startswith("Keep"):
        return {"index": index, "relevant": True, "reason": "相关"}
    if title.startswith("Drop"):
        return {"index": index, "relevant": False, "reason": "无关"}
    return {"index": index, "error": f"transport rejected {api_key}"}


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.lit = self.root / "structure" / "2_literature"
        self.lit.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def canonical(self, text: str, name: str = "direction1_wos.ris") -> Path:
        p = self.lit / name
        p.write_text(text, encoding="utf-8", newline="")
        return p

    def run_xr(self, canonical: Path) -> dict:
        with mock.patch.object(screen_xr, "load_xr2026", return_value=(XR, {})), \
                contextlib.redirect_stdout(io.StringIO()):
            return screen_xr.screen(str(canonical), 2)

    def run_llm(self, input_path: Path, run_dir: str | None = None) -> dict:
        with mock.patch.dict(os.environ, {"CHATANYWHERE_API_KEY": "secret-key"}), \
                mock.patch.object(screen_llm, "screen_one", side_effect=fake_llm), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return screen_llm.screen(str(input_path), "direction", threads=2, run_dir=run_dir)

    def fin(self, canonical, final, run_dir, mode, execute=False):
        ns = argparse.Namespace(canonical=str(canonical), final_ris=str(final), run_dir=str(run_dir),
                                mode=mode, note=None, dry_run=not execute, execute=execute)
        return finalize_screen.finalize(ns)


class RisRoundTrip(Base):
    def test_bom_continuation_raw_round_trip(self):
        source = ("TY  - JOUR\r\nTI  - First\r\nAB  - first line\r\n      second line\r\n"
                  "AU  - One, A\r\nAU  - Two, B\r\nER  - \r\n\r\n" + rec("Second"))
        p = self.lit / "in.ris"
        p.write_bytes(b"\xef\xbb\xbf" + source.encode("utf-8"))
        records = screen_xr.parse_ris(p)
        self.assertEqual("first line second line", records[0]["AB"])
        self.assertEqual(["One, A", "Two, B"], records[0]["AU"])
        out = self.root / "out.ris"
        screen_xr.write_ris(records, out)
        self.assertEqual(source, out.read_bytes().decode("utf-8"))

    def test_incomplete_record_rejected(self):
        p = self.lit / "bad.ris"
        p.write_text("TY  - JOUR\nTI  - Missing ER\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing ER"):
            screen_xr.parse_ris(p)


class XrStep(Base):
    def test_xr_writes_only_into_run_dir_and_keeps_order(self):
        c = self.canonical(rec("Unmatched", cont=True) + rec("Zone one", issn="1111-1111")
                           + rec("Zone three", issn="3333-3333"))
        stats = self.run_xr(c)
        run_dir = Path(stats["run_dir"])
        self.assertEqual(self.lit / "_screen_runs", run_dir.parent)
        self.assertEqual(["direction1_wos.ris"], sorted(x.name for x in self.lit.glob("*.ris")))
        kept = screen_xr.parse_ris(stats["output_path"])
        self.assertEqual(["Unmatched", "Zone one"], [r["TI"] for r in kept])
        self.assertIn("continued abstract line", Path(stats["output_path"]).read_text(encoding="utf-8"))

    def test_xr_refuses_top_level_run_dir(self):
        c = self.canonical(rec("A"))
        with self.assertRaisesRegex(ValueError, "顶层"):
            with mock.patch.object(screen_xr, "load_xr2026", return_value=(XR, {})):
                screen_xr.screen(str(c), 2, str(self.lit))


class LlmStep(Base):
    def test_every_record_audited_and_key_not_leaked(self):
        c = self.canonical(rec("Keep A") + rec("Drop B") + rec("Err C"))
        stats = self.run_llm(c)
        rows = [json.loads(l) for l in Path(stats["audit_output"]).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(["retain", "exclude", "error_retain"], [r["decision"] for r in rows])
        self.assertEqual(["Keep A", "Err C"], [r["TI"] for r in screen_xr.parse_ris(stats["output_path"])])
        self.assertEqual(["Drop B"], [r["TI"] for r in screen_xr.parse_ris(stats["excluded_output"])])
        blob = Path(stats["audit_output"]).read_text(encoding="utf-8") + (Path(stats["run_dir"]) / "run.json").read_text(encoding="utf-8")
        self.assertNotIn("secret-key", blob)
        self.assertEqual(self.lit / "_screen_runs", Path(stats["run_dir"]).parent)

    def test_llm_reuses_xr_run_dir(self):
        c = self.canonical(rec("Keep A", issn="1111-1111") + rec("Drop B") + rec("Keep Z", issn="3333-3333"))
        xr = self.run_xr(c)
        llm = self.run_llm(Path(xr["output_path"]))
        self.assertEqual(xr["run_dir"], llm["run_dir"])

    def test_api_key_argument_rejected_without_echo(self):
        script = SCRIPTS / "screen_llm.py"
        res = subprocess.run([sys.executable, str(script), "x.ris", "--direction", "d", "--api-key", "do-not-print-me"],
                             text=True, capture_output=True, check=False)
        self.assertEqual(2, res.returncode)
        self.assertNotIn("do-not-print-me", res.stdout + res.stderr)


class Finalize(Base):
    def test_zone_plus_llm_dry_run_then_execute(self):
        text = rec("Keep A", issn="1111-1111", cont=True) + rec("Drop B") + rec("Keep Z", issn="3333-3333")
        c = self.canonical(text)
        xr = self.run_xr(c)
        llm = self.run_llm(Path(xr["output_path"]))
        run_dir = Path(llm["run_dir"])
        plan = self.fin(c, llm["output_path"], run_dir, "zone+llm")
        self.assertEqual(text, c.read_bytes().decode("utf-8"))  # dry-run 不改文件
        self.assertEqual((3, 1), (plan["before_records"], plan["after_records"]))
        with mock.patch.object(finalize_screen, "_record_in_status", return_value=None) as rec_mock:
            res = self.fin(c, llm["output_path"], run_dir, "zone+llm", execute=True)
        self.assertTrue(res["published"])
        self.assertEqual(["Keep A"], [r["TI"] for r in screen_xr.parse_ris(c)])
        self.assertIn("continued abstract line", c.read_text(encoding="utf-8"))
        backup = self.lit / "_screen_runs" / "original" / "direction1_wos.ris"
        self.assertEqual(text, backup.read_bytes().decode("utf-8"))
        kwargs = rec_mock.call_args.kwargs
        self.assertEqual((1, "wos", 3, 1, "XR≤2区+LLM"),
                         (kwargs["direction"], kwargs["source"], kwargs["before"], kwargs["after"], kwargs["method"]))

    def test_second_screen_keeps_first_original(self):
        c = self.canonical(rec("Keep A", issn="1111-1111") + rec("Keep B", issn="3333-3333") + rec("Keep C"))
        xr1 = self.run_xr(c)
        with mock.patch.object(finalize_screen, "_record_in_status", return_value=None):
            self.fin(c, xr1["output_path"], xr1["run_dir"], "zone", execute=True)
            original = (self.lit / "_screen_runs" / "original" / "direction1_wos.ris").read_text(encoding="utf-8")
            llm = self.run_llm(c)
            res = self.fin(c, llm["output_path"], llm["run_dir"], "llm", execute=True)
        self.assertEqual(original, (self.lit / "_screen_runs" / "original" / "direction1_wos.ris").read_text(encoding="utf-8"))
        self.assertTrue(res["backup_to"].endswith("before_direction1_wos.ris"))

    def test_non_subset_is_rejected(self):
        c = self.canonical(rec("A") + rec("B"))
        xr = self.run_xr(c)
        Path(xr["output_path"]).write_text(rec("A") + rec("Injected"), encoding="utf-8", newline="")
        with self.assertRaisesRegex(ValueError, "有序子集"):
            self.fin(c, xr["output_path"], xr["run_dir"], "zone", execute=True)
        self.assertFalse((self.lit / "_screen_runs" / "original").exists())

    def test_stale_xr_run_after_canonical_replaced_is_rejected(self):
        c = self.canonical(rec("A", issn="1111-1111") + rec("B", issn="3333-3333"))
        xr = self.run_xr(c)
        c.write_text(rec("A", issn="1111-1111") + rec("B", issn="3333-3333") + rec("New"), encoding="utf-8", newline="")
        with self.assertRaisesRegex(ValueError, "不一致"):
            self.fin(c, xr["output_path"], xr["run_dir"], "zone")

    def test_audit_tamper_is_rejected(self):
        c = self.canonical(rec("Keep A") + rec("Drop B"))
        llm = self.run_llm(c)
        Path(llm["excluded_output"]).write_text(rec("Tampered"), encoding="utf-8", newline="")
        with self.assertRaisesRegex(ValueError, "排除序列"):
            self.fin(c, llm["output_path"], llm["run_dir"], "llm", execute=True)

    def test_llm_mode_requires_canonical_input(self):
        c = self.canonical(rec("Keep A", issn="1111-1111") + rec("Drop B"))
        xr = self.run_xr(c)
        llm = self.run_llm(Path(xr["output_path"]))
        with self.assertRaisesRegex(ValueError, "mode=llm"):
            self.fin(c, llm["output_path"], llm["run_dir"], "llm")

    def test_noncanonical_name_and_top_level_final_rejected(self):
        legacy = self.canonical(rec("A"), name="1-topic.ris")
        xr = self.run_xr(legacy)
        with self.assertRaisesRegex(ValueError, "文件名不规范"):
            self.fin(legacy, xr["output_path"], xr["run_dir"], "zone")
        c = self.canonical(rec("A"))
        other = self.canonical(rec("A"), name="direction2_wos.ris")
        xr2 = self.run_xr(c)
        with self.assertRaisesRegex(ValueError, "FINAL_RIS 必须位于"):
            self.fin(c, other, xr2["run_dir"], "zone", execute=True)

    def test_empty_result_cannot_replace_corpus(self):
        c = self.canonical(rec("Drop A") + rec("Drop B"))
        llm = self.run_llm(c)
        self.assertIsNone(llm["output_path"])
        with self.assertRaises(Exception):
            self.fin(c, Path(llm["run_dir"]) / "llm.ris", llm["run_dir"], "llm", execute=True)
        self.assertEqual(2, len(screen_xr.parse_ris(c)))


if __name__ == "__main__":
    unittest.main()
