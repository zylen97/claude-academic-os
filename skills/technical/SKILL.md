---
name: technical
description: 技术章节写作：Map（用户确认 technical_map.md，并写项目合同的「技术章节」一节）→ 直接写 manuscript.tex → 对照 results_register 审计 → 嵌入式润色 → 回归审计 → 编译 → 写"技术正文完成"日期。两种模式：新写 / 修复（register 重新发布、审计问题或结构调整后）。用于 analysis Release 之后撰写或修复 Methodology / Results / Simulation 等技术章节。不做新分析。
---

# technical — 技术章节：Map → Tex

唯一规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（§2、§4.4–4.6、§5）。冲突以规格为准。写作与审计都按 `~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。

```
Map【确认】→ technical_map.md + 项目合同 ## 技术章节
Tex → 写 manuscript.tex → 对照 register 审计 → 嵌入式润色 → 回归审计 → 编译 → 写"技术正文完成"日期
```

## 边界

- `manuscript.tex` 是唯一正文；不建 `methodology.md` / `results.md` / `simulation.md` 或其他技术正文草稿（内存中的段落不落盘）。
- 不做新分析、不改设计。缺证据回 `/analysis`；设计要变回 `/idea-refine`。
- 报告基准只决定组织与披露位置，不改模型、变量、主设定或结论强度。
- 正文中每个技术结论都能指回 register 中的一条；模型原语（假设、符号、模型设定式）可指回 `analysis_plan.md` 第 3 节或 `derivation/` 的设定部分。
- 只改技术章节；Introduction、Literature review、Discussion、Conclusion 等不动。
- 不自动 commit / push。

## 第 0 步：前置检查与模式

读取：项目 `CLAUDE.md`（`## 项目阶段`、"方法 profile"、`## 技术章节`、目标期刊）；`analysis_plan.md`（状态行、第 2、3、6 节、第 7 节最后一条日期）；`results_register.md`（发布日期）；`technical_map.md`（若有：依据日期、技术正文完成日期）；对应 profile（`~/.claude/skills/analysis/profiles/<name>.md`，找不到用 `_generic.md` 并提醒）。

- **阻断**：register 不存在或没有发布日期 → 停止，建议 `/analysis` Release。
- 项目阶段为 `foundation`（设计正在 idea-refine 中修改）→ 提醒先完成 `/idea-refine` 与 `/analysis`，用户可选择继续。
- **日期检查（§4.6，只提醒不阻断）**：
  - 计划第 7 节最后日期 > register 发布日期 → 提醒"register 可能未反映最新变更"，建议先 `/analysis` 重新 Release；用户可选择继续。
  - 计划第 7 节最后日期或 register 发布日期 > 技术正文完成日期（为空时跳过）→ 提醒技术正文已过期，进入**修复**模式；回流路线：register 变了 → 本技能修复；设计变了 → `/idea-refine` → `/analysis` Plan。
  - 按时刻严格比较（规格 §4.6）；只写了日期的旧条目与另一方同一天时不判先后，提醒用户确认。
- **模式**（只有两种）：
  - **新写**：没有 `technical_map.md`，或用户要求整体重写 → 从 Map 开始。
  - **修复**：已有 map 且"技术正文完成"有日期 → 按下方"修复模式"。
  - 已有 map 但"技术正文完成"为空（上次在 Tex 中途停止）→ 按新写从 Tex 继续，不重新确认 map；若 map 依据日期早于 register 发布日期，先按"修复模式"第 1–3 步更新 map。
  - 只涉及语言的问题转 `/polish`，不进本技能。
- 编译一次作为基线，记录已有的错误与警告。

## Map【用户确认】

**读**：register 全表与其来源文件（`derivation/*.md` 的结论块、`data/results/` 输出）；`idea.md`；profile 第 6、7 节；`structure/figures_tables/index.md`；`manuscript.tex` 现有章节结构与 Introduction / Literature review 中的术语；`structure/2_literature/citation_pool/METHOD.md`、`COMP.md`；`{ID}.bib`。

