# Method- and Benchmark-Driven Figure Design

Use this reference for every new academic figure and every major redesign.

## 1. Evidence hierarchy

Apply evidence in this order:

1. The manuscript's claim, research question, method, and actual data objects.
2. Benchmark papers using the same method and serving the same figure function.
3. Official target-journal production constraints.
4. Cross-figure semantics already established in the project.
5. The default visual profile.

Style never overrides method semantics. A polished figure that implies a false causal direction, feedback loop, temporal transition, network layer, or variable role is a failed figure.

## 2. Benchmark selection

Select 2--5 reference figures using the following priority:

1. Same method + same figure role + same discipline.
2. Same method + same figure role in an adjacent discipline.
3. Same figure role in the target journal or a close peer journal.
4. General visual references from Eagle only after academic benchmarks are exhausted.

Prefer figures that are recent, actually published, readable at article scale, and accompanied by enough methods text to interpret their visual grammar.

### What to extract

Do not extract only a palette. Record:

- Figure role and reader task.
- Main reading direction.
- Panel hierarchy and relative visual weight.
- Grid, columns, rows, baselines, and repeated coordinates.
- Shape vocabulary and what each shape means.
- Arrow and line semantics, including temporal versus causal links.
- How observed data, modeled processes, latent quantities, controls, and outputs are distinguished.
- Label density, direct labeling, legend strategy, and caption division of labor.
- Which complexity is method-essential and which is decoration.

### Benchmark design memo

Before coding, prepare this compact memo:

```text
Figure role:
Reader must understand:
Method semantics that must be visible:
Relationships that must NOT be implied:
Target width and journal constraints:

Benchmarks:
- Paper / figure / why comparable

Borrow:
- layout
- visual grammar
- alignment
- information hierarchy

Reject:
- feature / why it does not fit this study

Layout contract:
- rows
- columns
- fixed coordinates
- primary reading path

Encoding contract:
- shape meanings
- line meanings
- solid versus dashed frame meanings
- color exception and why grayscale is insufficient (default: none)
- direct labels / legend
```

## 3. Method-aware visual grammar

### Longitudinal network models and SAOM

- Separate observed waves from estimated inter-wave transitions.
- Preserve one common actor set when that is the design; do not visually add or remove actors without a composition-change meaning.
- Distinguish the dependent network, actor behavior, dyadic covariates, and actor covariates.
- Show whether a covariate is fixed, varying, lagged, copied, or endogenous.
- Draw selection and influence links asymmetrically when the model is asymmetric.
- Do not draw a reciprocal co-evolution loop unless both directions are endogenously estimated.
- Network snapshots should sit on a shared timeline or coordinate system; arrows between snapshots must be labeled as transitions, not generic data processing.

### Structural equation and latent-variable models

- Use distinct, consistent shapes for latent and observed variables.
- Keep causal or directional paths visually different from covariance paths.
- Align measurement blocks and structural blocks separately.
- Show residuals only when needed for the reader task; avoid a full software-output diagram when a conceptual path model is sufficient.

### Causal inference, DAGs, DID, and event studies

- A DAG encodes assumptions, not an analysis pipeline.
- Distinguish treatment assignment, observed outcomes, controls, mediators, colliders, and unobserved confounding using shape or line redundancy.
- DID figures should foreground treatment timing, comparison groups, and identifying contrast rather than generic process boxes.
- Never use decorative arrows that create additional causal paths.

### QCA and configurational methods

- Emphasize conditions, calibration, truth-table logic, configurations, and outcomes.
- Use set or matrix logic where it improves interpretation; do not force a linear causal pipeline.
- Preserve conjunction, equifinality, and asymmetry visually.

### Machine-learning and computational pipelines

- Separate data transformation, model components, training, inference, and evaluation.
- Annotate tensor/data forms only when they answer the reader task.
- Distinguish offline/online or train/test paths with grouping and line type before adding color.
- Emphasize the paper's novel component without making standard components visually disappear.

### Qualitative process and case research

- Use temporal phases, evidence sources, coding/analysis stages, or mechanism episodes according to the actual design.
- Avoid pseudo-causal arrows when the study provides process evidence rather than causal identification.
- Preserve iteration when coding or theory development is genuinely iterative.

### Data construction and sampling

- Separate filtering, entity resolution, variable construction, and model input.
- Counts belong near the step that changes them.
- Repeated waves or cohorts should share a locked grid.
- A sample pipeline must not be confused with a model mechanism; use panels or whitespace to separate them.

## 4. Borrowing without imitation

Borrow the benchmark's solution to a shared reader problem, not its surface decoration. A benchmark may justify:

- time-aligned columns;
- a dominant overview panel plus a smaller mechanism inset;
- direct vertical alignment between linked objects;
- separate line types for selection and influence;
- one shared legend or direct labels.

It does not justify copying colors, icons, arbitrary layer counts, or causal arrows whose meanings do not exist in the current study.

## 5. Failure conditions

Return to the design memo when any of the following occurs:

- The figure needs prose to explain what an unlabeled arrow means.
- Color is carrying a distinction that shape, position, or line type should carry.
- Repeated nodes drift off a shared row or column.
- A panel is visually dominant but scientifically secondary.
- The figure resembles a benchmark but misstates the current method.
- The figure is understandable only in a zoomed standalone PDF.

## 6. Required closeout

Before delivery, verify:

- Method semantics: PASS.
- Benchmark visual grammar: PASS or reasoned deviation.
- Final-size typography and line weight: PASS.
- Alignment and routing: PASS.
- Grayscale and color-accessibility: PASS.
- Manuscript placement, caption, and surrounding prose: PASS.
