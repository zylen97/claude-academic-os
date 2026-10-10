#!/usr/bin/env python3
"""Validate the filled review batch files listed in _review_runs/dispatch_plan.json.

Each batch file holds one block per source record (### D{N}-{source}-{ordinal}).
Blocking (the worker must redo the batch):
  * block set/order/titles differ from the RIS chunk; chunk/source changed
  * a record without 决定 include/exclude, an include without 级别, an empty 理由
  * include + exclude != records in the chunk
Reminders only: 证据 not found verbatim in the abstract; title-only include
without “仅凭标题”.

Status per batch: OK | EMPTY (not filled yet) | INVALID | MISSING.
Exit 0 only when every batch is OK. --json prints a machine-readable status map.
No files are written.
"""
from __future__ import annotations

import argparse
import json
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

DECISIONS = {"include": "include", "入选": "include", "exclude": "exclude", "淘汰": "exclude"}
TIER_MAP = {"核心": "core", "core": "core", "重要": "important", "important": "important",
            "备选": "backup", "backup": "backup"}
EMPTY_TIER = {"", "-", "—", "无", "淘汰", "excluded", "exclude"}
NO_SUSPECT = {"", "-", "—", "无", "否", "no", "none"}


def load_review_plan(lit_dir: Path) -> dict:
    path = lit_dir / dp.REVIEW_DIR / "dispatch_plan.json"
    if not path.exists():
        raise ValueError(f"DISPATCH_PLAN_MISSING: {path} (run dispatch_plan.py --mode ris first)")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("mode") != "ris":
        raise ValueError(f"DISPATCH_PLAN_WRONG_MODE: {path} is {plan.get('mode')!r}, expected 'ris'")
    return plan


def validate_batch(lit_dir: Path, b: dict) -> dict:
    """Return {status, errors, warnings, included:[paper dicts]}."""
    run = lit_dir / dp.REVIEW_DIR
    res = {"batch_id": b["batch_id"], "status": "OK", "errors": [], "warnings": [], "included": []}

    def fail(msg: str, status: str = "INVALID") -> dict:
        res["status"] = status
        res["errors"].append(msg)
        return res

    path, chunk = run / b["batch_file"], run / b["chunk_file"]
    if not path.exists():
        return fail(f"batch file missing: {path.name}", "MISSING")
    if not chunk.exists():
        return fail(f"chunk missing: {b['chunk_file']} (rerun dispatch)")
    text = path.read_text(encoding="utf-8")
    meta = {k: b[k] for k in ("batch_id", "direction", "source_type", "source_file", "chunk_file",
                              "item_start", "item_end", "item_count")}
    if dp.read_meta(text, dp.BATCH_PREFIX) != meta:
        return fail("first-line lit-batch metadata missing or edited")
    records = lc.split_ris_records(lc.read_text(chunk))
    if len(records) != b["item_count"]:
        return fail(f"chunk has {len(records)} records, plan says {b['item_count']}")
    source = lit_dir / b["source_file"]
    if not source.exists():
        return fail(f"SOURCE_CHANGED: {b['source_file']} missing (rerun dispatch)")
    src_records = lc.split_ris_records(lc.read_text(source))
    window = src_records[b["item_start"] - 1:b["item_end"]]
    if [lc.norm_text(dp.record_title(r)) for r in window] != [lc.norm_text(dp.record_title(r)) for r in records]:
        return fail(f"SOURCE_CHANGED: {b['source_file']} records {b['item_start']}-{b['item_end']} differ from chunk (rerun dispatch)")

    blocks = dp.parse_review_batch(text)
    expected_ids = [f"D{b['direction']}-{b['source_type']}-{b['item_start'] + i}" for i in range(len(records))]
    got_ids = [blk["record_id"] for blk in blocks]
    if got_ids != expected_ids:
        missing = sorted(set(expected_ids) - set(got_ids))
        extra = sorted(set(got_ids) - set(expected_ids))
        return fail(f"record blocks differ from chunk: missing={missing[:5]} extra={extra[:5]} "
                    f"(count {len(got_ids)}/{len(expected_ids)}, order must follow the chunk)")
    if all(not blk.get("决定", "").strip() for blk in blocks):
        return fail("not filled yet", "EMPTY")

    n_inc = n_exc = 0
    for blk, rec in zip(blocks, records):
        rid = blk["record_id"]
        title = dp.record_title(rec)
        if lc.norm_text(blk.get("标题", "")) != lc.norm_text(title):
            res["errors"].append(f"{rid}: 标题 was edited")
            continue
        decision = DECISIONS.get(blk.get("决定", "").strip().lower())
        tier_raw = blk.get("级别", "").strip()
        reason = blk.get("理由", "").strip()
        evidence = blk.get("证据", "").strip()
        if decision is None:
            res["errors"].append(f"{rid}: 决定 must be include/exclude, got {blk.get('决定', '')!r}")
            continue
        if not reason:
            res["errors"].append(f"{rid}: 理由 is empty")
        abstract = dp.ris_field(rec, "AB")
        if decision == "exclude":
            n_exc += 1
            if tier_raw.lower() not in EMPTY_TIER:
                res["errors"].append(f"{rid}: exclude with 级别 {tier_raw!r}")
            continue
        n_inc += 1
        tier = TIER_MAP.get(tier_raw.lower())
        if tier is None:
            res["errors"].append(f"{rid}: include needs 级别 核心/重要/备选, got {tier_raw!r}")
            continue
        if abstract:
            if not evidence or lc.norm_text(evidence) not in lc.norm_text(abstract):
                res["warnings"].append(f"{rid}: 证据 not found verbatim in abstract")
        elif "仅凭标题" not in reason + evidence:
            res["warnings"].append(f"{rid}: no abstract; reason should say 仅凭标题")
        suspect = blk.get("疑似竞品", "").strip()
        authors = dp.ris_values(rec, "AU") or dp.ris_values(rec, "A1")
        res["included"].append({
            "record_id": rid, "direction": b["direction"], "source_type": b["source_type"],
            "source_file": b["source_file"], "tier": tier, "reason": reason,
            "author": lc.surname(authors[0]) if authors else "",
            "title": title,
            "year": (dp.ris_field(rec, "PY") or dp.ris_field(rec, "Y1") or dp.ris_field(rec, "DA"))[:4],
            "journal": dp.ris_field(rec, "T2") or dp.ris_field(rec, "JF") or dp.ris_field(rec, "JO") or dp.ris_field(rec, "T3"),
            "doi": lc.normalize_doi(dp.ris_field(rec, "DO")),
            "database_id": dp.ris_field(rec, "UT"),
            "suspect": "" if suspect.lower() in NO_SUSPECT else suspect,
        })
    if not res["errors"] and n_inc + n_exc != b["item_count"]:
        res["errors"].append(f"include({n_inc}) + exclude({n_exc}) != records({b['item_count']})")
    if res["errors"]:
        res["status"] = "INVALID"
        res["included"] = []
    return res


