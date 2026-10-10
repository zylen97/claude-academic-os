---
description: "定稿收尾四步：Conclusion → Abstract → Cover Letter（只以 manuscript.tex 为事实来源，投稿元数据先确认）→ 脚手架归档。开始前做日期检查（规格 §4.6），逐块交互确认，language-polisher 润色。"
---

# Finalize — 定稿收尾

> 规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（冲突以规格为准）。正文精简规则：`~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。
> 子 agent：可以在需要时使用子 agent（定义在 `~/.claude/agents/`），并在执行前告诉用户将派出哪些。
> Git：本技能不自动 commit / push；每个 Phase 结束时给出建议的提交范围与提交信息，用户确认后才执行。

论文主体完成后的收尾流程，按固定顺序完成四个阶段：

```
Phase 1: Conclusion → Phase 2: Abstract → Phase 3: Cover Letter → Phase 4: 脚手架归档
```

Phase 1–3 为写作阶段，逐块交互确认，前一阶段的产出作为后一阶段的输入。Phase 1–3 的 reader-facing prose 遵循 `MANUSCRIPT-ECONOMY.md`：Conclusion、Abstract、Cover Letter 只浓缩已建立的 claim 与必要边界，不重新汇总全文 caveats，不预演审稿答辩。Phase 4 把施工脚手架移入项目 `_archive/`，不硬删。

**输入** `$ARGUMENTS`：可选，指定从哪个阶段开始：
- `/finalize` — 从 Phase 1 开始，完整走四步
- `/finalize abstract` — 从 Phase 2 开始（Conclusion 已写好）
- `/finalize cover-letter` — 从 Phase 3 开始
- `/finalize cleanup` — 只做 Phase 4

---

## 步骤 0：上下文加载

### 0.1 读取项目配置

读取项目合同 `CLAUDE.md`，提取：
- `{MAIN_TEX}`（主文件）、`{BIB_FILE}`、`{TARGET_JOURNAL}`、`{PUBLISHER}`
- 方法类型与"方法 profile"字段
- `## 技术章节` 表（`\section` 标题 → 角色 method / results / simulation）
- 作者信息（如有）

缺少 `{TARGET_JOURNAL}` → 停止，提示补全项目合同。

### 0.2 日期检查（`cleanup` 入口跳过）

**日期检查（规格 §4.6，取代哈希链；只提醒，不阻断）**

读取四个时刻（都在 `structure/0_global/` 下）：

| 记号 | 来源 |
|---|---|
| P | `analysis_plan.md` 第 7 节"变更记录"表中最晚的时刻（表为空 → 无） |
| R | `results_register.md` 的 `发布:` 行第一个日期（register 发布日期） |
| M | `technical_map.md` 的 `依据: results_register 发布 …` 中的时刻 |
| T | `technical_map.md` 的 `技术正文完成:` 日期（technical Tex 结束时写入） |

逐条判定（"晚于" = 按时刻严格晚于，规则见规格 §4.6）：

| # | 条件 | 含义 | 回流 |
|---|---|---|---|
| D0 | 三个文件都不存在 | 遗留项目，未走 analysis / technical 流程 | 只报告"跳过日期检查"，后续检查照常 |
| D0' | 只存在其中一部分 | 流程未走完 | 缺计划或 register → `/analysis`；缺 map → `/technical` |
| D1 | 计划状态行不是 `approved` | 设计未批准 | `/analysis` Plan |
| D2 | R 为空 | register 未发布 | `/analysis` Release |
| D3 | T 为空 | 技术正文未完成 | `/technical` |
| D4 | P 晚于 T | 技术正文完成后设计又被改动 | 按这些变更行的"影响"列决定（见下） |
| D5 | R 晚于 T | 技术正文完成后 register 重新发布 | `/technical` 修复受影响段落，并重写完成日期 |
| D6 | M ≠ R（两者都有） | technical_map 依据的不是当前 register | `/technical` Map 按当前 register 更新 |
| D7 | P 晚于 R，且该变更行"影响"列没有明确写"不影响 register" | 设计改了，register 还没跟进 | `/analysis` Run → Release |

D4 / D7 的回流范围按变更行"影响"列判断：

