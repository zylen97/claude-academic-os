# Screening and general-gap audit rules

## 0. Follow the evidence hierarchy

Use the completed lit workflow as the primary evidence base:

1. `master_report.md` for synthesis, prior gap judgments, competitor warnings, and sufficiency diagnostics;
2. `direction*_report.md` for study-level scope, inclusion rationales, and category construction;
3. `citation_pool/BG.md`, `LR.md`, `GAP.md`, and `COMP.md` for writing roles and representative-study candidates;
4. `citation_pool/master.bib` for canonical citation keys and bibliographic records;
5. OpenAlex only for targeted supplementation, recency checks, terminology checks, and adversarial counterexample searches.

Do not use `master_report.md` as the sole paper source. Do not use OpenAlex to repeat or bypass a completed literature workflow.

## 1. Record the evidence trail

For every category, retain:

- category definition and assignment rule;
- lit-workflow source files and screening provenance;
- OpenAlex query formulations, search date, candidate count, and major source distribution when supplemental searching was used;
- inclusion and exclusion decisions;
- DOI or stable identifier;
- representative-study verification source;
- nearest-counterexample disposition;
- source origin: completed lit workflow or admitted OpenAlex supplement;
- canonical citation-pool and `master.bib` presence.

Do not place the entire audit trail in the manuscript. Keep enough information to reproduce why a paper entered a category and why a representative was selected.

## 2. Build breadth before choosing representatives

Use two evidence layers.

### Breadth layer

List the full screened pool in a dedicated `Related studies` column or merged cell for every category.

- Target: 8–20 studies per category.
- Minimum: 6 studies, unless the category is explicitly emerging and the small pool is itself evidenced.
- If fewer than 6 relevant studies remain, merge the category, broaden its defensible boundary, or report insufficient evidence.
- Do not pad a thin category with tangential papers.

### Depth layer

Select 3–6 representative studies per category. Representatives should jointly cover:

- foundational or high-impact work;
- recent frontier work;
- target-domain or target-journal relevance;
- the nearest credible counterexample;
- variation in method, context, or level of analysis.

Every representative must occur in the breadth layer. Verify its title, authorship, year, outlet, DOI, method, context, and claimed contribution from the publisher page or original paper.

## 3. Use OpenAlex only to repair a diagnosed deficiency

OpenAlex supports targeted discovery and landscape checks; it is not the primary pool and does not prove novelty. Before querying, record which deficiency is being repaired: thin category, recent-literature gap, target-context gap, missing counterexample, or uncovered adjacent terminology/method stream.

Strong uses:

- compare alternative query formulations;
- identify high-impact and recent candidates;
- inspect outlet and field distribution;
- find adjacent terminology and counterexamples;
- recover DOI and stable work identifiers.

Invalid uses:

- repeating the full lit-workflow search without a diagnosed deficiency;
- treating a zero-hit exact phrase as proof that no prior study exists;
- defining categories from automated topics without conceptual review;
- ranking papers solely by citations;
- accepting a title/abstract match as proof of method or contribution;
- claiming a systematic review without a protocol.

When exact wording is rare, separate two questions: whether the broader construct has a literature base and whether the focal combination is a new framing.

An OpenAlex candidate becomes table-eligible only after DOI/publisher/original-text verification, ordinary screening, citation-key assignment, and admission into the appropriate citation-pool file and `master.bib`. Otherwise retain it as a discovery-only side artifact.

## 4. Derive the general gap from a common boundary

The table-derived gap is a single umbrella gap. It should identify a unified unresolved management problem shared across the categories.

Acceptable derivation patterns include:

- **common omission**: different streams all omit the same consequential actor, condition, or process;
- **shared assumption**: different approaches depend on an assumption that fails in the focal context;
- **fragmentation**: streams explain connected pieces separately, leaving their management interaction unresolved;
- **contextual boundary**: established explanations do not cover a materially different stress condition or governance setting;
- **dynamic boundary**: static explanations do not resolve an inherently adaptive or temporal management problem.

Reject these patterns:

- “No study combines A, B, and C” without an underlying management problem;
- a gap copied from the focal model's variables rather than induced from the literature;
- a gap that merely says more research is needed;
- a universal gap broad enough to describe most papers in the field;
- a narrow gap stated in equations, equilibrium labels, or solution jargon in the Introduction;
- a gap copied from `master_report.md` and then “confirmed” by categories selected to reproduce it.

Treat the gap judgment in `master_report.md` as a prior hypothesis. First derive the general gap from the table's independently classified corpus; only then compare the two judgments and investigate disagreement.

## 5. Run the compatibility gate without producing a mapping section

Use later specific gaps and RQs as a stress test, not as the source of the general gap.

### Coverage

Ask whether every specific gap is a recognizable dimension of the umbrella problem. A specific gap may sharpen an actor, mechanism, institution, or condition, but it cannot change the subject.

### No orphan mechanism

Flag any later actor, mechanism, level, or institution that appears without conceptual room in the general gap. The repair may be to broaden the general gap slightly, add relevant literature evidence, redesign a category, or remove an unsupported specific gap.

### Table support

Decompose the general-gap sentence into claims. Each claim must be supported by the categories' evidence or their demonstrated common boundary. Delete model-driven clauses that the table cannot support.

### Granularity

The general gap must sit above individual model parameters and below a field-wide slogan. A useful test is whether two or more specific gaps can fit beneath it without becoming identical to it.

### Answerability

Read the actual method, model solution, and results. A gap is not defensible merely because the Introduction can state it; the study must produce an analysis or result that addresses it.

## 6. Assign a status

Use one status in the working report only:

| Status | Meaning | Required response |
|---|---|---|
| `PASS` | Table, general gap, later gaps, and results are coherent | Proceed |
| `REVISE TABLE` | A later mechanism lacks literature foreshadowing | Add/reclassify evidence before writing |
| `REVISE GENERAL GAP` | Evidence exists but umbrella wording misstates it | Rewrite the umbrella gap |
| `REVISE SPECIFIC GAP` | A later gap falls outside the umbrella or results | Repair/remove the later gap |
| `NOT TESTABLE` | Later gaps/RQs/results are unavailable | Report the limitation; do not invent them |

Do not output a formal `Specific gaps and RQ mapping` section by default. If the user explicitly requests diagnostic detail, provide a short audit table outside the manuscript, clearly labeled as a working check.

## 7. Hard-stop conditions

Stop manuscript writeback when any of the following holds:

- a category lacks a defensible assignment rule;
- a category has fewer than 6 relevant studies without an emerging-field justification;
- representative studies have not been DOI/publisher/original-text verified;
- an OpenAlex-discovered study appears in the table but not in the canonical citation pool and `master.bib`;
- the claimed gap is contradicted by an unsynthesized counterexample;
- the general–specific compatibility status is not `PASS`;
- the study's results cannot answer the gap it claims.
