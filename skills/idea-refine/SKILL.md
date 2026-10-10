---
name: idea-refine
description: "交互式审 idea 与方法方向：idea-reviewer 做 Dim5 建模创新 / Dim6 假设逐条审查 + 设计基准（5–8 篇，写入 analysis_plan.md 第 2 节）+ 按方法 profile 的可行性检查；用户逐条确认后改 idea.md；设计层改动写 analysis_plan 第 7 节变更记录并把阶段回退为 foundation；技术材料只读作一致性证据；不自动 commit"
---

# Idea Refine — idea 与方法方向审稿迭代

唯一规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（§1 阶段、§4.3 analysis_plan、§4.7 本技能要点、§5 确认点）。冲突以规格为准。

调用 idea-reviewer 审查 `idea.md` 的研究问题、理论方向与方法设计，并为 `/analysis` Plan 准备设计基准。本技能**不跑模型、不写正文、不写 analysis_plan 第 1、3、4、5、6 节**（这些属于 `/analysis` Plan）。

**写入范围**（每项都需用户确认后写入）：
- `structure/0_global/idea.md`
- `structure/0_global/analysis_plan.md` 第 2 节（设计基准）与第 7 节（变更记录，只追加）；状态行不改
- 项目合同 `## 项目阶段`（仅在设计层改动且当前阶段为 analysis / drafting 时回退为 foundation，见步骤 4）
- `structure/0_global/idea-refine/` 下的轮次文件

**只读**：文献产物、`results_register.md`、`technical_map.md`、`manuscript.tex`、`structure/3_analysis/`、`data/`（作为一致性证据）。

**输入** `$ARGUMENTS`：可空。

---

## 步骤 0：前置准备

### 0.1 项目信息与 profile

- 读取 `CLAUDE.md`：项目编号、目标期刊、方法、**方法 profile**（`## 核心配置` 下的 `- **方法 profile**: <name>`）、`## 项目阶段`、`## 技术章节`。缺失项警告，不停止。
- profile 文件：`~/.claude/skills/analysis/profiles/{profile}.md`。合同无"方法 profile"字段 → 按"方法"推断并提醒用户补写合同；找不到对应文件 → 使用 `_generic.md` 并提醒，不停止；`_generic.md` 也不存在 → 无 profile 继续，并在审稿 prompt 中注明"无方法 profile，可行性按通用标准审查"。

### 0.2 idea.md

- 读取 `structure/0_global/idea.md`。不存在 → **停止**："idea.md 未找到。请先通过 `/idea-mine` 生成或手动创建。"；有效内容 < 100 字符 → **停止**："idea.md 内容过少，请先完善基本内容。"
- 版本号取头部 `> **版本**: vX.Y` 行；缺失视为 `v0.0`。

### 0.3 设计与技术状态（只读，用于选择审查重点）

| 状态 | 判定 | 审查重点 |
|---|---|---|
| `DESIGN` | `analysis_plan.md` 不存在或状态行为 draft | idea 架构、设计基准、可行性 |
| `PLAN` | 状态行为 approved，`results_register.md` 不存在 | 计划的完整性与可执行性 |
| `ANALYSIS` | `results_register.md` 存在且有发布日期 | 计划与已登记结果的一致性 |
| `TEXT` | `technical_map.md` 表头"技术正文完成"已填日期 | idea / 计划 / 正文技术章节的一致性 |

`TEXT` 状态下，正文技术章节按项目合同 `## 技术章节` 列出的 `\section` 标题定位（不按字面标题猜）。

展示：`📍 项目状态：{状态}（阶段 {项目阶段}，profile {profile}）`。

### 0.4 扫描可用材料

Glob 检查并记录存在 / 不存在：

