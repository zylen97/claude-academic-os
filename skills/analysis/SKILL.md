---
name: analysis
description: 分析阶段：Plan（用户批准 analysis_plan.md，阶段写为 analysis）→ Run（按方法 profile 推导 / 跑脚本 / 做检验）→ Release（用户确认 results_register.md 完整，阶段写为 drafting）。适用于 analytical-model、panel-regression、survey-sem、saom 及其他方法（_generic）。用于制定或修改分析计划、执行已批准的分析、补充分析（含审稿补分析）、发布或重新发布结果登记表。不写正文。
---

# analysis — 分析计划、执行与结果登记

唯一规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（§1 阶段、§2 目录、§4.2–4.4、§4.6、§5）。冲突以规格为准。

```
Plan【确认】→ analysis_plan.md（approved）→ 阶段 analysis
Run → derivation/ 或 data/ 下的推导、脚本、输出
Release【确认】→ results_register.md（发布日期）→ 阶段 drafting
```

## 边界

- 不写 `manuscript.tex`，不建 `methodology.md` / `results.md` / `simulation.md` 或任何技术章节正文草稿。
- 看过结果后改设计必须先写变更记录（计划第 7 节）并经用户确认；结果显著与否不是改设计的理由。
- 方法知识来自 profile：`~/.claude/skills/analysis/profiles/{saom,panel-regression,survey-sem,analytical-model,_generic}.md`。找不到对应 profile 时用 `_generic.md` 并提醒用户，不停止。
- 模板：`~/.claude/skills/analysis/templates/analysis_plan.md`、`templates/results_register.md`。
- 不自动 commit / push；不硬删文件（需要替换时先移入 `_archive/`）。

## 第 0 步：读状态并路由

读取：项目 `CLAUDE.md`（`## 项目阶段`、"方法"与"方法 profile"字段、目标期刊）、`structure/0_global/analysis_plan.md` 状态行与第 7 节、`structure/0_global/results_register.md` 发布行。

| 情形 | 进入 |
|---|---|
| 无计划，或状态 `draft` | Plan |
| 状态 `approved`，但第 7 节最后一条【设计层】条目之后没有"重新批准计划"条目（idea-refine 写入；阶段可能已回退为 `foundation`，投稿后或修改期则不回退） | Plan（重新批准） |
| 状态 `approved`，register 未发布或用户要继续跑 | Run |
| 用户要改计划第 1/3/4/5 节、补分析或回应审稿补分析 | 变更流程 → Run → Release |
| Run 已完成，用户要发布 | Release |

**阶段写入只在两种情况下发生**：Plan 批准时当前阶段为 `foundation` → 写 `analysis`；Release 确认时当前阶段为 `analysis` → 写 `drafting`。当前阶段为 `drafting` / `submitted` / `revision-R{N}` 时（如投稿后补分析）只更新计划与 register，**不改阶段**。写阶段时同时更新"更新时间"。

## Plan【用户确认】

1. **确定 profile**：取项目合同"方法 profile"字段；没有时按"方法"字段映射（SAOM → `saom`；面板 / 回归 → `panel-regression`；问卷 / SEM → `survey-sem`；博弈 / 合同 / 优化 / 运营模型 → `analytical-model`；其他 → `_generic`），映射结果放进批准问题中让用户确认。完整读该 profile。
2. **读上下文**：`idea.md`（RQ、方法论证）；`structure/2_literature/citation_pool/METHOD.md`、`COMP.md` 与 `method_landscape.md`（若有）；`data/notes/`；`structure/0_global/background/`；`data/raw/` 的说明文件。旧项目若有 `structure/3_methodology/methodology.md` 等旧技术 md，只读作参考；其中已有的推导（analytical-model）在 Run 中迁入 `derivation/`。
3. **设计基准（第 2 节）**：idea-refine 已写入的直接沿用；为空时从 METHOD/COMP 池提出 5–8 篇，每篇一句话写"借什么"，必要时读全文。引用池尚不存在（文献流水线未完成）时，从 `idea.md` 第 1 节与 `structure/2_literature/reading_notes/` 中提出，并提醒用户之后补跑文献流水线；不阻断。若用户在此过程中人工整理了 `method_landscape.md`，经同意后在其首行加入 `<!-- curated -->`。
4. **起草计划**：按模板逐节填写。要求：
   - 第 1 节：每个 RQ 有结论目标与证据类型；尚未推出的结论标"待证"。
   - 第 3 节：按 profile 第 2 节写全输入。analytical-model 写参与者、时序、信息结构、决策、收益与约束、假设清单（每条附合理性来源）、参数定义域，以及数值研究的参数来源与求解设置。survey-sem 可在数据到达前批准：写量表、抽样方案与计划样本量。
   - 第 4 节：每个任务写产出文件路径（见下方"文件约定"）。
   - 第 5 节：逐条列 profile 第 5 节必做项，不适用的写"不适用：原因"；再列项目特有项。
   - 第 6 节：把 profile 第 7 节具体化到本项目。
5. **确认**：在对话中展示完整计划，用 AskUserQuestion 询问：批准 / 修改后再看 / 先存为草稿。
   - 批准：写入计划，状态行为 `状态: approved（批准日期 YYYY-MM-DD）｜profile: <name>`；项目合同缺"方法 profile"字段时补写 `- **方法 profile**: <name>`（在 `## 核心配置` 下）；按上节规则写阶段。若是重新批准，在第 7 节表格末尾追加一行 `| YYYY-MM-DD HH:MM | 重新批准计划 | idea-refine 改动设计后 | 影响……（列出需重跑的任务与受影响的 register 条目） |`，并把状态行的批准日期改为当天。
   - 存为草稿：写入计划，状态 `draft`，不改阶段。

