# Introduction and Literature Review Workflow

## Contents

1. Scope and authority
2. Shared preparation and writing mode
3. Introduction architecture
4. Introduction evidence and audit gates
5. Literature Review profiles and architecture
6. Theory-to-hypothesis development
7. Literature Review evidence and audit gates
8. Literature-positioning assets
9. Anti-patterns

## 1. Scope and authority

Use this reference whenever `section=introduction` or `section=literature`. Treat the current
`manuscript.tex` as the manuscript-content authority. The planning contract is written to the
section blueprint first — `structure/1_introduction/introduction.md` or
`structure/2_literature/literature.md` — and confirmed by the user before any prose is generated
(SKILL.md steps 1.0 and 2.2). The blueprint is a logic contract, not a parallel draft: it holds
the function map, architecture, evidence plan, and protected boundaries, never finished English
paragraphs.

In this reference, "Methodology" means the manuscript sections whose role is `method`, and "Results" means the sections whose role is `results` or `simulation`, as listed in the project contract's `## 技术章节` table; actual section titles vary by method (for example `Equilibrium analysis` or `Numerical analysis`).

Draft directly in English. Preserve the approved research direction, exact RQ wording, construct
boundaries, analysis level, estimand language, and noncausal scope. Use the current method-role technical sections (located through the project contract's
`## 技术章节`) and the term table in `structure/0_global/technical_map.md` section 2 to keep factual
and model wording exact. For Literature Review, use the method-role sections for construct and process meaning; consult
statistic definitions and coding only when relevant to hypotheses. Never use Results to choose
or reverse a hypothesis direction.

## 2. Shared preparation and writing mode

Infer `{NARRATIVE_MODE}` before generating prose:

- `draft`: the target section is absent, empty, or still a TODO scaffold.
- `revise`: the target section already contains substantive prose. Preserve its approved architecture
  and change only user-approved rhetorical blocks.
- `audit`: the user asks to inspect, diagnose, or assess. Produce the relevant contract and gate
  results, then stop without generating replacement prose or writing files.
- `rebuild`: the user explicitly requests a whole-section rewrite. Preserve the approved RQs,
  theoretical role, estimands, and claim boundaries unless a separate Decision Card changes them.

Do not interpret `revise` as permission to rebuild the whole section. Require an explicit structural
Decision Card before changing section order, RQs, hypothesis direction, focal theory, or claim
strength.

Before drafting, build one Section Contract and record it in the blueprint. It contains:

- section profile and rhetorical-block order;
- exact RQs and, for Literature Review, exact hypothesis inventory;
- actor, unit of analysis, context, period, constructs, model effects, and estimands;
- focal theoretical lens and the roles of adjacent literature (for LR, required only when the
  user-selected profile calls for theoretical framing);
- citation plan by claim role;
- protected claim boundaries and prohibited inferences;
- soft word budget derived from rhetorical burden and the manuscript's total budget.

For LR, first obtain the user-selected profile and follow the topic-outline and evidence sequence
in Section 5; do not demand a finalized citation plan before the initial outline. Show the contract
in one compact Decision Card, write it to the blueprint only after the user confirms, and update
the blueprint again whenever a later change alters the argument (gap, aim, RQ, theory role,
hypothesis direction, or boundary). When the blueprint file has been archived after finalization
(project phase `submitted` or `revision-R{N}`), keep the contract in the session and say so in the
write confirmation.

## 3. Introduction architecture

Write the Introduction as a continuous argument. Treat the following as rhetorical blocks, not as
mandatory LaTeX `\subsection{}` headings.

### 3.1 Practice problem before literature gap

Open with one or two paragraphs that move through this chain:

1. Identify the changing technical, organizational, or managerial requirements faced by the focal
   actors.
2. Explain why the focal outcome requires capabilities, knowledge, or resources distributed across
   organizational boundaries.
3. Show why collaboration is therefore an engineering-management capability rather than a generic
   virtue.
4. State the concrete managerial problem created when valuable partners, relationships, or capability
   needs change.
5. Move from dyadic relationships to the relevant network, ecosystem, portfolio, or multilevel
   structure and explain why its evolution matters.