| 材料 | 路径 | 用途 |
|---|---|---|
| 源论文精读 | `structure/0_global/idea-mine-ref/paper_note.md` | 迁移基础 |
| 迁移方向预判 | `structure/0_global/idea-mine-ref/migration_analysis.md` | 迁移假设变化 |
| 期刊适配版本 | `structure/0_global/idea-mine-ref/idea_*.md` | 期刊定制 |
| idea-mine 审稿 | `structure/0_global/idea-mine-ref/review_*.md` | 前序评审 |
| 方法论综述 | `structure/2_literature/method_landscape.md` | 方法现状 |
| 方法 / 对比引用池 | `structure/2_literature/citation_pool/METHOD.md`、`COMP.md` | 设计基准候选 |
| 文献总报告 | `structure/2_literature/master_report.md` | 交叉验证 Gap |
| 带标签方向报告 | `structure/2_literature/tagged_reports/direction*_report.md` | 文献覆盖 |
| 文献清单 | `structure/2_literature/literature_manifest.json` | 文献覆盖（每篇唯一论文一行） |
| 分析计划 | `structure/0_global/analysis_plan.md` | 第 2 节基准、第 7 节变更 |
| 结果登记表 | `structure/0_global/results_register.md` | `ANALYSIS`/`TEXT` 一致性 |
| 技术结构 | `structure/0_global/technical_map.md` | `TEXT` 一致性 |
| 推导工作区 | `structure/3_analysis/derivation/*.md` | analytical-model 的假设与命题 |

展示材料可用性摘要。只有 idea.md 可用时提示：`⚠️ 可用上下文有限，建议先完成 /lit-workflow 再运行 /idea-refine。`（提醒，不停止）

### 0.5 工作目录、轮次与快照

- 工作目录 `structure/0_global/idea-refine/`（已存在则复用，支持跨 session）。
- 轮次 M = 已有 `review_r*.md` 的最大编号 + 1（无则 1）。
- 复制当前 `idea.md` → `idea-refine/idea_v{X.Y}_before_r{M}.md`。

---

## 步骤 1：设计基准（写入 analysis_plan.md 第 2 节）

目的：在分析之前为"做什么"找 5–8 篇全文先例。设计基准只决定设计，不决定正文章节标题（报告基准属于 `/technical` Map）。

### 1.1 是否需要（重新）选择

- `analysis_plan.md` 第 2 节已有 5–8 条且用户未要求更换 → 沿用，作为审稿输入。
- 第 2 节为空 / 不足 5 条 / 用户要求更换 → 执行 1.2。
- `analysis_plan.md` 不存在（旧项目）→ 执行 1.2，候选清单在步骤 4 经确认后写入；计划文件本身仍由 `/analysis` Plan 创建，本技能只在文件存在时写第 2 节。文件不存在时把已确认的基准清单保存到 `idea-refine/design_benchmarks_r{M}.md`，并提示 `/analysis` Plan 读取。

### 1.2 选择与阅读

- 候选来源：`citation_pool/METHOD.md`、`COMP.md`、`method_landscape.md`、带标签方向报告。
- 若用户在本步骤中人工整理了 `method_landscape.md`，经同意后在其首行加入 `<!-- curated -->`，此后 lit-pool 刷新不会覆盖它（规格 §3.2）。
- 角色覆盖（每篇标一个）：①同方法 + 同领域最近设计；②同方法、领域外的强设计；③方法 / 估计指南类权威文献；④最近的反例或明显不同的设定。
- 必须有全文：本地缺全文时通过 web-access skill 获取（若存在 `~/.claude/skills/web-access/references/benchmark-fulltext-workflow.md` 则按其执行），下载件归档到项目已有的 benchmark 目录；只有摘要的文献不能作为设计基准。
- 只提取文中实际报告的内容（未报告写"未报告"）：分析单元、样本与时点、构念 / 变量、模型设定、假设、检验与稳健性、解读边界。

### 1.3 按 profile 的可行性检查

| profile | 可行性含义 | 核对证据 |
|---|---|---|
| analytical-model | 可解性（是否有闭式解 / 可刻画的均衡，二阶条件能否成立）与参数可得（数值研究的参数是否有文献 / 案例 / 政策来源） | 推导草稿、基准论文的求解路径、参数来源 |
| survey-sem | 量表来源（是否有成熟量表及其情境适配）与样本可达（受访者群体、渠道、计划样本量） | 量表文献、抽样方案、接触渠道 |
| panel-regression | 变量覆盖（核心变量、控制变量、时间跨度、样本单位在数据源中是否可得）与识别可行 | 数据字典、样本覆盖统计 |
| saom | 行动者集合、观测波次、网络与行为变量是否可得且时点对齐 | 数据字典、波次表 |
| `_generic` / 无 profile | 关键输入是否可得、方法前提是否可满足 | 项目数据 / 模型设定说明 |

每项标为 `已核实` / `可修复` / `阻断`。`阻断` 项进入审稿意见，由用户决定如何处理（不自动停止流程）。

---

## 步骤 2：idea-reviewer 审稿

