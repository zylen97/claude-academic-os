#!/usr/bin/env python3
"""Write citation_pool/master.bib for every paper in _pool_runs/pool_prepare.json.

Matching order for a corpus paper (records come from the review provenance):
  1. its own source record (direction{N}_{src}.ris, ordinal from record_id),
  2. any canonical RIS record with the same DOI,
  3. same year + compatible first author,
and in every case the title must pass a high-similarity check (>= 0.90 or a
strong prefix) -- a lone author/year candidate is never accepted blindly.
Source-project papers (dissertations) are copied from --extra-bib.
Blocking: any paper without a verified record (no TODO stubs are ever written).
A changed existing master.bib is moved to _archive/ before being replaced.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
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

BIB_TYPES = {"JOUR": "article", "ABST": "article", "CONF": "inproceedings", "CPAPER": "inproceedings",
             "BOOK": "book", "EDITED": "book", "CHAP": "incollection", "CHAPT": "incollection",
             "THES": "phdthesis", "DISS": "phdthesis", "RPRT": "techreport"}


def load_records(lit_dir: Path) -> dict[str, list[dict]]:
    """source_file -> parsed records of every canonical input RIS."""
    out: dict[str, list[dict]] = {}
    for (_d, _s), path in sorted(lc.canonical_inputs(lit_dir).items()):
        recs = []
        for block in lc.split_ris_records(lc.read_text(path)):
            authors = dp.ris_values(block, "AU") or dp.ris_values(block, "A1")
            recs.append({
                "block": block, "TY": dp.ris_field(block, "TY").split()[0] if dp.ris_field(block, "TY") else "JOUR",
                "authors": authors, "title": dp.record_title(block),
                "year": (dp.ris_field(block, "PY") or dp.ris_field(block, "Y1") or dp.ris_field(block, "DA"))[:4],
                "journal": dp.ris_field(block, "T2") or dp.ris_field(block, "JF") or dp.ris_field(block, "JO") or dp.ris_field(block, "T3"),
                "VL": dp.ris_field(block, "VL"), "IS": dp.ris_field(block, "IS"),
                "SP": dp.ris_field(block, "SP"), "EP": dp.ris_field(block, "EP"),
                "doi": lc.normalize_doi(dp.ris_field(block, "DO")),
                "zh": any("LA:zh" in v for v in dp.ris_values(block, "N1")),
            })
        out[path.name] = recs
    return out


def title_ok(a: str, b: str) -> float:
    x, y = lc.norm_text(a), lc.norm_text(b)
    if not x or not y:
        return 0.0
    short, long_ = sorted((x, y), key=len)
    if long_.startswith(short) and (short == long_ or len(short) >= 40):
        return 1.0
    return SequenceMatcher(None, x, y).ratio()


def author_ok(paper_author: str, rec: dict) -> bool:
    if not rec["authors"]:
        return False
    a, b = lc.norm_text(lc.surname(paper_author)), lc.norm_text(lc.surname(rec["authors"][0]))
    return bool(a and b and (a in b or b in a))


def find_record(paper: dict, records: dict[str, list[dict]]) -> dict | None:
    cands: list[dict] = []
    for r in paper.get("records", []):
        m = re.match(r"^D\d+-[a-z]+-(\d+)$", r.get("record_id", ""))
        recs = records.get(r.get("source_file", ""), [])
        if m and 0 < int(m.group(1)) <= len(recs):
            cands.append(recs[int(m.group(1)) - 1])
    doi = lc.normalize_doi(paper.get("doi"))
    every = [x for recs in records.values() for x in recs]
    if doi:
        cands += [x for x in every if x["doi"] == doi]
    cands += [x for x in every if x["year"] == str(paper["year"]) and author_ok(paper["author"], x)]
    best, score = None, 0.0
    for c in cands:
        s = title_ok(paper["title"], c["title"])
        if s >= 0.90 and s > score:
            best, score = c, s
    return best


def esc(s: str) -> str:
    for a, b in (("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_")):
        s = s.replace(a, b)
    return s


def to_bibtex(key: str, rec: dict) -> str:
    kind = BIB_TYPES.get(rec["TY"], "article")
    lines = [f"@{kind}{{{key},", f"  author = {{{esc(' and '.join(rec['authors']))}}},",
             f"  title = {{{{{esc(rec['title'])}}}}},"]
    if rec["journal"]:
        lines.append(f"  {'journal' if kind == 'article' else 'booktitle'} = {{{esc(rec['journal'])}}},")
    lines.append(f"  year = {{{rec['year']}}},")
    for field, tag in (("volume", "VL"), ("number", "IS")):
        if rec[tag]:
            lines.append(f"  {field} = {{{esc(rec[tag])}}},")
    if rec["SP"]:
        lines.append(f"  pages = {{{rec['SP']}--{rec['EP']}}}," if rec["EP"] else f"  pages = {{{rec['SP']}}},")
    if rec["doi"]:
        lines.append(f"  doi = {{{rec['doi']}}},")
    if rec["zh"]:
        lines.append("  language = {chinese},")
    lines.append("}")
    return "\n".join(lines)


def parse_bib_entries(text: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"@\w+\s*\{\s*([^,\s]+)\s*,", text):
        depth, end = 0, m.start()
        for i in range(m.start(), len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        out[m.group(1)] = text[m.start():end]
    return out


def bib_keys(text: str) -> list[str]:
    return re.findall(r"^@\w+\s*\{\s*([^,\s]+)\s*,", text, re.M)


def check_bib(text: str, expected: list[str]) -> list[str]:
    errors = []
    keys = bib_keys(text)
    if sorted(keys) != sorted(expected):
        errors.append(f"BIB_KEYS: missing={sorted(set(expected) - set(keys))[:8]} extra={sorted(set(keys) - set(expected))[:8]}")
    depth = 0
    for ch in text:
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth < 0:
            break
    if depth != 0:
        errors.append("BIB_BRACES: unbalanced braces")
    for key, body in parse_bib_entries(text).items():
        for field in ("author", "title", "year"):
            if not re.search(rf"\b{field}\s*=", body):
                errors.append(f"BIB_FIELD: {key} lacks {field}")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lit-dir", required=True, help="structure/2_literature")
    ap.add_argument("--extra-bib", help="source-project .bib (dissertations)")
    args = ap.parse_args()
    lit_dir = Path(args.lit_dir)
    errors: list[str] = []
    try:
        prep = load_prepare(lit_dir)
        records = load_records(lit_dir)
        extra = parse_bib_entries(Path(args.extra_bib).read_text(encoding="utf-8")) if args.extra_bib else {}
        blocks = []
        for p in prep["papers"]:
            key = p["citation_key"]
            if p.get("source_cite_key") and p.get("is_source") and not p.get("records"):
                raw = extra.get(p["source_cite_key"])
                if raw is None:
                    errors.append(f"UNMATCHED: {key} source key {p['source_cite_key']} not in --extra-bib")
                    continue
                blocks.append(re.sub(r"(@\w+\s*\{)\s*" + re.escape(p["source_cite_key"]), lambda m: m.group(1) + key, raw, count=1))
                continue
            rec = find_record(p, records)
            if rec is None:
                errors.append(f"UNMATCHED: {key} — {p['author']} ({p['year']}) {p['title'][:70]}")
                continue
            if not rec["authors"] or not re.fullmatch(r"\d{4}", rec["year"]):
                errors.append(f"RIS_INCOMPLETE: {key} matched record lacks author/year")
                continue
            blocks.append(to_bibtex(key, rec))
        text = "\n\n".join(blocks) + "\n"
        if not errors:
            errors += check_bib(text, [p["citation_key"] for p in prep["papers"]])
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    print("=== RIS2BIB ===")
    if errors:
        print("=== VERIFY: FAIL ===")
        for e in errors[:30]:
            print(f"  ❌ {e}")
        print("master.bib not written (no TODO stubs). Fix the RIS record or the corpus entry, then rerun.")
        raise SystemExit(1)
    target = lit_dir / "citation_pool" / "master.bib"
    if target.exists() and lc.read_text(target) != text:
        print(f"NOTICE: archived old master.bib -> {lc.archive(target, lit_dir)}")
    dp.atomic_write(target, text)
    print(f"Entries: {len(prep['papers'])}")
    print("=== VERIFY: PASS ===")
    print(f"Output: {target}")


if __name__ == "__main__":
    main()
