---
name: build-intro-lit-table
description: Build, audit, or refresh an Introduction literature-landscape table from a completed lit-workflow corpus first, using OpenAlex only for targeted supplementation and counterexample checks. Use for early-Introduction literature tables, category design, representative-study selection, table-before/table-after prose, deriving one defensible general gap, or checking whether that gap can contain later specific gaps and research questions without outputting a mechanical gap-to-RQ mapping.
---

# Build an Introduction Literature Table

Construct an early-Introduction literature table as an argument, not a bibliography display. Show breadth through a large screened study pool in every category, show depth through representative rows, and derive exactly one general gap from the categories' shared explanatory boundary.

## Respect the interaction boundary

Treat category choice and gap wording as research-logic decisions.

- For diagnosis or discussion, inspect and report without editing project files.
- Before changing categories, the Introduction, a literature table, bibliography, or project state, present the proposed architecture and obtain explicit approval.
- Before durable writes, identify exact files and validation steps.
- Keep OpenAlex exports and search logs as side artifacts. Do not introduce an OpenAlex-discovered paper into the table or manuscript until it has entered the project's canonical literature artifacts.
- Do not stage, commit, push, send, or publish unless separately authorized.

## Choose the operating mode

Select the narrowest mode that satisfies the request.

1. **Audit**: assess an existing table, category logic, evidence breadth, representative studies, and general-gap derivation.
2. **Build**: design categories and create the table plus surrounding Introduction prose from project materials and literature evidence.
3. **Refresh**: rebuild from the current lit-workflow corpus, then use targeted OpenAlex supplementation only for diagnosed deficiencies.
4. **Stress-test**: search for nearby counterexamples and test whether the claimed general gap is too strong.

## Load the project and lit-workflow evidence

Read the project-level instructions first. Then locate the research-design context:

1. the current Introduction;
2. `idea.md` or the project's authoritative research-design file;
3. current specific gaps, RQs, contributions, and model/result summary;
4. any existing table source, appendix, or supplement.

Next detect whether the lit workflow is complete. Treat its permanent outputs as the primary evidence base and use them by function:

1. `structure/2_literature/literature_manifest.json`: use as the primary unique-corpus truth (one row per unique paper: citation key, bibliographic fields, tier, merged tags, pools, source directions, reasons, source origin, record provenance);
2. `structure/2_literature/tagged_reports/direction{N}_report.md`: use for direction-specific occurrence context, category assignment reasoning, functional labels, and detailed inclusion evidence; keep root-level `direction{N}_report.md` as immutable review provenance only;
3. `structure/2_literature/master_report.md`: use only as the synthesis index for feasibility, prior gap judgments, competitor warnings, and pool sufficiency;
4. `structure/2_literature/citation_pool/BG.md`, `LR.md`, `GAP.md`, and `COMP.md`: use for writing roles and representative-study candidates;
5. `structure/2_literature/citation_pool/master.bib`: use as the canonical bibliographic source and cross-check every manifest citation key;
6. `screening_summary_report.md`, `tag_report.md`, and `lit_status.md`: use to audit retrieval coverage, skipped/failed directions, and stage completeness.

Do not treat `master_report.md` as the complete study corpus. It is a synthesis and navigation layer. Start the unique paper set from `literature_manifest.json`; consult direction reports for occurrence-level context rather than performing a fourth ad hoc deduplication.

Require the finished corpus and validate it read-only (manifest keys = pool keys, every pool key in `master.bib`, no `JUDGE` placeholder in `master_report.md`):

```bash
python3 ~/.claude/skills/lit-pool/finalize_pool.py --lit-dir structure/2_literature --check-only
``` If the lit workflow is incomplete, do not silently replace it with an OpenAlex search. Offer either a provisional table explicitly labeled as such or completion/refresh of the literature workflow.

Do not invent specific gaps or RQs when they are unavailable. Mark compatibility as not testable and continue with the table-derived general gap only.

## Design categories from the screened corpus

Use three to five categories by default. Define each category by what the literature primarily explains, not by keywords copied from the focal paper's contribution statement.

Require all categories to be:

- mutually intelligible, with a clear assignment rule;
- collectively sufficient to describe the relevant literature landscape;
- comparable at a similar level of abstraction;
- useful for exposing a shared boundary rather than merely displaying variety.

Read [references/table-archetypes.md](references/table-archetypes.md) before selecting the table form. Present the proposed category architecture and assignment rules for approval before writing project files.

