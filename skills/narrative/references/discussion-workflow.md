# Discussion on Research Questions Workflow

## Contents

1. Scope and default output
2. Interactive state machine
3. Evidence boundary and RQ Answer Card
4. Interpretive Arguments Card
5. Local-corpus subagent search
6. Literature Dialogue Card
7. Claim ladder and theory grounding
8. Multi-effect integration and drafting
9. Contribution Ledger handoff
10. Theory, terminology, pre-display language gates, and anti-patterns

## 1. Scope and default output

Use this reference for the RQ-by-RQ part of a manuscript Discussion and for producing the Contribution Ledger consumed by Theoretical implications. Do not apply its paragraph architecture to Practical implications, Limitations, Introduction, or Literature Review.

Treat the technical sections of the current manuscript — located through the `## 技术章节` table in the project contract (roles `method`, `results`, `simulation`), never by literal title — as the sole authority for conclusion targets and findings. Use theory, industry context, and literature to interpret those findings, never to overwrite them. From upstream files read only what SKILL.md step 3.1 needs: the term table in `structure/0_global/technical_map.md` section 2, its "技术正文完成" date, the last change date in `analysis_plan.md` section 7, and the release date of `results_register.md`. Do not use the register, data outputs, or derivation files to supply, correct, or replace manuscript findings. If the technical sections are missing or internally inconsistent, stop and route the problem to `/technical`.

In this reference, "Methodology" means the manuscript sections whose role is `method`, and "Results" means the sections whose role is `results` or `simulation`, as listed in the project contract's `## 技术章节` table; actual section titles vary by method (for example `Equilibrium analysis` or `Numerical analysis`).

Default output profile:

- Work on one RQ at a time.
- Confirm the result answer, interpretive arguments, and literature dialogue separately before drafting prose.
- Target 300--500 words per RQ; prefer 350--450 when an RQ contains two or more related effects.
- Use three or four functional paragraphs: concise answer, mechanism/context discussion, related mechanism discussion when needed, and integrated punchline.
- State observed results directly and compress statistical machinery.
- Prioritize unsupported hypotheses, temporal heterogeneity, divergent/asymmetric results, and the integrated punchline.
- Ground every theoretical mechanism in the actors, capabilities, interfaces, or decisions of the study context.
- Use one umbrella hedge for an untested contextual explanation instead of repeated defensive caveats.
- Use citations by argumentative role, not by density or target-journal quota.
- End one abstraction level above the findings; do not repeat the Results section.

## 2. Interactive state machine

Run this sequence for every RQ:

```text
RQ Answer Card
  → user confirms the empirical answer
Interpretive Arguments Card
  → user confirms the theoretical/contextual logic
Subagent Run Board and local evidence search
Literature Dialogue Card
  → user confirms the literature relationships
Internal draft and semantic gates
Theory hierarchy and canonical terminology gates
Embedded candidate-only language and fidelity gate
Regression-only claim lock
Final RQ prose
  → user confirms wording
RQ-scoped Write Gate
  → user approves the exact manuscript block
Write, compile, and audit
Validated Contribution Ledger entry
```

Do not configure citations before the interpretive arguments are confirmed. Do not draft final prose before the Literature Dialogue Card is confirmed.

Apply state invalidation strictly:

- If the RQ Answer changes, invalidate the arguments, evidence search, literature card, draft,
  polished candidate, and contribution seeds.
- If an Interpretive Argument changes, invalidate its evidence search, literature relation,
  draft, polished candidate, and contribution seed status.
- If a Literature relation or claim-fit judgment changes, invalidate the draft, polished
  candidate, and contribution seed status.
- A wording-only revision that preserves confirmed claims does not invalidate earlier cards,
  but it invalidates the language/fidelity result. Rerun the embedded gate and treat wording
  explicitly required by the user as a protected span.
- If the user reports that a result sentence is incomprehensible, too technical, or requires
  rereading, treat it as a semantic-source readability failure rather than a wording-only
  revision. Keep the confirmed empirical, argument, and literature cards unless meaning changes,
  but invalidate that sentence and the polished candidate. Return to substantive-first result
  translation and do not recycle a near-synonymous estimand-first construction.
