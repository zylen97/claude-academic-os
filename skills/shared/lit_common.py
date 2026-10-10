#!/usr/bin/env python3
"""Shared helpers for the literature pipeline (Academic OS Lite §3.2).

Single source of truth for:
  * canonical RIS input naming   -> classify_ris()
  * RIS record splitting / sanity -> split_ris_records(), check_ris()
  * OpenAlex credentials          -> openalex_credentials(), openalex_params()

Identical copies live in:
  ~/.claude/skills/shared/lit_common.py
  ~/.codex/skills/_academic-shared/scripts/lit_common.py
"""
from __future__ import annotations

import os
import re
from pathlib import Path

RIS_NAME_RE = re.compile(r"^direction(\d+)_(wos|cnki|openalex)\.ris$")
ENW_NAME_RE = re.compile(r"^direction(\d+)_cnki\.enw$")
SOURCES = ("wos", "cnki", "openalex")
RUN_DIRS = ("_screen_runs", "_review_runs", "_tag_runs", "_pool_runs")
OPENALEX_ENV_FILE = Path.home() / "Library/CloudStorage/Dropbox/Apps/secrets-vault/openalex.env"

_TY_RE = re.compile(r"^TY  - ")
_ER_RE = re.compile(r"^ER  -")


def classify_ris(path: str | os.PathLike) -> tuple[int, str] | None:
    """Return (direction, source) for a canonical corpus RIS, else None."""
    m = RIS_NAME_RE.match(Path(path).name)
    return (int(m.group(1)), m.group(2)) if m else None


def classify_enw(path: str | os.PathLike) -> int | None:
    """Return direction for a raw CNKI EndNote export, else None."""
    m = ENW_NAME_RE.match(Path(path).name)
    return int(m.group(1)) if m else None


def canonical_inputs(lit_dir: str | os.PathLike) -> dict[tuple[int, str], Path]:
    """Map (direction, source) -> canonical RIS directly under lit_dir."""
    out: dict[tuple[int, str], Path] = {}
    for p in sorted(Path(lit_dir).glob("*.ris")):
        key = classify_ris(p)
        if key:
            out[key] = p
    return out


def nonconforming_ris(lit_dir: str | os.PathLike) -> list[Path]:
    """Top-level *.ris files that do not follow the canonical name (warn only)."""
    return [p for p in sorted(Path(lit_dir).glob("*.ris")) if classify_ris(p) is None]


def read_text(path: str | os.PathLike) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def split_ris_records(text: str) -> list[str]:
    """Split RIS text into records (TY..ER), keeping continuation lines verbatim."""
    records: list[str] = []
    buf: list[str] | None = None
    for line in text.splitlines():
        if _TY_RE.match(line):
            buf = [line]
        elif buf is not None:
            buf.append(line)
            if _ER_RE.match(line):
                records.append("\n".join(buf))
                buf = None
    return records


def check_ris(path: str | os.PathLike) -> tuple[int, list[str]]:
    """Return (record_count, errors). Blocking errors: unreadable, TY != ER, zero records."""
    try:
        text = read_text(path)
    except UnicodeDecodeError:
        return 0, [f"{Path(path).name}: not UTF-8"]
    ty = sum(1 for l in text.splitlines() if _TY_RE.match(l))
    er = sum(1 for l in text.splitlines() if _ER_RE.match(l))
    errors = []
    if ty == 0:
        errors.append(f"{Path(path).name}: no records")
    if ty != er:
        errors.append(f"{Path(path).name}: TY count {ty} != ER count {er}")
    return ty, errors


def openalex_credentials() -> tuple[str, str]:
    """Return (api_key, mailto) from environment, falling back to the vault env file."""
    key = os.environ.get("OPENALEX_API_KEY", "")
    mail = os.environ.get("OPENALEX_MAILTO", "")
    if (not key or not mail) and OPENALEX_ENV_FILE.exists():
        for line in OPENALEX_ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip().removeprefix("export ").strip()
            if "=" not in line or line.startswith("#"):
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k.strip() == "OPENALEX_API_KEY" and not key:
                key = v
            elif k.strip() == "OPENALEX_MAILTO" and not mail:
                mail = v
    if not key or not mail:
        raise RuntimeError("OpenAlex requires both OPENALEX_API_KEY and OPENALEX_MAILTO "
                           f"(env vars or {OPENALEX_ENV_FILE})")
    return key, mail