Use empirical industry evidence when it directly establishes the practical problem. Do not begin
with a dictionary definition, a broad claim that innovation is important, or an abstract literature
gap detached from managerial action.

### 3.2 Gap-and-aim paragraphs

Develop one substantive paragraph for each distinct research aim. Use this five-move sequence:

1. **Problem facet**: introduce the next decision layer or process in the study's causal or temporal
   ordering.
2. **Established knowledge**: synthesize the closest literature and name what it has demonstrated.
3. **Design-specific limitation**: identify the unresolved issue through unit of analysis, actor set,
   temporal design, process distinction, partner type, or estimand—not through a blanket absence
   claim.
4. **Consequence**: explain what theoretical or managerial judgment remains impaired while the issue
   is unresolved.
5. **Declarative aim**: end with one precise research aim. Keep the aim as a statement; reserve
   question marks for the later RQ list. Style all aims consistently with the project convention;
   bold italics are an acceptable default when the template permits.

Order the paragraphs by the study's substantive process, not by citation-pool folders. When the study
models a progression such as opportunity formation → partner selection → subsequent actor activity,
preserve that progression in the Introduction.

Map every aim to at least one RQ, but do not force a mechanical one-gap-per-RQ structure when the
approved design is many-to-one or one-to-many. Check exact construct, actor, temporal, and analysis-
level wording across the gap, aim, and RQ.

### 3.3 Research design, theoretical lens, and RQs

After the gap-and-aim paragraphs, integrate the design in one coherent block:

1. Define the empirical process and actor boundary.
2. State the context, sampling boundary, observation periods, and longitudinal or comparative design
   at the level needed to understand the study.
3. Name the method and explain what it represents jointly or distinguishes analytically.
4. Introduce the focal theoretical lens and map it to the observable processes.
5. State what the lens and method do **not** directly measure or establish.
6. Present the exact RQs.

Format RQs so downstream Discussion parsing remains deterministic:

```latex
\begin{itemize}
  \item \textbf{RQ1:} ...?
  \item \textbf{RQ2:} ...?
\end{itemize}
```

End with a short paper-organization paragraph. Do not force a standalone contribution-preview
paragraph. Add one only when the approved outline, target-journal convention, or user explicitly
requires it; do not relabel the research aims or method novelty as theoretical contributions.

### 3.4 Introduction word budget

Use a soft default of roughly 950--1200 words for an empirical paper with two to four RQs:

- practice and network-level problem: about 180--260 words;
- each gap-and-aim paragraph: about 150--220 words, adjusted for evidentiary burden;
- design, lens, boundary, and RQs: about 180--280 words;
- organization: about 35--60 words.

Treat these as planning ranges, not truncation targets. Prefer a complete logical move over hitting a
round number. Any journal or manuscript-wide limit overrides these defaults.

## 4. Introduction evidence and audit gates

Assign citations by claim role:

- Cite external facts, industry evidence, theoretical propositions, and prior empirical findings.
- Use `\citet{}` when a named study's specific contribution matters; use `\citep{}` for thematic
  synthesis or a cluster of convergent studies.
- Allow a clearly signposted synthesis sentence to inherit the immediately preceding citation cluster.
- Do not add citations merely to aims, RQs, paper organization, study-specific method descriptions,
  or authorial `so what` statements.
- Count an approved literature-landscape table or figure reference as an evidence anchor when it
  performs the stated positioning function.

Do not compute or optimize a universal sentence-level citation density. Require instead:

`unsupported citation-required claims = 0`.

Before showing the Introduction candidate, apply these semantic gates:

1. **Practice-to-network gate**: the opening reaches a concrete managerial problem and the correct
   relational level before entering the literature gap.
2. **Gap-evidence gate**: every gap follows from cited prior work and names a defensible design- or
   process-specific limitation.
3. **Gap–aim–RQ gate**: each chain preserves constructs, actors, temporal scope, and analysis level.
4. **Design-fit gate**: the method description explains why the approved design can answer the RQs.
5. **Theory-scope gate**: the focal lens organizes interpretation without being presented as a direct
   measure, universal mechanism, or causal effect.
6. **Setting-boundary gate**: the empirical setting is analytically useful and bounded, not
   automatically representative of a population.