- If a meaning-bearing theory role or terminology-contract entry changes, invalidate the
  draft, polished candidate, language/fidelity result, and affected contribution seed, then
  return to the card that established that role or term. Do not classify it as wording-only.

Use a fast path only when the user has already stated and confirmed all three components in the current conversation. Compress the cards into one recap, but preserve the same evidence and claim-fit checks. A command such as “continue” or “write it” does not by itself approve unshown assumptions.

## 3. Evidence boundary and RQ Answer Card

### 3.1 Build the evidence boundary

Extract every finding relevant to the RQ and separate three lists internally:

1. **Essential findings**: directions, periods, contrasts, asymmetries, or null patterns required to answer the RQ.
2. **Supporting diagnostics**: coefficients, p-values, standard errors, confidence intervals, joint tests, robustness results, model labels, and figure/table numbers.
3. **Interpretive candidates**: theoretical or contextual mechanisms not directly estimated.

Use only essential findings in the opening paragraph by default. Use supporting diagnostics to verify accuracy, not to fill Discussion prose. Include a diagnostic only when omitting it would materially alter the interpretation.

State the substantive pattern before the model mechanics. The direct answer must identify the
study actor or unit, the outcome or modeled process, the direction, and the relevant comparator
in language that a reader familiar with the substantive field can understand without knowing the
estimation software. Model-internal objects such as candidate states, objective functions,
statistics, coefficients, and conditional attractiveness may qualify or verify the answer in a
following sentence, but must not carry the main answer when a faithful actor-level formulation is
available. Paraphrase the proposed sentence back into actor--outcome--direction--comparator form
and verify that conditioning, time, scope, and any formal contrast remain unchanged.

Do not treat statistical insignificance as proof that an effect is exactly zero, absent, or reversed. Preserve the Results meaning, such as `statistically indistinguishable from zero`, `not statistically supported`, or `weakened relative to`.

### 3.2 Set interpretive priority

Assign each essential finding a priority:

- **P1**: an unsupported or contrary-to-expectation hypothesis; statistically supported temporal change; divergence or asymmetry between effects central to the RQ.
- **P2**: a persistent or expected effect needed to understand the P1 contrast or integrated punchline.
- **P3**: a secondary expected pattern or diagnostic that does not change the RQ answer.

Discuss P1 findings most deeply. Use P2 findings to build the comparison. Mention P3 only if it prevents a misleading conclusion. “Hypothesis unsupported” must not be rewritten as “effect absent.”

### 3.3 Show the RQ Answer Card

Keep the opening answer to roughly 45--80 words and show this card before explaining causes:

```text
🧾 RQ{i} Answer Card
- Reader-facing direct answer: {one or two substantive actor--outcome--direction--comparator sentences}
- Essential findings: {directions, periods, and central contrasts}
- Technical fidelity lock (not intended prose): {mapping to the exact estimand, conditioning,
  temporal scope, and formal contrast}
- Priority: {P1/P2/P3 for each finding}
- Joint contrast: {what becomes visible only when findings are read together}
- Prohibited inference: {causal, substitutive, performance, or generative claim not supported}

Please confirm the empirical answer. Explanations and citations come next.
```

Omit by default coefficient values, test names, sensitivity specifications, and sample/model details already stated in Methodology or Results.

## 4. Interpretive Arguments Card

### 4.1 Build arguments around results, not around available citations

Construct one to three arguments after the RQ Answer is confirmed. Begin with P1 findings and the joint contrast. Avoid one generic story per coefficient when several effects answer the same theoretical question.

Every argument must specify:

| Field | Required content |
|---|---|
| Result addressed | Exact confirmed finding or contrast |
| Theory baseline | What the focal theory currently explains or expects |
| Theory logic | The pathway connecting the modeled pattern to a theoretical meaning |
| Industry grounding | Actors, differentiated capabilities, technical/organizational interfaces, and relevant decisions |
| Interpretation type | `theory-based meaning` or `possible contextual interpretation` |
| Context evidence need | What period-aligned industry evidence would be required, if any |
| Claim boundary | Causal, substitutive, performance, or generative inference that remains unavailable |
| Contribution Seed | Potential theoretical move, or `none` |