- 涉及 RQ、模型族、主设定、数据边界或核心构念（设计层）→ `/idea-refine` → `/analysis` Plan 重新批准 → Run → Release → `/technical` 修复；
- 计划第 1、3、4、5 节的其他改动 → `/analysis` Run → Release（重新发布 register）→ `/technical` 修复；
- "影响"列明确写"不影响 register / technical"（只影响 narrative）→ 只提醒复核 narrative 对应部分；
- "影响"列为空或写不清 → 按第二种（analysis → technical）提醒。

比较的一方是只写了日期的旧条目、且与另一方同一天时，不判为晚于，但注明"旧条目只有日期，无法区分先后，请确认该变更已反映在技术正文中"。

输出格式：先列出触发的条目（编号、涉及的日期、对应变更行原文），再给出**一条合并后的回流路线**（去重并按 idea-refine → analysis Plan → analysis Run/Release → technical → narrative 的顺序排列），最后注明"完成回流后重新运行本技能"。没有触发任何条目时输出"日期检查：通过（P=…，R=…，M=…，T=…）"。日期只用于判断先后，不作为任何正文内容的来源。

有任何触发条目时，展示条目与回流路线，用 AskUserQuestion 询问：**1** = 先回流（停止 finalize）/ **2** = 知悉，继续 finalize。选 2 时把触发条目写进最终完成提示，提醒投稿前处理。`cover-letter` 入口同样执行本检查，但日期只用于提醒，Cover Letter 的事实来源规则不变（见 Phase 3）。

### 0.3 读取全文上下文

- 读取 `{MAIN_TEX}` 全文 → `{MANUSCRIPT_CONTENT}`。
- `cover-letter` 入口：`{MANUSCRIPT_CONTENT}` 是所有论文事实与主张的**唯一来源**。不读取、不使用 `idea.md`、`analysis_plan.md`、`results_register.md`、`technical_map.md`、`structure/3_analysis/` 下的推导、`data/` 下的结果、旧报告或参考文献来补充、改写或覆盖正文。正文未明确提供的论文事实一律省略；用户确认不能把正文外信息变成可用的论文事实。用户认为正文遗漏了必要内容时，先在相应写作流程中修改 manuscript，再重新进入 Phase 3。
- 其他入口：
  - 读取 `structure/0_global/idea.md` → `{IDEA_CONTEXT}`（RQ、Gap、贡献点、方法框架）；
  - 按 `## 技术章节` 的角色从 `{MANUSCRIPT_CONTENT}` 提取：method → `{METHOD_CONTEXT}`，results → `{RESULTS_CONTEXT}`，simulation → `{SIMULATION_CONTEXT}`（可选）。**不按字面标题匹配**；项目合同没有 `## 技术章节` 时，列出 manuscript 的全部 `\section` 标题，请用户指出各自角色（只用于本次运行，不写回合同）；
  - Discussion 章节 → `{DISCUSSION_CONTEXT}`（标题含 "Discussion" 且唯一时直接使用，否则请用户指定）；
  - `results_register.md` 存在时读取，只用于**核对** Conclusion / Abstract 中的数字、空结果、未通过的检验与解读边界是否与正文和 register 一致，不作为新增内容的来源。

**空内容检测**：非 `cover-letter` 入口若 `{RESULTS_CONTEXT}` 为空或仍为 TODO → 停止，提示先完成论文主体（`/technical`）。`cover-letter` 入口在 Phase 3.1 用新读取的正文执行专用检查。

### 0.4 确定起始阶段

- 空 → Phase 1
- `abstract` → Phase 2，检查 manuscript.tex 中 Conclusion 是否已有非 TODO 内容
- `cover-letter` → Phase 3，检查标题、Abstract、method 角色章节、results 角色章节，以及 Discussion 或 Conclusion 是否已有足以支撑投稿信的非占位内容
- `cleanup` → 直接 Phase 4（跳过 0.2–0.3）

跳过阶段时前置内容不存在 → 警告但允许继续；`cover-letter` 例外：上述必要正文不足或仍为 TODO 时停止，不得用用户口述、旧稿或其他项目资产补齐。

---

## Phase 1: Conclusion

### 1.1 Conclusion 结构（所有方法类型通用）

