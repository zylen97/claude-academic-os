# Literature Landscape Table Preference

This protocol captures the preferred style for literature-review landscape tables across research-paper projects. Use it when drafting or revising Introduction, Literature Review, Appendix, Supplemental Materials, or any table that summarizes prior research.

## Core Principle

Literature landscape tables should be problem-oriented rather than method-oriented.

The table should show how prior research addresses different parts of the practical or theoretical problem, what each stream has already established, and why an integrated gap remains. Methods can be reported for transparency, but they should not become the main organizing logic unless the paper itself is explicitly a methods paper.

## Preferred Placement

Prefer an appendix or supplemental-materials placement when the table is broad and evidence-mapping oriented.

- Main text: use a compact paragraph to introduce the literature streams and their shared limitation.
- Appendix / Supplemental Materials: provide the full landscape table with related studies and representative studies.
- Main-text table: use only when the table is short, central, and needed for immediate reader comprehension.

## Preferred Structure

Use `3 +/- 1` substantive research streams. Name each stream by the problem it addresses, not by the method it uses.

For each stream:

1. Define the substantive research stream.
2. List the broader pool of related studies in a compact cell.
3. Select representative studies from that pool.
4. Explain the representative studies by research focus, context, and contribution.
5. Identify the remaining boundary in the main text or table note, not through a repetitive "gap" cell on every row unless the manuscript needs that contrast.

## Preferred Columns

For appendix-style evidence maps, use this default column set:

| Column | Purpose |
|:---|:---|
| `Research stream` or `Perspective` | Names the substantive literature stream. |
| `Related studies` | Lists the broader pool of studies belonging to the stream. |
| `Representative study` | Selects the most important studies for detailed explanation. |
| `Research focus` | States the concrete problem or mechanism examined by the study. |
| `Empirical / theoretical context` | Locates the setting, level, data, or theoretical domain. |
| `Main purpose or contribution` | Explains what the study establishes for the present paper's problem. |

Optional columns:

- `Methodology or framework`: include only when method transparency helps the reader.
- `Remaining boundary`: include only when the table must make the gap explicit; avoid turning every row into formulaic criticism.
- `Relevance to this study`: useful for revision responses or very broad interdisciplinary tables.

## Main-Text Companion Paragraph

The main text should summarize the table without repeating it row by row. A preferred pattern is:

1. "Prior studies relevant to the practical problem span three streams."
2. One sentence for Stream 1: what it has shown.
3. One sentence for Stream 2: what it has examined.
4. One sentence for Stream 3: what it has explained.
5. A synthesis sentence: what these streams collectively establish.
6. A limitation sentence: what remains unexplained.
7. A transition sentence: how the present study's general aim follows.

Example skeleton:

```text
Prior studies relevant to this practical problem span three streams (Appendix A). The first stream ... The second stream ... The third stream ... Taken together, these studies show that ... However, they have not yet explained ... This study therefore aims to ...
```

## Study Selection Rules

- The `Related studies` cell should be broad enough to show the literature landscape.
- The `Representative study` rows should be selective, high-quality, and explanatory.
- Do not turn the table into a full bibliography dump.
- Prefer recent, top-field, or directly comparable studies as representative studies.
- Include non-dominant methods when they address the substantive problem.
- Exclude generic theory papers from the table unless they directly structure the literature landscape; use them in main-text theory development instead.
- If a study is important background but not part of the focal empirical landscape, cite it in the text rather than forcing it into the table.

## Method Column Rules

- Do not classify streams by `SNA`, `SAOM`, `SEM`, `QAP`, `case study`, or other methods when the research gap is substantive.
- Do not bold a method unless method comparison is the point of the paper.
- A method column may remain as a secondary descriptor.
- The table's interpretive force should come from `research focus`, `context`, and `contribution`, not from method labels.

## Anti-Patterns

Avoid:

- A table whose implicit argument is "prior studies used method X, while we use method Y."
- Rows that list papers without explaining why they matter.
- Panels named after methods when the manuscript's practical problem is substantive.
- Repeating the same generic gap in every row.
- Hiding relevant non-SNA/non-SAOM studies because they do not match the focal method.
- Putting every citation from the literature pool into the table.

## Recommended LaTeX Pattern

For broad literature landscapes, use an appendix or supplemental table with grouped rows:

```latex
\begin{table}[!htbp]
\centering
\caption{Prior studies related to ...}
\label{tab:app_literature_landscape}
\small
\begin{threeparttable}
\begin{adjustbox}{max width=\linewidth,max totalheight=.85\textheight,center}
\begin{tabular}{p{2.8cm}p{4.2cm}p{2.8cm}p{3.4cm}p{3.2cm}p{5.0cm}}
\toprule
\textbf{Research stream} & \textbf{Related studies} & \textbf{Representative study} & \textbf{Research focus} & \textbf{Context} & \textbf{Main purpose or contribution} \\
\midrule
...
\bottomrule
\end{tabular}
\end{adjustbox}
\begin{tablenotes}[flushleft]
\small
\item \textit{Note}: The table maps the literature landscape behind the present study. The first column groups prior work into substantive streams; the second column lists related studies in each stream; the remaining columns summarize representative studies.
\end{tablenotes}
\end{threeparttable}
\end{table}
```

For very long tables, use `longtable` in supplemental materials.

## Reuse Checklist

Before finalizing a literature landscape table, check:

- Streams are named by substantive problems.
- Each stream has a related-study pool.
- Representative studies are chosen from the pool.
- Non-method evidence relevant to the practical problem is not omitted.
- Method labels are secondary.
- The main text synthesizes the streams and states a general gap.
- Citation keys used in the table exist in the project bibliography or are synchronized from the citation pool.
