#!/usr/bin/env python3
"""
RIS 解析 + XR2026 新锐分区过滤（lit-screen Step 1）

用法:
  python3 screen_xr.py <canonical_ris> [--zone 2] [--run-dir DIR]

只读 canonical RIS，结果写入运行目录（默认 <RIS 所在目录>/_screen_runs/<stem>_<时间>/）：
  - xr_zone{N}.ris       保留记录（1..N 区 + 未匹配），为原 RIS 记录块的有序子集，续行原样保留
  - xr_screening.csv     逐篇匹配明细
stdout 输出统计 JSON（含 output_path / csv_path / run_dir）。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# Claude 平铺：<skill>/data；Codex：<skill>/scripts/../data
XR_CSV = next(
    (p for p in (_HERE / "data" / "XR2026-UTF8.csv", _HERE.parent / "data" / "XR2026-UTF8.csv") if p.is_file()),
    _HERE / "data" / "XR2026-UTF8.csv",
)

TAG_RE = re.compile(r"^([A-Z][A-Z0-9])  -(?:\s?(.*))?$")
RAW_BLOCK_KEY = "_raw_block"
ORDINAL_KEY = "_ordinal"
RUNS_DIRNAME = "_screen_runs"


def _append_value(record: dict, tag: str, value: str) -> None:
    """Append a RIS tag while retaining repeated fields such as AU/SN/KW."""
    if tag in record:
        if isinstance(record[tag], list):
            record[tag].append(value)
        else:
            record[tag] = [record[tag], value]
    else:
        record[tag] = value


def _append_continuation(record: dict, tag: str | None, value_index: int, text: str) -> None:
    """Merge an untagged RIS continuation line into the preceding field value."""
    if not tag or not text.strip():
        return
    continuation = text.strip()
    value = record.get(tag, "")
    if isinstance(value, list):
        if 0 <= value_index < len(value):
            value[value_index] = f"{value[value_index]} {continuation}".strip()
    else:
        record[tag] = f"{value} {continuation}".strip()


def _parse_block(raw_block: str, ordinal: int) -> dict:
    """Parse searchable fields while preserving the complete source block verbatim."""
    record: dict = {RAW_BLOCK_KEY: raw_block, ORDINAL_KEY: ordinal}
    last_tag: str | None = None
    last_value_index = 0
    saw_ty = False
    saw_er = False

    for raw_line in raw_block.splitlines():
        match = TAG_RE.match(raw_line.rstrip("\r"))
        if match:
            tag = match.group(1)
            value = (match.group(2) or "").strip()
            if tag == "ER":
                saw_er = True
                last_tag = None
                continue
            _append_value(record, tag, value)
            last_tag = tag
            current = record[tag]
            last_value_index = len(current) - 1 if isinstance(current, list) else 0
            saw_ty = saw_ty or tag == "TY"
        elif not saw_er:
            _append_continuation(record, last_tag, last_value_index, raw_line)

    if not saw_ty or not saw_er:
        raise ValueError(f"RIS record {ordinal + 1} is incomplete (requires TY and ER)")
    return record


def parse_ris(ris_path: str | Path) -> list[dict]:
    """Parse complete ER-terminated RIS records without reconstructing their raw text.

    Files are decoded with ``utf-8-sig`` so a BOM never pollutes the first TY tag.
    Continuation lines are merged for field-level screening, while ``_raw_block``
    retains every source line for byte-faithful subset output (apart from BOM removal).
    """
    with open(ris_path, "r", encoding="utf-8-sig", newline="") as handle:
        lines = handle.readlines()

    records: list[dict] = []
    current: list[str] = []
    saw_er = False
    pending_prefix: list[str] = []

    for line_no, line in enumerate(lines, start=1):
        tag_match = TAG_RE.match(line.rstrip("\r\n"))
        tag = tag_match.group(1) if tag_match else None

        if tag == "TY":
            if current:
                if not saw_er:
                    raise ValueError(f"RIS record before line {line_no} is missing ER")
                records.append(_parse_block("".join(current), len(records)))
            current = list(pending_prefix)
            pending_prefix = []
            current.append(line)
            saw_er = False
            continue

        if current:
            current.append(line)
            if tag == "ER":
                saw_er = True
        elif line.strip():
            raise ValueError(f"Unexpected content before first TY at line {line_no}")
        else:
            pending_prefix.append(line)

    if current:
        if not saw_er:
            raise ValueError("Final RIS record is missing ER")
        records.append(_parse_block("".join(current), len(records)))

    return records


def write_ris(records: list[dict], output_path: str | Path) -> None:
    """Atomically write selected raw RIS blocks in their original relative order."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous_ordinal = -1
    chunks: list[str] = []
    for rec in records:
        raw_block = rec.get(RAW_BLOCK_KEY)
        if not isinstance(raw_block, str):
            raise ValueError("RIS record is missing preserved _raw_block")
        ordinal = rec.get(ORDINAL_KEY)
        if isinstance(ordinal, int):
            if ordinal <= previous_ordinal:
                raise ValueError("RIS records must remain in original input order")
            previous_ordinal = ordinal
        chunks.append(raw_block)
    # 顺序不变 ⇒ 只有原文件最后一条可能缺结尾换行，而它在输出中也必然最后，不会与其他块粘连
    text = "".join(chunks)

    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", prefix=f".{destination.name}.",
            suffix=".tmp", dir=destination.parent, delete=False,
        ) as handle:
            tmp_name = handle.name
            handle.write(text)
            handle.flush()
        Path(tmp_name).replace(destination)
    except Exception:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)
        raise