```
Block A: 研究概述（1-2 句：问题 + 方法 + 情境）
         紧接过渡句："The conclusions of this paper are as follows."
Block B: 核心发现——按 RQ 组织，用 First/Second/Third 连接
  - First, {对应 RQ1 的核心结论}
  - Second, {对应 RQ2 的核心结论}
  - ...（RQ 数量决定条目数）
Block C: 局限性与未来研究（只纳入会实质影响解释、外推或复现的局限；数量由证据决定）
```

> 没有单独的"贡献与启示"Block——贡献在 Discussion 中已展开，Conclusion 不重复。用户要求时可在 Block B 之后插入，默认不加。

### 1.2 逐块交互

按 Block A → B → C 顺序，逐块"提议 → 用户确认 → 循环"：

1. **提议**：基于 `{IDEA_CONTEXT}`、`{RESULTS_CONTEXT}`、`{SIMULATION_CONTEXT}` 生成**中文要点**；
2. **确认**：AskUserQuestion，循环直到满意；
3. **暂存**：全部 Block 确认后统一转英文。

**Block A 示例**：
```
📝 Phase 1 — Conclusion > Block A: 研究概述

提议（1-2 句 + 过渡句）：
> {这篇研究做了什么的中文要点}
> 过渡句: "The conclusions of this paper are as follows."

确认？
```

**Block B**（最重要，按 RQ 逐条提议）：

```
📝 Phase 1 — Conclusion > Block B: 核心发现 > RQ1

RQ1: {RQ1 原文}

提议 First 结论（{N} 个分层要点）：
1. {要点1：从 Proposition X / 核心估计结果 提炼}
2. {要点2}
3. {要点3：从比较静态 / 敏感性分析 提炼}

确认这些要点？可以增删改、调整措辞、合并/拆分。
```

确认 RQ1 后继续 RQ2（Second）、RQ3（Third）……

**Block C**：
```
📝 Phase 1 — Conclusion > Block C: 局限性与未来研究

提议 {M} 个已通过 minimum-sufficient qualification gate 的局限（不凑数量）：
- 局限: {已准入的实质局限} → 未来: {由该局限直接推出的研究方向}

确认？
```

局限准入（`MANUSCRIPT-ECONOMY.md` 的 minimum-sufficient qualification gate）：每条局限须说明它限定的具体 claim、不写会造成的具体误读、对应的证据或设计边界；正文已在最合适位置充分限定的同一风险不在 Conclusion 重复（one-risk-one-home）。凑不出合格局限时 Block C 可以很短。

### 1.3 字数估算

全部 Block 确认后展示：

```
📊 Conclusion 字数预估

| Block | 要点数 | 预估字数 |
|-------|--------|---------|
| A: 研究概述 + 过渡句 | — | ~60 |
| B: 核心发现 | {N} RQ × {avg} 要点 | ~{total_B} |
| C: 局限与未来 | {M} | ~{M×50} |
| 合计 | — | ~{total} |

确认？可调整各 Block 比重。
```

### 1.4 生成英文初稿

主 agent 基于确认的中文要点直接生成英文 LaTeX：
- Conclusion 不引用文献（极少数例外：局限中提及的方法论文献）；
- 不重复 Results 的全部细节，只提炼关键发现；
- 可引用命题编号、关键数值、效应模式——服务于结论陈述，不堆数据；数字与 `{RESULTS_CONTEXT}` 一致，register 存在时再与 register 核对；
- Block B 每条结论对应一个 RQ，用 First/Second/Third 连接；
- 术语遵守 `technical_map.md` 第 2 节术语表（如存在）；
- 生成后做 one-risk-one-home 检查；已确认的发现直接陈述，不再包裹 caveat。

### 1.5 Language Polisher 润色

执行前告诉用户：将派出 1 个 language-polisher 与 3 个并行 language-auditor。调用方式：Agent 工具，`subagent_type` 取角色名（如 `language-polisher`、`language-auditor`）。

language-polisher prompt 要素：

```
Mode B (Ad-hoc). Polish the following academic English text.

## Section: Conclusion
## Task: Improve grammar, coherence, sentence flow, and naturalness while preserving ALL academic content, technical terms, mathematical expressions, and argument structure.

## Text to Polish
{英文初稿}

## Terminology (binding, if available)
{technical_map.md 第 2 节术语表}

## Constraints
- Do NOT change any technical content, numbers, or mathematical expressions
- Do NOT add or remove citations
- Do NOT change the argument structure or conclusions
- Do NOT add hedges, caveats, limitations, or defensive sentences
- Target: {TARGET_JOURNAL} style
- Word count: maintain within ±5%
```

