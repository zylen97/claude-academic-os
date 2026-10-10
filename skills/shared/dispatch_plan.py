#!/usr/bin/env python3
"""Deterministic work split for the literature review and tag stages.

  --mode ris     review stage: canonical direction{N}_{wos|cnki|openalex}.ris
                 -> _review_runs/dispatch_plan.json + one fill-in batch file per
                    <=30 records (+ the exact RIS chunk the worker reads)
  --mode report  tag stage: direction{N}_report.md
                 -> _tag_runs/dispatch_plan.json + one tag template per <=30 rows

The two plans live in different run directories and never overwrite each other.
Re-running is a resume: a batch file whose records still match is kept as is;
a batch whose records changed is moved to _archive/ and regenerated.

Identical copies: ~/.claude/skills/shared/ and ~/.codex/skills/_academic-shared/scripts/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lit_common as lc  # noqa: E402

ITEM_LIMIT = 30
REVIEW_DIR = "_review_runs"
TAG_DIR = "_tag_runs"
BATCH_PREFIX = "<!-- lit-batch: "
TAGS_PREFIX = "<!-- lit-tags: "
SOURCE_ORDER = {s: i for i, s in enumerate(lc.SOURCES)}  # wos, cnki, openalex
REVIEW_FIELDS = ("标题", "有摘要", "决定", "级别", "理由", "证据", "疑似竞品")


class PlanError(Exception):
    pass


# ---------------------------------------------------------------------------
# search plan / quota
# ---------------------------------------------------------------------------

def fallback_caps(quota: int) -> dict[str, int]:
    core = -(-quota * 25 // 100)
    important = -(-quota * 40 // 100)
    return {"core": core, "important": important, "backup": max(0, quota - core - important)}


def load_plan(lit_dir: Path, plan_file: Path | None = None) -> dict:
    """Directions, names, per-track quota/tier caps and total budget.

    _quota_result.json (lit-plan) is authoritative; without it the search plan's
    '## 方向N' headings and '| D1 | ... | 40篇 |' rows are used.
    """
    quota_path = lit_dir / "_quota_result.json"
    plan_path = plan_file or lit_dir / "literature_search_plan.md"
    out = {"directions": [], "names": {}, "tracks": {}, "budget": 0, "source": ""}
    if quota_path.exists():
        try:
            data = json.loads(quota_path.read_text(encoding="utf-8"))
            for e in data.get("directions", []):
                d = int(e["id"])
                out["directions"].append(d)
                out["names"][d] = str(e.get("name") or f"方向{d}")
                wq = int(e.get("wos_quota", e.get("quota", 0)) or 0)
                out["tracks"][(d, "wos")] = {"quota": wq, "tiers": e.get("wos_tiers") or fallback_caps(wq)}
                cq = int(e.get("cnki_quota", 0) or 0)
                if cq > 0:
                    out["tracks"][(d, "cnki")] = {"quota": cq, "tiers": e.get("cnki_tiers") or fallback_caps(cq)}
            out["budget"] = int(data.get("total_budget", 0) or 0)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise PlanError(f"QUOTA_JSON_INVALID: {quota_path}: {exc}") from exc
        out["source"] = quota_path.name
    elif plan_path.exists():
        text = plan_path.read_text(encoding="utf-8")
        for m in re.finditer(r"^#{2,4}\s*(?:方向|Direction)\s*D?(\d+)\s*[：:]?\s*(.*)$", text, re.M | re.I):
            d = int(m.group(1))
            if d not in out["directions"]:
                out["directions"].append(d)
                out["names"][d] = m.group(2).strip() or f"方向{d}"
        for m in re.finditer(r"^\|\s*D(\d+)\b[^\n]*?\|\s*(\d+)\s*篇\s*\|", text, re.M):
            d, q = int(m.group(1)), int(m.group(2))
            if d not in out["directions"]:
                out["directions"].append(d)
                out["names"].setdefault(d, f"方向{d}")
            out["tracks"][(d, "wos")] = {"quota": q, "tiers": fallback_caps(q)}
        out["source"] = plan_path.name
    else:
        raise PlanError(f"PLAN_MISSING: neither {quota_path.name} nor {plan_path.name} in {lit_dir}")
    out["directions"] = sorted(set(out["directions"]))
    if not out["directions"]:
        raise PlanError(f"PLAN_DIRECTIONS_UNPARSEABLE: {out['source']}")
    for (d, track), cfg in out["tracks"].items():
        caps = {t: int(cfg["tiers"].get(t, 0)) for t in lc.TIERS}
        if sum(caps.values()) != cfg["quota"]:
            raise PlanError(f"TIER_CAPS_MISMATCH: D{d}/{track} caps {caps} != quota {cfg['quota']}")
        cfg["tiers"] = caps
    return out


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def ris_field(block: str, tag: str) -> str:
    """All values of one RIS tag, continuation lines joined (verbatim records)."""
    values: list[str] = []
    active = False
    for line in block.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  -\s?(.*)$", line)
        if m:
            active = m.group(1) == tag
            if active:
                values.append(m.group(2).strip())
        elif active and line[:1] in (" ", "\t") and values:
            values[-1] += " " + line.strip()
        else:
            active = False
    return " ".join(v for v in values if v).strip()


def ris_values(block: str, tag: str) -> list[str]:
    out = []
    for line in block.splitlines():
        m = re.match(rf"^{tag}  -\s?(.*)$", line)
        if m and m.group(1).strip():
            out.append(m.group(1).strip())
    return out


def record_title(block: str) -> str:
    return ris_field(block, "TI") or ris_field(block, "T1")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_meta(text: str, prefix: str) -> dict | None:
    for line in text.splitlines():
        if line.startswith(prefix) and line.rstrip().endswith("-->"):
            try:
                return json.loads(line[len(prefix):line.rstrip().rfind("-->")].strip())
            except json.JSONDecodeError:
                return None
    return None


def meta_line(prefix: str, meta: dict) -> str:
    return f"{prefix}{json.dumps(meta, ensure_ascii=False, sort_keys=True)} -->"


def parse_review_batch(text: str) -> list[dict]:
    """Blocks '### <record_id>' with '- 字段: 值' lines (continuations appended)."""
    blocks: list[dict] = []
    cur: dict | None = None
    last = None
    for line in text.splitlines():
        h = re.match(r"^###\s+(D\d+-[a-z]+-\d+)\s*$", line.strip())
        if h:
            cur = {"record_id": h.group(1)}
            blocks.append(cur)
            last = None
            continue
        if cur is None:
            continue
        f = re.match(r"^\s*[-*]\s*(\S+?)\s*[:：]\s?(.*)$", line)
        if f and f.group(1) in REVIEW_FIELDS:
            last = f.group(1)
            cur[last] = f.group(2).strip()
        elif last and line.strip() and not line.lstrip().startswith("#"):
            cur[last] = (cur[last] + " " + line.strip()).strip()
    return blocks


def parse_tag_batch(text: str) -> tuple[dict[tuple[str, int], str], list[str]]:
    tags: dict[tuple[str, int], str] = {}
    errors: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(core|important|backup):(\d+)\s*(?:→|->)\s*(.*)$", line.strip())
        if not m:
            continue
        key = (m.group(1), int(m.group(2)))
        if key in tags:
            errors.append(f"DUPLICATE_ROW {key[0]}:{key[1]}")
        tags[key] = m.group(3).strip()
    return tags, errors


def harvest_tags(run_root: Path, d: int) -> dict[str, str]:
    """normalized title -> filled tags from existing tag batches of direction d."""
    out: dict[str, str] = {}
    for f in sorted(run_root.glob(f"d{d}_b*_tags.md")):
        text = f.read_text(encoding="utf-8")
        meta = read_meta(text, TAGS_PREFIX) or {}
        tags, _ = parse_tag_batch(text)
        for ref in meta.get("refs", []):
            value = tags.get((ref.get("tier"), ref.get("row")), "")
            if value:
                out[lc.norm_text(ref.get("title", ""))] = value
    return out


def keep_or_archive(path: Path, fresh_meta: dict, prefix: str, same_records, lit_dir: Path) -> bool:
    """True when an existing batch file still matches; stale files go to _archive/."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if read_meta(text, prefix) == fresh_meta and same_records(text):
        return True
    dest = lc.archive(path, lit_dir)
    print(f"NOTICE: stale batch file archived: {path.name} -> {dest}")
    return False