def default_run_dir(ris_path: Path) -> Path:
    """<lit_dir>/_screen_runs/<stem>_<timestamp>/ — never the top-level corpus directory."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return ris_path.parent / RUNS_DIRNAME / f"{ris_path.stem}_{stamp}"


def load_xr2026() -> tuple[dict, dict]:
    """加载 XR2026 新锐分区表。返回 (ISSN/EISSN 索引, 期刊名索引)。"""
    issn_lookup = {}
    name_lookup = {}
    with open(XR_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            issn = row.get("ISSN", "").strip()
            eissn = row.get("EISSN", "").strip()
            journal_name = row.get("Journal", "").strip()
            zone_str = row.get("大类新锐分区", "").strip()
            zone_match = re.match(r"(\d)", zone_str)
            zone_num = int(zone_match.group(1)) if zone_match else 9
            info = {
                "journal": journal_name,
                "zone_num": zone_num,
                "zone_str": zone_str,
                "top": row.get("Top", "").strip(),
                "category": row.get("大类中文名", "").strip(),
                "warning": row.get("预警标记", "").strip(),
            }
            if issn and issn != "-":
                issn_lookup[issn.upper()] = info
            if eissn and eissn != "-":
                issn_lookup[eissn.upper()] = info
            if journal_name:
                name_lookup[journal_name.upper()] = info
    return issn_lookup, name_lookup


def get_issns(record: dict) -> list[str]:
    sn = record.get("SN", [])
    if isinstance(sn, str):
        sn = [sn]
    return [s.strip().upper() for s in sn if s.strip()]


def get_journal_name(record: dict) -> str:
    """优先 T2 (Secondary Title)，其次 J2, JO, JF。"""
    for tag in ("T2", "J2", "JO", "JF"):
        val = record.get(tag, "")
        if isinstance(val, list):
            val = val[0]
        if val.strip():
            return val.strip().upper()
    return ""


def screen(ris_path: str, max_zone: int = 2, run_dir: str | None = None) -> dict:
    source = Path(ris_path).expanduser().resolve()
    records = parse_ris(source)
    total = len(records)
    if total == 0:
        raise ValueError(f"RIS contains no complete records: {source}")

    out_dir = Path(run_dir).expanduser().resolve() if run_dir else default_run_dir(source)
    if out_dir == source.parent:
        raise ValueError("运行目录不能是 RIS 所在的顶层目录；请使用 _screen_runs/ 下的子目录")
    out_dir.mkdir(parents=True, exist_ok=True)

    xr_issn, xr_name = load_xr2026()

    zone_dist = {1: 0, 2: 0, 3: 0, 4: 0}
    unmatched = 0
    kept = []
    kept_with_unmatched = []
    removed = []
    detail_rows = []

    for rec in records:
        title = rec.get("TI", rec.get("T1", ""))
        if isinstance(title, list):
            title = " ".join(title)
        journal_in_ris = get_journal_name(rec)

        matched_info = None
        match_method = ""
        issns = get_issns(rec)
        for issn in issns:
            if issn in xr_issn:
                matched_info = xr_issn[issn]
                match_method = "ISSN"
                break
        if matched_info is None and journal_in_ris and journal_in_ris in xr_name:
            matched_info = xr_name[journal_in_ris]
            match_method = "期刊名"

        if matched_info is None:
            unmatched += 1
            kept_with_unmatched.append(rec)
            detail_rows.append({
                "标题": title, "期刊": journal_in_ris, "ISSN": ", ".join(issns),
                "匹配方式": "未匹配", "XR2026期刊名": "", "大类": "", "分区": "", "Top": "",
                "结果": "保留（未匹配）",
            })
            continue

        zone = matched_info["zone_num"]
        if zone in zone_dist:
            zone_dist[zone] += 1
        if zone <= max_zone:
            kept.append(rec)
            kept_with_unmatched.append(rec)
            action = "保留"
        else:
            removed.append(rec)
            action = "过滤"
        detail_rows.append({
            "标题": title, "期刊": journal_in_ris, "ISSN": ", ".join(issns),
            "匹配方式": match_method, "XR2026期刊名": matched_info["journal"],
            "大类": matched_info["category"], "分区": matched_info["zone_str"],
            "Top": matched_info["top"], "结果": action,
        })

    output_path = out_dir / f"xr_zone{max_zone}.ris"
    if kept_with_unmatched:
        write_ris(kept_with_unmatched, output_path)

    csv_path = out_dir / "xr_screening.csv"
    fieldnames = ["序号", "标题", "期刊", "ISSN", "匹配方式", "XR2026期刊名", "大类", "分区", "Top", "结果"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in enumerate(detail_rows, start=1):
            writer.writerow({"序号": index, **row})

    stats = {
        "input_path": str(source),
        "original": total,
        "zone_distribution": {
            "1区": zone_dist[1], "2区": zone_dist[2], "3区": zone_dist[3], "4区": zone_dist[4],
            "未匹配": unmatched,
        },
        "max_zone": max_zone,
        "kept": len(kept),
        "kept_with_unmatched": len(kept_with_unmatched),
        "removed": len(removed),
        "unmatched": unmatched,
        "run_dir": str(out_dir),
        "output_path": str(output_path) if kept_with_unmatched else None,
        "csv_path": str(csv_path),
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RIS + XR2026 新锐分区筛选（只写运行目录）")
    parser.add_argument("ris_path", help="canonical RIS，如 structure/2_literature/direction1_wos.ris")
    parser.add_argument("--zone", type=int, default=2, help="保留的最大分区 (默认 2 = 保留1区+2区)")
    parser.add_argument("--run-dir", help="运行目录（默认 <RIS目录>/_screen_runs/<stem>_<时间>/）")
    args = parser.parse_args()
    try:
        screen(args.ris_path, args.zone, args.run_dir)
    except Exception as exc:
        raise SystemExit(f"ERROR: {exc}")