### 1.5b Language Auditor 审查

对润色结果并行调用 3 个 language-auditor（Group 1/2/3），同时提供初稿作为 source。主 agent 只整合 HIGH-confidence 且 `semantic_risk: no` 的语言修复；其余建议不自动采用，可在 1.6 中列出供用户参考。

### 1.6 用户确认并写入

展示润色后的英文全文，AskUserQuestion：

```
📝 Conclusion 终稿（{WORD_COUNT} 词）

{英文全文预览}

- 确认写入 manuscript.tex → 输入 "ok"
- 修改某处 → 指出具体位置和修改意见
- 重新润色 → 输入 "redo"
```

用户确认 → 用 Edit 工具 把内容写入 `{MAIN_TEX}` 的 `\section{Conclusion` 下（替换 TODO 或现有内容）。

### 1.7 提交建议

给出建议：`git add {MAIN_TEX}`，提交信息 `finalize: write Conclusion`。用户确认后执行；否则不提交。

---

## Phase 2: Abstract

### 2.1 读取 Conclusion

Phase 1 刚完成 → 复用；从 Phase 2 开始 → 从 `{MAIN_TEX}` 提取 Conclusion → `{CONCLUSION_CONTENT}`。

### 2.2 Abstract 结构（固定 5 块）

```
Block 1: Background（研究背景 + 问题，1-2 句）
Block 2: Purpose（研究目的 + 理论框架，1-2 句）
Block 3: Method（方法 + 数据/样本，1-2 句）
Block 4: Findings（核心发现，2-4 句——从 Conclusion Block B 浓缩）
Block 5: Implications（理论/实践价值，1-2 句）
```

### 2.3 逐块交互

按 Block 1 → 5 顺序，逐块提议中文要点 → 用户确认。

```
📝 Phase 2 — Abstract > Block 1: Background

提议：
> {研究背景的中文要点，1-2 句。从 idea.md 的 Gap 中提炼}

确认？可以调整措辞和侧重点。
```

**Block 4**：从 Phase 1 确认的 Conclusion Block B 进一步浓缩；展示 Conclusion 核心发现作为参考。

### 2.4 字数控制

```
📊 Abstract 字数预估

| Block | 预估字数 |
|-------|---------|
| Background | ~30 |
| Purpose | ~30 |
| Method | ~30 |
| Findings | ~60 |
| Implications | ~30 |
| 合计 | ~180 |

目标期刊 {TARGET_JOURNAL} 的摘要字数限制：{已知则展示，否则标注"未知，建议 150-250 词"}
```

### 2.5 生成英文初稿

- 一段连续文本（不分段、不加小标题），不引用文献；
- 建模类可包含关键数学结果（如 $\eta^* \approx 0.572$）；问卷类包含样本信息（如 "255 large-scale construction project teams"）；
- 结尾落在 implications 或 practical guidance 上，不落在 limitations 上；
- 摘要是独立文本：只有不写就会被实质误读的边界才保留一次。

### 2.6 润色与审查

同 1.5 / 1.5b，section 改为 "Abstract"。

### 2.7 用户确认并写入

展示润色后的摘要，用户确认 → 写入 `{MAIN_TEX}` 的 `\begin{abstract}...\end{abstract}` 之间。同时检查 Keywords（`\begin{keyword}` 或 `\keywords{}`），仍为 TODO 时提议 4–6 个关键词供确认。

### 2.8 提交建议

建议提交信息 `finalize: write Abstract and Keywords`，用户确认后执行。

---

## Phase 3: Cover Letter

### 3.1 读取前置内容

- **每次进入 Phase 3** 都重新读取当前 `{MAIN_TEX}`，覆盖内存中的 `{MANUSCRIPT_CONTENT}`，并保留这份读取结果用于 3.7 的变化比较。完整 `/finalize` 在 Phase 1/2 加载的 `{IDEA_CONTEXT}`、register 等上下文在 Cover Letter 阶段一律丢弃、禁止引用。
- 从这次读取的正文检查：标题、Abstract、method 角色章节、results 角色章节，以及 Discussion 或 Conclusion。缺失、为空或仍为 TODO → 立即停止。
- 只从当前 `{MAIN_TEX}` 提取 `{MANUSCRIPT_COVER_FACTS}`：
  - 题目、研究背景与 gap、aim，以及正文明确列出的 RQ / Hypotheses；
  - 数据 / 样本 / 观察期、变量与方法或模型设定；
  - results 角色章节报告的主要发现、空结果、诊断与稳健性结果；
  - Discussion / Conclusion 明确提出的理论贡献、实践意义、局限与 claim boundaries。