# ---------------------------------------------------------------------------
# ris mode (review)
# ---------------------------------------------------------------------------

def plan_ris(lit_dir: Path, plan_file: Path | None, only: list[int] | None, limit: int) -> dict:
    plan = load_plan(lit_dir, plan_file)
    skipped = lc.skipped_directions(lit_dir, ("review",))
    run_dirs = sorted(set(only)) if only else [d for d in plan["directions"] if d not in skipped]
    unknown = set(run_dirs) - set(plan["directions"])
    if unknown:
        raise PlanError(f"UNKNOWN_DIRECTIONS: {sorted(unknown)} not in {plan['source']}")
    inputs = lc.canonical_inputs(lit_dir)
    warnings: list[str] = [f"SKIPPED_BY_USER: D{d} (review SKIPPED in lit_status.md)" for d in sorted(skipped) if d not in run_dirs]
    warnings += [f"SKIPPED_DIRECTION_REQUESTED: D{d} is marked SKIPPED; rerunning it as a repair" for d in sorted(skipped) if d in run_dirs]
    for p in lc.nonconforming_ris(lit_dir):
        warnings.append(f"NONCONFORMING_RIS_IGNORED: {p.name} (expected direction{{N}}_{{wos|cnki|openalex}}.ris)")
    for (d, s), p in inputs.items():
        if d not in plan["directions"]:
            warnings.append(f"PLAN_EXTERNAL_INPUT_IGNORED: {p.name} (D{d} not in {plan['source']})")
    for enw in sorted(lit_dir.glob("*.enw")):
        d = lc.classify_enw(enw)
        if d is not None and (d, "cnki") not in inputs:
            warnings.append(f"CNKI_NOT_CONVERTED: {enw.name} has no direction{d}_cnki.ris (convert in lit-workflow input stage)")

    errors: list[str] = []
    for d in run_dirs:
        have = [s for (dd, s) in inputs if dd == d]
        required = [s for (dd, s), cfg in plan["tracks"].items() if dd == d and cfg["quota"] > 0]
        if not have:
            errors.append(f"MISSING_INPUT: D{d} has no direction{d}_*.ris")
        for s in required:
            if s not in have:
                errors.append(f"MISSING_INPUT: D{d} quota needs direction{d}_{s}.ris")
        for s in have:
            if s == "openalex" and (d, "wos") not in plan["tracks"]:
                errors.append(f"NO_QUOTA: D{d} openalex input but no WoS/international quota")
            if s == "cnki" and (d, "cnki") not in plan["tracks"]:
                errors.append(f"NO_QUOTA: D{d} cnki input but cnki_quota is 0/absent")

    run_root = lit_dir / REVIEW_DIR
    sources: list[dict] = []
    batches: list[dict] = []
    keys = sorted(((d, s) for (d, s) in inputs if d in run_dirs), key=lambda k: (k[0], SOURCE_ORDER[k[1]]))
    for d, s in keys:
        path = inputs[(d, s)]
        n, errs = lc.check_ris(path)
        if errs:
            errors.extend(f"RIS_INVALID: {e}" for e in errs)
            continue
        records = lc.split_ris_records(lc.read_text(path))
        if len(records) != n:
            errors.append(f"RIS_INVALID: {path.name}: parsed {len(records)} records, TY={n}")
            continue
        untitled = [i for i, r in enumerate(records, 1) if not record_title(r)]
        if untitled:
            errors.append(f"RIS_TITLE_MISSING: {path.name}: records {untitled[:20]}")
            continue
        sources.append({"direction": d, "source_type": s, "source_file": path.name, "record_count": n})
        for k, start in enumerate(range(1, n + 1, limit), 1):
            end = min(start + limit - 1, n)
            bid = f"d{d}_{s}_b{k}"
            batches.append({
                "batch_id": bid, "direction": d, "source_type": s, "source_file": path.name,
                "batch_file": f"{bid}.md", "chunk_file": f"chunks/{bid}.ris",
                "item_start": start, "item_end": end, "item_count": end - start + 1,
                "_records": records[start - 1:end],
            })
    if errors:
        raise PlanError("\n".join(errors))

    for b in batches:
        recs = b.pop("_records")
        chunk_text = "\n\n".join(r.rstrip() for r in recs) + "\n"
        atomic_write(run_root / b["chunk_file"], chunk_text)
        meta = {k: b[k] for k in ("batch_id", "direction", "source_type", "source_file", "chunk_file",
                                  "item_start", "item_end", "item_count")}
        expected = []
        lines = [meta_line(BATCH_PREFIX, meta),
                 f"# D{b['direction']} {b['source_type']} 第{b['batch_id'].rsplit('_b', 1)[1]}批"
                 f"（记录 {b['item_start']}–{b['item_end']}，共 {b['item_count']} 条；原文见 {b['chunk_file']}）",
                 "",
                 "填写说明：只填写每条记录 决定/级别/理由/证据/疑似竞品 冒号后的内容；不得改动 ### 行、标题、有摘要。",
                 "决定 = include 或 exclude；级别 = 核心/重要/备选（exclude 留空）；理由 = 中文，必填；",
                 "证据 = 摘要中的一个连续原文短语（无摘要写“仅凭标题”）；疑似竞品 = 仅当与本研究问题/对象/机制高度重叠时写一句中文，否则留空。",
                 ""]
        for off, rec in enumerate(recs):
            ordinal = b["item_start"] + off
            rid = f"D{b['direction']}-{b['source_type']}-{ordinal}"
            title = record_title(rec)
            expected.append((rid, lc.norm_text(title)))
            lines += [f"### {rid}", f"- 标题: {title}",
                      f"- 有摘要: {'是' if ris_field(rec, 'AB') else '否'}",
                      "- 决定: ", "- 级别: ", "- 理由: ", "- 证据: ", "- 疑似竞品: ", ""]

        def same(text: str, expected=expected) -> bool:
            got = [(blk["record_id"], lc.norm_text(blk.get("标题", ""))) for blk in parse_review_batch(text)]
            return got == expected

        path = run_root / b["batch_file"]
        if not keep_or_archive(path, meta, BATCH_PREFIX, same, lit_dir):
            atomic_write(path, "\n".join(lines) + "\n")

    return {
        "mode": "ris", "created": dt.date.today().isoformat(), "item_limit": limit,
        "plan_source": plan["source"], "plan_directions": plan["directions"],
        "directions": run_dirs, "names": {str(d): plan["names"].get(d, f"方向{d}") for d in run_dirs},
        "sources": sources, "batches": batches,
        "total_records": sum(s["record_count"] for s in sources), "total_batches": len(batches),
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# report mode (tag)
# ---------------------------------------------------------------------------

def plan_report(lit_dir: Path, only: list[int] | None, limit: int) -> dict:
    reports = lc.direction_reports(lit_dir)
    warnings = [f"NONCONFORMING_REPORT_IGNORED: {p.name} (expected direction{{N}}_report.md)"
                for p in sorted(lit_dir.glob("direction*_report.md")) if lc.classify_report(p) is None]
    if not reports:
        raise PlanError(f"NO_REVIEW_REPORTS: no direction{{N}}_report.md in {lit_dir} (run lit-review first)")
    skipped = lc.skipped_directions(lit_dir, ("review", "tag"))
    run_dirs = sorted(set(only)) if only else [d for d in sorted(reports) if d not in skipped]
    warnings += [f"SKIPPED_BY_USER: D{d} (review/tag SKIPPED in lit_status.md)" for d in sorted(skipped) if d in reports and d not in run_dirs]
    missing = [d for d in run_dirs if d not in reports]
    if missing:
        raise PlanError(f"REPORT_MISSING: {['D%d' % d for d in missing]}")
    run_root = lit_dir / TAG_DIR
    report_items, batches = [], []
    for d in run_dirs:
        rows = lc.parse_report_rows(lc.read_text(reports[d]))
        carry = harvest_tags(run_root, d)
        bad = [r for r in rows if r["ncols"] != 6]
        if bad:
            raise PlanError(f"REPORT_TABLE_SCHEMA: {reports[d].name} rows must have 6 columns (review output)")
        report_items.append({"direction": d, "report_file": reports[d].name, "row_count": len(rows)})
        for k, start in enumerate(range(0, len(rows), limit), 1):
            chunk = rows[start:start + limit]
            bid = f"d{d}_b{k}"
            refs = [{"tier": r["tier"], "row": r["row"], "title": r["title"]} for r in chunk]
            meta = {"batch_id": bid, "direction": d, "report_file": reports[d].name, "refs": refs}
            b = {"batch_id": bid, "direction": d, "report_file": reports[d].name,
                 "batch_file": f"{bid}_tags.md", "item_count": len(chunk), "refs": refs}
            lines = [meta_line(TAGS_PREFIX, meta),
                     f"# D{d} 标签第{k}批（共 {len(chunk)} 篇；来源 {reports[d].name}）", "",
                     "填写说明：只在每行 → 后填写标签，多个标签用 + 连接；不得改动 tier:row；“>” 行是该文献信息，仅供参考，可保留。", ""]
            for r in chunk:
                lines += [f"{r['tier']}:{r['row']} → {carry.get(lc.norm_text(r['title']), '')}".rstrip() + " ",
                          f"  > {r['author']} ({r['year']}) {r['title']} | {r['journal']} | 入选理由：{r['reason']}", ""]
            path = run_root / b["batch_file"]
            if not keep_or_archive(path, meta, TAGS_PREFIX, lambda text: True, lit_dir):
                atomic_write(path, "\n".join(lines) + "\n")
            batches.append(b)
    return {
        "mode": "report", "created": dt.date.today().isoformat(), "item_limit": limit,
        "directions": run_dirs, "reports": report_items, "batches": batches,
        "total_rows": sum(r["row_count"] for r in report_items), "total_batches": len(batches),
        "warnings": warnings,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", required=True, choices=["ris", "report"])
    ap.add_argument("--lit-dir", "--input-dir", dest="lit_dir", required=True,
                    help="structure/2_literature")
    ap.add_argument("--plan-file", help="default: <lit-dir>/literature_search_plan.md")
    ap.add_argument("--directions", help="comma list, e.g. 1,3 (default: all)")
    ap.add_argument("--limit", type=int, default=ITEM_LIMIT)
    args = ap.parse_args()
    if not 1 <= args.limit <= ITEM_LIMIT:
        ap.error(f"--limit must be 1..{ITEM_LIMIT}")
    lit_dir = Path(args.lit_dir)
    only = [int(x) for x in re.split(r"[,\s]+", args.directions.strip()) if x] if args.directions else None
    try:
        if args.mode == "ris":
            data = plan_ris(lit_dir, Path(args.plan_file) if args.plan_file else None, only, args.limit)
            out = lit_dir / REVIEW_DIR / "dispatch_plan.json"
        else:
            data = plan_report(lit_dir, only, args.limit)
            out = lit_dir / TAG_DIR / "dispatch_plan.json"
        atomic_write(out, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    except (PlanError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=== VERIFY: FAIL ===")
        raise SystemExit(1)
    for w in data["warnings"]:
        print(f"⚠️ {w}")
    print(f"=== DISPATCH PLAN ({args.mode}) ===")
    print(f"Directions: {', '.join('D%d' % d for d in data['directions'])}")
    print("| # | batch | 方向 | 来源 | 条目 |")
    print("|--:|:------|:----:|:-----|----:|")
    for i, b in enumerate(data["batches"], 1):
        src = b.get("source_type") or b.get("report_file")
        rng = f"{b['item_start']}-{b['item_end']}" if "item_start" in b else str(b["item_count"])
        print(f"| {i} | {b['batch_id']} | D{b['direction']} | {src} | {rng} |")
    print(f"Total batches: {data['total_batches']}")
    print("=== VERIFY: PASS ===")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