def openalex_params(**params) -> dict:
    """Add api_key and mailto to an OpenAlex query-parameter dict."""
    key, mail = openalex_credentials()
    params.update(api_key=key, mailto=mail)
    return params


# ---------------------------------------------------------------------------
# Unique-paper rule (one rule for review, tag and pool)
# Two records are the same paper when they share a DOI, a WoS UT, or
# first-author surname + year + normalized title[:80].
# ---------------------------------------------------------------------------
import datetime as _dt
import json as _json
import shutil as _shutil
import unicodedata as _ud

REPORT_NAME_RE = re.compile(r"^direction(\d+)_report\.md$")
TIERS = ("core", "important", "backup")
TIER_HEADINGS = {"core": "核心文献（Core）", "important": "重要文献（Important）", "backup": "备选文献（Backup）"}
TIER_CN = {"core": "核心", "important": "重要", "backup": "备选"}
RECORDS_PREFIX = "<!-- lit-records: "


def norm_text(value: object) -> str:
    """Lowercase, NFKD, punctuation -> space, collapse whitespace (CJK kept)."""
    s = _ud.normalize("NFKD", str(value or "").lower().strip())
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normalize_doi(value: object) -> str:
    v = str(value or "").strip().lower()
    v = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi\s*:\s*)", "", v)
    return v.rstrip(".,; )]")


def _has_cjk(s: str) -> bool:
    return any("一" <= c <= "鿿" for c in s)


def surname(author: object) -> str:
    """First author's surname from an RIS AU value or a report cell."""
    a = str(author or "").split(";")[0].strip()
    if "," in a:
        return a.split(",")[0].strip()
    if _has_cjk(a) or " " not in a:
        return a
    return a.split()[-1].strip()


def identity_keys(paper: dict) -> list[str]:
    keys: list[str] = []
    doi = normalize_doi(paper.get("doi"))
    if doi:
        keys.append("doi:" + doi)
    ut = str(paper.get("database_id") or "").strip().lower()
    if len(ut) >= 8:
        keys.append("ut:" + ut)
    title = norm_text(paper.get("title"))[:80]
    if title:
        author = norm_text(surname(paper.get("author") or paper.get("first_author")))
        keys.append(f"ayt:{author}|{paper.get('year', '')}|{title}")
    return keys


