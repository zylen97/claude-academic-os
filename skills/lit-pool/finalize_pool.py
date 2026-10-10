#!/usr/bin/env python3
"""Final literature-pool check; writes literature_manifest.json (one row per unique paper).

Default mode (end of lit-pool), from _pool_runs/pool_prepare.json:
  BLOCK  master_report.md missing or still containing JUDGE placeholders
  BLOCK  a pool key missing from citation_pool/master.bib
  BLOCK  pool key sets differ from the prepared corpus (manifest rows must equal
         the unique key set of the six pool files)
  WARN   method landscape missing; tagged_reports/ changed after pool_prepare
then writes literature_manifest.json (no hashes, no status field).

--check-only (downstream, e.g. build-intro-lit-table): validates an existing
literature_manifest.json against the pool files, master.bib and master_report.md;
writes nothing.
"""
from __future__ import annotations

import argparse
import datetime as dt
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from format_pool_agents import load_prepare  # noqa: E402
from pool_merge import pool_keys  # noqa: E402
from ris2bib import bib_keys  # noqa: E402

RULE = "same paper = same DOI, or same WoS UT, or same first-author surname + year + normalized title[:80]"


def common_checks(lit_dir: Path, manifest_keys: set[str], groups: dict[str, set[str]] | None) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    pool = lit_dir / "citation_pool"
    union: set[str] = set()
    for g in lc.POOL_FILES:
        path = pool / f"{g}.md"
        if not path.exists():
            errors.append(f"POOL_FILE_MISSING: citation_pool/{g}.md")
            continue
        keys = pool_keys(path)
        union |= keys
        if groups is not None and keys != groups[g]:
            errors.append(f"POOL_KEYS_{g}: missing={sorted(groups[g] - keys)[:8]} extra={sorted(keys - groups[g])[:8]}")
        if not keys and g in ("COMP", "METHOD"):
            warnings.append(f"{g}.md is empty — report as residual risk")
    if union != manifest_keys:
        errors.append(f"MANIFEST_VS_POOL: manifest-only={sorted(manifest_keys - union)[:8]} pool-only={sorted(union - manifest_keys)[:8]}")
    bib = pool / "master.bib"
    if not bib.exists():
        errors.append("MASTER_BIB_MISSING")
    else:
        bk = set(bib_keys(lc.read_text(bib)))
        if union - bk:
            errors.append(f"KEYS_NOT_IN_MASTER_BIB: {sorted(union - bk)[:10]}")
        if bk - manifest_keys:
            warnings.append(f"master.bib has keys outside the corpus: {sorted(bk - manifest_keys)[:8]}")
    report = lit_dir / "master_report.md"
    if not report.exists():
        errors.append("MASTER_REPORT_MISSING")
    elif lc.read_text(report).count("JUDGE"):
        errors.append(f"JUDGE_PENDING: master_report.md has {lc.read_text(report).count('JUDGE')} JUDGE placeholder(s)")
    land = lit_dir / "method_landscape.md"
    if not land.exists():
        warnings.append("method_landscape.md missing")
    else:
        first = (lc.read_text(land).splitlines() or [""])[0]
        if "<!-- curated -->" in first and not (lit_dir / "method_landscape_refresh.md").exists():
            warnings.append("method_landscape.md is curated; literature refresh not written to method_landscape_refresh.md")
    return errors, warnings


def tagged_occurrences(lit_dir: Path) -> list[tuple]:
    out = []
    for d, path in sorted(lc.active_tagged_reports(lit_dir).items()):
        out += [(d, *sig) for sig in lc.row_signature(lc.parse_report_rows(lc.read_text(path)))]
    return sorted(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    manifest_path = lit_dir / "literature_manifest.json"
    try:
        if args.check_only:
            if not manifest_path.exists():
                raise ValueError("LITERATURE_MANIFEST_MISSING: lit-pool has not finished")
            man = json.loads(manifest_path.read_text(encoding="utf-8"))
            keys = [p["citation_key"] for p in man.get("papers", [])]
            errors, warnings = common_checks(lit_dir, set(keys), None)
            if len(keys) != len(set(keys)):
                errors.append("MANIFEST_DUPLICATE_KEYS")
            papers = man.get("papers", [])
        else:
            prep = load_prepare(lit_dir)
            papers = prep["papers"]
            groups = {g: set() for g in lc.POOL_FILES}
            for p in papers:
                for t in p["tags"]:
                    groups[lc.label_group(t)].add(p["citation_key"])
            errors, warnings = common_checks(lit_dir, {p["citation_key"] for p in papers}, groups)
            recorded = sorted((r["direction"], r["tier"], r["row"], lc.norm_text(r["title"]))
                              for p in papers for r in p["records"])
            if recorded != tagged_occurrences(lit_dir) or lc.compare_tagged_to_review(lit_dir):
                warnings.append("tagged_reports/ or review reports changed after pool_prepare — rerun lit-pool from prepare to refresh")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors, warnings, papers = [str(exc)], [], []
    print("=== FINALIZE LITERATURE POOL ===")
    for w in warnings:
        print(f"  ⚠️ {w}")
    if errors:
        print("=== VERIFY: FAIL ===")
        for e in errors[:20]:
            print(f"  ❌ {e}")
        raise SystemExit(1)
    if not args.check_only:
        rows = [{
            "citation_key": p["citation_key"], "author": p["author"], "year": p["year"], "title": p["title"],
            "journal": p["journal"], "doi": p.get("doi", ""), "database_id": p.get("database_id", ""),
            "tier": p["tier"], "tags": p["tags"],
            "pools": sorted({lc.label_group(t) for t in p["tags"]}),
            "directions": p["directions"], "reasons": p["reasons"], "source_origin": p["source_origin"],
            "records": p["records"],
        } for p in sorted(papers, key=lambda x: x["citation_key"])]
        data = {"generated": dt.date.today().isoformat(), "unique_paper_rule": RULE,
                "count": len(rows), "papers": rows}
        dp.atomic_write(manifest_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"Wrote {manifest_path} ({len(rows)} papers)")
    print(f"Papers: {len(papers)}")
    print("=== VERIFY: PASS ===")


if __name__ == "__main__":
    main()