Theory-based meaning explains what a result can signify through an established theoretical pathway. A possible contextual interpretation proposes an unestimated industry, policy, technological, or institutional reason for the observed temporal or relational pattern. Do not blur them.

### 4.2 Define Contribution Seeds conservatively

A Contribution Seed is a candidate for later theoretical synthesis, not a finished contribution. Each seed must contain:

1. **Theoretical baseline**: the established claim or unresolved issue being engaged.
2. **Potential conceptual move**: extend, qualify, differentiate, temporalize, or integrate.
3. **Evidence anchor**: the confirmed RQ finding or cross-effect contrast.
4. **Context-to-theory abstraction**: the general theoretical insight abstracted from the focal industry circumstance.
5. **Target-journal relevance**: why the move matters for managing engineering or technological collaboration.
6. **Claim boundary**: what the evidence does not establish.

Industry change alone is not a theoretical contribution. For example, “digital construction broadened required capabilities” is a contextual explanation. A possible seed would instead ask whether changing capability and coordination demands alter the temporal relevance of different relational positions.

Allow zero seeds for an RQ. Keep no more than two unless the RQ genuinely supports separate, non-overlapping theoretical moves. Expected results often need no seed.

### 4.3 Show the Interpretive Arguments Card

```text
🧠 RQ{i} Interpretive Arguments Card
| ID | Result | Theory logic | Industry grounding | Type | Contribution Seed | Boundary |
|---|---|---|---|---|---|---|
| A1 | ... | ... | ... | theory-based / possible context | ... / none | ... |

- Joint spine: {how the arguments work together}
- Main punchline candidate: {one abstraction level above Results}
- Highest-risk inference: {the claim most likely to overreach}

Please confirm, revise, or reject each argument before evidence search.
```

## 5. Local-corpus subagent search

### 5.1 Search order and evidence authority

Search the project’s durable local corpus before considering external search:

1. Manuscript Literature Review: cited keys, adjacent claims, theoretical baseline, and level/context already established.
2. `structure/2_literature/citation_pool/DISC.md`, `COMP.md`, and `LR.md`.
3. Relevant `BG.md` or `GAP.md` entries for industry context or boundary claims.
4. `master_report.md`, `tagged_reports/direction{N}_report.md`, `literature_manifest.json`, canonical RIS records, and retained abstracts or review notes.
5. `citation_pool/master.bib` and the project bibliography for key and metadata validation only.

A bibliography entry proves existence, not claim fit. A citation-pool scenario or abstract supports only the detail it actually contains. Prefer an original locally available paper or full review record when a strong contrast, extension, or mechanism claim depends on it.

Exclude stale or intermediate artifacts by default: `_tmp*`, `_batch/*_raw.md`, scratch agent outputs, superseded manifests, and `legacy_*` reports. Use a legacy file only when the durable corpus lacks the needed record, and label that fallback for the main agent rather than treating it as final authority.

If the local corpus does not support an argument, first narrow, downgrade, or remove the argument. If a new source is genuinely required, pause and route it through `/lit-workflow` (OpenAlex records → `openalex_to_ris.py` → `direction{N}_openalex.ris` → review → pool); cite it only after it is in `citation_pool/master.bib`. Do not browse merely to decorate the paragraph.

### 5.2 Show a Subagent Run Board

Use two primary read-only subagents in parallel and an optional auditor. Never exceed three workers, and add the auditor only if a slot is available.

| Agent | Role | Required inputs | Required output |
|---|---|---|---|
| A | LR Dialogue Extractor | manuscript LR, its cited keys, confirmed arguments | Exact manuscript claim, candidate key, relation possibility, source location |
| B | Corpus Evidence Miner | DISC/COMP/LR pools, relevant BG/GAP, master report, RIS/review records, bib | Actual source claim, context/level/method, evidence location, caveat |
| C optional | Claim-Fit & Contribution Auditor | merged A/B table, confirmed RQ Answer and Arguments | relation validity, overclaim risk, seed novelty verdict |

Trigger Agent C when any of these conditions holds:

- the draft would claim `extends`, `qualifies`, or `contrasts with` a close literature;
- a target-journal paper is being used to support the contribution;
- contextual evidence risks being presented as direct mechanism evidence;
- A and B disagree about claim fit;
- a Contribution Seed appears close to an existing claim.

