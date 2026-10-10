#!/usr/bin/env python3
"""用一次筛选运行的结果替换 canonical RIS（lit-screen Step 4/5）。

  --dry-run   只校验并打印替换计划，不改任何文件
  --execute   用户确认后执行：
                1. 原 canonical 备份到 _screen_runs/original/<文件名>（已有原始备份时，
                   当前文件改存到本次运行目录 before_<文件名>，两者都不覆盖）
                2. 原子替换 canonical
                3. 在 lit_status.md 的「筛选记录」追加一行并刷新状态表

校验（任何一项失败都不改动 canonical）：
  - canonical 文件名符合 lit_common.classify_ris，TY = ER > 0
  - FINAL_RIS 位于 <lit_dir>/_screen_runs/<run>/ 内，TY = ER > 0
  - FINAL_RIS 的每个原始记录块按原顺序出现在 canonical 中（有序子集，续行原样）
  - XR 分支：xr_screening.csv 的逐篇标题与当前 canonical 一致（防止旧运行覆盖新导出）
  - LLM 分支：decisions.jsonl 每条输入一行、序号连续、标题与 LLM 输入逐条一致；
    排除/保留序列分别和 excluded.ris / FINAL_RIS 一致；run.json 的输入与链路一致
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from screen_xr import RAW_BLOCK_KEY, RUNS_DIRNAME, parse_ris  # noqa: E402

for _cand in (_HERE.parent / "shared", _HERE.parent.parent / "_academic-shared" / "scripts"):
    if (_cand / "lit_common.py").is_file():
        sys.path.insert(0, str(_cand))
        break
import lit_common  # noqa: E402

LLM_MODES = {"llm", "zone+llm"}
MODE_LABEL = {"zone": "XR 分区", "llm": "LLM 相关性", "zone+llm": "XR 分区 + LLM 相关性"}


def _check(path: Path, label: str) -> int:
    count, errors = lit_common.check_ris(path)
    if errors:
        raise ValueError(f"{label} 不可用：{'; '.join(errors)}")
    return count


def _titles(records: list[dict]) -> list[str]:
    out = []
    for rec in records:
        title = rec.get("TI", rec.get("T1", ""))
        out.append(" ".join(title) if isinstance(title, list) else title)
    return out


def validate_ordered_subset(canonical: Path, final_ris: Path) -> dict:
    canonical_records = parse_ris(canonical)
    final_records = parse_ris(final_ris)
    cursor = 0
    for index, rec in enumerate(final_records, start=1):
        block = rec[RAW_BLOCK_KEY]
        while cursor < len(canonical_records) and canonical_records[cursor][RAW_BLOCK_KEY] != block:
            cursor += 1
        if cursor >= len(canonical_records):
            raise ValueError(f"FINAL_RIS 不是 canonical 的有序子集（第 {index} 条无法对应）")
        cursor += 1
    return {"canonical_records": len(canonical_records), "final_records": len(final_records)}


def validate_llm_run(run_dir: Path, final_ris: Path, canonical: Path, mode: str) -> dict:
    run_json = run_dir / "run.json"
    audit_path = run_dir / "decisions.jsonl"
    excluded_path = run_dir / "excluded.ris"
    for p in (run_json, audit_path, excluded_path):
        if not p.is_file():
            raise FileNotFoundError(f"LLM 运行缺少文件：{p}")
    meta = json.loads(run_json.read_text(encoding="utf-8"))
    if Path(meta.get("output_path") or "").resolve() != final_ris:
        raise ValueError("FINAL_RIS 不是本运行目录 LLM 步骤的输出 llm.ris")
    llm_input = Path(meta.get("input_path", "")).resolve()
    if mode == "llm" and llm_input != canonical:
        raise ValueError(f"mode=llm 要求 LLM 输入就是 canonical，实际为 {llm_input}")
    if mode == "zone+llm" and not (llm_input.parent == run_dir and re.fullmatch(r"xr_zone\d+\.ris", llm_input.name)):
        raise ValueError(f"mode=zone+llm 要求 LLM 输入是本运行目录的 xr_zone*.ris，实际为 {llm_input}")

    rows = []
    for n, line in enumerate(audit_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"decisions.jsonl 第 {n} 行不是合法 JSON：{exc}") from exc
        if row.get("decision") not in {"retain", "exclude", "error_retain"}:
            raise ValueError(f"decisions.jsonl 第 {n} 行 decision 非法：{row.get('decision')!r}")
        rows.append(row)
    if [r.get("ordinal") for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("decisions.jsonl 序号不连续或缺行")
    if len(rows) != int(meta.get("input", -1)):
        raise ValueError(f"decisions.jsonl 行数 {len(rows)} ≠ LLM 输入篇数 {meta.get('input')}")
    if not llm_input.is_file():
        raise FileNotFoundError(f"LLM 输入文件不存在：{llm_input}")
    if [r.get("title") for r in rows] != _titles(parse_ris(llm_input)):
        raise ValueError("decisions.jsonl 与 LLM 输入文件当前内容不一致（输入在筛选后被改动？）")

    excluded_records = parse_ris(excluded_path)
    final_records = parse_ris(final_ris)
    kept_titles = [r["title"] for r in rows if r["decision"] != "exclude"]
    excl_titles = [r["title"] for r in rows if r["decision"] == "exclude"]
    if kept_titles != _titles(final_records):
        raise ValueError("decisions.jsonl 的保留序列与 FINAL_RIS 不一致")
    if excl_titles != _titles(excluded_records):
        raise ValueError("decisions.jsonl 的排除序列与 excluded.ris 不一致")
    return {
        "rows": len(rows),
        "retain": sum(r["decision"] == "retain" for r in rows),
        "error_retain": sum(r["decision"] == "error_retain" for r in rows),
        "exclude": len(excl_titles),
    }


def validate_xr_run(run_dir: Path, canonical: Path) -> dict:
    """xr_screening.csv 逐篇对应 XR 的输入；必须与当前 canonical 逐条一致，防止用旧运行覆盖新导出。"""
    csv_path = run_dir / "xr_screening.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"XR 运行缺少 {csv_path}")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        csv_titles = [row["标题"] for row in csv.DictReader(handle)]
    if csv_titles != _titles(parse_ris(canonical)):
        raise ValueError("xr_screening.csv 与当前 canonical 不一致（canonical 在 XR 运行后被改动？请重跑 XR）")
    return {"xr_input_records": len(csv_titles)}


def _method_text(mode: str, final_ris: Path, run_dir: Path) -> str:
    zones = sorted(run_dir.glob("xr_zone*.ris"))
    if mode in ("zone", "zone+llm"):
        src = final_ris if mode == "zone" else (zones[0] if zones else None)
        m = re.search(r"xr_zone(\d+)\.ris$", src.name) if src else None
        zone_txt = f"XR≤{m.group(1)}区" if m else "XR 分区"
        return zone_txt if mode == "zone" else f"{zone_txt}+LLM"
    return "LLM"


def _atomic_replace(source: Path, target: Path) -> None:
    tmp_name: str | None = None
    try:
        with source.open("rb") as src, tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, delete=False,
        ) as dst:
            tmp_name = dst.name
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        if Path(tmp_name).read_bytes() != source.read_bytes():
            raise OSError("临时副本与 FINAL_RIS 不一致")
        os.replace(tmp_name, target)
        tmp_name = None
    finally:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)


def _record_in_status(lit_dir: Path, **kwargs) -> str | None:
    """调用 lit-workflow 的 lit_status.record_screen；失败时返回需手动执行的提示。"""
    for cand in (_HERE.parent / "lit-workflow", _HERE.parent.parent / "lit-workflow" / "scripts"):
        if (cand / "lit_status.py").is_file():
            sys.path.insert(0, str(cand))
            try:
                import lit_status  # noqa: WPS433
                lit_status.record_screen(lit_dir, **kwargs)
                return None
            except Exception as exc:  # canonical 已发布，记录失败只提醒
                return f"lit_status.md 记录失败（{exc}）"
    return "未找到 lit-workflow 的 lit_status.py"


def finalize(args: argparse.Namespace) -> dict:
    canonical = Path(args.canonical).expanduser().resolve()
    final_ris = Path(args.final_ris).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    mode = args.mode

    key = lit_common.classify_ris(canonical)
    if key is None:
        raise ValueError(f"canonical 文件名不规范（应为 directionN_wos|cnki|openalex.ris）：{canonical.name}")
    direction, source = key
    lit_dir = canonical.parent
    runs_root = lit_dir / RUNS_DIRNAME
    if run_dir.parent != runs_root or run_dir.name == "original" or not run_dir.is_dir():
        raise ValueError(f"--run-dir 必须是已存在的 {runs_root}/<运行目录>")
    if final_ris.parent != run_dir:
        raise ValueError("FINAL_RIS 必须位于 --run-dir 内")
    if mode == "zone" and not re.fullmatch(r"xr_zone\d+\.ris", final_ris.name):
        raise ValueError("mode=zone 的 FINAL_RIS 应为 xr_zone{N}.ris")
    if mode in LLM_MODES and final_ris.name != "llm.ris":
        raise ValueError(f"mode={mode} 的 FINAL_RIS 应为 llm.ris")

    before = _check(canonical, "canonical")
    after = _check(final_ris, "FINAL_RIS")
    subset = validate_ordered_subset(canonical, final_ris)
    xr = validate_xr_run(run_dir, canonical) if mode in ("zone", "zone+llm") else None
    audit = validate_llm_run(run_dir, final_ris, canonical, mode) if mode in LLM_MODES else None

    original_dir = runs_root / "original"
    original_backup = original_dir / canonical.name
    backup = original_backup if not original_backup.exists() else run_dir / f"before_{canonical.name}"
    if backup.exists():
        raise ValueError(f"备份目标已存在，拒绝覆盖：{backup}")
    method = args.note or _method_text(mode, final_ris, run_dir)
    plan = {
        "action": "execute" if args.execute else "dry-run",
        "direction": direction,
        "source": source,
        "mode": mode,
        "method": method,
        "canonical": str(canonical),
        "final_ris": str(final_ris),
        "before_records": before,
        "after_records": after,
        "ordered_subset": subset,
        "xr_run": xr,
        "llm_audit": audit,
        "backup_to": str(backup),
    }
    if not args.execute:
        return plan

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(canonical, backup)
    if backup.read_bytes() != canonical.read_bytes():
        raise OSError("备份校验失败，未替换 canonical")
    _atomic_replace(final_ris, canonical)
    if _check(canonical, "替换后的 canonical") != after:
        raise OSError("替换后 canonical 篇数与 FINAL_RIS 不一致")

    warning = _record_in_status(
        lit_dir, direction=direction, source=source, method=method, before=before, after=after,
        run_dir=run_dir, backup=backup, day=date.today().isoformat(),
    )
    plan["published"] = True
    if warning:
        plan["warning"] = (
            f"{warning}；canonical 已替换。请手动补记：lit_status.py record-screen "
            f"--direction {direction} --source {source} --method '{method}' --before {before} "
            f"--after {after} --run-dir '{run_dir}' --backup '{backup}'"
        )
    return plan


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="用筛选结果替换 canonical RIS（先 dry-run，确认后 execute）")
    p.add_argument("--canonical", required=True, help="structure/2_literature/directionN_<source>.ris")
    p.add_argument("--final-ris", required=True, help="运行目录中的 xr_zone{N}.ris 或 llm.ris")
    p.add_argument("--run-dir", required=True, help="_screen_runs/<运行目录>")
    p.add_argument("--mode", required=True, choices=("zone", "llm", "zone+llm"))
    p.add_argument("--note", help="写入筛选记录的方法说明（默认按 mode 自动生成）")
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--execute", action="store_true")
    return p


if __name__ == "__main__":
    try:
        print(json.dumps(finalize(build_parser().parse_args()), ensure_ascii=False, indent=2))
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}")
