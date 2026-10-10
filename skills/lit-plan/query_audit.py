#!/usr/bin/env python3
"""Deterministic gate for lit-plan WoS query calibration.

Input JSON contains either one direction object or {"directions": [...]}.
The model supplies sample_relevant after reading the calibration RIS; this
script converts count, quota, precision, and iteration into a stable decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PASS_STATUSES = {"PASS", "PASS_TRUNCATE_1000", "PASS_PROBE"}
MIN_SAMPLE_SIZE = 20


def audit_direction(item: dict[str, Any]) -> dict[str, Any]:
    did = item.get("id", item.get("direction_id"))
    name = item.get("name", "")
    direction_type = item.get("direction_type", "corpus")
    quota = int(item.get("quota", 0) or 0)
    hits = int(item.get("actual_hits", 0) or 0)
    sample_size = int(item.get("sample_size", 0) or 0)
    sample_relevant = int(item.get("sample_relevant", 0) or 0)
    iteration = int(item.get("iteration", 1) or 1)

    if direction_type not in {"corpus", "targeted_probe"}:
        raise ValueError(f"方向{did}: invalid direction_type={direction_type!r}")
    if min(quota, hits, sample_size, sample_relevant) < 0:
        raise ValueError(f"方向{did}: counts must be non-negative")
    if sample_relevant > sample_size:
        raise ValueError(f"方向{did}: sample_relevant cannot exceed sample_size")
    if sample_size > hits:
        raise ValueError(f"方向{did}: sample_size cannot exceed actual_hits")
    if iteration < 1:
        raise ValueError(f"方向{did}: iteration must be >= 1")

    precision = sample_relevant / sample_size if sample_size else None
    required_sample = min(MIN_SAMPLE_SIZE, hits)
    reasons: list[str] = []

    if direction_type == "targeted_probe":
        if hits == 0:
            status = "ESCALATE" if iteration >= 3 else "REVISE_NO_HITS"
            reasons.append("targeted probe 未命中任何文献")
        elif sample_size < required_sample:
            status = "ESCALATE" if iteration >= 3 else "NEEDS_SAMPLE"
            reasons.append(
                f"抽样量 {sample_size} < 冻结所需 {required_sample}"
            )
        elif precision is not None and precision < 0.40:
            status = "ESCALATE" if iteration >= 3 else "REVISE_LOW_PRECISION"
            reasons.append(f"抽样相关率 {precision:.0%} < 40%")
        else:
            status = "PASS_PROBE"
            reasons.append("targeted probe 可作为窄 gap/竞品核查，不承担正式配额")
    else:
        failures: list[str] = []
        if hits < quota:
            failures.append(f"实际命中 {hits} < 正式配额 {quota}")
        if hits < 50:
            failures.append(f"实际命中 {hits} < corpus direction 建议下限 50")
        if failures:
            status = "ESCALATE" if iteration >= 3 else "REVISE"
            reasons.extend(failures)
        elif sample_size < required_sample:
            status = "ESCALATE" if iteration >= 3 else "NEEDS_SAMPLE"
            reasons.append(
                f"抽样量 {sample_size} < 冻结所需 {required_sample}"
            )
        else:
            if precision is not None and precision < 0.40:
                failures.append(f"抽样相关率 {precision:.0%} < 40%")
            if failures:
                status = "ESCALATE" if iteration >= 3 else "REVISE"
                reasons.extend(failures)
            elif hits > 1000:
                status = "PASS_TRUNCATE_1000"
                reasons.append("数量和相关性通过；按近180天使用量降序导出前1000条")
            else:
                status = "PASS"
                reasons.append("数量和抽样相关性均通过；导出全部结果")

    return {
        "id": did,
        "name": name,
        "direction_type": direction_type,
        "quota": quota,
        "actual_hits": hits,
        "sample_size": sample_size,
        "sample_relevant": sample_relevant,
        "sample_precision": None if precision is None else round(precision, 4),
        "iteration": iteration,
        "status": status,
        "reasons": reasons,
        "export_records": 0 if status not in PASS_STATUSES else min(hits, 1000),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit calibrated WoS queries")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        items = data.get("directions") if isinstance(data, dict) else None
        if items is None:
            items = [data]
        if not isinstance(items, list) or not items:
            raise ValueError("input must contain one direction or a non-empty directions list")
        results = [audit_direction(item) for item in items]
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = {
        "directions": results,
        "verify": "PASS" if all(r["status"] in PASS_STATUSES for r in results) else "FAIL",
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    print(f"=== VERIFY: {payload['verify']} ===")
    return 0 if payload["verify"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