- 以上内容必须能逐项追溯到 `{MANUSCRIPT_CONTENT}`。`idea.md`、analysis / register / map、推导与结果文件、历史报告、旧版正文都不得作为 Cover Letter 的事实依据，即使看起来更新、更详细或与正文冲突。
- 作者姓名与通讯方式属于投稿元数据：可把当前 title page 作为候选来源，但必须经用户确认；投稿状态、全体作者同意与利益冲突声明只能来自用户对本次投稿的明确确认。它们都不得反向改变论文内容。

### 3.2 期刊信息

- 主编姓名 `{EDITOR_NAME}`、Aims & Scope 关键方向 `{JOURNAL_SCOPE}`；
- 通过 `web-access` 只核对期刊 / 出版社官方页面上的现任主编与 Aims & Scope；
- 获取失败 → `{EDITOR_NAME}` 设为 "Editor"，只使用能核实的 scope 表述。

> 期刊信息是外部投稿元数据，只用于称呼和 journal-fit 措辞，不能新增、扩大或重释 `{MANUSCRIPT_COVER_FACTS}` 中没有的论文主张。

### 3.3 Cover Letter 结构（内置固定结构；不读取或仿写任何旧 cover letter）

```
[自动] 称呼（Dear {Professor {EDITOR_NAME} | Editor},）

Block 1: 投稿声明 + 论文概述
  - 第一段：submit manuscript titled "XXX" for consideration in {JOURNAL}
  - 第二段：按"研究问题/情境 → 一般 gap → 本文的理论视角与研究设计"组织
  - manuscript 明确列出 RQ 时，第二段以引导句和 RQ 列表收束；RQ 逐字采用 manuscript 原文并保留编号
  - manuscript 未明确列出 RQ 时，不自行生成 RQ；第二段改以 aim 收束
  - 关键发现放到后续贡献段中与意义结合，不在第二段提前堆叠结果

Block 2: 贡献 1 — Journal Fit
  - 粗体标题："\textbf{1. Direct relevance to ...}"
  - 说明主题如何匹配期刊 Aims & Scope；引用正文具体内容（如 "As shown in Table 1 of the manuscript"）

Block 3: 贡献 2 — Theoretical Advancement
  - 粗体标题："\textbf{2. Theoretical advancement through ...}"

Block 4: 贡献 3 — Practical Implications
  - 粗体标题："\textbf{3. Actionable practical guidance for ...}"
  - 引用正文中的具体产出（如 "visualized in Figure 4"）

[确认后生成] 标准结尾（未在他处投稿 + 全体作者同意 + 利益冲突声明）+ 署名
```

> 贡献段数量随 manuscript 的 Discussion / Conclusion 中实际明确提出的贡献调整（2–4 段）。每段粗体标题针对论文具体内容定制。

### 3.4 逐块交互

Block 1–4 逐块提议中文要点 → 用户确认。称呼可自动生成；标准结尾与署名必须通过投稿元数据确认门。

manuscript 明确列出 RQ 时，Block 1 的确认材料单独展示：①第二段"问题—gap—视角/设计"逻辑；②RQ 引导句；③从 manuscript 逐字提取的完整 RQ 列表。RQ 列表放在第二段末、Journal Fit 之前；除必要的 LaTeX 转义外不调整措辞；字数紧张时压缩其他段落，不删改 RQ。

**投稿元数据确认门**：生成全文前，要求用户逐项明确确认本次投稿的：
- 非一稿多投状态；
- 全体作者知情并同意投稿；
- 利益冲突声明的准确措辞；
- 署名、单位、通讯作者与联系方式。

未确认的项保留 TODO，并停止最终写入。这些元数据只用于声明与署名，不能成为论文事实。