### 2.1 调用

通过 Agent 工具（`subagent_type: "idea-reviewer"`，定义见 `~/.claude/agents/idea-reviewer.md`） 调用 idea-reviewer。prompt 要素：

```
Read `structure/0_global/idea.md` as the primary review target.

## Project Info
- Project: {项目编号} | Target journal: {目标期刊}
- Method: {方法} | Method profile: {profile 名称与绝对路径，或"none"}
- Project phase: {项目阶段} | Design/technical state: {DESIGN/PLAN/ANALYSIS/TEXT}

## Available Context Materials
{逐条列出步骤 0.4 中存在的文件的绝对路径}

## Design Benchmarks
{analysis_plan.md 第 2 节现有条目，或步骤 1 新选候选：citation key、角色、全文路径、借什么}

## Feasibility Table (from Step 1.3)
{表格}

## Technical Evidence (read-only consistency evidence)
{PLAN: analysis_plan.md 路径}
{ANALYSIS: + results_register.md 路径}
{TEXT: + technical_map.md 路径与 manuscript.tex 中以下 \section（来自项目合同 ## 技术章节）: {标题与角色}}
{analytical-model: + structure/3_analysis/derivation/ 下的文件路径}

{M > 1 时：}
## Prior Rounds
This is Round {M}. Already addressed: {confirmed_r*.md 的绝对路径}
Do NOT repeat addressed suggestions; flag only new, incompletely fixed, or regression issues.

Follow the output format in your instructions (Part I tables incl. Dim 5 and Dim 6, Part II, Part III with exactly one route per item). 用中文输出。
```

保存审稿意见 → `idea-refine/review_r{M}.md`。reviewer 调用失败 → 报告错误，等待用户指示（不自动重试）。

### 2.2 用户确认

先展示 Part II 总体评价（可发表潜力、最大亮点、最大风险、成熟度），再展示 Part III 编号建议：

```
📋 第{M}轮审稿建议（共 N 条）：
1. [§X / Dim Y → 路由] {问题} → {建议}
...
- 接受：编号（如 "1,3,5" 或 "all"）  - 拒绝："reject 2,4"
- 修改某条："3: 改为..."             - 结束："done"
```

用户选 "done" → 跳到步骤 6。否则生成确认清单 → `idea-refine/confirmed_r{M}.md`。

---

## 步骤 3：修改方案

按路由分组，展示**修改方案与写入清单**：

```
📝 修改方案（共 K 条）

=== idea.md ===
1. [意见#1, §2 Gap] 当前: "…" → 改为: "…"

=== analysis_plan.md 第 2 节（设计基准）===
2. 新增 / 替换: `citekey`（角色）：借……

=== 设计层改动判定 ===
是否涉及 RQ→结论目标、模型族 / 主设定 / 数据边界、任务、检验（即计划第 1、3、4、5 节的内容）：是 / 否
{是且计划已 approved：}
  - analysis_plan.md 第 7 节追加：| {当前时刻 YYYY-MM-DD HH:MM} | 【设计层】{改了什么} | {原因} | {影响 register / technical / narrative 的哪些部分} |
  - 项目阶段：仅当当前为 analysis 或 drafting 时 → foundation（状态行保持 approved；第 7 节最后一条【设计层】之后没有"重新批准计划"行，即表示须经 /analysis Plan 重新批准）；当前为 foundation 则不变；submitted / revision-R{N} 不改阶段
  - 下一步：/analysis Plan 更新第 1、3、4、5 节并重新批准

=== 下游回流（本技能不修改）===
3. [意见#4 → technical] 原因… 下一步: /technical 修复
```

用 AskUserQuestion 确认方案或调整某条。"继续 / ok" 只对当前展示的方案生效。

### 路由定义（reviewer 每条意见恰好一个）

| 路由 | 含义 | 处理 |
|---|---|---|
| `idea.md` | 方向、Gap、RQ、贡献、风险表述 | 本技能修改 |
| `analysis-plan` | 设计基准、结论目标、模型设定、任务、检验、解读边界 | 第 2 节由本技能写；其余交 `/analysis` Plan |
| `analysis-run` | 已批准设计下缺少的推导 / 脚本 / 检验 | `/analysis` |
| `technical` | 正文技术章节与 register 或计划不一致 | `/technical` 修复 |
| `polish` | 技术英文的纯语言问题 | `/polish` |
| `narrative` | Introduction / LR / Discussion 内容问题 | `/narrative` |

