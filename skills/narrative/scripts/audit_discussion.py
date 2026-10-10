#!/usr/bin/env python3
"""Mechanical audit for one RQ-by-RQ Discussion block in a LaTeX manuscript."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SUBSUBSECTION_RE = re.compile(r"^\s*\\subsubsection\*?\{([^}]*)\}\s*$")
SECTION_BOUNDARY_RE = re.compile(r"^\s*\\(?:subsubsection|subsection|section)\*?\{")
CITATION_RE = re.compile(r"\\cite[pt]?\{([^}]*)\}")
BIB_KEY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a Discussion subsubsection identified by an RQ token."
    )
    parser.add_argument("--tex", required=True, type=Path, help="Main LaTeX file")
    parser.add_argument("--rq", required=True, help='RQ token, for example "RQ1"')
    parser.add_argument("--bib", type=Path, help="BibTeX file used by the manuscript")
    parser.add_argument("--min-words", type=int, default=300)
    parser.add_argument("--max-words", type=int, default=500)
    parser.add_argument("--min-paragraphs", type=int, default=3)
    parser.add_argument("--max-paragraphs", type=int, default=5)
    parser.add_argument(
        "--allow-stats",
        action="store_true",
        help="Allow detailed statistical or robustness language in the Discussion block",
    )
    parser.add_argument(
        "--allow-network-inference",
        action="store_true",
        help="Suppress warnings for preferential-attachment or scale-free language",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc


def extract_rq_block(tex: str, rq: str) -> tuple[str, str]:
    lines = tex.splitlines()
    target = rq.casefold()
    start = None
    title = ""

    for index, line in enumerate(lines):
        match = SUBSUBSECTION_RE.match(line)
        if match and target in match.group(1).casefold():
            start = index + 1
            title = match.group(1)
            break

    if start is None:
        raise RuntimeError(f'no subsubsection heading contains "{rq}"')

    end = len(lines)
    for index in range(start, len(lines)):
        if SECTION_BOUNDARY_RE.match(lines[index]):
            end = index
            break

    block = "\n".join(lines[start:end]).strip()
    if not block:
        raise RuntimeError(f'Discussion block for "{rq}" is empty')
    return title, block


def strip_comments(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        cleaned.append(re.split(r"(?<!\\)%", line, maxsplit=1)[0])
    return "\n".join(cleaned)


def prose_for_count(text: str) -> str:
    text = strip_comments(text)
    text = CITATION_RE.sub(" ", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    text = re.sub(r"\\[A-Za-z*]+(?:\[[^]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    text = re.sub(r"--+", " ", text)
    return text


def count_words(text: str) -> int:
    prose = prose_for_count(text)
    words = re.findall(r"\b[A-Za-z]+(?:[-'][A-Za-z]+)*\b", prose)
    return len(words)


def split_paragraphs(text: str) -> list[str]:
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", strip_comments(text)):
        paragraph = paragraph.strip()
        if paragraph and not paragraph.startswith("%"):
            paragraphs.append(paragraph)
    return paragraphs


def citation_keys(text: str) -> list[str]:
    keys = []
    for group in CITATION_RE.findall(text):
        keys.extend(key.strip() for key in group.split(",") if key.strip())
    return keys


def main() -> int:
    args = parse_args()
    failures: list[str] = []
    warnings: list[str] = []

    try:
        tex = read_text(args.tex)
        title, block = extract_rq_block(tex, args.rq)
    except RuntimeError as exc:
        print(f"DISCUSSION_AUDIT: FAIL\n- {exc}")
        return 2

    words = count_words(block)
    paragraphs = split_paragraphs(block)
    keys = citation_keys(block)

    if not args.min_words <= words <= args.max_words:
        failures.append(
            f"word count {words} is outside {args.min_words}--{args.max_words}"
        )
    if not args.min_paragraphs <= len(paragraphs) <= args.max_paragraphs:
        failures.append(
            f"paragraph count {len(paragraphs)} is outside "
            f"{args.min_paragraphs}--{args.max_paragraphs}"
        )

    if not args.allow_stats:
        stats_patterns = {
            "exact p-value": r"(?<![A-Za-z])p\s*(?:<|>|=|\\le|\\ge)",
            "standard error": r"(?<![A-Za-z])SE\s*(?:=|\(|<|>)",
            "confidence interval": r"(?:\bCI\b|confidence interval)",
            "test machinery": r"(?:joint test|endpoint contrast|score[- ]type test)",
            "robustness detail": r"(?:robustness|sensitivity (?:analysis|analyses|model))",
        }
        for label, pattern in stats_patterns.items():
            if re.search(pattern, block, re.IGNORECASE):
                failures.append(f"contains default-excluded {label} language")

    causal_patterns = {
        "causal attribution": r"\b(?:caused|causes|was driven by|resulted from|resulted in)\b",
        "over-certain explanation": r"\bexplains why\b",
    }
    for label, pattern in causal_patterns.items():
        if re.search(pattern, block, re.IGNORECASE):
            warnings.append(f"review possible {label}")

    if not args.allow_network_inference and re.search(
        r"\b(?:preferential attachment|scale[- ]free)\b", block, re.IGNORECASE
    ):
        warnings.append(
            "review preferential-attachment/scale-free language against the estimand"
        )

    hedge_count = len(
        re.findall(
            r"\b(?:may|might|could|possibly|perhaps)\b|"
            r"one (?:possible|context-consistent) (?:interpretation|explanation)",
            block,
            re.IGNORECASE,
        )
    )
    if hedge_count > 6:
        warnings.append(f"high hedge count ({hedge_count}); check serial caveats")

    boundary_count = len(
        re.findall(
            r"\b(?:does not|do not|cannot|did not) (?:measure|observe|establish|identify|prove)\b",
            block,
            re.IGNORECASE,
        )
    )
    if boundary_count > 2:
        warnings.append(
            f"boundary-language count is {boundary_count}; check defensive pile-up"
        )

    paragraph_key_sets = [set(citation_keys(paragraph)) for paragraph in paragraphs]
    for index in range(len(paragraph_key_sets) - 1):
        repeated = sorted(paragraph_key_sets[index] & paragraph_key_sets[index + 1])
        if repeated:
            warnings.append(
                "adjacent paragraphs repeat citation key(s) " + ", ".join(repeated)
            )

    if args.bib:
        try:
            bib_keys = set(BIB_KEY_RE.findall(read_text(args.bib)))
        except RuntimeError as exc:
            failures.append(str(exc))
        else:
            missing = sorted(set(keys) - bib_keys)
            if missing:
                failures.append("citation key(s) missing from bib: " + ", ".join(missing))

    status = "FAIL" if failures else "WARN" if warnings else "PASS"
    print(f"DISCUSSION_AUDIT: {status}")
    print(f"title: {title}")
    print(f"words: {words}")
    print(f"paragraphs: {len(paragraphs)}")
    print(f"citations: {len(keys)} uses / {len(set(keys))} unique keys")
    for item in failures:
        print(f"FAIL: {item}")
    for item in warnings:
        print(f"WARN: {item}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