7. **Hedge gate**: remove `unexplored`, `no prior research`, `the first study`, `completely absent`,
   and equivalent absolute claims unless exhaustive evidence genuinely supports them.
8. **No-premature-results gate**: do not leak significance, coefficient direction, or realized findings
   into the Introduction merely because Results already exist.

## 5. Literature Review profiles and architecture

### 5.1 User choice and budgets

The user chooses `review_only`, `review_plus_theory`, or `review_theory_hypothesis`.
Reuse an explicit prior choice; otherwise explain the options and ask. The agent may recommend,
but must not select or switch profiles based on the method, journal, existing draft, or benchmark.
The profile definitions and word budgets have one authority: SKILL.md Section 2.0. Apply that
whole-section budget, not additive quotas per subsection or hypothesis. A thematic review can
explain concepts and mechanisms without adopting one organizing theory. Game-theoretic methods
do not by themselves require a theory-led LR.

### 5.2 RQ-led outline before targeted evidence retrieval

Read the current Introduction/RQs, LR, and relevant Methodology. If the user supplies benchmarks,
read their complete LR and the Introduction's questions before proposing the outline. Extract
section-to-RQ relationships, paragraph progression, how studies are compared, and where theory,
gaps, and method justification appear. Reuse suitable existing benchmarks when available; do not
require a fresh search or a fixed number of examples on every run. Do not assume a published
benchmark's claims are sound or its finished organization proves the author's writing sequence.

If suitable examples or their full texts are missing, use the web-access skill (following its
`references/benchmark-fulltext-workflow.md` when that file exists) to discover, download through
available authenticated browser access, verify, name, and archive them in the existing project
benchmark folder before reading. Downloads is only a staging location.

Propose topics, subsection order, paragraph tasks, evidence needs, and the relation to RQs under
the selected profile. Keep existing approved text when the task is a local revision. Explain the
proposed scope and total word allocation in a compact card for user confirmation. Outline tasks
and open questions before committing to substantive conclusions. Chinese discussion of this
outline is allowed; generate final English prose directly rather than translating a Chinese draft.

Use substantive topic headings. Neither citation-pool folders nor RQ numbering mechanically
sets the subsection count. A context → mechanism → coordination sequence can suit an analytical
paper, but is an example, not a required three-section template.

### 5.3 Find evidence, then revise the outline

After direction is approved, search the project citation pool, tagged direction reports, master
report, and bibliography by paragraph task. Read relevant source passages. When the pool lacks
evidence, first narrow or remove the claim. If a new source is genuinely required, pause the
section and route it through `/lit-workflow`: verified OpenAlex records are converted by
`openalex_to_ris.py` into `direction{N}_openalex.ris` and re-run from review to pool. A source may be
cited only after it is in `citation_pool/master.bib`. Metadata alone cannot establish claim fit.
Copying entries from `master.bib` into the project bib belongs to the final write scope.

For each paragraph, connect its proposed claim or question with representative sources, their
relevant passages, agreements or differences, and the implication for the focal study. Include
credible alternative explanations and nearby counterexamples. Revise or remove unsupported claims;
do not draft fixed conclusions and then look only for confirming citations. Routine evidence
selection requires no extra approval round. Changes to the chosen profile, overall architecture,
focal theory, RQs, or hypothesis direction return to the user before dependent prose is drafted.

### 5.4 Profile-specific composition

- `review_only`: synthesize what is known about the RQ topics, define needed concepts, explain
  relevant mechanisms in context, and position the study. Paragraphs can combine a thematic
  judgment, comparison of representative studies, and synthesis. No compulsory focal theory,
  hypothesis packet, statistical mapping, or gap ending for every subsection.
- `review_plus_theory`: add an explicit theoretical explanation to the thematic synthesis.
  Explain the theory's relevant propositions, why they apply to the actors and context, and how
  they organize the research questions. Distinguish adjacent literature from the focal lens.
  A separate theory subsection is optional; directional hypotheses are not automatically added.
- `review_theory_hypothesis`: develop the theoretical explanation into supported directional
  arguments and testable hypotheses, using Section 6. A roadmap → domain → focal lens → process
  explanation → hypothesis families sequence is useful when it matches the paper, not a universal
  schema for the other two profiles.

