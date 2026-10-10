# TikZ Journal-Minimal Monochrome Profile

Use this profile by default for academic structure diagrams, methodology flows, conceptual frameworks, and model-mechanism figures.

## 1. Visual stance

- White background.
- Near-black text and primary structure.
- No persistent accent color by default.
- Use near-black, middle gray, light rules, and optional pale-gray wash only.
- Ordinary nodes remain white. Use `wash` only for fixed, contextual, inactive, or deliberately de-emphasized objects.
- Emphasize focal content with position, whitespace, border weight, solid/dashed frame semantics, or pale-gray wash before considering color.
- A single non-gray accent is an exception that requires a written reason showing that line type, shape, position, and direct labeling are insufficient.
- Alignment and whitespace carry grouping. Avoid decorative panel boxes, large tinted bands, shadows, gradients, 3D, clip art, and ornamental icons.
- Every visible element must encode information.

## 2. Default design tokens

```latex
\definecolor{ink}{HTML}{25272A}
\definecolor{muted}{HTML}{6F747A}
\definecolor{rule}{HTML}{B9BEC4}
\definecolor{wash}{HTML}{F3F5F7}
```

Rules:

- Core, observed, or directly modeled box: white fill, solid `ink` border.
- Auxiliary, derived, copied, intermediate, or contextual box: white fill, dashed `muted` border.
- Fixed, inactive, or de-emphasized box: `wash` fill with solid `rule` border.
- Focal box: solid `ink` border with slightly greater weight, central placement, additional whitespace, or `wash` fill.
- Primary arrow: `ink`, solid.
- Copy, lag, or derived relation: `muted`, dashed.
- Secondary dependency or influence: `muted`, dotted, when distinct from copy/lag.
- A line type may carry only one meaning within a figure. Directly label uncommon relations.
- Do not add hue to distinguish layers, stages, periods, node types, or focal boxes when grayscale encodings suffice.

## 3. Typography at final size

- Design for the actual manuscript width before coding.
- Generic journal default: body labels 7--8 pt, annotations at least 6.5--7 pt, panel labels 8 pt bold.
- Use Times New Roman consistently for all figure labels. For TikZ, load the installed font with XeLaTeX and `fontspec`; pair it with `texgyretermes-math.otf` (TeX Gyre Termes Math) for mathematical notation.
- Use sentence case. Avoid title case inside every box.
- Bold only panel labels, short group headings, and the unique focal component.
- Put detailed definitions in the caption when keeping them inside the figure would reduce readability.
- Check the embedded manuscript page, not only the standalone PDF.

## 4. Line and shape standards

At final size:

| Element | Default |
|---|---:|
| Box border | 0.5--0.6 pt |
| Primary arrow | about 0.75 pt |
| Secondary/dashed arrow | 0.5--0.6 pt |
| Group separator | 0.4--0.5 pt |
| Emphasis border | no more than 0.9 pt |
| Corner radius | 0--2 pt; 3 pt maximum |

Prefer simple rectangles, circles, and familiar method-specific shapes. Shape changes must carry meaning.

## 5. Alignment contract

Before adding nodes, write a coordinate ledger in comments:

```text
target width = ... mm
columns x = ...
rows y = ...
standard node width/height = ...
horizontal gutter = ...
vertical gutter = ...
arrow routing lanes = ...
```

Requirements:

- Repeated columns reuse exactly the same x coordinates.
- Repeated rows reuse exactly the same y coordinates.
- Same-role boxes share width, height, padding, font size, and corner radius.
- Panel titles share a baseline and left edge.
- Connectors use reserved gutters and never pass through text or boxes.
- Labels sit consistently above, below, or beside equivalent arrows.
- During development, draw light alignment guides; remove them before final export unless they encode time or correspondence.

Do not repair poor alignment with extra containers, gray bands, or color.

## 6. Layout hierarchy

Choose hierarchy from the reader task:

- **Sequential pipeline**: one main axis, restrained branches.
- **Aligned longitudinal design**: repeated time columns plus labeled transition intervals.
- **Layered mechanism**: rows for genuinely different data/model objects, with only meaningful inter-layer links.
- **Schematic-led composite**: one dominant overview panel and one or two smaller explanatory panels.
- **Comparison**: shared input and aligned alternatives; identical components remain visually identical.

Panels do not need equal size. The scientifically primary panel should receive the most space.

## 7. Color exception test

The default answer is no color. Before adding any non-gray color, answer:

1. What exact semantic meaning does it encode?
2. Is the same meaning used everywhere in this figure and project?
3. Could line type, shape, direct label, or position encode it more cleanly?
4. Does the figure remain interpretable in grayscale?

Delete the color unless all four answers are satisfactory. Aesthetic preference, benchmark imitation, or a desire to make the figure look more complex is not sufficient.

## 8. Final-size QA

1. Compile the standalone PDF.
2. Render and inspect it at the target physical width.
3. Embed it in the manuscript and render the actual page.
4. Inspect at 100% and 50% zoom.
5. Create a grayscale preview and confirm all semantic distinctions remain.
6. Check panel alignment, node alignment, arrow routing, clipped text, natural-language wrapping, and math baselines.
7. Check that the caption carries secondary explanation instead of duplicating a large in-figure legend.

The figure fails if it is clean only when enlarged, or if color is necessary to infer structure.

## 9. Standards basis

This profile synthesizes, rather than copies, the following sources:

- Nature figure preparation: final physical widths, consistent lettering, vector artwork, panel labeling, and final-size line weights. This profile applies the project's Times New Roman requirement while retaining those consistency principles.
  `https://www.nature.com/nature/for-authors/final-submission`
- Nature research figure guide: alignment, accessibility, minimal decoration, and final-size panel construction.
  `https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/`
- SNL-UCSB paper-writing-skill: figure spec/generate/critique workflow, venue sizing, data-ink ratio, grayscale checks, and TikZ archetype skeletons.
  `https://github.com/SNL-UCSB/paper-writing-skill`
- K-Dense scientific schematic guidance: final-size typography, minimum line weights, vector output, grayscale, and color-accessibility checks.
  `https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/scientific-skills/scientific-schematics`
- Nature-skills design theory: schematic-led hierarchy, restrained palette families, direct labels, alignment, and whitespace over decorative panel boxes.
  `https://github.com/Yuan1z0825/nature-skills/tree/main/skills/nature-figure`