```
📝 Phase 3 — Cover Letter > Block 2: 贡献 1 — Journal Fit

参考 manuscript Discussion/Conclusion 贡献点 #1：{原文}
参考期刊 Scope：{JOURNAL_SCOPE}

提议：
> {中文要点：本研究主题如何匹配期刊定位、对期刊读者的价值}

确认？可以调整侧重点。
```

### 3.5 生成英文全文

主 agent 基于确认的要点生成 `\begin{document}` 到 `\end{document}` 之间的正文：
- 正式学术英文，400–600 词；
- 题目和列出的 RQ 使用 manuscript 原文；
- manuscript 明列 RQ 时，投稿句之后的研究概述段以 RQ 引导句和完整 RQ 列表收束，之后再进入 journal fit、理论贡献、实践意义与主要发现；
- 每个研究对象、时期、样本量、方法细节、数值、发现、空结果、诊断、稳健性结果、贡献、实践启示和边界表述都必须由当前 manuscript 明确支持；
- manuscript 与其他本地材料冲突时以 manuscript 为准；manuscript 内部有无法安全消解的冲突时停止并告诉用户；
- 不读取、复用或改写现有 `submission/coverletter.tex` 正文、旧草稿或其他论文的 cover letter；
- 不使用 "novel"、"first of its kind"、"groundbreaking" 等过度宣称；不复述整个摘要；使用 "we"；不提审稿人推荐。

### 3.6 Language Polisher 润色

使用独立 prompt，不复用其他 Phase 的 prompt：

```
Mode B (Ad-hoc).
## Section: Cover Letter
## Task
Polish the supplied cover-letter draft for grammar, coherence, concision, and natural academic
English. Target the general professional style of {TARGET_JOURNAL}; the journal name is a style
label only.

## Current manuscript — sole factual reference for manuscript-specific content
{MANUSCRIPT_CONTENT}

## Confirmed external metadata — preserve exactly; do not research or expand
{EDITOR_NAME}
{JOURNAL_SCOPE}
{CONFIRMED_SUBMISSION_METADATA}

## Text to polish
{COVER_LETTER_DRAFT}

## Constraints
- Polish wording only. Do not add, remove, strengthen, weaken, or reinterpret content.
- The current manuscript text above is the sole source of all manuscript-specific facts and claims.
- Preserve official journal metadata and user-confirmed submission metadata exactly as supplied.
- Do not read or use idea.md, analysis plans, results registers, technical maps, derivations,
  data outputs, historical reports, older manuscript versions, existing cover-letter body text,
  prior cover-letter drafts, or other papers' cover letters.
- Preserve all numbers, technical terms, claim boundaries, null findings, and LaTeX commands.
- Keep the word count within ±5%.
```

### 3.6b Language Auditor 审查

同 1.5b。审计时严格区分三类来源：
1. 论文事实与主张只对照 Phase 3 新读取的 `{MANUSCRIPT_CONTENT}`；
2. 主编与 scope 只对照本次读取的官方页面记录；
3. 作者、通讯信息与投稿声明只对照本次用户确认的投稿元数据。

三类信息不得互相补充或反向改写。

### 3.7 用户确认并写入

展示前重新读取 `{MAIN_TEX}`，与 3.1 读取的内容比较。正文在交互期间有变化 → 重新提取 `{MANUSCRIPT_COVER_FACTS}` 并重做事实保真核对。每个论文事实性句子都必须能在最新读取的正文中定位依据，无法定位的删除；用户想保留该内容，应先修改 manuscript 再重新进入 Phase 3。

展示润色后的全文。用户确认且投稿元数据确认门全部通过 → 读取 `submission/coverletter.tex`，只保留 LaTeX preamble 与版式定义，替换 `\begin{document}` 到 `\end{document}` 之间的正文。

- `submission/coverletter.tex` 不存在 → 停止，提示先运行 `/paper-init` 或手动创建；
- 已有实质内容 → AskUserQuestion 确认覆盖（覆盖前把旧文件复制到 `_archive/finalize-{TODAY}/submission/coverletter.tex`）。

编译验证：
```bash
cd submission && latexmk coverletter.tex 2>&1 | tail -20
```

### 3.8 提交建议

建议提交信息 `finalize: write Cover Letter`，用户确认后执行。

---

## Phase 4: 脚手架归档