Literature synthesis must deepen the knowledge base beyond the Introduction's motivation; do not
repeat its Gap–Aim cycle throughout LR. Method justification belongs here only when it explains a
substantive literature distinction, not as a detached history of a tool. Do not disclose the focal
paper's results as premises for its theoretical arguments. Boundaries admitted to prose still pass
the manuscript-economy contract.

## 6. Theory-to-hypothesis development

Apply this section only to `review_theory_hypothesis`. The other profiles do not require these
packets or hypothetical H placeholders. Changes to approved RQs or hypotheses require user
confirmation; do not silently replace an unsupported H with a new RQ.

Build one Argument Packet for every hypothesis or tightly coupled hypothesis set:

| Field | Required content |
|---|---|
| Modeled process | Exact actor, dyad, network, or behavior process |
| Theoretical baseline | Focal theory proposition used for the argument |
| Mechanism chain | Why the predictor changes the modeled tendency |
| Context bridge | Focal actors, capabilities, interfaces, or decisions |
| Competing logic | Credible countervailing mechanism or cost |
| Construct/proxy boundary | What the observed variable does not directly measure |
| Exact estimand | Statistic, coding, reference category, and conditional interpretation |
| Directional entailment | Why the premises imply the stated sign or contrast |
| Temporal scope | Directional H, temporal H, or temporal RQ |
| Claim boundary | Causal, performance, realization, or mechanism inference prohibited |
| Citations | Sources supporting each premise, not decorative citations on the H sentence |

Write each argument through this sequence:

1. Define the modeled tendency precisely and distinguish it from superficially similar processes.
2. State the directional expectation.
3. Develop two or more nonredundant mechanisms when the argument needs them.
4. Ground those mechanisms in the focal context.
5. Admit the strongest plausible competing logic.
6. Explain why the stated directional expectation still follows, or weaken it to an RQ when it does
   not follow.
7. State the hypothesis in wording that matches the model and level of analysis.

For SAOM network objectives, prefer wording such as “increases the tendency for ties to be created or
maintained,” not causal outcome language. For SAOM behavior objectives, state that, conditional on the
other effects in the objective function, candidate states become more attractive as the relevant
statistic increases or decreases. Translate these examples into the exact estimand language of other
methods rather than copying SAOM wording mechanically.

When two coefficients have a theoretically meaningful joint implication, state the expected contrast
explicitly and align it with the formal test. Do not infer a contrast merely from separate significance
tests.

### 6.1 Directional hypotheses and temporal questions

Separate two questions:

- Does theory justify the direction of the modeled tendency?
- Does theory justify a particular trajectory or difference across periods?

If theory supports only the first, state a directional hypothesis and leave temporal heterogeneity to
an RQ or exploratory contrast. Do not invent a monotonic, lifecycle, or maturity hypothesis merely
because transition-specific coefficients will be estimated.

### 6.2 Proxy and directional-entailment discipline

Apply these hard rules:

- Do not equate organizational affiliation with governance quality, shared region with physical
  proximity, observed activity with absorptive capacity, network position with realized value, or a
  similarity statistic with realized convergence.
- Do not infer that every cross-category pair is complementary merely because categories differ.
- Do not infer a negative similarity tendency only from complementarity; identify the functional-
  differentiation logic that supplies the direction.
- Distinguish actor-level participation from dyadic partner attractiveness, selection from behavior
  adjustment, and candidate-state preference from realized change.
- Keep controls, baseline effects, matching effects, and substantive hypotheses in their correct
  roles.

## 7. Literature Review evidence and audit gates

Use citations by argumentative role, not by density:

- Cite theory definitions, theoretical propositions, prior empirical findings, effect definitions,
  and context-specific mechanism premises.
- Use `\citet{}` only when the named study's particular design or finding matters; use `\citep{}` for
  literature synthesis.
- Allow roadmap, synthesis, hypothesis, joint-implication, and scope-boundary sentences to remain
  uncited when their premises are already supported.