All agents must:

- remain read-only;
- search only the assigned local sources;
- return structured evidence, not Discussion prose;
- quote or paraphrase only enough to identify the claim;
- provide file path and record/key for every item;
- flag missing evidence instead of inventing support;
- avoid deciding the final narrative or theoretical contribution.

The main agent owns merging, deduplication, citation-key validation, literature-relation classification, and final prose. If subagents are unavailable, perform the same searches sequentially and disclose the fallback in the Literature Dialogue Card.

### 5.3 Required evidence-table schema

Require each candidate row to include:

| Argument | Citation key | Source claim | Context/level/tie type | Evidence source | Possible role | Fit limitation |
|---|---|---|---|---|---|---|

Reject rows that provide only a title, journal name, broad topic match, or unlocated assertion.

## 6. Literature Dialogue Card

### 6.1 Assign an explicit relationship

Use only these relationships:

- **consistent with**: a sufficiently comparable study reports the same substantive pattern.
- **extends**: the present study adds a new level, relationship type, temporal process, method, or estimand to an established finding.
- **qualifies**: the present result identifies a limitation, temporal contingency, asymmetry, or scope restriction in a prior claim.
- **contrasts with**: a comparable study reports a substantively opposing pattern; state the context or estimand difference.
- **contextualizes**: the source documents an industry, technological, policy, or institutional backdrop that makes an interpretation plausible.

Do not use `contrasts with` when studies differ so much that no meaningful comparison exists. Do not use `extends` merely because the focal setting is new. Do not let `contextualizes` confirm a coefficient mechanism, causal driver, or theoretical pathway.

### 6.2 Validate contribution implications

For each Contribution Seed, assign a novelty verdict:

- **supported**: evidence shows a traceable and non-duplicative theoretical move.
- **duplicate**: the proposed move is already made by the closest literature; merge or drop it.
- **overstated**: the result supports a narrower move than proposed; revise the seed.
- **insufficient evidence**: the corpus cannot establish the baseline or novelty; do not promote it.

A target-journal citation does not itself create target-journal contribution. Its claim must fit the argument, and the contribution must change what engineering-management scholars understand about the mechanism, temporal boundary, relationship type, or management of technological interdependence.

Treat target-journal identity as internal source-selection and claim-fit metadata, not as manuscript rhetoric. In prose, describe prior work by its substantive field, topic, or mechanism (for example, `engineering management research`, `AEC innovation research`, or `research on temporal proximity effects`), never as `IEEE TEM research`, `[Journal name] research`, or similar journal-name signaling. Name a journal only when journal provenance is itself substantively relevant, such as in a bibliometric or journal-comparison analysis.

### 6.3 Show the Literature Dialogue Card

```text
📚 RQ{i} Literature Dialogue Card
| Argument | Candidate literature | Actual claim | Relation | Same/different boundary | Proposed use |
|---|---|---|---|---|---|
| A1 | key(s) | ... | consistent / extends / qualifies / contrasts / contextualizes | ... | ... |

| Seed | Contribution implication | Novelty verdict | Required revision |
|---|---|---|---|
| S1 | ... | supported / duplicate / overstated / insufficient | ... |

- Unresolved claim-fit risks: ...
- Target-journal fit (internal only): exact claim fit / none
- Local-corpus coverage: sufficient / argument must narrow / external search proposed

Please confirm the literature relationships before prose drafting.
```

## 7. Claim ladder and theory grounding

### 7.0 Fix the theory hierarchy before drafting

Build a three-level theory-role map from the manuscript Introduction and Literature Review:

1. **Focal theoretical lens**: the theory explicitly designated as the manuscript's
   organizing lens.
2. **Adjacent theoretical or empirical literature**: work that sharpens a selection,
   coordination, learning, or network argument without becoming another organizing lens.
3. **Contextual evidence**: industry or period evidence used only to situate a possible
   interpretation.

Every cited source must retain its confirmed level in the prose. Conceptual compatibility
does not establish theoretical descent: do not call adjacent work an extension, component,
or operationalization of the focal theory unless the cited source and Literature Review
explicitly establish that relation. Do not introduce a named theory in Discussion if it has
not been positioned in the Literature Review; return to the Literature Review for a new
theoretical decision. Do not turn one setting-specific paper into an invented field label
such as `construction-alliance research`; describe the actual actors, setting, or substantive
research topic instead.