Use the existing gap judgments in `master_report.md` only as hypotheses and consistency constraints. Derive categories and their common boundary independently from the underlying direction reports and citation pools; otherwise the table merely reproduces a preselected gap and creates circular reasoning.

## Build the primary pools from the lit workflow

Map the screened lit-workflow corpus into the approved categories before any supplemental search. For each candidate, retain its citation key, original direction, functional tags, tier, inclusion rationale, and source artifact.

Use `literature_manifest.json` to establish unique breadth, tagged reports to recover direction-level context, and citation-pool files to understand writing roles. Resolve citation metadata against `master.bib`; do not rededuplicate a manifest that has already passed the final gate.

Do not force the lit workflow's search directions or functional tags to become the final table categories. Reclassify studies by the table's approved analytical assignment rule while preserving their source provenance.

## Supplement and stress-test with OpenAlex

Before any network operation, load and follow the installed `web-access` skill. Prefer the official OpenAlex API for discovery and lightweight evidence checks. Every OpenAlex request carries both `api_key` and `mailto`; the script reads `OPENALEX_API_KEY` and `OPENALEX_MAILTO` through `lit_common.openalex_credentials()` (environment or `~/Library/CloudStorage/Dropbox/Apps/secrets-vault/openalex.env`) and fails if either is missing.

Run OpenAlex only when the primary corpus shows a specific deficiency:

1. a category retains fewer than 6–8 relevant studies;
2. the most recent 2–3 years are materially underrepresented;
3. target-journal, target-domain, or target-context coverage is weak;
4. the corpus lacks a nearest credible counterexample to the proposed general gap;
5. a necessary adjacent term or external method stream was outside the original search plan.

Use [scripts/openalex_landscape.py](scripts/openalex_landscape.py) to collect auditable supplemental candidates. Query only the diagnosed deficiency and include a nearest-counterexample query when the gap could be contested.

```bash
python3 ~/.claude/skills/build-intro-lit-table/scripts/openalex_landscape.py \
  --topic "interregional emergency electricity assistance" \
  --category "Emergency cooperation::interorganizational emergency cooperation" \
  --category "Electricity exchange::interregional electricity trading" \
  --counterexample "Information platform::government information sharing emergency coordination" \
  --from-year 2000 \
  --max-per-group 50 \
  --output-dir /absolute/path/to/openalex-intro-table
```

Never expose the API key or mailto in commands shown to the user, logs, reports, or URLs. The script redacts both from its audit trail.

Treat OpenAlex as discovery evidence, not final proof:

- inspect hit counts, source distribution, field fit, and high-impact works together;
- do not infer absence from a zero-hit exact-title search;
- do not let an automated rank define the categories or representative studies;
- verify every representative paper through its DOI, publisher page, or original text;
- call the output a selected or screened literature landscape, not a systematic review, unless a review protocol justifies that label.

For every admitted OpenAlex paper, apply the same inclusion and source verification rules as the lit workflow, then generate the supplement only with lit-workflow's converter (never hand-write RIS):

```bash
python3 ~/.claude/skills/lit-workflow/openalex_to_ris.py --direction N --doi <verified DOI> [...]   # or --json verified_works.json; --append / --replace when the file exists
```

This writes `structure/2_literature/direction{N}_openalex.ris` for a real plan direction `N` (TY = ER checked). OpenAlex shares the international (WoS) quota of that direction, so a supplement can displace previously selected papers; tell the user. Then rerun `/lit-workflow from=review` (review → tag → pool) so the paper receives a screening decision, citation key, tags, `source_origin = OpenAlex supplement`, a `literature_manifest.json` row, pool membership, and a `master.bib` entry. Existing citation keys are kept by lit-pool. Only after `finalize_pool.py --check-only` passes again may the paper enter the table or manuscript. Never create an orphan table citation or edit a pool file or `master.bib` by hand.

## Screen each category

Apply explicit topical, contextual, methodological, and publication-type inclusion rules. Deduplicate by DOI first and stable work identifier second.

Hard requirements:

- Every category must contain a dedicated **Related studies** column or merged cell listing the full screened pool.
- Target 8–20 included studies per category; use at least 6 unless the field is demonstrably emerging. Merge or redesign a thin category instead of padding it with irrelevant papers.
- Follow each category pool with 3–6 detailed representative-study rows.
- Every representative study must also appear in that category's full pool.
- Include the nearest credible counterexample rather than screening it out because it weakens novelty.
- Record whether every included study came from the completed lit workflow or an admitted OpenAlex supplement.