def validate_all(lit_dir: Path) -> tuple[dict, list[dict]]:
    plan = load_review_plan(lit_dir)
    skipped = lc.skipped_directions(lit_dir, ("review",))
    if skipped & set(plan["directions"]):  # skipped after dispatch: leave those batches out
        plan["directions"] = [d for d in plan["directions"] if d not in skipped]
        plan["batches"] = [b for b in plan["batches"] if b["direction"] not in skipped]
        plan["sources"] = [s for s in plan["sources"] if s["direction"] not in skipped]
    return plan, [validate_batch(lit_dir, b) for b in plan["batches"]]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--json", action="store_true", help="print {batch_id: {status, errors}} only")
    args = ap.parse_args()
    try:
        plan, results = validate_all(Path(args.lit_dir))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    ok = all(r["status"] == "OK" for r in results)
    if args.json:
        print(json.dumps({r["batch_id"]: {"status": r["status"], "errors": r["errors"][:10]} for r in results},
                         ensure_ascii=False, indent=2))
        raise SystemExit(0 if ok else 1)
    print("=== REVIEW BATCH CHECK ===")
    for r in results:
        line = f"{r['batch_id']}: {r['status']}"
        if r["status"] == "OK":
            line += f" (入选 {len(r['included'])})"
        print(line)
        for e in r["errors"][:10]:
            print(f"  ❌ {e}")
        for w in r["warnings"][:10]:
            print(f"  ⚠️ {w}")
    bad = [r["batch_id"] for r in results if r["status"] != "OK"]
    print(f"OK {len(results) - len(bad)}/{len(results)}")
    if bad:
        print("Redo batches: " + ", ".join(bad))
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    print("=== VERIFY: PASS ===")


if __name__ == "__main__":
    main()
