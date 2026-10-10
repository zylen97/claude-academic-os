#!/usr/bin/env python3
"""Prepare the citation pool from tagged_reports/ (lit-pool step 1).

Blocking: tag_report.md missing; tagged_reports/ not mirroring the review
reports; invalid/missing labels; placeholder authors; bad or duplicate keys.
Unique papers follow the shared rule in lit_common (DOI / WoS UT / first author +
year + title[:80]); duplicates merge labels, reasons, directions; best tier wins.
Citation keys: auth.lower + year + first content word initial, conflicts get
b/c/... suffixes. Keys already present in literature_manifest.json are reused
for the same paper, so a refresh does not renumber keys already cited.

Output (all under _pool_runs/): pool_prepare.json and one prefilled template
pool_agent{N}_raw.md per worker (<= --agent-limit paper-label assignments).
Filled templates are kept on rerun when the assignment plan is unchanged;
otherwise the old run files are moved to _archive/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
from collections import defaultdict
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
from format_pool_agents import parse_blocks  # noqa: E402

try:
    from pypinyin import lazy_pinyin
    HAS_PINYIN = True
except ImportError:  # pragma: no cover
    HAS_PINYIN = False

POOL_DIR = "_pool_runs"
RANK = {t: i for i, t in enumerate(lc.TIERS)}
_COMPOUND_SURNAMES = {"欧阳", "司马", "上官", "诸葛", "司徒", "令狐", "宇文", "长孙",
                      "慕容", "皇甫", "东方", "端木", "公孙", "南宫", "独孤", "赫连"}
_CN_STOP = set("的了是在有和与及其对从以为被把将而也都能要不")
STOP_WORDS = {"a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or", "is", "are", "was",
              "were", "be", "been", "by", "with", "from", "as", "into", "through", "during", "before",
              "after", "between", "how", "what", "when", "where", "which", "who", "whom", "why", "do",
              "does", "did", "has", "have", "had", "can", "could", "will", "would", "shall", "should",
              "may", "might", "must", "not", "no", "nor", "but", "if", "then", "than", "so", "its", "it",
              "this", "that", "these", "those"}
PLACEHOLDER_AUTHORS = {"unknown", "unk", "n/a", "na", "tbd", "anon", "anonymous", ""}
CK_PATTERN = re.compile(r"^[a-z][a-z0-9]*\d{4}[a-z][a-z]?$")


# ---- citation keys (names kept for source_bib_to_pool.py) -------------------

def _has_cjk(s: str) -> bool:
    return lc._has_cjk(s)


def normalize_text(s: str) -> str:
    return lc.norm_text(s)


def dedup_key(author: str, year: int, title: str) -> str:
    """Author/year/title part of the shared identity (used by source_bib_to_pool)."""
    return f"{normalize_text(lc.surname(author))}|{year}|{normalize_text(title)[:80]}"


def chinese_surname_to_pinyin(name: str) -> str:
    if not name:
        return "unknown"
    if not HAS_PINYIN:
        return "cn" + format(ord(name[0]), "x")
    for cs in _COMPOUND_SURNAMES:
        if name.startswith(cs):
            return "".join(lazy_pinyin(cs)) or "cn" + format(ord(name[0]), "x")
    return "".join(lazy_pinyin(name[0])) or "cn" + format(ord(name[0]), "x")


def chinese_title_initial(title: str) -> str:
    for ch in title:
        if "一" <= ch <= "鿿" and ch not in _CN_STOP:
            if HAS_PINYIN:
                py = lazy_pinyin(ch)
                return py[0][0] if py and py[0] else "x"
            return "x"
    return "x"


def generate_citation_key(author: str, year: int, title: str) -> str:
    """auth.lower + year + shorttitle(1,1): smith2024w, tao2026j, ouyang2025s."""
    fa_raw = lc.surname(author)
    fa_raw = re.sub(r"\s+[A-Z]\.?$", "", fa_raw).strip()
    if _has_cjk(fa_raw):
        fa = chinese_surname_to_pinyin(fa_raw)
    else:
        fa = re.sub(r"[^a-z]", "", lc.norm_text(fa_raw).replace(" ", ""))
    fa = fa or "unknown"
    words = re.findall(r"[a-zA-Z]+", title.lower())
    initial = next((w[0] for w in words if w not in STOP_WORDS), words[0][0] if words else "")
    if not initial:
        initial = chinese_title_initial(title) if _has_cjk(title) else "x"
    return f"{fa}{year}{initial}"


def resolve_key_conflicts(keys: dict[str, str], taken: set[str] | None = None) -> dict[str, str]:
    """{identity: raw_key} -> unique keys; second and later get b, c, ... (stable order)."""
    taken = set(taken or ())
    groups: dict[str, list[str]] = defaultdict(list)
    for ident, ck in keys.items():
        groups[ck].append(ident)
    out: dict[str, str] = {}
    for ck, idents in groups.items():
        suffixes = iter([""] + [chr(c) for c in range(ord("b"), ord("z") + 1)])
        for ident in sorted(idents):
            cand = ck + next(suffixes)
            while cand in taken:
                cand = ck + next(suffixes)
            out[ident] = cand
            taken.add(cand)
    return out


# ---- corpus ---------------------------------------------------------------

def read_rq_count(tag_report: Path) -> int:
    m = re.search(r"\*\*RQ 数\*\*:\s*(\d+)", lc.read_text(tag_report))
    if not m:
        raise ValueError("TAG_REPORT_OUTDATED: tag_report.md has no 'RQ 数' line (rerun tag_aggregate.py)")
    return int(m.group(1))


def load_corpus(lit_dir: Path, source_pool: Path | None) -> tuple[list[dict], list[str], list[str]]:
    errors, warnings = [], []
    tag_report = lit_dir / "tag_report.md"
    if not tag_report.exists():
        return [], ["TAG_REPORT_MISSING: run lit-tag (tag_aggregate.py) first"], []
    errors += lc.compare_tagged_to_review(lit_dir)
    allowed = lc.allowed_labels(read_rq_count(tag_report))
    tagged = lc.active_tagged_reports(lit_dir)
    newest = max((p.stat().st_mtime for p in tagged.values()), default=0)
    if newest > tag_report.stat().st_mtime + 1:
        warnings.append("tag_report.md is older than tagged_reports/ (rerun tag_aggregate.py)")
    rows: list[dict] = []
    for d, path in sorted(tagged.items()):
        for r in lc.report_papers(path):
            labels = lc.split_labels(r.get("tags"))
            bad = [t for t in labels if t not in allowed]
            if r["ncols"] != 7 or not labels or bad:
                errors.append(f"TAG_INVALID: D{d} {r['tier']}:{r['row']} {r.get('tags')!r}")
                continue
            r["labels"] = labels
            r["is_source"] = False
            rows.append(r)
    if source_pool:
        data = json.loads(source_pool.read_text(encoding="utf-8"))
        for p in data.get("papers", []):
            labels = [t for t in p.get("tags", []) if t in allowed]
            rows.append({"direction": 0, "tier": p.get("tier", "important"), "row": 0,
                         "author": p["author"], "title": p["title"], "year": str(p["year"]),
                         "journal": p.get("journal", ""), "labels": labels or ["LR"],
                         "reason": f"源项目引用（{data.get('source_project', '')}）",
                         "doi": p.get("doi", ""), "database_id": "", "source_type": "source_project",
                         "source_file": "", "record_id": "", "is_source": True,
                         "source_cite_key": p.get("source_cite_key", "")})
    return rows, errors, warnings


def merge_papers(rows: list[dict], old_keys: dict[str, str]) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    papers: list[dict] = []
    for group in lc.group_duplicates(rows):
        best = rows[min(group, key=lambda i: (RANK.get(rows[i]["tier"], 1), i))]
        occ = [rows[i] for i in group]
        labels: list[str] = []
        for r in occ:
            labels += [t for t in r["labels"] if t not in labels]
        p = {
            "author": best["author"], "year": str(best["year"]), "title": best["title"],
            "journal": best["journal"], "tier": best["tier"], "tags": labels,
            "doi": next((r["doi"] for r in occ if r.get("doi")), ""),
            "database_id": next((r["database_id"] for r in occ if r.get("database_id")), ""),
            "reasons": list(dict.fromkeys(r["reason"] for r in occ if r.get("reason"))),
            "directions": sorted({r["direction"] for r in occ if r["direction"]}),
            "records": [{"direction": r["direction"], "tier": r["tier"], "row": r["row"], "title": r["title"],
                         "source_type": r["source_type"], "source_file": r["source_file"],
                         "record_id": r["record_id"], "doi": r.get("doi", "")}
                        for r in occ if not r["is_source"]],
            "is_source": any(r["is_source"] for r in occ),
            "source_cite_key": next((r.get("source_cite_key") for r in occ if r.get("source_cite_key")), ""),
            "identity": lc.identity_keys(best)[-1] if lc.identity_keys(best) else best["title"],
        }
        types = {r["source_type"] for r in occ}
        p["source_origin"] = ("source_project" if p["is_source"] else
                              "OpenAlex supplement" if types == {"openalex"} else "lit-workflow")
        if p["author"].strip().lower() in PLACEHOLDER_AUTHORS:
            errors.append(f"PLACEHOLDER_AUTHOR: {p['title'][:60]}")
        if not re.fullmatch(r"\d{4}", p["year"]):
            errors.append(f"YEAR_INVALID: {p['author']} {p['title'][:60]}")
        reuse = next((old_keys[k] for r in occ for k in lc.identity_keys(r) if k in old_keys), "")
        p["citation_key"] = reuse
        papers.append(p)
    use = defaultdict(int)
    for p in papers:
        use[p["citation_key"]] += 1
    for p in papers:  # two current papers matched the same old key: neither reuses it
        if p["citation_key"] and use[p["citation_key"]] > 1:
            p["citation_key"] = ""
    reused = {p["citation_key"] for p in papers if p["citation_key"]}
    raw = {p["identity"]: generate_citation_key(p["author"], p["year"], p["title"])
           for p in papers if not p["citation_key"]}
    resolved = resolve_key_conflicts(raw, taken=reused)
    for p in papers:
        if not p["citation_key"]:
            p["citation_key"] = resolved[p["identity"]]
    seen: dict[str, int] = defaultdict(int)
    for p in papers:
        seen[p["citation_key"]] += 1
        if not CK_PATTERN.match(p["citation_key"]) or p["citation_key"].startswith("unknown"):
            errors.append(f"KEY_FORMAT: {p['citation_key']!r} for {p['author']} ({p['year']})")
    errors += [f"KEY_DUPLICATE: {k}" for k, n in seen.items() if n > 1]
    return papers, errors


def plan_agents(papers: list[dict], limit: int) -> list[dict]:
    """Assignments = (label, key) pairs; large labels split, small labels bin-packed."""
    by_tag: dict[str, list[str]] = defaultdict(list)
    for p in papers:
        for t in p["tags"]:
            by_tag[t].append(p["citation_key"])
    agents: list[dict] = []
    small = []
    for tag, keys in sorted(by_tag.items()):
        if len(keys) > limit // 2:
            n = math.ceil(len(keys) / limit)
            per = math.ceil(len(keys) / n)
            for i in range(n):
                agents.append({"assignments": [[tag, k] for k in keys[i * per:(i + 1) * per]]})
        else:
            small.append((tag, keys))
    bins: list[dict] = []
    for tag, keys in sorted(small, key=lambda x: (-len(x[1]), x[0])):
        target = next((b for b in bins if len(b["assignments"]) + len(keys) <= limit), None)
        if target is None:
            target = {"assignments": []}
            bins.append(target)
        target["assignments"] += [[tag, k] for k in keys]
    agents += bins
    for i, a in enumerate(agents, 1):
        a["agent_id"] = i
        a["raw_file"] = f"pool_agent{i}_raw.md"
        a["formatted_file"] = f"pool_agent{i}.md"
        a["tags"] = sorted({t for t, _ in a["assignments"]})
    return agents


def template(agent: dict, by_key: dict[str, dict], carry: dict | None = None) -> str:
    lines = [f"<!-- lit-pool-agent: {agent['agent_id']} -->",
             f"# 引用池 worker {agent['agent_id']}（{len(agent['assignments'])} 条：{'、'.join(agent['tags'])}）", "",
             "填写说明：只填写每条的“引用场景”（中文，写作视角：这篇可以支撑什么论点）；",
             "COMP 条目在引用场景中加“；关键差异：…”。不得改动其他行，不得增删条目。", ""]
    for n, (tag, key) in enumerate(agent["assignments"], 1):
        p = by_key[key]
        lines += [f"### paper{n}", f"- 标签: {tag}", f"- citation_key: {key}",
                  f"- 分级: {lc.TIER_CN.get(p['tier'], p['tier'])}", f"- 作者: {p['author']}",
                  f"- 年份: {p['year']}", f"- 期刊: {p['journal']}", f"- 标题: {p['title']}",
                  f"- 入选理由: {'；'.join(p['reasons'])[:300]}",
                  f"- 引用场景: {(carry or {}).get((tag, key), '')}", ""]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--agent-limit", type=int, default=30)
    ap.add_argument("--source-pool", help="_source_pool.json from source_bib_to_pool.py (dissertations)")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    run = lit_dir / POOL_DIR
    try:
        rows, errors, warnings = load_corpus(lit_dir, Path(args.source_pool) if args.source_pool else None)
        old_keys: dict[str, str] = {}
        manifest = lit_dir / "literature_manifest.json"
        if manifest.exists():
            for p in json.loads(manifest.read_text(encoding="utf-8")).get("papers", []):
                for k in lc.identity_keys(p):
                    old_keys.setdefault(k, p["citation_key"])
        papers, key_errors = merge_papers(rows, old_keys) if not errors else ([], [])
        errors += key_errors
        if not papers and not errors:
            errors.append("NO_PAPERS: tagged_reports/ is empty")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors, warnings, papers = [str(exc)], [], []
    for w in warnings:
        print(f"⚠️ {w}")
    if errors:
        print("=== VERIFY: FAIL ===")
        for e in errors[:30]:
            print(f"  ❌ {e}")
        raise SystemExit(1)
    papers.sort(key=lambda p: (RANK.get(p["tier"], 1), p["citation_key"]))
    agents = plan_agents(papers, args.agent_limit)
    by_key = {p["citation_key"]: p for p in papers}
    data = {"created": dt.date.today().isoformat(), "total_occurrences": len(rows),
            "total_unique": len(papers), "papers": papers, "agents": agents}

    old_plan = run / "pool_prepare.json"
    carry: dict[tuple[str, str], str] = {}
    if old_plan.exists():
        old = json.loads(old_plan.read_text(encoding="utf-8"))
        if [a["assignments"] for a in old.get("agents", [])] != [a["assignments"] for a in agents]:
            for f in sorted(run.glob("pool_agent*_raw.md")):
                for blk in parse_blocks(f.read_text(encoding="utf-8")):
                    if blk.get("scene") and "{{" not in blk["scene"]:
                        carry[(blk.get("tag", ""), blk.get("key", ""))] = blk["scene"]
            for f in sorted(run.glob("pool_agent*.md")) + [old_plan]:
                lc.archive(f, lit_dir)
            print(f"NOTICE: assignment plan changed; previous _pool_runs files archived, {len(carry)} filled scenes carried over")
    for a in agents:
        path = run / a["raw_file"]
        if not path.exists():
            dp.atomic_write(path, template(a, by_key, carry))
    dp.atomic_write(run / "pool_prepare.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    print("=== POOL PREPARE ===")
    print(f"Occurrences: {len(rows)} -> unique papers: {len(papers)}")
    counts = defaultdict(int)
    for p in papers:
        for t in p["tags"]:
            counts[t] += 1
    for t in sorted(counts):
        print(f"  {t}: {counts[t]}")
    print("| agent | 标签 | 条目 |")
    for a in agents:
        print(f"| {a['agent_id']} | {'+'.join(a['tags'])} | {len(a['assignments'])} |")
    print("=== VERIFY: PASS ===")
    print(f"Output: {run / 'pool_prepare.json'}")


if __name__ == "__main__":
    main()