**报告基准（map 第 3 节）**：默认复用计划第 2 节的设计基准，另加 1–2 篇目标期刊、同方法的近期样例（从 METHOD/COMP 池或定向检索选，读全文）。只提取章节顺序、披露位置、表图安排；不复制措辞。引用池不存在时从计划第 2 节与 `reading_notes/` 中选，并提醒。若样例暴露出缺少某项分析 → 建议走 `/analysis` 变更流程，不在正文中补。

**起草 `technical_map.md`**（结构严格按规格 §4.5）：
- 第 1 节章节结构：每行 `section/subsection 标题｜角色(method/results/simulation)｜段落任务｜register ID｜表/图`。顺序按 profile 第 6 节报告顺序；偏离时在段落任务中写一句理由。不要按脚本机械地一项一节。
- 覆盖：每条 `必报=是` 的 register ID 在第 1 节中恰好出现一次；`必报=否` 的条目要么映射，要么在第 4 节写省略原因。
- 第 2 节术语表：只收承载含义、跨章节必须一致的术语（主体 / 单位、构念与变量、效应或命题对象、模型与情景名称、缩写）；每条写定义与"不得混用的近义词"。术语含义以计划与 register 为准；用词优先级：用户在本流程中确认的 > manuscript 已有正式定义 > 一致的现有用法。
- 第 4 节省略说明。
- 表 / 图：核对 `index.md`，缺的列出来并建议先用 `/figure` 或 `/latex-table` 补；数据图必须来自 register 登记的来源。
- 旧项目若有 `structure/3_methodology/` 等旧技术 md：只读参考；在确认问题中一并提出把它们移入 `structure/_archive/`（不删除）。其中若有 register 未覆盖的推导或结果，先回 `/analysis` 登记，不能直接搬进正文。

**确认**：展示完整 map，用 AskUserQuestion 询问：批准结构并授权写入下列技术章节 / 修改 / 暂停。问题中列明将被替换或新建的 `\section` 标题（批准即授权本次只改这些章节及其所需的 `{ID}.bib` 条目）。

批准后写入：
1. `structure/0_global/technical_map.md`，表头 `依据: results_register 发布 YYYY-MM-DD HH:MM｜技术正文完成: `（留空）。
2. 项目 `CLAUDE.md` 的 `## 技术章节`（已有则替换该节内容；无则新建，放在 `## 项目阶段` 之后）：
   ```
   ## 技术章节
   | \section 标题 | 角色 |
   |---|---|
   | Model | method |
   | Equilibrium analysis | results |
   | Numerical study | simulation |
   ```
3. 用户同意的旧技术 md 归档移动。

## Tex：写入 manuscript.tex

- 逐节按 manuscript 顺序写。每节交给子 agent `sci-writer`（Agent 工具，定义在 `~/.claude/agents/sci-writer.md`），传入：该节 map 行、相关 register 行及其来源文件路径、计划第 3、6 节、术语表、profile 路径、`MANUSCRIPT-ECONOMY.md` 路径、`{ID}.bib` 与 `citation_pool/master.bib` 路径、相邻章节文本。子 agent 返回 LaTeX 与忠实性清单，不写文件；主 agent 负责写回。
- 引用：只用 `{ID}.bib` 中已有的键；`citation_pool/master.bib` 中有而项目 bib 没有的，复制该条目到 `{ID}.bib`；两处都没有（或引用池尚不存在）→ 不引用，提醒回 `/lit-workflow`。不插 `(ref)` 或占位符。
- analytical-model：命题陈述与条件逐字对应 `derivation/` 的结论块；正文给证明思路，完整证明放附录（项目已有附录结构则沿用，否则新建 `\appendix` 下的证明节，列在 map 中）。
- 表图只用 `\ref` 引用已登记的 label，不在正文中嵌表格代码。
- 替换章节时保留章节外的全部内容；`\section` 标题按 map。

## 审计（对照 register）