### 7.1 Apply the claim ladder

Assign every sentence to one of four levels:

1. **Observed finding**: state directly from Results; do not hedge verified results with `may`.
2. **Theory-based meaning**: explain what a modeled structure or attribute can represent through theory. Use `can`, `suggests`, `provides a basis for`, or `is consistent with`.
3. **Contextual explanation**: introduce an untested industry or institutional mechanism with one umbrella qualifier such as `One possible interpretation is that ...`. Do not switch later to `caused`, `was driven by`, or `explains why`.
4. **Literature dialogue**: state the confirmed relationship and the exact commonality or difference.

Do not equate a network statistic with an unmeasured theoretical construct. Degree is not resource access, closure is not governance quality, and a tie is not relational rent. Explain the pathway through which the observable pattern could matter.

### 7.2 Ground theory in the study context

Build a short context mechanism map:

- actors and legally relevant boundaries;
- differentiated capabilities or resources;
- technical, organizational, or knowledge interfaces;
- coordination tasks;
- partner-search or activity decisions represented by the model.

Run the substitution test:

> If the industry label were replaced with another industry, would the paragraph remain essentially unchanged?

If yes, rewrite it with context-specific actors and interfaces. Do not add jargon merely to pass the test.

Under the relational view specifically:

- Explain network position as conditioning which relationships and complementary capabilities may be reachable.
- Explain relational arrangements as shaping whether distributed capabilities can be coordinated and combined.
- State that position itself is not relational rent.
- Use changing capability and coordination requirements to explain why different relational positions may have different temporal relevance.
- Do not claim that the relational view predicts a transition-specific coefficient unless the theory and hypothesis actually did so.

Align contextual explanations with the actual observation period. Prefer evidence overlapping the relevant transition and setting. If only cross-industry or global evidence exists, present it as a comparison rather than proof of the focal mechanism.

## 8. Multi-effect integration and drafting

### 8.1 Build an integration map

When one RQ contains multiple effects, complete this map before drafting:

| Field | Required content |
|---|---|
| Essential trajectory | What happened to each effect across periods or categories? |
| Joint contrast | What is theoretically informative about coexistence or divergence? |
| Theoretical role | What relational, behavioral, or organizational pathway can each effect represent? |
| Shared context | Is one evidenced development relevant to both effects? |
| Differential relevance | Why might the context matter differently for the two roles? |
| Prohibited inference | What causal, substitutive, performance, or generative conclusion was not tested? |
| Integrated punchline | What is learned only by considering the effects together? |

Prefer one shared interpretive spine when it genuinely fits. Preserve distinct theoretical roles under that spine. Do not force a common explanation when effects address unrelated processes.

For divergent temporal effects, avoid claiming a handoff, replacement, or stronger mechanism unless a direct comparison on a meaningful common scale was estimated. Describe different temporal profiles instead.

### 8.2 Use functional paragraphs

For related multiple effects, use:

1. **Answer** (45--80 words): essential results and joint contrast.
2. **Effect A** (100--150 words): theory role, industry grounding, direct literature dialogue, and one possible contextual interpretation if needed.
3. **Effect B** (100--150 words): distinct theory role under the shared spine, literature dialogue, and connection to the contrast.
4. **Punchline** (45--80 words): integrated theoretical meaning and, if validated, a restrained contribution seed.

For a single effect, use three paragraphs: answer; context-grounded theoretical meaning and literature dialogue; integrated implication.

Balance paragraphs by function. Do not let the answer or punchline become longer than either mechanism paragraph. Do not repeat robustness tests unless they change the interpretation.

## 9. Contribution Ledger handoff

After the user confirms the RQ prose, approves the RQ-scoped Write Gate, and the written block passes citation, compilation, and Discussion audit checks, place only `supported` seeds into the session-level validated ledger:

| Seed ID | RQ evidence | Focal theory baseline | Adjacent literature role | Contextual evidence role | Conceptual move | Literature support | Context-to-theory abstraction | Target-journal relevance | Claim boundary |
|---|---|---|---|---|---|---|---|---|---|

