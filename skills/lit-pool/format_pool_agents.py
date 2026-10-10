#!/usr/bin/env python3
"""Validate filled pool templates and write formatted tables (lit-pool step 3).

Input : _pool_runs/pool_prepare.json and pool_agent{N}_raw.md (filled by workers).
Each assignment (label, citation_key) of an agent must appear exactly once with a
non-empty 引用场景. Bibliographic fields come from pool_prepare.json, not from the
worker. Status per agent: OK | EMPTY | INVALID | MISSING; formatted files
(_pool_runs/pool_agent{N}.md) are written only when every agent is OK.
--check validates only (JSON status with --json).
"""
from __future__ import annotations

import argparse
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

POOL_DIR = "_pool_runs"
FIELDS = {"标签": "tag", "tag": "tag", "citation_key": "key", "citationkey": "key", "引用场景": "scene"}
TABLE_HEADER = ["| 分级 | 作者 | 年份 | citation key | 引用场景 | 期刊 |",
                "|:----:|:-----|:----:|:------------|:---------|:-----|"]


def load_prepare(lit_dir: Path) -> dict:
    path = lit_dir / POOL_DIR / "pool_prepare.json"
    if not path.exists():
        raise ValueError(f"POOL_PREPARE_MISSING: {path} (run pool_prepare.py first)")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_blocks(text: str) -> list[dict]:
    blocks, cur, last = [], None, None
    for line in text.splitlines():
        if re.match(r"^###\s+", line.strip()):
            cur, last = {}, None
            blocks.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^\s*[-*]\s*([^:：]+?)\s*[:：]\s?(.*)$", line)
        if m:
            name = m.group(1).strip().lower().replace(" ", "")
            last = FIELDS.get(name, FIELDS.get(m.group(1).strip()))
            if last:
                cur[last] = m.group(2).strip()
        elif last == "scene" and line.strip() and not line.lstrip().startswith("#"):
            cur["scene"] = (cur.get("scene", "") + " " + line.strip()).strip()
    return blocks


def validate_agent(lit_dir: Path, agent: dict) -> dict:
    res = {"agent_id": agent["agent_id"], "status": "OK", "errors": [], "scenes": {}}
    path = lit_dir / POOL_DIR / agent["raw_file"]
    if not path.exists():
        res.update(status="MISSING", errors=[f"{agent['raw_file']} missing"])
        return res
    blocks = parse_blocks(path.read_text(encoding="utf-8"))
    expected = {(t, k) for t, k in agent["assignments"]}
    got: dict[tuple[str, str], str] = {}
    errors = []
    for b in blocks:
        pair = (lc.split_labels(b.get("tag", ""))[0] if b.get("tag") else "", b.get("key", ""))
        if pair in got:
            errors.append(f"duplicate {pair[1]}@{pair[0]}")
        got[pair] = b.get("scene", "")
    if set(got) != expected:
        errors.append(f"assignments differ: missing={sorted(expected - set(got))[:5]} extra={sorted(set(got) - expected)[:5]}")
    if not errors and all(not v for v in got.values()):
        res.update(status="EMPTY", errors=["not filled yet"])
        return res
    empty = [f"{k}@{t}" for (t, k), v in got.items() if (t, k) in expected and (not v or "{{" in v)]
    if empty:
        errors.append(f"引用场景 empty: {empty[:5]}")
    if errors:
        res.update(status="INVALID", errors=errors)
    else:
        res["scenes"] = got
    return res


def formatted(agent: dict, scenes: dict, by_key: dict) -> str:
    out = []
    for tag in agent["tags"]:
        out += [f"# {tag}", "", *TABLE_HEADER]
        for t, k in agent["assignments"]:
            if t != tag:
                continue
            p = by_key[k]
            out.append(f"| {lc.TIER_CN.get(p['tier'], p['tier'])} | {lc.cell(p['author'])} | {p['year']} | {k} | "
                       f"{lc.cell(scenes[(t, k)])} | {lc.cell(p['journal'])} |")
        out.append("")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    try:
        prep = load_prepare(lit_dir)
        results = [validate_agent(lit_dir, a) for a in prep["agents"]]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    bad = [r for r in results if r["status"] != "OK"]
    if args.check and args.json:
        print(json.dumps({str(r["agent_id"]): {"status": r["status"], "errors": r["errors"][:10]} for r in results},
                         ensure_ascii=False, indent=2))
        raise SystemExit(1 if bad else 0)
    print("=== POOL AGENT CHECK ===")
    for r in results:
        print(f"agent {r['agent_id']}: {r['status']}")
        for e in r["errors"][:10]:
            print(f"  ❌ {e}")
    if bad:
        print("Redo agents: " + ", ".join(str(r["agent_id"]) for r in bad))
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    if not args.check:
        by_key = {p["citation_key"]: p for p in prep["papers"]}
        for a, r in zip(prep["agents"], results):
            dp.atomic_write(lit_dir / POOL_DIR / a["formatted_file"], formatted(a, r["scenes"], by_key))
    print("=== VERIFY: PASS ===")


if __name__ == "__main__":
    main()