- Never add a source solely to alternate `\citet` and `\citep` forms or to reach a percentage target.
- Verify both citation-key existence and semantic claim fit.

Use the user-selected profile's whole-section word target and interval in SKILL.md Section 2.0.
Check that allocation follows paragraph tasks without multiplying a fixed quota by the number of
hypotheses. User-approved overrides take precedence; do not expand local edits to meet a total.

Before presenting a candidate, apply the relevant checks:

**All profiles**

1. Topic coverage and distinction: the section serves the RQs with coherent, nonredundant topics.
2. Synthesis: representative studies are compared and integrated, not listed as isolated abstracts.
3. Evidence fit: concepts, factual premises, and substantive claims are supported by the cited
   passages; distinguish literature findings from the author's contextual inference.
4. Section roles: deepen the literature foundation without repeating Introduction motivation or
   prematurely supplying the focal paper's results or full Methodology.
5. Construct and level alignment: actors, units, context, temporal scope, and model meaning remain
   consistent with the approved manuscript. Do not overstate inference strength.
6. Citation integrity: verify keys under the final write gate; every key must already be in the
   project bib or `citation_pool/master.bib`; sources outside the pool go back to `/lit-workflow`.
7. Economy and budget: remove redundancy, generic gap endings, and unnecessary defenses; report
   the whole-section word count against the selected budget.

**Additionally for `review_plus_theory` and `review_theory_hypothesis`**

8. Theory role: explain why the chosen lens applies and how its propositions connect to the focal
   problem; keep adjacent theories distinct. Do not invent a focal theory to satisfy this check.

**Additionally for `review_theory_hypothesis` only**

9. Argument completeness: each hypothesis has supported premises, a contextual mechanism,
   directional reasoning, and a model-compatible meaning; address substantive competing logic.
10. Hypothesis–method alignment: check relevant statistic, coding, reference, level, and sign without
    equating a proxy with an unmeasured mechanism or conflating distinct processes.
11. Temporal scope and results independence: distinguish directional and trajectory hypotheses;
    never use observed results to select a hypothesis direction.

Missing focal theory or hypotheses is not a failure for `review_only`. Do not run inapplicable
checks as if they were mandatory fields.

## 8. Literature-positioning assets

Treat literature positioning as a required argumentative function, not a mandatory inline table.
Before proposing a new asset, search the manuscript, appendix, labels, macros, table registry, and
figure/table source files for an existing literature landscape or positioning table.

When a general literature overview introduces several streams, use a shared rhetorical skeleton
rather than an identical sentence template: category → principal analytical focus → representative
topics or studies. Adapt the verb and summary noun to the nature of each stream. For example,
technical studies may examine approaches, economic studies may investigate valuation or allocation
issues, and governance studies may examine institutional or behavioral mechanisms. Keep each
umbrella clause short, introduce representative topics with `including` or `such as`, and leave
study-specific contexts and findings to the literature table. Do not turn each stream sentence into
a miniature literature review or repeat one fixed `has focused on ... including ...` construction.

- If an adequate asset exists, preserve it and reference it at the point where it supports the general
  landscape or gap.
- If prose already performs the positioning function, do not create a table for symmetry.
- If a new or revised landscape table is genuinely needed, route to `build-intro-lit-table` and then
  `latex-table` or the project's table-registry workflow. Do not embed an unregistered table directly
  in the Literature Review.

## 9. Anti-patterns

Reject drafts that do any of the following:

- start with generic importance claims instead of a concrete managerial problem;
- list literature chronologically without a theoretical or process function;
- repeat the same gap at the end of every subsection;
- force a contribution paragraph when the approved Introduction architecture closes with aims, design,
  RQs, and organization;
- use citation density as a quality proxy or add decorative citations;
- make all Literature Reviews 1500 words regardless of hypothesis burden;
- allocate more space to the last subsection merely because it appears last;
- present a proxy as the theoretical mechanism it only imperfectly represents;
- let the focal theory claim temporal predictions it does not supply;
- word hypotheses more strongly than the model's estimand;
- infer causal or realized change from a conditional network or behavior statistic;
- add an inline literature-positioning table without checking existing appendix and registry assets;
- overwrite a mature section when a block-level revision can preserve approved prose.