Merge `duplicate` seeds into an existing seed where appropriate. Revise and revalidate `overstated` seeds before entry. Keep `insufficient evidence` seeds out of the ledger.

The ledger is an input to SKILL.md Section 3.4, not a finished Theoretical implications outline. After all RQs:

1. remove weak or non-theoretical seeds;
2. cluster by theoretical issue rather than RQ number;
3. distinguish result, contextual explanation, and conceptual move;
4. merge overlaps and select the strongest two or three;
5. show a Contribution Synthesis Card for user confirmation;
6. draft each contribution as baseline → evidence → conceptual move → scope/boundary → target-journal relevance.

No theoretical contribution may appear if it cannot be traced to a validated seed. A possible contextual mechanism must not be promoted to an estimated moderator, identified boundary condition, or causal explanation.

If the validated ledger is empty, stop and return to the relevant Interpretive Arguments and Literature Dialogue Cards. Do not create contributions independently. When candidate contributions overlap or their novelty remains ambiguous, run one read-only cross-RQ Claim-Fit & Contribution Auditor before showing the Contribution Synthesis Card.

## 10. Theory, terminology, pre-display language gates, and anti-patterns

### 10.1 Run semantic gates before showing prose

- **Result-compression gate**: answer the RQ without repeating Results machinery.
- **Substantive-first readability gate**: require the direct answer to expose actor/unit,
  outcome/process, direction, and comparator after one reading by a substantive-field reader who
  does not know the estimation software. Model-internal syntax may follow as a compact qualifier,
  but cannot carry the answer. Reverse-map the sentence to the estimand and preserve conditioning,
  time, scope, direction, and contrast before freezing the semantic source.
- **Priority gate**: give the deepest discussion to unsupported, heterogeneous, divergent, or punchline-defining findings.
- **Integration gate**: make multiple effects one argument while preserving distinct theoretical roles.
- **Claim-strength gate**: separate observed finding, theory-based meaning, contextual interpretation, and literature dialogue.
- **Theory-hierarchy gate**: keep the focal lens, adjacent literature, and contextual evidence
  in their confirmed roles; block new theory labels and invented field names.
- **Canonical-terminology gate**: compare every theory label, actor/unit, construct,
  effect/estimand, period, and context term with its authoritative manuscript wording.
- **Domain-grounding gate**: name actors, capabilities, interfaces, and decisions; pass the industry-substitution test.
- **Citation-role gate**: require exact support and an explicit relation for every citation group.
- **Contribution-seed gate**: trace every seed to confirmed evidence and a supported novelty verdict.
- **Punchline gate**: end above Results without becoming an ungrounded contribution claim.
- **Economy gate**: delete method repetition, robustness summaries, adjacent theory duplication, and serial caveats.

### 10.2 Build and enforce the canonical terminology contract

Before drafting, build an in-memory RQ-scoped contract. Use this authority order:

1. wording explicitly approved by the user in the active RQ workflow;
2. the term table in `structure/0_global/technical_map.md` section 2 (preferred term, definition,
   near-synonyms that must not be mixed);
3. formal definitions and theoretical roles in Introduction/Literature Review;
4. conclusion-target and result meaning in the technical sections;
5. otherwise consistent local usage.

If the term table and the manuscript disagree in a meaning-bearing way, stop and ask the user;
route a technical-section conflict to `/technical`. Do not resolve it by polishing.

For each controlled concept record the preferred term, allowed abbreviation, construct
boundary, terms that must remain distinct, and prohibited ambiguous synonyms. At minimum
cover the focal theory, adjacent-literature labels, actor and legal unit, organizational
attributes, modeled effects, waves/transitions, and causal versus conditional language.
Terminology alignment means conceptual consistency, not mechanical repetition. A new synonym
is allowed only when it is nontechnical, cannot change the construct, and does not create a
second label for an estimand. A meaning-bearing conflict is substantive and returns to the
relevant confirmation card; do not let a language polisher decide it.

