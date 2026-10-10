#!/usr/bin/env python3
"""Validate that academic language polishing preserved protected LaTeX content."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Callable, Iterable


COMMAND_TOKEN_RE = re.compile(r"\\(?:[A-Za-z@]+\*?|.)", re.DOTALL)
ENV_TOKEN_RE = re.compile(r"\\(begin|end)\{([^{}]+)\}")
COMMAND_NAME_RE = re.compile(r"\\([A-Za-z@]+)(\*)?")
WORD_RE = re.compile(r"\b[A-Za-z]+(?:['’][A-Za-z]+)?\b")
NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:[<>≤≥≈=]\s*)?"
    r"[+\-−±]?\s*"
    r"(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+\-−]?\d+)?%?"
)
NUMBER_WORD_RE = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|"
    r"twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|"
    r"thousand|million|billion|first|second|third|fourth|fifth|sixth|"
    r"seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|"
    r"fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth)\b",
    re.IGNORECASE,
)
SYMBOL_RE = re.compile(r"[<>≤≥≈=±−]")
REF_MARKER_RE = re.compile(r"\(\s*ref\s*\)", re.IGNORECASE)
IDENTIFIER_RE = re.compile(
    r"\b(?:RQ\d+[a-z]?|H\d+[a-z]?|M\d+[A-Z]?|SAOM|RSiena|IncoPat|"
    r"modelType|avSimW|sameFunction|sameGroup|sameRegion|priorActivity|"
    r"inPopSqrt|effFrom|[A-Za-z]*[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|"
    r"[A-Z]{2,}[a-z][A-Za-z0-9]*|"
    r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+|"
    r"[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9_]+)+)\b"
)
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,}(?:-[A-Z0-9]+)*(?:s|es)?\b")
HEADING_COMMANDS = (
    "part", "chapter", "section", "subsection", "subsubsection",
    "paragraph", "subparagraph",
)
REFERENCE_COMMANDS = {
    "label", "ref", "eqref", "autoref", "cref", "Cref", "pageref",
    "nameref", "vref", "Vref", "subref", "hyperref", "crefrange",
    "Crefrange", "cpagerefrange", "Cpagerefrange", "vrefrange",
    "Vrefrange",
}
REFERENCE_ARGUMENT_SPECS = {
    "crefrange": 2, "Crefrange": 2,
    "cpagerefrange": 2, "Cpagerefrange": 2,
    "vrefrange": 2, "Vrefrange": 2,
}
PROTECTED_ARGUMENT_SPECS = {
    "caption": 1,
    "captionof": 2,
    "footnote": 1,
    "footnotetext": 1,
    "url": 1,
    "href": 2,
    "path": 1,
    "ensuremath": 1,
    "includegraphics": 1,
    "input": 1,
    "include": 1,
    "bibliography": 1,
    "bibliographystyle": 1,
    "documentclass": 1,
    "usepackage": 1,
    "texttt": 1,
    "detokenize": 1,
}
PROTECTED_ENVIRONMENTS = {
    "table", "table*", "longtable", "tabular", "tabular*",
    "figure", "figure*", "tikzpicture",
    "itemize", "enumerate", "description",
    "verbatim", "verbatim*", "Verbatim", "lstlisting", "minted",
    "algorithm", "algorithm*", "algorithmic",
    "proposition", "proposition*", "lemma", "lemma*", "theorem", "theorem*",
    "corollary", "corollary*", "definition", "definition*", "proof",
}
MATH_ENVIRONMENTS = {
    "equation", "equation*", "align", "align*", "alignat", "alignat*",
    "gather", "gather*", "multline", "multline*", "flalign", "flalign*",
    "displaymath", "math", "eqnarray", "eqnarray*", "split", "cases",
    "IEEEeqnarray", "IEEEeqnarray*",
}


def normalized_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def balanced_group(
    text: str, start: int, opener: str, closer: str
) -> tuple[str, int] | None:
    if start >= len(text) or text[start] != opener:
        return None
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start:index + 1], index + 1
    return None


def parse_command_invocation(
    text: str,
    start: int,
    required_count: int,
    *,
    allow_repeated_groups: bool = False,
) -> tuple[str, int] | None:
    match = COMMAND_NAME_RE.match(text, start)
    if match is None:
        return None
    index = match.end()
    while index < len(text) and text[index].isspace():
        index += 1

    while index < len(text) and text[index] == "[":
        group = balanced_group(text, index, "[", "]")
        if group is None:
            return None
        _, index = group
        while index < len(text) and text[index].isspace():
            index += 1

    parsed_required = 0
    while parsed_required < required_count:
        group = balanced_group(text, index, "{", "}")
        if group is None:
            return None
        _, index = group
        parsed_required += 1
        while index < len(text) and text[index].isspace():
            index += 1

    if allow_repeated_groups:
        while True:
            checkpoint = index
            while index < len(text) and text[index] == "[":
                group = balanced_group(text, index, "[", "]")
                if group is None:
                    return None
                _, index = group
                while index < len(text) and text[index].isspace():
                    index += 1
            if index < len(text) and text[index] == "{":
                group = balanced_group(text, index, "{", "}")
                if group is None:
                    return None
                _, index = group
                while index < len(text) and text[index].isspace():
                    index += 1
            else:
                index = checkpoint
                break

    return text[start:index].rstrip(), index


def command_spans(
    text: str,
    selector: Callable[[str], bool],
    required_counts: dict[str, int] | None = None,
    *,
    repeated_selector: Callable[[str], bool] | None = None,
) -> list[tuple[int, int, str]]:
    required_counts = required_counts or {}
    spans: list[tuple[int, int, str]] = []
    for match in COMMAND_NAME_RE.finditer(text):
        name = match.group(1)
        if not selector(name):
            continue
        parsed = parse_command_invocation(
            text,
            match.start(),
            required_counts.get(name, 1),
            allow_repeated_groups=bool(
                repeated_selector is not None and repeated_selector(name)
            ),
        )
        if parsed is not None:
            invocation, end = parsed
            spans.append((match.start(), end, invocation))
    return spans


def command_invocations(
    text: str,
    selector: Callable[[str], bool],
    required_counts: dict[str, int] | None = None,
    *,
    repeated_selector: Callable[[str], bool] | None = None,
) -> list[str]:
    return [
        invocation
        for _, _, invocation in command_spans(
            text,
            selector,
            required_counts,
            repeated_selector=repeated_selector,
        )
    ]


def citation_invocations(text: str) -> list[str]:
    return command_invocations(
        text,
        lambda name: "cite" in name.lower() or name.lower() == "nocite",
        repeated_selector=lambda name: name.lower().endswith("cites"),
    )


def reference_invocations(text: str) -> list[str]:
    return command_invocations(
        text,
        lambda name: name in REFERENCE_COMMANDS,
        REFERENCE_ARGUMENT_SPECS,
    )


def protected_argument_invocations(text: str) -> list[str]:
    return command_invocations(
        text,
        lambda name: name in PROTECTED_ARGUMENT_SPECS,
        PROTECTED_ARGUMENT_SPECS,
    )


def heading_invocations(text: str) -> list[str]:
    return command_invocations(text, lambda name: name in HEADING_COMMANDS)


def environment_spans(
    text: str, selected: Iterable[str]
) -> list[tuple[int, int, str]]:
    selected_set = set(selected)
    stack: list[tuple[str, int]] = []
    spans: list[tuple[int, int, str]] = []
    for match in ENV_TOKEN_RE.finditer(text):
        kind, env = match.groups()
        if kind == "begin":
            stack.append((env, match.start()))
            continue
        for index in range(len(stack) - 1, -1, -1):
            if stack[index][0] != env:
                continue
            _, start = stack.pop(index)
            if env in selected_set:
                spans.append((start, match.end(), text[start:match.end()]))
            break

    spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    outer: list[tuple[int, int, str]] = []
    for span in spans:
        if any(parent[0] <= span[0] and span[1] <= parent[1] for parent in outer):
            continue
        outer.append(span)
    return outer


def verb_command_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    pattern = re.compile(r"\\(?:verb|Verb|lstinline)\*?(?:\[[^\]]*\])?")
    for match in pattern.finditer(text):
        if match.end() >= len(text):
            continue
        delimiter = text[match.end()]
        if delimiter.isspace() or delimiter.isalnum():
            continue
        end = text.find(delimiter, match.end() + 1)
        if end != -1:
            spans.append((match.start(), end + 1, text[match.start():end + 1]))
    return spans


def comment_spans(
    text: str, excluded: Iterable[tuple[int, int, str]]
) -> list[tuple[int, int, str]]:
    blocked = [(start, end) for start, end, _ in excluded]
    spans: list[tuple[int, int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        line_end = offset + len(line)
        index = 0
        while index < len(line):
            absolute = offset + index
            if any(start <= absolute < end for start, end in blocked):
                index += 1
                continue
            if line[index] == "%":
                preceding = 0
                cursor = index - 1
                while cursor >= 0 and line[cursor] == "\\":
                    preceding += 1
                    cursor -= 1
                if preceding % 2 == 0:
                    spans.append((absolute, line_end, text[absolute:line_end]))
                    break
            index += 1
        offset = line_end
    return spans


def is_escaped(text: str, index: int) -> bool:
    preceding = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        preceding += 1
        cursor -= 1
    return preceding % 2 == 1


def mask_from_spans(length: int, spans: Iterable[tuple[int, int, str]]) -> bytearray:
    mask = bytearray(length)
    for start, end, _ in spans:
        mask[start:end] = b"\x01" * (end - start)
    return mask


def find_unescaped(text: str, token: str, start: int, mask: bytearray) -> int:
    index = start
    while True:
        index = text.find(token, index)
        if index == -1:
            return -1
        if not mask[index] and not is_escaped(text, index):
            return index
        index += max(1, len(token))


def math_blocks(text: str) -> list[str]:
    env_spans = environment_spans(text, MATH_ENVIRONMENTS)
    verb_spans = verb_command_spans(text)
    protected_spans = command_spans(
        text,
        lambda name: name in PROTECTED_ARGUMENT_SPECS,
        PROTECTED_ARGUMENT_SPECS,
    )
    verbatim_spans = environment_spans(
        text, {"verbatim", "verbatim*", "Verbatim", "lstlisting", "minted"}
    )
    comments = comment_spans(
        text, [*verb_spans, *protected_spans, *verbatim_spans]
    )
    mask = mask_from_spans(
        len(text), [
            *env_spans, *verb_spans, *protected_spans, *verbatim_spans, *comments
        ]
    )
    spans = list(env_spans)

    index = 0
    while index < len(text):
        if mask[index]:
            index += 1
            continue
        opener = None
        closer = None
        open_len = 0
        if text.startswith(r"\[", index) and not is_escaped(text, index):
            opener, closer, open_len = r"\[", r"\]", 2
        elif text.startswith(r"\(", index) and not is_escaped(text, index):
            opener, closer, open_len = r"\(", r"\)", 2
        elif text.startswith("$$", index) and not is_escaped(text, index):
            opener, closer, open_len = "$$", "$$", 2
        elif text[index] == "$" and not is_escaped(text, index):
            opener, closer, open_len = "$", "$", 1

        if opener is None:
            index += 1
            continue

        end_start = find_unescaped(text, closer, index + open_len, mask)
        if end_start == -1:
            index += open_len
            continue
        end = end_start + len(closer)
        spans.append((index, end, text[index:end]))
        mask[index:end] = b"\x01" * (end - index)
        index = end

    spans.sort(key=lambda item: item[0])
    return [item[2] for item in spans]


def protected_environment_blocks(text: str) -> list[str]:
    return [item[2] for item in environment_spans(text, PROTECTED_ENVIRONMENTS)]


def verb_blocks(text: str) -> list[str]:
    return [item[2] for item in verb_command_spans(text)]


def latex_comments(text: str) -> list[str]:
    verb_spans = verb_command_spans(text)
    protected_spans = command_spans(
        text,
        lambda name: name in PROTECTED_ARGUMENT_SPECS,
        PROTECTED_ARGUMENT_SPECS,
    )
    verbatim_spans = environment_spans(
        text, {"verbatim", "verbatim*", "Verbatim", "lstlisting", "minted"}
    )
    return [
        item[2]
        for item in comment_spans(
            text, [*verb_spans, *protected_spans, *verbatim_spans]
        )
    ]


def sanitized_for_structure(text: str) -> str:
    spans = [
        *verb_command_spans(text),
        *command_spans(text, lambda name: name in PROTECTED_ARGUMENT_SPECS,
                       PROTECTED_ARGUMENT_SPECS),
        *environment_spans(
            text, {"verbatim", "verbatim*", "Verbatim", "lstlisting", "minted"}
        ),
    ]
    spans.extend(comment_spans(text, spans))
    chars = list(text)
    for start, end, _ in spans:
        for index in range(start, end):
            if chars[index] != "\n":
                chars[index] = " "
    return "".join(chars)


def remove_first_exact(text: str, token: str) -> str:
    index = text.find(token)
    if index == -1:
        return text
    replacement = "".join("\n" if char == "\n" else " " for char in token)
    return text[:index] + replacement + text[index + len(token):]


def prose_for_word_count(text: str) -> str:
    cleaned = sanitized_for_structure(text)
    protected = [
        *protected_environment_blocks(cleaned),
        *math_blocks(cleaned),
        *citation_invocations(cleaned),
        *reference_invocations(cleaned),
        *protected_argument_invocations(cleaned),
        *heading_invocations(cleaned),
    ]
    for token in protected:
        cleaned = remove_first_exact(cleaned, token)
    return COMMAND_TOKEN_RE.sub(" ", cleaned)


def paragraphs(text: str) -> list[str]:
    return [
        part
        for part in re.split(r"\n[ \t]*\n+", text.strip())
        if part.strip()
    ]


def normalized_prose_words(text: str) -> list[str]:
    cleaned = sanitized_for_structure(text)
    cleaned = COMMAND_TOKEN_RE.sub(" ", cleaned)
    return [word.lower() for word in WORD_RE.findall(cleaned)]


def paragraph_order_issues(before: str, after: str) -> list[dict[str, object]]:
    before_paragraphs = paragraphs(before)
    after_paragraphs = paragraphs(after)
    if len(before_paragraphs) != len(after_paragraphs):
        return []
    before_words = [normalized_prose_words(item) for item in before_paragraphs]
    after_words = [normalized_prose_words(item) for item in after_paragraphs]
    failures: list[dict[str, object]] = []
    for index, source_words in enumerate(before_words):
        if not source_words:
            continue
        scores = [
            difflib.SequenceMatcher(None, source_words, candidate_words).ratio()
            for candidate_words in after_words
        ]
        diagonal = scores[index]
        best_index = max(range(len(scores)), key=scores.__getitem__)
        best = scores[best_index]
        if best_index != index and best >= 0.35 and best > diagonal + 0.15:
            failures.append({
                "source_paragraph": index + 1,
                "best_candidate_paragraph": best_index + 1,
                "same_position_similarity": round(diagonal, 4),
                "best_similarity": round(best, 4),
            })
    return failures


def paragraph_protected_signatures(text: str) -> list[dict[str, object]]:
    signatures: list[dict[str, object]] = []
    for paragraph in paragraphs(text):
        signatures.append({
            "citations": citation_invocations(paragraph),
            "references": reference_invocations(paragraph),
            "math": math_blocks(paragraph),
            "numbers": NUMBER_RE.findall(paragraph),
            "number_words": NUMBER_WORD_RE.findall(paragraph),
            "symbols": SYMBOL_RE.findall(paragraph),
            "ref_markers": REF_MARKER_RE.findall(paragraph),
            "identifiers": IDENTIFIER_RE.findall(paragraph),
            "acronyms": ACRONYM_RE.findall(paragraph),
            "protected_commands": protected_argument_invocations(paragraph),
        })
    return signatures


def brace_balance(text: str) -> tuple[int, bool]:
    text = sanitized_for_structure(text)
    depth = 0
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return depth, False
    return depth, depth == 0


def compare(
    name: str,
    before: object,
    after: object,
    failures: list[dict[str, object]],
) -> None:
    if before == after:
        return
    if isinstance(before, list) and isinstance(after, list):
        limit = min(len(before), len(after))
        index = next((i for i in range(limit) if before[i] != after[i]), limit)
        def compact(value: object) -> object:
            if not isinstance(value, str) or len(value) <= 500:
                return value
            return {
                "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                "excerpt": value[:240] + " ... " + value[-120:],
                "length": len(value),
            }

        failures.append({
            "check": name,
            "before_count": len(before),
            "after_count": len(after),
            "first_mismatch_index": index,
            "before_item": compact(before[index]) if index < len(before) else None,
            "after_item": compact(after[index]) if index < len(after) else None,
        })
        return
    failures.append({"check": name, "before": before, "after": after})


def validate(before: str, after: str, max_word_change: float) -> dict[str, object]:
    before = normalized_newlines(before)
    after = normalized_newlines(after)
    before_structural = sanitized_for_structure(before)
    after_structural = sanitized_for_structure(after)
    failures: list[dict[str, object]] = []

    compare("citations", citation_invocations(before), citation_invocations(after), failures)
    compare(
        "references_and_labels",
        reference_invocations(before),
        reference_invocations(after),
        failures,
    )
    compare("headings", heading_invocations(before), heading_invocations(after), failures)
    compare(
        "environment_order",
        ENV_TOKEN_RE.findall(before_structural),
        ENV_TOKEN_RE.findall(after_structural),
        failures,
    )
    compare(
        "latex_command_sequence",
        COMMAND_TOKEN_RE.findall(before_structural),
        COMMAND_TOKEN_RE.findall(after_structural),
        failures,
    )
    compare("math", math_blocks(before), math_blocks(after), failures)
    compare("numeric_tokens", NUMBER_RE.findall(before), NUMBER_RE.findall(after), failures)
    compare(
        "spelled_number_tokens",
        NUMBER_WORD_RE.findall(before),
        NUMBER_WORD_RE.findall(after),
        failures,
    )
    compare("comparison_symbols", SYMBOL_RE.findall(before), SYMBOL_RE.findall(after), failures)
    compare("ref_markers", REF_MARKER_RE.findall(before), REF_MARKER_RE.findall(after), failures)
    compare(
        "protected_identifiers",
        IDENTIFIER_RE.findall(before),
        IDENTIFIER_RE.findall(after),
        failures,
    )
    compare("acronyms", ACRONYM_RE.findall(before), ACRONYM_RE.findall(after), failures)
    compare(
        "protected_environments",
        protected_environment_blocks(before),
        protected_environment_blocks(after),
        failures,
    )
    compare(
        "protected_command_arguments",
        protected_argument_invocations(before),
        protected_argument_invocations(after),
        failures,
    )
    compare("verb_commands", verb_blocks(before), verb_blocks(after), failures)
    compare("latex_comments", latex_comments(before), latex_comments(after), failures)

    before_paragraphs = paragraphs(before)
    after_paragraphs = paragraphs(after)
    compare("paragraph_count", len(before_paragraphs), len(after_paragraphs), failures)
    compare(
        "paragraph_protected_associations",
        paragraph_protected_signatures(before),
        paragraph_protected_signatures(after),
        failures,
    )
    order_failures = paragraph_order_issues(before, after)
    if order_failures:
        failures.append({"check": "paragraph_order", "issues": order_failures})

    before_depth, before_balanced = brace_balance(before)
    after_depth, after_balanced = brace_balance(after)
    if not before_balanced:
        failures.append({"check": "source_brace_balance", "depth": before_depth})
    if not after_balanced:
        failures.append({"check": "candidate_brace_balance", "depth": after_depth})

    before_words = len(WORD_RE.findall(prose_for_word_count(before)))
    after_words = len(WORD_RE.findall(prose_for_word_count(after)))
    if before_words == 0:
        ratio = None
        if after_words != 0:
            failures.append({
                "check": "word_count",
                "before": before_words,
                "after": after_words,
            })
    else:
        ratio = (after_words - before_words) / before_words
        if abs(ratio) > max_word_change:
            failures.append({
                "check": "word_count_tolerance",
                "before": before_words,
                "after": after_words,
                "change_ratio": round(ratio, 6),
                "max_absolute_change": max_word_change,
            })

    return {
        "status": "PASS" if not failures else "FAIL",
        "before_words": before_words,
        "after_words": after_words,
        "word_change_ratio": ratio,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    parser.add_argument("--max-word-change", type=float, default=0.10)
    args = parser.parse_args()
    if not 0 <= args.max_word_change <= 1:
        parser.error("--max-word-change must be between 0 and 1")
    result = validate(
        args.before.read_text(encoding="utf-8"),
        args.after.read_text(encoding="utf-8"),
        args.max_word_change,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