def group_duplicates(papers: list[dict]) -> list[list[int]]:
    """Union-find over identity_keys; groups of indices ordered by first index."""
    parent = list(range(len(papers)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owner: dict[str, int] = {}
    for i, paper in enumerate(papers):
        for key in identity_keys(paper):
            if key in owner:
                a, b = find(owner[key]), find(i)
                if a != b:
                    parent[max(a, b)] = min(a, b)
            else:
                owner[key] = i
    groups: dict[int, list[int]] = {}
    for i in range(len(papers)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: g[0])


# ---------------------------------------------------------------------------
# Direction-report tables (review writes 6 columns; tagged copies add 功能标签)
# ---------------------------------------------------------------------------

def classify_report(path: str | os.PathLike) -> int | None:
    m = REPORT_NAME_RE.match(Path(path).name)
    return int(m.group(1)) if m else None


def direction_reports(folder: str | os.PathLike) -> dict[int, Path]:
    out: dict[int, Path] = {}
    for p in sorted(Path(folder).glob("direction*_report.md")):
        d = classify_report(p)
        if d is not None:
            out[d] = p
    return out


def split_row(line: str) -> list[str]:
    safe = line.strip().replace("\\|", "\x00")
    if safe.startswith("|"):
        safe = safe[1:]
    if safe.endswith("|"):
        safe = safe[:-1]
    return [c.strip().replace("\x00", "\\|") for c in safe.split("|")]


def cell(value: object) -> str:
    return str(value if value is not None else "").replace("|", "/").replace("\n", " ").strip()


def parse_report_rows(text: str) -> list[dict]:
    """Rows of the three tier tables. Any other '##' heading ends a tier table."""
    rows: list[dict] = []
    tier = None
    for line in text.splitlines():
        if line.startswith("##"):
            tier = next((t for t, h in TIER_HEADINGS.items() if h[:4] in line), None)
            continue
        if tier and re.match(r"^\|\s*\d+\s*\|", line):
            cells = split_row(line)
            row = {"tier": tier, "row": int(cells[0]), "ncols": len(cells)}
            if len(cells) == 6:
                row.update(author=cells[1], title=cells[2], year=cells[3], journal=cells[4], tags=None, reason=cells[5])
            elif len(cells) == 7:
                row.update(author=cells[1], title=cells[2], year=cells[3], journal=cells[4], tags=cells[5], reason=cells[6])
            rows.append(row)
    return rows


def parse_report_records(text: str) -> dict[tuple[str, int], dict]:
    """(tier,row) -> provenance record from the trailing lit-records comment."""
    for line in text.splitlines():
        if line.startswith(RECORDS_PREFIX) and line.rstrip().endswith("-->"):
            data = _json.loads(line[len(RECORDS_PREFIX):line.rstrip().rfind("-->")].strip())
            return {(r["tier"], int(r["row"])): r for r in data}
    return {}


def report_papers(path: str | os.PathLike) -> list[dict]:
    """Rows + provenance of one direction report (review or tagged copy)."""
    text = read_text(path)
    records = parse_report_records(text)
    d = classify_report(path)
    out = []
    for row in parse_report_rows(text):
        rec = records.get((row["tier"], row["row"]), {})
        out.append({**row, "direction": d, "doi": rec.get("doi", ""),
                    "database_id": rec.get("database_id", ""),
                    "source_type": rec.get("source_type", ""),
                    "source_file": rec.get("source_file", ""),
                    "record_id": rec.get("record_id", "")})
    return out


def row_signature(rows: list[dict]) -> list[tuple]:
    """Record-level identity of a report: (tier, row, normalized title)."""
    return [(r["tier"], r["row"], norm_text(r.get("title"))) for r in rows]


def compare_tagged_to_review(lit_dir: str | os.PathLike) -> list[str]:
    """Blocking errors when tagged_reports/ does not mirror the review reports."""
    lit = Path(lit_dir)
    skip = skipped_directions(lit, ("review", "tag"))
    review = {d: p for d, p in direction_reports(lit).items() if d not in skip}
    tagged = {d: p for d, p in direction_reports(lit / "tagged_reports").items() if d not in skip}
    errors: list[str] = []
    for d in sorted(set(review) - set(tagged)):
        errors.append(f"TAGGED_COPY_MISSING: D{d} (run lit-tag for this direction)")
    for d in sorted(set(tagged) - set(review)):
        errors.append(f"TAGGED_COPY_WITHOUT_REVIEW: D{d}")
    for d in sorted(set(review) & set(tagged)):
        r = parse_report_rows(read_text(review[d]))
        t = parse_report_rows(read_text(tagged[d]))
        if row_signature(r) != row_signature(t):
            errors.append(f"TAGGED_COPY_STALE: D{d} rows differ from {review[d].name} (re-run lit-tag for D{d})")
    return errors


# ---------------------------------------------------------------------------
# Archive instead of overwrite/delete (spec §5)
# ---------------------------------------------------------------------------

def archive(path: str | os.PathLike, root: str | os.PathLike) -> Path:
    """Move path to root/_archive/YYYY-MM-DD/<relative path>; never overwrites."""
    src, base = Path(path), Path(root)
    rel = src.resolve().relative_to(base.resolve())
    dest = base / "_archive" / _dt.date.today().isoformat() / rel
    n = 1
    while dest.exists():
        dest = dest.with_name(f"{rel.name}.{n}")
        n += 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    _shutil.move(str(src), str(dest))
    return dest


def _self_check_identity() -> None:
    a = {"author": "Smith, Jane", "year": 2024, "title": "Alpha first paper", "doi": "10.1/X"}
    b = {"author": "Smith", "year": 2024, "title": "Alpha: first paper!", "doi": ""}
    c = {"author": "Jane Smith", "year": 2024, "title": "Variant title", "doi": "https://doi.org/10.1/x"}
    d = {"author": "张三", "year": 2022, "title": "纵向信息共享平台研究"}
    assert surname("Jane Smith") == "Smith" and surname("张三") == "张三"
    assert group_duplicates([a, b, c, d]) == [[0, 1, 2], [3]]
    rows = parse_report_rows("## 核心文献（Core）\n\n| # | a | b | c | d | e |\n|:--|\n| 1 | S | T \\| x | 2024 | J | R |\n\n## 竞品判断边界\n| 2 | x | x | 2024 | x | x |\n")
    assert len(rows) == 1 and rows[0]["title"] == "T \\| x", rows


# ---------------------------------------------------------------------------
# Functional labels (lit-tag taxonomy)
# ---------------------------------------------------------------------------
STATIC_LABELS = ("BG", "LR", "COMP", "METHOD-基础", "METHOD-先例")
POOL_FILES = ("BG", "LR", "GAP", "METHOD", "DISC", "COMP")


def allowed_labels(rq_count: int) -> set[str]:
    if int(rq_count) < 1:
        raise ValueError("RQ count must be >= 1 (count the RQs in idea.md)")
    return set(STATIC_LABELS) | {f"{p}-RQ{n}" for p in ("GAP", "DISC") for n in range(1, int(rq_count) + 1)}


def split_labels(raw: object) -> list[str]:
    """'LR+GAP-RQ1' -> ['LR', 'GAP-RQ1']; 'BG(2024-2026)' -> 'BG'; order kept, no duplicates."""
    out: list[str] = []
    for t in str(raw or "").replace("`", "").replace("＋", "+").split("+"):
        t = t.strip()
        if re.match(r"^BG\s*[（(]", t):
            t = "BG"
        if t and t not in out:
            out.append(t)
    return out


def label_group(label: str) -> str:
    """Pool file (without .md) a label belongs to."""
    for g in ("GAP", "DISC", "METHOD"):
        if label.startswith(g):
            return g
    return label


# ---------------------------------------------------------------------------
# User-confirmed skips (lit_status.md, parsed by lit-workflow's lit_status.py)
# ---------------------------------------------------------------------------

def _lit_status_module():
    import importlib.util
    import sys as _sys
    if "lit_status" in _sys.modules:
        return _sys.modules["lit_status"]
    here = Path(__file__).resolve()
    for base in here.parents:
        for cand in (base / "lit-workflow" / "lit_status.py", base / "lit-workflow" / "scripts" / "lit_status.py"):
            if cand.is_file():
                spec = importlib.util.spec_from_file_location("lit_status", cand)
                mod = importlib.util.module_from_spec(spec)
                _sys.modules["lit_status"] = mod
                try:
                    spec.loader.exec_module(mod)
                except Exception:
                    _sys.modules.pop("lit_status", None)
                    raise
                return mod
    return None


def skipped_directions(lit_dir: str | os.PathLike, stages: tuple[str, ...] = ("review",)) -> set[int]:
    """Directions whose latest mark for any of `stages` is SKIPPED (no later CLEARED)."""
    mod = _lit_status_module()
    if mod is None:
        return set()
    _screen, marks = mod.read_logs(Path(lit_dir))
    latest = mod.latest_marks(marks)
    return {d for (d, stage), m in latest.items() if stage in stages and m.get("state") == "SKIPPED"}


def active_tagged_reports(lit_dir: str | os.PathLike) -> dict[int, Path]:
    """tagged_reports/ minus directions skipped at review or tag."""
    skip = skipped_directions(lit_dir, ("review", "tag"))
    return {d: p for d, p in direction_reports(Path(lit_dir) / "tagged_reports").items() if d not in skip}


if __name__ == "__main__":  # self-check
    assert classify_ris("direction3_wos.ris") == (3, "wos")
    assert classify_ris("direction12_openalex.ris") == (12, "openalex")
    for bad in ("3-topic.ris", "direction1-topic.ris", "direction1_wos_v2.ris", "direction1_zone2.ris"):
        assert classify_ris(bad) is None, bad
    assert classify_enw("direction2_cnki.enw") == 2
    sample = "TY  - JOUR\nTI  - A title\n  continued\nER  - \n\nTY  - JOUR\nER  - \n"
    assert len(split_ris_records(sample)) == 2
    _self_check_identity()
    assert split_labels("LR+BG(2024-2026)＋LR") == ["LR", "BG"] and label_group("METHOD-先例") == "METHOD"
    assert "DISC-RQ2" in allowed_labels(2) and "DISC-RQ3" not in allowed_labels(2)
    print("lit_common self-check: PASS")