## 变更流程（approved 之后）

- 改第 1、3、4、5 节任何内容：先向用户展示拟追加的第 7 节表格行（`| YYYY-MM-DD HH:MM | 改了什么 | 原因 | 影响 register/technical/narrative 的哪些部分 |`），确认后再追加并修改对应节；状态保持 `approved`。
- **属于设计层的变化**（RQ、模型族、主设定、数据边界、核心构念）：不在本技能内改，停止并建议运行 `/idea-refine`（由它写带【设计层】标记的变更记录；当前阶段为 analysis/drafting 时它会回退为 `foundation`，submitted/revision 时不改阶段），之后回到本技能：第 0 步按"最后一条【设计层】条目之后没有重新批准条目"识别并进入 Plan 重新批准，不会再转回 idea-refine。
- survey-sem 数据到达：追加一行"数据入库"（格式见 `profiles/survey-sem.md` 第 1 节），展示后写入，不需重新批准计划。
- 计划中登记过的空结果、失败检验，不能通过变更记录删除；它们必须进入 register。

## Run

前提：计划 `approved` 且项目阶段不是 `foundation`。survey-sem 需要正式数据的任务，要等第 7 节有"数据入库"一行后再跑（预调研分析可先跑）。按第 4 节顺序执行，逐任务核对产出路径。

**文件约定**
- analytical-model：
  - 推导写 `structure/3_analysis/derivation/`（不存在则创建；长期保留，不是正文草稿，technical 之后也不删除）。按模型或部分分文件，如 `01_setup.md`、`02_benchmark.md`、`03_main.md`、`04_extensions.md`。
  - 每个结论块用带方括号 ID 的标题作锚点：`### [P1] 标题`，引用写作 `derivation/03_main.md#P1`。块内包含：陈述、成立条件与参数域、证明骨架（关键步骤齐全；完整证明可写在块内或标明放附录）、比较静态与阈值、管理直觉、复核脚本与结果。
  - 复核脚本（SymPy / 数值抽样）与输出放 `derivation/checks/`，如 `{ID}_check_P1.py` → `{ID}_check_P1.out`（输出含抽样范围、次数、反例数）。
  - 数值研究（仿真、两阶段随机规划、MILP 算例）：脚本 `data/scripts/`，输出 `data/results/`，参数来源表放 `data/processed/`（文件名写入计划第 3 节）；图交给 `/figure`，表交给 `/latex-table`。
- 实证类（panel-regression / survey-sem / saom / _generic）：`data/raw/` 只读；脚本 `data/scripts/`；中间文件 `data/processed/`；模型对象 `data/models/`；输出 `data/results/`；稳健性 `data/robustness/`。脚本输出不得写到项目根目录。
- 每次运行记录软件与版本、关键设置、随机种子，写在对应输出或日志的开头。

**执行规则**
- 逐项完成 profile 第 5 节与计划第 5 节的检验。
- 只为修实现错误而改脚本 / 推导，不改设计；执行中发现必须改第 1/3/4/5 节时，停下走变更流程。
- 推不出的待证结论、被反例否定的不等式、未通过的检验：如实保留输出，Release 时登记为 `null` 或失败检验，不得删掉或改写成支持性结论。
- 过程性思考（试过什么、为什么放弃）写 `data/notes/{YYYY-MM-DD}_{topic}.md`，不写进推导文件的结论块。

Run 进度只在对话中汇报，不写进计划（计划第 4 节的改动需要变更记录）；新会话按第 4 节各任务的产出文件是否存在判断进度。

## Release【用户确认】

1. 起草 `results_register.md`（按模板）：每条结果一行；类型取自 profile 第 4 节；来源写到文件与锚点（或 脚本 → 输出）；`必报` 默认：回答 RQ 的结果、计划登记的空结果、未通过的必做检验为"是"，细节性稳健性可为"否"。
2. 完整性自查（主 agent 逐项核对，结果在对话中列出）：
   - 计划第 1 节每个结论目标至少有一行（或一行 `null`）；
   - 计划第 5 节每项检验都有结果行（通过或未通过）；
   - 第 4 节每个任务的产出都被引用，或在对话中说明为何不进 register；
   - 每个来源文件存在、锚点存在；analytical-model 的每个命题都有复核结果；
   - 结果与计划一致：若输出显示模型或变量与计划不符且第 7 节无记录 → **阻断**，先走变更流程；来源文件缺失 → **阻断**。
3. 展示完整 register 与自查结果，用 AskUserQuestion 询问"register 是否完整、可以发布"。
4. 确认后写入：发布行 `发布: YYYY-MM-DD HH:MM（对应 analysis_plan 批准日期 YYYY-MM-DD）`（时刻取当前本地时间，规格 §4.6）；按"第 0 步"规则写阶段（`analysis → drafting`）。
5. **重新发布**（补分析、审稿补分析）：沿用原有 ID，新增条目往后编号；写入前若 git 显示旧 register 有未提交改动，先复制到 `structure/0_global/_archive/results_register_{旧发布日期}.md`。若 `technical_map.md` 已有"技术正文完成"日期，提醒：register 晚于技术正文 → 需要 `/technical` 修复。

## 收尾

汇报：模式、profile、计划状态与批准日期、完成的任务数、register 条目数（按类型与必报）、空结果与未通过检验、需要回流的下游（technical / narrative）。给出建议的提交范围与提交信息，由用户决定是否提交。下一步通常是 `/technical`。