Select representatives for complementary functions: foundational/high-impact, recent frontier, target-domain or target-journal fit, nearest counterexample, and method/context diversity. Do not select only the most supportive papers.

Read [references/screening-gap-rules.md](references/screening-gap-rules.md) for the screening record, evidence-strength rules, and failure statuses.

## Construct the table argument

Use this default schema unless the chosen archetype requires a justified variation:

`Category | Related studies | Representative study | Research focus | Context | Method/framework | Main contribution`

Use a multirow category cell and a multirow Related studies cell spanning that category's representative rows. Keep the broad pool visible even when the table is moved to an appendix or supplement.

Place or cite the table in Introduction paragraph 2 or 3: after the practical management problem and before the detailed specific gaps. Keep the table in the main text when compact; move a wide or long landscape to an appendix or supplement while citing it early.

Write two short prose bridges:

1. **Before the table**: name the categories and state what each stream explains.
2. **After the table**: compare the categories and identify their shared explanatory boundary.

In the before-table bridge, use the common information skeleton `category → principal analytical
focus → representative topics or studies`, but do not force every stream into the same sentence
template. Match the verb and summary noun to the literature: technical streams may examine
approaches, economic streams may investigate valuation or allocation issues, and governance streams
may examine institutional or behavioral mechanisms. Keep the umbrella clause short, use `including`
or `such as` for representative topics, and leave study-specific contexts and findings to the table.

Do not fill either bridge with model formulas, equilibrium jargon, or detailed solution mechanics.

## Derive one general gap

Derive the general gap from the common boundary visible across categories. Do not manufacture novelty by saying only that no prior study combines A, B, and C.

Use this reasoning sequence:

1. State what the categories collectively explain well.
2. Identify the management problem they collectively leave unresolved.
3. Explain why that unresolved problem matters in the focal context.
4. Express one umbrella-level general gap in accessible Introduction language.

A useful pattern is:

> Although these streams explain [established knowledge], they leave unresolved how or when [unified management problem] under [critical contextual condition].

The table supports only this umbrella gap. Leave later paragraphs to unpack specific gaps and RQs.

Cross-check the derived general gap against `master_report.md` only after deriving it from the table. If the two differ, inspect the underlying evidence and explain the discrepancy rather than forcing agreement.

## Run the general–specific compatibility gate

Use existing specific gaps and RQs only as constraints on the proposed general gap. Do not add a “Specific gaps and RQ mapping” section to the manuscript or default deliverable.

Check internally:

1. **Coverage**: every specific gap is a plausible dimension of the general gap.
2. **No orphan mechanism**: later gaps do not introduce an actor, mechanism, level, or institution that the general gap cannot contain.
3. **Table support**: every component of the general gap follows from the table's evidence and cross-category boundary.
4. **Granularity**: the general gap is neither paper-universal nor as narrow as one model parameter.
5. **Answerability**: the focal study's actual analysis and results can address the downstream gaps.

Return one internal status in the work report:

- `PASS`: the umbrella gap can coherently contain the later gaps;
- `REVISE TABLE`: a downstream mechanism is not foreshadowed by the literature landscape;
- `REVISE GENERAL GAP`: the table supports the content, but the umbrella wording is too narrow, broad, or misframed;
- `REVISE SPECIFIC GAP`: a later gap falls outside the study's evidence or answerable scope;
- `NOT TESTABLE`: specific gaps/RQs or results are unavailable.

When the status is not `PASS`, stop manuscript writeback and explain the smallest research-logic repair. Never conceal the failure by inserting a mechanical mapping paragraph.

## Deliverables

Return only what the selected mode requires. For a full build, provide:

1. category definitions and assignment rules;
2. the screened Related studies pool for every category;
3. representative-study rows with verified details;
4. the table in the project's required format;
5. the short table-before and table-after paragraphs;
6. exactly one table-derived general gap;
7. a compact source-provenance audit, plus an OpenAlex query trail and verification flags when supplemental searching was actually used;
8. the compatibility-gate status in the work report, not as a gap-to-RQ section in the manuscript.

If the table changes LaTeX sources, follow the project's LaTeX compilation rules and report citation, label, float-size, and compilation failures explicitly.