---

## 步骤 4：执行修改（用户确认后）

1. **idea.md**：只改方案列出的内容，保留结构；版本号 minor +1（`v2.3 → v2.4`），更新 `> **日期**` 行。
2. **设计基准**：`analysis_plan.md` 存在 → 写入或替换第 2 节条目（5–8 条，每条一句"借什么"）；不存在 → 写 `idea-refine/design_benchmarks_r{M}.md`。
3. **设计层改动且计划状态为 approved**：
   - 在第 7 节表格末尾追加一行（只追加，不改旧行）；
   - 状态行不改（`/analysis` 以"第 7 节最后一条【设计层】行之后没有'重新批准计划'行"判定需要重新批准——该判据在 submitted / revision 阶段同样有效；重新批准时由它更新批准日期并追加"重新批准计划"行）；
   - 项目阶段（规格 §1）：当前为 `analysis` 或 `drafting` → 项目合同 `## 项目阶段` 改为 `状态: foundation`、`更新时间: {今天}`；当前已是 `foundation` → 不改；当前为 `submitted` 或 `revision-R{N}` → 不改阶段，只追加第 7 节，并提示经 `/rev-respond` → `/analysis` → `/technical` 回流。
4. **设计层改动但计划仍为 draft 或不存在**：不写第 7 节（批准前的迭代无需变更记录），阶段保持不变；提示 `/analysis` Plan 吸收这些改动。
5. 不直接修改 `manuscript.tex`、register、technical_map 或任何正文。
6. 保存修改后快照 → `idea-refine/idea_v{新版本}_after_r{M}.md`。

Edit 因找不到原文失败（用户在审稿期间手动改了文件）→ 重新读取、说明外部修改、重新生成方案并再次确认。

---

## 步骤 5：下一轮

```
第{M}轮修改完成。Reviewer 成熟度判断：{Part II 摘录}
(1) 进行下一轮审稿  (2) 结束
```

(1) → M += 1，回到 0.5 快照 → 步骤 2（设计基准未变更时不重做步骤 1）。(2) → 步骤 6。

---

## 步骤 6：收尾（不自动 commit）

```
✅ idea-refine 完成
- 总轮数 {M}；版本 v{START} → v{FINAL}；采纳 {a}/{n}
- 写入：idea.md {✓/–}；analysis_plan 第 2 节 {✓/–}；第 7 节 {✓/–}；阶段回退 {✓/–}
- 工作目录：structure/0_global/idea-refine/（列出文件）

💡 下一步：{按状态与回流清单：/analysis Plan、/technical、/narrative、/polish 等}

📦 建议提交（需你确认后才执行）：
  范围：structure/0_global/idea.md structure/0_global/analysis_plan.md structure/0_global/idea-refine/ CLAUDE.md（仅列本次实际改动的文件）
  信息：idea-refine round {M} (v{FINAL})
```

用户确认后才执行 `git add` / `git commit`；未确认不做任何 git 操作。

**文献同步提醒**（本轮修改了 Gap / RQ 时追加）：
```
⚠️ Gap/RQ 已变更，以下产物可能过时：literature_search_plan.md、tagged_reports/、citation_pool/、master_report.md
  (a) 微调（方向不变）→ 无需重跑；写 Intro / LR / Discussion 时复查对齐
  (b) 显著变更（方向漂移）→ /lit-plan → /lit-workflow
```

---

## 边界条件

| 情况 | 处理 |
|---|---|
| idea.md 不存在或近空 | 停止，提示先创建 |
| idea.md 无版本行 | 视为 v0.0，首次修改时补写 |
| 无 idea-mine-ref/ | 正常运行 |
| 找不到 profile | 用 `_generic` 并提醒；`_generic` 也缺失则无 profile 继续 |
| analysis_plan.md 不存在 | 设计基准存入 `idea-refine/design_benchmarks_r{M}.md`；不创建计划文件 |
| 用户立即选 "done" | 不创建 confirmed 文件，保留快照与 review，进入收尾 |
| reviewer 调用失败 | 报告错误，等待指示 |
| 跨 session 续用 | 按已有文件续接轮次 |
| 意见涉及正文 | 不直接修改，按路由回流 |
| `## 技术章节` 为占位 | 状态不可能为 `TEXT`；按 `ANALYSIS` 或更早处理 |