> 只处理叙述型 blueprint 与 `drafts/`。不动：`idea.md`、`analysis_plan.md`、`results_register.md`、`technical_map.md`、`structure/3_analysis/`（含 derivation/）、`background/`、文献流水线产物、`figures_tables/`、`data/`、修订基线。

### 4.1 扫描并生成清单（只列出实际存在的项）

```
📦 拟移入 _archive/finalize-{TODAY}/（保持相对路径，不删除）：

structure/1_introduction/              ← Introduction blueprint
structure/2_literature/literature.md   ← Literature Review blueprint
structure/*discussion*/                ← 旧项目遗留的 Discussion 脚手架（如有）
structure/**/_citation_paths.json      ← 旧版本残留（如有）
drafts/                                ← 写作中间产物（drafts/writing_brief.md 如有，先移到 submission/）

✅ 保留不动：
structure/0_global/                    ← idea.md、analysis_plan.md、results_register.md、technical_map.md、background/
structure/2_literature/（除 literature.md）
structure/3_analysis/                  ← 推导工作区，长期保留
structure/figures_tables/、data/
manuscript-R*.tex / .revision-baseline ← 修订基线，永不移动
```

发现旧流程的技术章节 md（如 `methodology.md`、`results.md`、`simulation.md`）时，只在清单中报告为"遗留文件"，不在本流程中处理。

### 4.2 用户确认

AskUserQuestion：

```
📋 以上是脚手架归档清单。

- 确认执行 → 输入 "ok"
- 跳过 → 输入 "skip"
- 调整清单 → 指出要保留或额外归档的项
```

"skip" → 跳过 Phase 4，进入步骤 Final。

### 4.3 执行归档

```bash
A="_archive/finalize-{TODAY}"
# 目标已存在时停止并询问，不覆盖
mkdir -p submission
[ -f drafts/writing_brief.md ] && mv drafts/writing_brief.md submission/writing_brief.md
# 对清单中每个确认的路径 p：
mkdir -p "$A/$(dirname "$p")" && mv "$p" "$A/$p"
```

### 4.4 提交建议

建议提交范围：被移动的路径（删除 + 新增）与 `submission/writing_brief.md`；提交信息 `chore: archive writing scaffolding after finalize`。用户确认后执行；push 只在用户明确要求时执行。

---

## 步骤 Final：完成提示

在项目合同 `## 项目阶段` 中：存在 → 只更新 `更新时间: {TODAY}`（状态保持 `drafting`；`/pre-submit` 通过并经用户确认后才转为 `submitted`）；不存在 → 不追加。

```
✅ 定稿收尾完成

📄 Conclusion: {WORD_COUNT_CONC} 词 → manuscript.tex
📄 Abstract: {WORD_COUNT_ABS} 词 → manuscript.tex
📄 Cover Letter: {WORD_COUNT_CL} 词 → submission/coverletter.tex
📦 脚手架归档: {已完成 / 跳过}
🗓 日期检查: {通过 / 未处理的提醒条目}
🔖 提交: {已提交的 commit / 未提交}

下一步：运行 /pre-submit 做投稿前终检
```

---

## 全局约束

### 交互模式
- 每个 Block 都走"提议中文要点 → 用户确认 → 循环"；
- 用户可在任何 Block 输入 "skip" 跳过该块（保留现有内容或 TODO）；Phase 3 中 "skip" 只表示省略该 block，绝不保留或继承旧 cover-letter 正文；
- 用户可在任何 Phase 结束后输入 "stop" 中断流程。

### 语言流程
中文要点交互 → 主 agent 写英文 → language-polisher 润色 + language-auditor 审查 → 写入英文 LaTeX。

### 不越界
- Phase 1–3 只写 Conclusion、Abstract、Cover Letter；不修改其他章节与 bib；
- Phase 4 只移动清单中经确认的路径，不修改任何保留文件。

### 署名信息
候选来源优先级：①用户为本次投稿明确确认的信息；②当前 `submission/titlepage.tex`；③项目合同中的作者信息；④都没有 → 保留 TODO 并停止最终写入。无论来源为何，最终署名与联系方式都必须通过投稿元数据确认门；非一稿多投、全体作者同意与利益冲突声明必须由用户逐项确认，不能从 title page、项目合同或惯例推断。

### 幂等
可反复运行，每次覆盖对应位置的内容，支持从任意 Phase 开始。
