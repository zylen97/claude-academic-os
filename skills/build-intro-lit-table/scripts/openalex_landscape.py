#!/usr/bin/env python3
"""Collect auditable OpenAlex candidate pools for Introduction literature tables.

The script performs discovery only. It does not classify papers as included, select
representative studies, or prove a research gap.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _shared() -> None:
    for base in Path(__file__).resolve().parents:
        for cand in (base / "shared", base / "_academic-shared" / "scripts"):
            if (cand / "lit_common.py").is_file():
                sys.path.insert(0, str(cand))
                return
    raise SystemExit("ERROR: lit_common.py not found (shared scripts directory)")


_shared()
import lit_common  # noqa: E402  (OpenAlex credentials: api_key + mailto, never printed)


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
SELECT_FIELDS = (
    "id,doi,display_name,publication_year,type,language,cited_by_count,"
    "primary_location,authorships"
)


@dataclass(frozen=True)
class SearchSpec:
    kind: str
    label: str
    query: str


def parse_labeled_query(raw: str) -> tuple[str, str]:
    if "::" not in raw:
        raise argparse.ArgumentTypeError(
            "Expected LABEL::QUERY, for example 'Market design::electricity market design'"
        )
    label, query = (part.strip() for part in raw.split("::", 1))
    if not label or not query:
        raise argparse.ArgumentTypeError("Both LABEL and QUERY must be non-empty")
    return label, query


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Query OpenAlex for broad category pools and nearest-counterexample pools. "
            "Outputs JSON and Markdown with redacted query logs."
        )
    )
    parser.add_argument("--topic", required=True, help="Broad focal topic added to every query")
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        metavar="LABEL::QUERY",
        help="Category query; repeat the same label for synonyms",
    )
    parser.add_argument(
        "--counterexample",
        action="append",
        default=[],
        metavar="LABEL::QUERY",
        help="Nearest-counterexample query; may be repeated",
    )
    parser.add_argument("--from-year", type=int, default=2000)
    parser.add_argument("--to-year", type=int, default=date.today().year)
    parser.add_argument(
        "--types",
        default="article,review",
        help="Comma-separated OpenAlex work types (default: article,review)",
    )
    parser.add_argument("--per-query", type=int, default=100, choices=range(1, 201))
    parser.add_argument("--max-per-group", type=int, default=50)
    parser.add_argument("--min-citations", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print redacted planned requests without networking",
    )
    args = parser.parse_args()

    if not args.category:
        parser.error("At least one --category LABEL::QUERY is required")
    if args.from_year > args.to_year:
        parser.error("--from-year cannot be later than --to-year")
    if args.max_per_group < 1:
        parser.error("--max-per-group must be positive")
    if args.min_citations < 0:
        parser.error("--min-citations cannot be negative")
    return args


def build_search_specs(args: argparse.Namespace) -> list[SearchSpec]:
    specs: list[SearchSpec] = []
    for kind, entries in (
        ("category", args.category),
        ("counterexample", args.counterexample),
    ):
        for raw in entries:
            label, query = parse_labeled_query(raw)
            specs.append(SearchSpec(kind=kind, label=label, query=query))
    return specs


def build_params(args: argparse.Namespace, spec: SearchSpec, creds: tuple[str, str]) -> dict[str, str]:
    work_types = [item.strip() for item in args.types.split(",") if item.strip()]
    filters = [
        f"from_publication_date:{args.from_year}-01-01",
        f"to_publication_date:{args.to_year}-12-31",
        f"cited_by_count:>{max(args.min_citations - 1, -1)}",
    ]
    if work_types:
        filters.append("type:" + "|".join(work_types))
    params = {
        "search": f"{args.topic} {spec.query}".strip(),
        "filter": ",".join(filters),
        "per-page": str(args.per_query),
        "sort": "cited_by_count:desc",
        "select": SELECT_FIELDS,
    }
    params["api_key"], params["mailto"] = creds
    return params


def redacted_url(params: dict[str, str]) -> str:
    safe = dict(params)
    for secret in ("api_key", "mailto"):
        if secret in safe:
            safe[secret] = "REDACTED"
    return OPENALEX_WORKS_URL + "?" + urlencode(safe)


def fetch_json(params: dict[str, str], timeout: int, attempts: int = 3) -> dict[str, Any]:
    url = OPENALEX_WORKS_URL + "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "build-intro-lit-table/1.0"})
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts:
                raise RuntimeError(f"OpenAlex HTTP error {exc.code}") from exc
        except URLError as exc:
            if attempt == attempts:
                raise RuntimeError(f"OpenAlex network error: {exc.reason}") from exc
        time.sleep(2 ** (attempt - 1))
    raise RuntimeError("OpenAlex request failed")


def author_names(work: dict[str, Any], limit: int = 6) -> list[str]:
    names: list[str] = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(name)
    if len(names) > limit:
        return names[:limit] + ["et al."]
    return names


def source_name(work: dict[str, Any]) -> str:
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    return source.get("display_name") or "Unknown source"


def normalized_work(work: dict[str, Any], matched_query: str) -> dict[str, Any]:
    doi = work.get("doi")
    return {
        "openalex_id": work.get("id"),
        "doi": doi,
        "title": work.get("display_name") or "Untitled",
        "year": work.get("publication_year"),
        "type": work.get("type"),
        "language": work.get("language"),
        "cited_by_count": work.get("cited_by_count") or 0,
        "source": source_name(work),
        "authors": author_names(work),
        "matched_queries": [matched_query],
        "verification_status": "discovery_only",
    }


def identity(work: dict[str, Any]) -> str:
    doi = (work.get("doi") or "").lower().strip()
    if doi:
        return "doi:" + doi
    openalex_id = (work.get("openalex_id") or "").lower().strip()
    if openalex_id:
        return "openalex:" + openalex_id
    return "title:" + (work.get("title") or "").lower().strip()


def merge_work(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    target["matched_queries"] = sorted(
        set(target.get("matched_queries", [])) | set(incoming.get("matched_queries", []))
    )
    if incoming.get("cited_by_count", 0) > target.get("cited_by_count", 0):
        target["cited_by_count"] = incoming["cited_by_count"]


def summarize_sources(works: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    counts = Counter(work.get("source") or "Unknown source" for work in works)
    return [{"source": source, "count": count} for source, count in counts.most_common(limit)]


def markdown_escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def short_authors(authors: list[str]) -> str:
    if not authors:
        return "Unknown"
    if authors[-1] == "et al.":
        return f"{authors[0]} et al."
    if len(authors) == 1:
        return authors[0]
    return f"{authors[0]} et al."


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenAlex Introduction-table landscape",
        "",
        f"- Topic: {report['topic']}",
        f"- Search date: {report['search_date']}",
        f"- Year range: {report['from_year']}–{report['to_year']}",
        "- Status: discovery only; representative studies require DOI/publisher/original-text verification.",
        "",
    ]
    for kind, heading in (("categories", "Category candidate pools"), ("counterexamples", "Counterexample pools")):
        groups = report[kind]
        if not groups:
            continue
        lines.extend([f"## {heading}", ""])
        for label, group in groups.items():
            lines.extend(
                [
                    f"### {label}",
                    "",
                    f"Retrieved across queries: {group['retrieved_total']}; unique retained: {len(group['works'])}.",
                    "",
                    "Top sources: "
                    + "; ".join(
                        f"{item['source']} ({item['count']})" for item in group["top_sources"]
                    ),
                    "",
                    "| # | Study | Year | Source | Citations | DOI/OpenAlex | Matched query |",
                    "|---:|---|---:|---|---:|---|---|",
                ]
            )
            for index, work in enumerate(group["works"], start=1):
                identifier = work.get("doi") or work.get("openalex_id") or ""
                study = f"{short_authors(work['authors'])}: {work['title']}"
                lines.append(
                    "| "
                    + " | ".join(
                        markdown_escape(value)
                        for value in (
                            index,
                            study,
                            work.get("year"),
                            work.get("source"),
                            work.get("cited_by_count"),
                            identifier,
                            "; ".join(work.get("matched_queries", [])),
                        )
                    )
                    + " |"
                )
            lines.append("")
    lines.extend(["## Redacted query audit", ""])
    for item in report["query_audit"]:
        lines.append(
            f"- [{item['kind']}] {item['label']} — `{item['query']}` — "
            f"{item['result_count']} results — {item['url']}"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    specs = build_search_specs(args)
    if args.dry_run:
        creds = ("REDACTED", "REDACTED")
    else:
        try:
            creds = lit_common.openalex_credentials()  # both OPENALEX_API_KEY and OPENALEX_MAILTO required
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    if args.dry_run:
        for spec in specs:
            params = build_params(args, spec, creds)
            print(f"[{spec.kind}] {spec.label}: {redacted_url(params)}")
        return 0

    grouped: dict[str, dict[str, dict[str, dict[str, Any]]]] = {
        "category": defaultdict(dict),
        "counterexample": defaultdict(dict),
    }
    retrieved_totals: dict[tuple[str, str], int] = Counter()
    query_audit: list[dict[str, Any]] = []

    for spec in specs:
        params = build_params(args, spec, creds)
        payload = fetch_json(params, timeout=args.timeout)
        results = payload.get("results") or []
        result_count = int((payload.get("meta") or {}).get("count") or len(results))
        retrieved_totals[(spec.kind, spec.label)] += len(results)
        query_audit.append(
            {
                "kind": spec.kind,
                "label": spec.label,
                "query": spec.query,
                "result_count": result_count,
                "url": redacted_url(params),
            }
        )
        pool = grouped[spec.kind][spec.label]
        for raw_work in results:
            work = normalized_work(raw_work, matched_query=spec.query)
            key = identity(work)
            if key in pool:
                merge_work(pool[key], work)
            else:
                pool[key] = work

    report: dict[str, Any] = {
        "topic": args.topic,
        "search_date": datetime.now(timezone.utc).date().isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "from_year": args.from_year,
        "to_year": args.to_year,
        "types": [item.strip() for item in args.types.split(",") if item.strip()],
        "categories": {},
        "counterexamples": {},
        "query_audit": query_audit,
        "notes": [
            "Discovery output only; do not treat as an included-study set.",
            "Citation sorting is a screening aid, not representative-study selection.",
            "Verify representative studies at DOI/publisher/original-text level.",
        ],
    }

    for kind, output_key in (("category", "categories"), ("counterexample", "counterexamples")):
        for label, pool in grouped[kind].items():
            works = sorted(
                pool.values(),
                key=lambda item: (
                    -int(item.get("cited_by_count") or 0),
                    -(int(item.get("year") or 0)),
                    item.get("title") or "",
                ),
            )[: args.max_per_group]
            report[output_key][label] = {
                "retrieved_total": retrieved_totals[(kind, label)],
                "unique_before_cap": len(pool),
                "top_sources": summarize_sources(works),
                "works": works,
            }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "openalex_landscape.json"
    markdown_path = args.output_dir / "openalex_landscape.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(build_markdown(report), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