Separate semantic authority from surface wording. Methodology and Results control the estimand,
conditioning, time, direction, comparison, and inference boundary; they do not require Discussion
to copy model-internal subjects or predicates. Preserve stable construct names such as the actor,
outcome, partner category, and conditional-tendency boundary, while translating model mechanics
into reader-facing substantive syntax.

### 10.3 Run the embedded pre-display language gate

After all semantic, theory-hierarchy, terminology, citation-role, and contribution-seed gates
pass, freeze the draft as the semantic source. Invoke `/polish` in embedded mode with
`POLISH_EMBEDDED_CANDIDATE_ONLY`, passing the source, canonical terminology contract,
user-protected spans, target journal, and section context. Require `EMBEDDED-PASS`; the call
may not locate or edit project files, compile, change paragraph functions, revisit literature
relations, or create a contribution.

If `/polish` returns `FAIL-BLOCKED: SOURCE-OPAQUE`, return to the substantive-first readability
gate and rewrite the semantic source. Do not ask `/polish` to make the meaning-bearing translation
or treat an unchanged opaque candidate as a language pass.

Then run one regression-only claim lock on the polished candidate. Check result direction,
statistical-support meaning, temporal qualification, modality/causality, contextual hedge,
construct boundaries, citation attachment, paragraph count, and target word range. Restore
any drift to the semantic source and rerun the bounded embedded gate at most once. A second
substantive drift is `FAIL-BLOCKED` and the candidate may not be displayed or written. Only a candidate that
passes semantic audit, theory hierarchy, terminology alignment, language audit, fidelity,
and the claim lock may be shown as final RQ prose.

After the user confirms that prose and approves the RQ-scoped Write Gate, write only the
approved block, read it back, and require exact equality with the approved polished candidate
before citation regression, compilation, and `audit_discussion.py`.

### 10.4 Reject these anti-patterns

- **Result dump**: coefficients, p-values, robustness tests, and model labels dominate the opening.
- **Estimand transcription**: a model-internal object such as `candidate states` or
  `conditional attractiveness` carries the substantive answer even though an actor--outcome--
  direction--comparator statement is available.
- **Explanation before answer**: theory or industry context appears before the user confirms what the RQ result is.
- **Citation-led argument**: an argument exists because a convenient paper was found.
- **Parallel generic stories**: each effect receives an explanation that could fit any industry.
- **Theory naming**: the theory is cited but does not connect the effects or decisions.
- **Theory promotion**: adjacent partner-selection or context literature is presented as part
  of the focal theory, or a new named theory appears only in Discussion.
- **Invented field label**: a setting-specific source is generalized into an unofficial field
  name such as `construction-alliance research`.
- **Terminology drift**: an established construct or estimand is renamed for stylistic
  variety, thereby changing or blurring its meaning.
- **Context as cause**: recent industry development is presented as the identified driver of a coefficient change.
- **Context as coefficient proof**: industry evidence is used as direct confirmation of the estimated mechanism.
- **Boundary pile-up**: several sentences list what the model did not measure instead of calibrating the positive claim.
- **Contribution inflation**: an industry observation or expected finding is labeled a theoretical contribution.
- **Target-journal quota filling**: a weakly matched journal article displaces a stronger source.
- **Target-journal name-dropping**: manuscript prose labels evidence as `IEEE TEM research` or `[Journal] studies` instead of naming the substantive research field, topic, or mechanism.
- **Structural overreach**: degree is interpreted as preferential attachment or scale-free generation without the corresponding estimand.
- **False handoff**: effects on different scales are described as one replacing the other.
- **Method repetition**: sample boundaries and model design are restated without serving interpretation.

### 10.5 Transferable example

For an RQ where Effect A weakens and Effect B persists:

1. Confirm both trajectories and identify their divergence as P1.
2. Define each effect as a distinct theoretical pathway under one shared question.
3. Ask whether one period-aligned contextual development could change the usefulness of the two pathways differently.
4. Present that development as a possible interpretation, not an identified cause.
5. Search the manuscript LR and local corpus for direct comparisons and contextual evidence separately.
6. Confirm whether the present result is consistent with, extends, or qualifies each closest study.
7. Form a seed only if the combined result changes a theoretical expectation beyond the focal setting.
8. Conclude that the mechanisms have different temporal profiles; do not claim substitution or compare coefficient magnitudes across scales.
