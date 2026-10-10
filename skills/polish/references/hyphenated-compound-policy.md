# Hyphenated Compound Policy

Use this policy when polishing or auditing academic English. Its purpose is to remove locally invented, code-like compounds without damaging established terminology or grammatically necessary hyphenation.

## Core rule

Prefer ordinary English syntax to locally invented hyphenated labels. Do not remove hyphens mechanically. A phrase is not a technical term merely because it looks technical.

Canonicalize terminology before enforcing consistency. Do not preserve an unnatural compound only because it is used consistently in the source.

## Scope and protected content

Audit hyphenated lexical compounds in editable prose. Distinguish them from:

- LaTeX `--` and `---` used as en/em dashes;
- minus signs, negative values, mathematical notation, and equation content;
- citation keys and citation commands;
- `\label{}`, `\ref{}`, `\eqref{}`, URLs, filenames, and paths;
- literal code, software parameters, and identifiers inside `\texttt{}` or code environments.

Do not alter protected content. If a protected identifier also appears as a reader-facing prose or table label, audit only the reader-facing occurrence within the authorized editing scope.

## Classification

Classify every distinct hyphenated prose form before editing.

### KEEP — established or necessary

Retain the hyphen when at least one condition holds:

1. The compound is established in standard English or the relevant discipline.
2. Hyphenation is grammatically necessary in an attributive compound and prevents ambiguity.
3. The expression is the formal name of a method, measure, or research design.
4. The expression is an externally established technical term rather than a label invented for the current sentence.

Examples: `actor-oriented model`, `time-homogeneous model`, `goodness-of-fit assessment`, `project-based organization`, `score-type test`.

### CONTROLLED — defined analytical label

Retain a locally defined paired or analytical label only where its compact form performs a clear function, such as its first definition, a formal effect name, a table heading, or a direct comparison. Reduce repeated use in ordinary prose by returning to natural syntax or an unambiguous collective reference.

Examples: `within-function` and `cross-function` may be retained as formal paired labels, then varied with `partners performing the same function`, `partners performing different functions`, or `the two partner types` when no ambiguity results.

### REWRITE — locally invented compound

Rewrite a compound when it compresses an ordinary grammatical relationship into a temporary label. The following are mandatory review signals, not automatic string-replacement rules:

- `X-minus-Y` labels, such as `late-minus-early`;
- temporary `X-side` labels, such as `actor-side` or `ego-side`;
- chains of three or more lexical elements;
- one-off labels that have no external convention or explicit definition;
- compounds encoding possession, agency, comparison, time, location, group membership, or a noun's complement when ordinary syntax is clearer.

Typical rewrites:

| Avoid | Prefer |
|---|---|
| `late-minus-early contrast` | `contrast between the late and early periods` |
| `transition-specific estimates` | `estimates for each transition` |
| `same-business-group matching` | `matching between enterprises in the same business group` |
| `prior-activity participation` | `participation associated with prior innovation activity` |
| `focal-enterprise participation` | `participation by the focal enterprise` |
| `candidate-state similarity` | `similarity of a candidate state` |
| `degree-related cumulative advantage` | `cumulative advantage associated with degree` |

The preferred rewrite depends on the sentence. Use these examples as patterns, not a global replacement dictionary.

## Execution sequence

1. Inventory distinct hyphenated lexical forms in the editable text.
2. Exclude protected content.
3. Classify each remaining form as KEEP, CONTROLLED, or REWRITE.
4. Establish one canonical natural form for each CONTROLLED or REWRITE item.
5. Rewrite complete sentences contextually. Never perform blind global replacement.
6. Use the canonical form consistently across editable prose. Report related occurrences in protected or out-of-scope captions, tables, or figures instead of silently changing them.
7. Run the regression gate below.

## Post-rewrite regression gate

For every changed sentence, verify:

- articles, plurals, possessives, and prepositions remain grammatical;
- modifier attachment and the intended semantic relation remain clear;
- the rewrite has not created noun stacking or excessive `noun + of` nominalization;
- sentence length and subject-verb distance remain within the language policy;
- the new wording does not change claim strength, model meaning, variable identity, or comparison direction;
- the canonical replacement is used consistently;
- citations, numbers, formulas, labels, and code identifiers are unchanged.

## Required ledger

Return a `Hyphenated Compound Ledger` even when no changes are required. Consolidate repeated forms.

| Original form | Class | Canonical form or retained form | Action | Rationale |
|---|---|---|---|---|

List every CONTROLLED and REWRITE form. List KEEP forms in a consolidated inventory so the auditor can detect both missed rewrites and overcorrection.

If the editable text contains no hyphenated lexical form, write `No hyphenated lexical forms detected` below the Ledger heading. Do not leave the Ledger blank and do not invent entries.

## Acceptance criteria

The hyphenation pass is complete only when:

- no unexplained locally invented compound remains in editable prose;
- established or necessary compounds have not been damaged;
- controlled labels are not overused in continuous prose;
- all rewrites pass the post-rewrite regression gate;
- terminology, citations, formulas, LaTeX identifiers, and code identifiers remain consistent.
