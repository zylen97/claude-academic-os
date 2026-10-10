#!/usr/bin/env python3
"""Validate filled tag batches and write tagged copies of the review reports.

Input : _tag_runs/dispatch_plan.json (dispatch_plan.py --mode report) and its
        filled d{N}_b{M}_tags.md files; review reports direction{N}_report.md.
Output: tagged_reports/direction{N}_report.md for every direction in the plan
        (review reports are never modified; an older tagged copy is archived).

Blocking: plan missing; a batch missing/unfilled/invalid (every row needs >=1
valid label joined with '+'); review report rows changed since dispatch.
Transactional: nothing is written unless every batch of the plan is OK.
--check validates only and prints per-batch status (JSON with --json).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
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

def allowed_tags(rq_count: int) -> set[str]:
    return lc.allowed_labels(rq_count)


split_tags = lc.split_labels


def load_tag_plan(lit_dir: Path) -> dict:
    path = lit_dir / dp.TAG_DIR / "dispatch_plan.json"
    if not path.exists():
        raise ValueError(f"DISPATCH_PLAN_MISSING: {path} (run dispatch_plan.py --mode report first)")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("mode") != "report":
        raise ValueError(f"DISPATCH_PLAN_WRONG_MODE: {path} is {plan.get('mode')!r}, expected 'report'")
    skipped = lc.skipped_directions(lit_dir, ("review", "tag"))
    plan["reports"] = [r for r in plan["reports"] if r["direction"] not in skipped]
    plan["batches"] = [b for b in plan["batches"] if b["direction"] not in skipped]
    return plan


def validate_batch(lit_dir: Path, b: dict, allowed: set[str]) -> dict:
    res = {"batch_id": b["batch_id"], "status": "OK", "errors": [], "tags": {}}
    path = lit_dir / dp.TAG_DIR / b["batch_file"]
    if not path.exists():
        res.update(status="MISSING", errors=[f"batch file missing: {path.name}"])
        return res
    text = path.read_text(encoding="utf-8")
    meta = {"batch_id": b["batch_id"], "direction": b["direction"], "report_file": b["report_file"], "refs": b["refs"]}
    if dp.read_meta(text, dp.TAGS_PREFIX) != meta:
        res.update(status="INVALID", errors=["first-line lit-tags metadata missing or edited"])
        return res
    report = lit_dir / b["report_file"]
    current = {(r["tier"], r["row"]): lc.norm_text(r["title"]) for r in lc.parse_report_rows(lc.read_text(report))} if report.exists() else {}
    stale = [f"{x['tier']}:{x['row']}" for x in b["refs"] if current.get((x["tier"], x["row"])) != lc.norm_text(x["title"])]
    if stale:
        res.update(status="INVALID", errors=[f"REVIEW_REPORT_CHANGED: {b['report_file']} rows {stale[:5]} differ (rerun dispatch --mode report)"])
        return res
    tags, dup = dp.parse_tag_batch(text)
    expected = {(x["tier"], x["row"]) for x in b["refs"]}
    errors = [f"{e} appears twice" for e in dup]
    if set(tags) != expected:
        errors.append(f"rows differ from plan: missing={sorted(expected - set(tags))[:5]} extra={sorted(set(tags) - expected)[:5]}")
    if not errors and all(not v for v in tags.values()):
        res.update(status="EMPTY", errors=["not filled yet"])
        return res
    for key in sorted(expected & set(tags)):
        labels = split_tags(tags[key])
        if not labels:
            errors.append(f"{key[0]}:{key[1]} has no label")
            continue
        bad = [t for t in labels if t not in allowed]
        if bad:
            errors.append(f"{key[0]}:{key[1]} invalid label(s) {bad} (use + between labels)")
            continue
        res["tags"][key] = "+".join(dict.fromkeys(labels))
    if errors:
        res.update(status="INVALID", errors=errors, tags={})
    return res


def render_tagged(review_text: str, tags: dict[tuple[str, int], str]) -> str:
    out, tier = [], None
    for line in review_text.splitlines():
        if line.startswith("##"):
            tier = next((t for t, h in lc.TIER_HEADINGS.items() if h[:4] in line), None)
        elif tier and line.startswith("|"):
            cells = lc.split_row(line)
            if len(cells) == 6:
                if re.fullmatch(r"\d+", cells[0]):
                    cells.insert(5, tags[(tier, int(cells[0]))])
                elif set(cells[0]) <= set(":-") and cells[0]:
                    cells.insert(5, ":------")
                else:
                    cells.insert(5, "功能标签")
                line = "| " + " | ".join(cells) + " |"
        out.append(line)
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--rq-count", type=int, required=True, help="number of RQs in idea.md")
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    ap.add_argument("--json", action="store_true", help="with --check: print JSON status map")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    try:
        allowed = allowed_tags(args.rq_count)
        plan = load_tag_plan(lit_dir)
        results = [validate_batch(lit_dir, b, allowed) for b in plan["batches"]]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    bad = [r for r in results if r["status"] != "OK"]
    if args.check and args.json:
        print(json.dumps({r["batch_id"]: {"status": r["status"], "errors": r["errors"][:10]} for r in results},
                         ensure_ascii=False, indent=2))
        raise SystemExit(1 if bad else 0)
    print("=== TAG BATCH CHECK ===")
    for r in results:
        print(f"{r['batch_id']}: {r['status']}")
        for e in r["errors"][:10]:
            print(f"  ❌ {e}")
    if bad:
        print("Redo batches: " + ", ".join(r["batch_id"] for r in bad))
        print("No tagged report was written.")
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    if args.check:
        print("=== VERIFY: PASS ===")
        return

    by_dir: dict[int, dict] = {}
    for b, r in zip(plan["batches"], results):
        by_dir.setdefault(b["direction"], {}).update(r["tags"])
    out_dir = lit_dir / "tagged_reports"
    rendered: dict[Path, str] = {}
    try:
        for item in plan["reports"]:
            report = lit_dir / item["report_file"]
            rows = lc.parse_report_rows(lc.read_text(report))
            keys = {(x["tier"], x["row"]) for x in rows}
            tags = by_dir.get(item["direction"], {})
            if len(rows) != item["row_count"] or keys != set(tags):
                raise ValueError(f"REVIEW_REPORT_CHANGED: {report.name} rows no longer match the tag plan (rerun dispatch --mode report)")
            rendered[out_dir / report.name] = render_tagged(lc.read_text(report), tags)
        out_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".tag-stage-", dir=out_dir) as tmp:
            for target, text in rendered.items():
                (Path(tmp) / target.name).write_text(text, encoding="utf-8")
            for target, text in rendered.items():
                if target.exists():
                    if target.read_text(encoding="utf-8") == text:
                        print(f"  = {target.name}: unchanged")
                        continue
                    print(f"NOTICE: archived old tagged copy -> {lc.archive(target, lit_dir)}")
                os.replace(Path(tmp) / target.name, target)
                print(f"  ✓ tagged_reports/{target.name}")
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    print(f"Directions written: {', '.join('D%d' % i['direction'] for i in plan['reports'])}")
    print("=== VERIFY: PASS ===")


if __name__ == "__main__":
    main()