主 agent 对全部技术章节做一次整体审计，逐项列出结果：
1. **覆盖**：每条 `必报=是` 的结果恰好报告一次（作为结果陈述；后文简短回指不算重复报告，但不得再次给出数值）。
2. **证据**：每个技术结论、数字、命题、检验结果都能指回 register 行；数值与来源文件一致；没有超出证据的说法（新机制、新变量、因果动词、"实践中会"）。
3. **解读边界**：register 每行的"解读边界"、计划第 6 节、profile 第 7 节都被遵守。
4. **报告顺序**：与 map 第 1 节一致（map 的顺序已按 profile 第 6 节确定）。
5. **术语**：与术语表一致，无近义词混用。
6. **精简规则**：按 `MANUSCRIPT-ECONOMY.md`；正文不出现 register、profile、map、release、gate、audit 等内部流程词。
7. **LaTeX**：引用键存在、label 唯一可解析、环境与括号闭合、无 TODO / 占位符。

结论只取其一：
- **通过** → 嵌入式润色。
- **修正文**：证据与 map 足以支持局部修复 → 修复后重跑整体审计；连续两轮仍不通过，停下与用户对齐。
- **回到 Map**：需要改章节划分、顺序或映射 → 重新走 Map 确认。
- **回到 analysis**（阻断）：缺证据、来源互相矛盾、需要 register 之外的结果 → 停止，建议 `/analysis`。

## 嵌入式润色

审计通过后，逐个技术章节调用 `/polish`（Skill 工具）的**嵌入模式**：参数开头写 `POLISH_EMBEDDED_CANDIDATE_ONLY`（嵌入模式：只返回候选文本，不写文件），并传入：章节标题与来源角色（角色为 results 或 simulation 时标为 Results，method 标为 Methodology）、当前文本（审计通过版本，即 exact source）、术语表（`technical_map.md` 第 2 节）、受保护内容（数字、公式、符号、引用、label、命题编号）。polish 只改语言；空洞表述信号由 polish 自行从项目 profile 第 8 节读取。

按返回状态处理：
- `EMBEDDED-PASS` → 收下候选。
- `FAIL-BLOCKED: SOURCE-OPAQUE` → 这是正文问题而非语言问题：主 agent 按 register 对应条目的含义把被点名的句子改写成"实质在前"（谁、什么结果、方向、相对什么），写回该章节并重跑审计第 1–6 项（此版本成为新的审计通过版本）后再提交一次；仍失败则保留审计通过版本并在收尾中列出这些句子。
- 其他失败，或 polish 不支持嵌入模式 → 该章节跳过润色，保留审计通过版本，收尾中写"润色未执行"，建议之后单独运行 `/polish`。

收齐候选后统一写回，然后做**回归审计**（重跑审计第 1–6 项）。某一章节出现含义、数字、结论强度、引用归属或术语的漂移 → 该章节恢复为润色前（审计通过）的文本，并在收尾中注明。

## 编译

用项目 `latexmkrc` 编译。与基线相比不得新增：错误、未定义引用 / 交叉引用、重复 label、`Float too large`、紧急停止。未通过 → 修 LaTeX 层面的问题后重编译；仍无法解决则停止，不写完成日期。

## 写完成日期

编译通过后，把 `technical_map.md` 表头改为 `依据: results_register 发布 <register 当前发布时刻>｜技术正文完成: <当前时刻 YYYY-MM-DD HH:MM>`。

## 修复模式

1. 对比 register 当前版本与 map 依据日期对应的版本（git 历史或 `structure/0_global/_archive/` 中的备份），列出新增、删除、数值变化的条目。
2. 只是数值或表述变化、ID 与结构不变 → 不需重新确认 map，直接改受影响的段落。
3. 有新增 / 删除的必报条目，或要改章节结构 → 更新 map 第 1、4 节，重新走 Map 确认（同时更新项目合同 `## 技术章节`，若标题或角色有变）。
4. 之后同新写：整体审计 → 嵌入式润色（受影响章节）→ 回归审计 → 编译 → 写完成日期。

## 收尾

汇报：模式、写入的章节、必报条目覆盖数、审计结论、润色与回归结果（含恢复的章节）、编译结果、仍未解决的风险。给出建议的提交范围与提交信息，由用户决定是否提交。下一步通常是 `/narrative section=discussion`（Introduction / Literature review 可在本技能之前或之后）。
