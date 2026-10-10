---
description: "逐条处理 Editor / AE / Reviewer 意见（rev-init 之后）：策略确认 → 前置证据门（补分析类先回流 analysis → technical）→ 回复与稿件修改起草 → 语言润色与审计 → 最终综合确认 → 写入、编译、条件式提交；全部完成后 finalize 做修订包收尾"
---

# Rev-Respond — 两次确认式逐条审稿回复

> 规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（冲突以规格为准）。正文精简规则：`~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。
> 子 agent：可以在需要时使用子 agent（定义在 `~/.claude/agents/`），并在执行前告诉用户将派出哪些。
> Git：只有最终综合确认中用户明确选择提交时才 stage / commit；从不 push。
> 阶段：修改期间项目阶段保持 `revision-R{N}`。补分析与设计调整都在 revision 阶段内完成：`/analysis`、`/idea-refine` 在此阶段只在 `analysis_plan.md` 第 7 节记变更、不改阶段；本技能也不写阶段。

对单条审稿意见执行完整闭环：策略对齐 → 内容起草 → 语言润色与审计 → 最终综合确认 → 写入、验证与条件式 checkpoint。

**正常路径只设两次确认**：
1. **策略确认**：确认回应方向、修改范围和证据边界。
2. **最终综合确认**：一次性确认润色后的最终回复与稿件文本、Write Gate、验证计划、focused staging 范围和 commit message。

Round 2 的未润色草稿不单独确认；Round 3 的润色结果、Round 4 的 Write Gate 和审计通过后的 Git checkpoint 合并为第二次确认。

**核心原则**：AI 自动完成只读准备工作，用户拍板研究方向和最终写入包。最终综合确认前不得修改 `{MAIN_TEX}`、`response-letter.tex` 或其他核心研究文件；策略提案等 L1 侧产物可在对应策略确认后保存。

**回退原则**：任何轮次中，如果用户的反馈表明需要调整前序轮次的决策，流程可以回退。回退时，从目标轮次重新开始，后续轮次全部重走。具体回退触发条件在各轮次的用户交互环节中定义。

**子 agent 调用**：`language-polisher` / `language-auditor` 的定义在 `~/.claude/agents/`；调用方式：Agent 工具，`subagent_type` 取角色名（如 `language-polisher`、`language-auditor`）。

## 输入说明

`$ARGUMENTS` 格式：
- Comment 编号：`E-1` / `AE-1` / `R1-1` / `R1-m2` / `R2-3` 等
- 可选附加指令用 `|` 分隔：`R2-3 | 重点说明 fsQCA 校准问题`
- 全部 Comment 完成后的独立收尾：`finalize`
- 空参数 → 停止，提示用户指定 Comment 编号

编号映射到 response-letter.tex：
- `E-1` → `Comment \#E-1`
- `AE-1` → `Comment \#AE-1`
- `R1-1` → `Comment \#1-1`
- `R1-m1` → `Comment \#1-m1`
- `R2-3` → `Comment \#2-3`

---

## Step 0: 上下文加载

### 0a. 解析输入

从 `$ARGUMENTS` 中提取：
- Comment ID（如 `R2-3`）
- 可选用户附加指令（`|` 后的内容）

如 `$ARGUMENTS = finalize`，设置 `FINALIZE_MODE=true`，完成 0b 的轮次与环境检查后读取 `{MAIN_TEX}`、`response-letter.tex`、全部 `Comment_*.md` 和必要编译产物，跳过 Comment-specific 的 0c--0e 与 Round 1--4d，直接进入 4e。

否则验证格式：`E-数字`、`AE-数字`，或 `R` + 数字 + `-` + 数字/`m`+数字。无效 → 停止，提示正确格式。

### 0b. 前置环境检查 + 轮次检测

从 CLAUDE.md 的 `## 项目阶段` 字段提取当前轮次 `{ROUND}`（如 `revision-R2` → `ROUND=2`）。当前轮次的工作目录为 `revision-R{ROUND}/`。

检查 `/rev-init` 是否已执行：
- 确认 `revision-R{ROUND}/comment-letter-clean.md` 存在
- 确认 `revision-R{ROUND}/revision-guide.md` 存在
- 确认 `response-letter.tex` 存在
- 确认 `.revision-main` 存在并读取为 `{MAIN_TEX}`；若不存在，则从 CLAUDE.md / `manuscript.tex` / `main.tex` fallback 推断，并提示用户这是兼容路径

任一文件缺失 → **停止**，提示用户："请先运行 `/rev-init` 初始化修改工作流。"

### 0c. 读取项目上下文

依次读取以下文件：
1. `revision-R{ROUND}/comment-letter-clean.md` → 定位该 Comment 的完整评论文本
2. `revision-R{ROUND}/revision-guide.md` → 找到所属 Cluster、核心问题、修改计划、锚点信息
3. `{MAIN_TEX}` → 全文（重点关注与该 Comment 相关的 section）
4. 项目 `.bib` 文件 → 可用引用（从 CLAUDE.md 或 `{MAIN_TEX}` 的 `\bibliography{}` 确认文件名）
5. `response-letter.tex` → 定位该 Comment 的填写位置，同时检查哪些 Comment 的 `[TO BE FILLED]` 已被替换（= 已完成）
6. 如 `supplemental-materials.tex` 存在 → 读取（该 Comment 可能涉及补充材料修改）
7. 对 `E-K` / `AE-K`，读取对应 Editor / AE 全文与所有已确认策略，避免将总体决定误当作单条意见

### 0d. 检查同 Cluster 上下文

扫描 `revision-R{ROUND}/drafts/` 目录：
- 查找同 Cluster 的 `Proposal_*.md` 和 `Comment_*.md`
- 如有 → 读取已确认的策略和回复，保持一致性
- 判断交叉引用类型：
  - **同审稿人**（如 R1-4 和 R1-1 同属 C1）→ 回复中可直接引用（"As discussed in our response to Comment #1-1 above..."）
  - **跨来源**（不同 Reviewer，或 Editor/AE 与 Reviewer 之间）→ **必须自含式回复**，不可依赖其他来源的 Comment

### 0e. 防护检查

- `revision-R{ROUND}/drafts/Proposal_{Comment_ID}.md` 或 `Comment_{Comment_ID}.md` 已存在 → AskUserQuestion："该 Comment 已有草稿文件：**1** = 覆盖重做 / **2** = 跳过"；若 Proposal 的"回流状态"为 `待回流`，增加选项 **3** = 沿用已确认策略继续（回流已完成，直接进入 Round 2 的前置证据门）
- `response-letter.tex` 中该 Comment 的 `\response{[TO BE FILLED]}` 已被替换（即已有实质回复内容）→ 警告用户，AskUserQuestion："该 Comment 已有回复内容：**1** = 覆盖重做 / **2** = 跳过"
- 该 Cluster 依赖的其他 Cluster 尚未完成（检查方法：revision-guide.md 中依赖 Cluster 的 Comments 在 response-letter.tex 中仍有 `[TO BE FILLED]`）→ 警告（非阻断）："⚠️ C2 依赖 C1，但 C1 尚未完成。建议先处理 C1。"

---

## Round 1: 策略对齐

### 1a. 生成策略提案

在对话中展示策略提案（**不写文件**）：

```
## 策略提案 — {Comment ID}

### 意见原文
> [从 comment-letter-clean.md 摘录该 Comment 的完整原文]

### 真正关切
[1-2 句话提炼该意见本质上在问什么——不是转述原话，而是分析后的核心]

### 所属 Cluster
C{N}: {名称} | 角色: {Anchor/Satellite} | 同 Cluster 已确认: {列出或"无"}

### 执行类型
[Text-only / Bibliography / Analysis-data / Figure-table / Supplemental / Mixed]

### 前置证据与产物
- [需要先获得或验证的文献、分析结果、脚本输出、图表/表格或补充材料；无则写“无”]
- [证据文件路径与当前状态]

### 回流路线（仅 Analysis-data，或需要新数据图表的 Figure-table / Mixed）
- 需要的新结果：[一句话；对应 analysis_plan 第 1/3/4/5 节哪一处]
- register 中是否已有可用条目：[register ID（如 F7）或"无"]
- 路线：/analysis（第 7 节追加变更记录并确认 → Run → Release 重新发布 results_register）→ /technical 修复受影响技术段落 → 回到本 Comment
- 是否触及设计层（RQ / 模型族 / 主设定 / 数据边界 / 核心构念）：[否 / 是 → 先 /idea-refine]

### 修改方向
- [要点 1: 改什么、在哪里]
- [要点 2: 补什么]
- [要点 3: 回复怎么论证]

### 影响位置
- {MAIN_TEX}: {Section Name}, Lines {XXX--YYY}
- supplemental-materials.tex: {如涉及}

### 风险/权衡
- [风险 1: 如 "新增定义可能与 Eq.(3) 冲突"]
- [风险 2: 如 "审稿人可能期望超出我们数据支撑的内容"]

### 回复策略
- 论证路径: [怎么构建论证——用什么逻辑、从哪个角度]
- 文献支撑: [具体可引用的文献]
- 与同 Cluster 关系: [需要与哪些已确认策略协调/完全独立]
```

### 1b. 用户交互

AskUserQuestion：

```
以上是 {Comment ID} 的策略提案。请审阅：
- 方向是否正确？
- 有无遗漏的关键点？
- 对风险的判断是否合理？
- 有无要补充的信息/约束？

**1** = 确认策略，或直接输入调整意见。
```

用户输入调整意见 → 根据反馈修改策略，重新展示 → 再次 AskUserQuestion。**迭代直到用户输入 1**。

### 1c. 保存确认的策略

写入 `revision-R{ROUND}/drafts/Proposal_{Comment_ID}.md`：

```markdown
# 策略提案 — {Comment ID}

> **来源**: Editor / Associate Editor / Reviewer #{X}
> **所属集群**: C{N} — {Cluster 名称}
> **角色**: {Anchor/Satellite}
> **确认日期**: {当前日期}

## 意见原文
> {从 comment-letter-clean.md 摘录的完整原文}

## 真正关切
{确认的内容}

## 修改方向
{确认的内容}

## 影响位置
{确认的内容}

## 回复策略
{确认的内容}

## 执行类型与前置产物
{确认的内容}

## 回流
- 回流状态: 不需要 | 待回流 | 已完成（YYYY-MM-DD）
- 需要的新结果与对应 register ID: {确认的内容}

## 用户附加指令
{用户在讨论中提出的额外要求，如有}
```

---

### 1d. 补分析回流（回流状态 = 待回流 时）

策略确认后、起草之前执行。本技能不做分析、不改技术章节正文，也不改项目阶段：

1. 告诉用户回流路线，并停止本次运行：
   - `/analysis`：在 `analysis_plan.md` 第 7 节追加一行（时刻 YYYY-MM-DD HH:MM｜改了什么｜原因：回应 {Comment ID}｜影响：register 的哪些条目 / technical 的哪些段落 / narrative 的哪些部分），经用户确认后 Run → Release，重新发布 `results_register.md`（新结果追加新 ID，原 ID 不改号）。修改阶段内 analysis 不改阶段。
   - 意见触及设计层时，先 `/idea-refine`（同样只记变更、不改阶段），再回到 `/analysis`。
   - `/technical`（修复模式）：按新 register 修复受影响的技术段落，完成后重写 `technical_map.md` 的依据日期与"技术正文完成"日期。
2. 回流完成后，用户重新运行 `/rev-respond {Comment ID}`，在 0e 选 **3** 沿用策略继续。

---

## Round 2: 内容起草

### 2a. 生成两部分内容

基于确认的策略，生成：

#### Part A — Response Letter 文本（LaTeX）

完整的回复文本，可直接粘贴到 `response-letter.tex`：

```latex
\response{[开场：感谢并承认问题 — 1-2句，措辞独特；不使用 First/Second/Third]}

\response{First, [第一项实质解决动作或论证]. [说明具体修改及其如何解决问题].}

\manuscriptquote{[修改后的稿件文本] \lineref{Lines XXX--YYY}}

\response{Second, [第二项实质解决动作或论证]. [展开].}

\manuscriptquote{[修改后的稿件文本] \lineref{Lines XXX--YYY}}

\response{Third, [第三项实质解决动作或论证]. [展开].}

\response{[总结句]}
```

注意：`\responseheader` 已在骨架中存在，回复内容只需填入 `\response{}` 中，不要重复添加 `\responseheader`。

**格式规则**（铁律）：
- `\response{}`、`\manuscriptquote{}`、`\lineref{}` **不可嵌套**
- `\response{}` 在 `\manuscriptquote{}` 之前关闭，之后重新打开
- `\response{}` **内部不能有空行**（会导致 `\par` 错误）
- `\lineref{}` 放在 `\manuscriptquote{}` 的**内容末尾**
- `\lineref{}` **一律写 `\lineref{Lines [TBD]}`**，不在逐条处理时填真实行号。原因：`\lineref{}` 中的行号 = 编译后 PDF 的 running line numbers（由模板 cls 自动生成），不是 .tex 源文件行号；且每次改稿后行号会漂移。所有 Comment 完成后在 Round 4e 批量回填
- Section 引用格式：`the ``Introduction'' section`（section 名称加引号，小写 section）
- 感谢、认同或承认问题只属于未编号的开场段，不计为 `First`。`First`、`Second`、`Third` 必须从实际解决问题的修改动作、证据或论证开始。

**引用格式**（response-letter.tex 不使用 natbib）：
- `(Author et al., Year)` 替代 `\citep{}`
- `Author et al. (Year)` 替代 `\citet{}`
- 两位作者写全：`(Smith and Jones, 2023)`
- 三位及以上用 et al.：`(Wang et al., 2024)`
- 从项目 `.bib` 文件查找实际作者和年份

**感谢措辞**（每条 Comment 不同）：
- "We thank the reviewer for this comment on [具体话题]."
- "We appreciate the reviewer's attention to [具体方面]."
- "This is a constructive observation. We address it as follows."
- "The reviewer raises a valid concern about [具体问题]."
- "Thank you for the careful examination of [具体方面]."
- 检查 `revision-R{ROUND}/drafts/` 中已有回复，确保不重复
- `E-K` / `AE-K` 使用 "the Editor" / "the Associate Editor"，不得统称 reviewer
- 感谢后可以直接承认问题或推断边界，但不得把这段机械开场编号为 `First`

**跨来源引用规则**：
- **同审稿人内**：可直接引用，如 "As discussed in our response to Comment #1-1 above, ..."
- **跨来源**：**禁止**依赖其他 Reviewer、Editor 或 AE 的 Comment。回复必须自含。

**来源级收尾规则（强制）**：
- Editor、AE 或 Reviewer 的最后一条实质性 Comment 结束后，必须另设一段整体感谢；该段不属于最后一条实质性 Comment
- 若原始意见在全部 Major/Minor Comments 之后含 `Recommendation` 或总结性评估，必须将其保留为来源末尾的独立 `\reviewercomment{Recommendation.}` block，不得并入 General Assessment；对该 block 的回应应概括已完成的对应修改并以整体感谢收尾
- 若原始意见含 ``Hope the comments might help'' 等 closing courtesy，必须用独立的 `\reviewercomment{Closing comment.}` 保留原文，并在 `\responseheader` 后回应
- 若原始意见没有 closing courtesy，直接在该来源部分末尾添加独立的 `\response{}` 整体感谢
- 收尾感谢不使用 First/Second/Third，不添加 `\manuscriptquote{}` 或 `\lineref{}`，也不计入 actionable comment 数量
- 对现有项目，发现 closing courtesy 被并入最后一条 Comment 时，将其拆出并同步对应 Proposal/Comment 侧产物
- 对现有项目，发现来源级 Recommendation 被并入 General Assessment 时，将其移回该来源末尾，并同步 General Response 与 Recommendation 侧产物

**论证要求**：
- 开场感谢与承认问题后，再使用 `First`/`Second`/`Third` 组织三项实质回应
- 每个编号项必须说明一项实际修改、证据处理或 rebuttal 论证；不得用 `First` 仅重复“我们同意该问题”
- 不要只说"我们改了"，要说明**为什么这样改**和**如何解决审稿人的问题**
- 引用具体文献支持论证
- 对方法论/假设类问题，从学科理论基础和文献先例两个角度论证
- 审稿人建议无法完全采纳 → 礼貌但坚定解释原因 + 提出替代改进

#### Part B — 稿件修改方案

逐条列出具体修改（polish 风格）。除 `{MAIN_TEX}` 和补充材料外，可列入本条意见确实需要的 `.bib`、分析脚本/结果、表格或图文件：

```
### 修改 1: [简述]
**文件**: {MAIN_TEX}
**位置**: {Section Name}, Lines {XXX--YYY}
**类型**: Rewrite / Insert / Delete

**当前文本**:
> [从 {MAIN_TEX} 精确摘录的当前文本]

**修改为**:
> [提议的新文本]

**理由**: [为什么这样改]

### 修改 2: [简述]
**文件**: supplemental-materials.tex（如涉及）
**位置**: ...
...
```

修改文本同样遵循科技写作纪律。方法描述中的被动语态（如 "samples were collected"）属学科惯例，可保留。

如不需要修改原稿（纯解释类回复），明确声明："本条意见无需修改原稿。"

**证据门槛**：
- 如需新增文献，先核实文献并准备准确的 bib 条目；不得编造引用
- 如需新增/重跑分析（回流状态 ≠ 不需要），起草前逐项核对，任一不满足 → 停在这里并给出缺的回流步骤：
  1. Proposal 列出的新结果在 `results_register.md` 中有对应 register ID，来源文件存在；
  2. `analysis_plan.md` 第 7 节有回应本 Comment 的变更行；
  3. register 发布日期不早于该变更行日期，`technical_map.md` 的"技术正文完成"日期不早于 register 发布日期，依据日期等于当前发布日期（即日期检查 D4 / D5 / D6 / D7 均不触发）。
  通过后把 Proposal 的回流状态改为 `已完成（日期）`。技术章节中的新内容已由 `/technical` 写入：Part B 对这些段落只引用当前正文（用于 `\manuscriptquote{}`），不再改写；Part B 只包含技术章节以外的修改。回复中的数字与结论必须与 register 条目一致，不得超出其解读边界。
- 如需新增图表，先确认数据来源、编号和最终文件路径
- 前置产物未就绪 → 停在 Round 2，列出缺口；不得进入润色或执行

**生成完成后，执行质量自检（见文末 4 项清单），修正发现的问题后直接进入 Round 3，不展示未润色草稿。**

### 2b. 内部内容审查（不设用户确认卡）

生成 Part A 和 Part B 后，执行文末 4 项质量自检并修正明显问题。不要展示未润色草稿，也不要要求用户确认；直接进入 Round 3。

如出现以下情况，停止而不是继续润色：
- 前置证据、分析结果、文献或图表尚未就绪；
- 起草过程暴露出与 Round 1 策略实质冲突的新问题；
- 修改范围需要超出策略确认时列出的文件或研究主张。

前置产物缺失 → 列出缺口并等待用户处理。策略或范围发生实质变化 → 回退 Round 1，重新展示策略确认卡。这属于异常回退，不是正常路径中的新增确认。

### 2c. 准备 Comment 侧产物内容

在内存中按以下结构准备 `revision-R{ROUND}/drafts/Comment_{Comment_ID}.md`，待最终综合确认后再与核心文件一起写入：

```markdown
# Comment {Comment_ID} 回复

> **来源**: Editor / Associate Editor / Reviewer #{X}
> **意见编号**: {Comment ID} — {简短标题}
> **所属集群**: C{N} — {Cluster 名称}
> **角色**: {Anchor/Satellite}
> **确认日期**: {当前日期}

---

## 意见原文
> {从 comment-letter-clean.md 摘录的完整原文}

---

## Part 1: 策略（来自 Proposal）

{从 Proposal 文件复制确认的策略}

---

## Part 2: 回复正文 (LaTeX)

以下文本可直接粘贴到 `response-letter.tex`。

```latex
{待润色的 LaTeX 回复文本}
```

---

## Part 3: 原稿修改

{待润色的修改方案，或 "本条意见无需修改原稿。"}

---

## 交叉引用

- **同来源相关意见**: {可直接引用的 Comment}
- **跨来源相关意见**: {必须自含式的 Comment}
```

---

## Round 3: 语言润色

### 3a. 准备润色文本

从 Round 2 生成并自检的内容中提取所有英文文本：
- **Part A**: Response Letter 回复正文（`\response{}` 内的英文文本）
- **Part B**: 稿件修改方案中"修改为"部分的英文文本

将两部分合并为一个润色请求，保留 LaTeX 命令结构（`\response{}`、`\manuscriptquote{}`、`\lineref{}` 等不动，只润色其中的英文内容）。

### 3b. 调用 language-polisher agent

执行前告诉用户：将派出 1 个 language-polisher，完成后再由 3 个 language-auditor 并行只读审查；所有 agent 不直接写项目文件。

调用 language-polisher（Mode B — Ad-hoc；Agent 工具，`subagent_type` 取角色名（如 `language-polisher`、`language-auditor`）），prompt：

```
  "Mode B (Ad-hoc). Polish the following academic English text.
           This is a response letter and manuscript revision for
           {期刊名，从 revision-guide.md Section 1 或 CLAUDE.md 读取}.
           Preserve all LaTeX commands exactly as-is.

           IMPORTANT: Text inside \manuscriptquote{} in Part A is a direct
           quotation from the revised manuscript. It MUST remain identical
           to the corresponding revised text in Part B. If you polish a
           sentence in Part B, apply the exact same change inside the
           matching \manuscriptquote{} in Part A.

           --- Part A: Response Letter ---
           {Part A 文本}

           --- Part B: Manuscript Revisions ---
           {Part B 修改文本}

           Terminology (binding, if available): {technical_map.md 第 2 节术语表}
           Do not add hedges, caveats, or defensive sentences."
```

### 3b2. Language Auditor 系统审查

对润色后的文本，**并行**调用 3 个 language-auditor（`subagent_type: "language-auditor"`），分别指定 Group 1/2/3。收集报告后，如有 issues，汇总到润色结果中一并展示给用户。

### 3c. Dry-run + Final Approval, Write, and Checkpoint Gate

完成 language-polisher 和 3 组 language-auditor 后，主 Agent 保守整合审计建议；不得为满足形式化语言规则而改变论证强度、技术术语或用户要求的修改边界。

在展示最终版本前先完成只读 dry-run：
1. 对每条修改的旧文本或结构锚点确认精确存在且唯一。
2. 确认回复信中目标 Comment 块及占位符/旧回复的结构边界唯一。
3. 运行 `git status --short` 和 `git diff --cached`，识别目标文件中的既有未提交或已暂存修改。既有 staged 状态与本条目标文件重叠且无法安全保留时，将 `conditional commit = blocked` 写入确认卡。
4. 为包含无关修改的目标文件规划 partial-hunk staging；无法安全拆分时，将 `conditional commit = blocked` 写入确认卡。

任一核心写入锚点失败 → `FAIL-BLOCKED`，不得展示可执行授权卡。

一次性展示：
- 策略摘要与修改边界；
- 润色后的 Part A（完整 LaTeX 回复文本）；
- 润色后的 Part B（全部最终新文本及必要 old/new）；
- Change Summary；
- Audit Report 与主 Agent 的采纳/拒绝说明；
- 将写入的精确文件、修改类型和验证命令；
- 将 stage 的精确文件或 hunks、明确排除的工作区修改；
- 建议 commit message；
- `git push = not authorized`。

最终综合确认（AskUserQuestion）：

```
📌 Final Approval + Write + Conditional Checkpoint — {Comment ID}

本次确认将授权：
1. 接受以上润色后的最终回复和稿件修改；
2. 写入或更新 Comment/polish 侧产物；Round 1 已保存的 Proposal 仅在策略发生经确认的变化时更新；
3. 对列出的核心文件执行一次原子 patch；
4. 编译 {MAIN_TEX}、response-letter.tex 和 tracked-changes 稿并执行 Audit Gate；
5. 仅当 Audit Gate = PASS 或 PASS-WITH-LOG 时，按上面列出的精确范围 focused stage 并创建：
   C{N} {Comment_ID}: {brief description}

**1** = 批准最终文本、写入、验证及审计通过后的 focused commit
**2** = 批准最终文本、写入和验证，但不 stage/commit
或直接输入调整意见。

本确认不授权 git push，也不授权暂存任何未列出的修改。
```

如 dry-run 已标记 `conditional commit = blocked`，不得展示上述 commit 授权选项。改用：

```
**1** = 批准最终文本、写入和验证；本次不 stage/commit
或直接输入调整意见。
```

并在同一卡片中写明阻断 commit 的具体原因。

用户输入调整内容 → 根据调整幅度分三种处理：

**场景 A — 语言微调**（换个词、删一句、调语序）：
主 Agent 直接修改对应文本，不重新调用 polisher。重新执行相关一致性检查和 dry-run 后，再次展示最终综合确认卡。

**场景 B — 局部重写**（加了新句子、重写了一段、补充了新论点）：
主 Agent 先按用户意见修改文本，然后**仅将改动部分**重新丢给 language-polisher agent 润色。重新执行对应 auditor、一致性检查和 dry-run 后，再次展示最终综合确认卡。

**场景 C — 方向推翻**（论证方向错误、内容策略需要调整、需要重新组织整体结构）：
**回退到 Round 2**。重新起草内容并进入 Round 3 走完整润色、审计和 dry-run；Round 2 不新增确认。如果方向性调整涉及策略层面的改变，进一步回退到 Round 1 重新对齐策略。

**判断标准**：由主 Agent 根据用户反馈的性质判断属于哪种场景。如不确定，询问："您的调整是语言层面的修改，还是内容方向需要调整？"

**迭代直到用户输入 1 或 2**。

### 3d. 记录最终综合授权

- 正常最终综合确认卡中，用户输入 `1` → `write_authorized = true`，`conditional_commit_authorized = true`。
- 正常最终综合确认卡中，用户输入 `2` → `write_authorized = true`，`conditional_commit_authorized = false`。
- `conditional commit = blocked` 版本的确认卡中，用户输入 `1` → `write_authorized = true`，`conditional_commit_authorized = false`。
- 其他输入不授权写入、stage 或 commit。

用户输入 `1` 或 `2` 后，用润色后的最终版本写入 `revision-R{ROUND}/drafts/Comment_{Comment_ID}.md`。Comment 中 Part 2 与 Part 3 必须与最终综合确认卡逐字一致。

---

## Round 4: 执行

### 4a. 已授权的原子写入

从 `revision-R{ROUND}/drafts/Comment_{Comment_ID}.md`（Round 3 润色后的最终版本）读取 Part 3 原稿修改。

**执行顺序（严格）**：

1. **授权校验**：必须存在 Round 3 最终综合确认卡的用户输入 `1` 或 `2`；否则停止。
2. **Dry-run 复核**：立即写入前再次确认锚点与工作区状态未变化。与确认卡不一致 → `FAIL-BLOCKED`，不得静默改用其他锚点。
3. **成组写入**：写入前在内存中保存每处 old_string；按确认卡顺序逐处用 Edit 工具写入（含 `response-letter.tex`）。任一处失败 → 用保存的 old_string 逐处恢复本次已写入的部分，确认恢复后停止并报告 `FAIL-BLOCKED`。
4. **非文本产物**：仅使用已经通过前置证据门槛且用户确认的图表、分析结果等产物，不在 Round 4 临时生成或改写研究结果。

**铁律**：仅改确认内容，不做额外修改。

### 4b. 回复信 patch 定位（**支持 0e 覆盖重做**）

从 `revision-R{ROUND}/drafts/Comment_{Comment_ID}.md`（Round 3 润色后的最终版本）读取 Part 2 回复正文。定位策略两种：

**情况 A — 占位符仍在**（首次填写 或 0e 选"跳过"后重跑）：
- 从该 Comment 的唯一 header 开始定位整块，只替换该块内的 `\response{[TO BE FILLED]}`；禁止对全文件相同占位符做无上下文替换。

**情况 B — 占位符已被替换**（0e 选"覆盖重做"或用户提前手填过）：
- 不存在 `[TO BE FILLED]` 锚点，但存在旧的 `\response{...}` 段。
- 使用结构锚点定位整块：`old_string` **必须从该 Comment 的 `\reviewercomment{Comment \#{Comment_ID}.}` 整行开始**（Reviewer ID 在模板中去掉前缀 `R`，E/AE 保持原样），**到下一个分隔锚点之前**为止。分隔锚点三类：
  1. 下一个 `\reviewercomment{Comment \#...}` 行
  2. `\newpage`
  3. `\end{document}`
  `new_string` = 新的整块（可保留多段 `\response{}` + `\manuscriptquote{}` 交替结构，与情况 A 产出保持一致），**必须原样保留开头的 Comment header**——否则整条 comment header 消失。
- ⚠️ **`\bigskip` 不是分隔锚点**——它是 Part A 模板在同一 Comment 内多段 response/manuscriptquote 之间的段内间隔符（见 168-183 行示例）。若把 `\bigskip` 当作终止会在第一个段内间隔就截断，漏掉本 Comment 后续的 response。
- **多匹配消歧**：完整 Comment header 必须全局唯一；同一 Comment 下若有多段 `\response{}` 与 `\manuscriptquote{}` 交替，必须把整块作为替换单元。
- **dry-run 前置**：整块 old_string 很长，空格/换行若有细微差异会 Edit 失败。4a 的 dry-run 规则同样适用 4b：先 Read 目标行区间验证 old_string 能精确匹配，再调 Edit。
- 0e 若选"覆盖重做"，**必须**走情况 B 路径，严禁退化为"找不到就跳过"（这是之前的 bug：覆盖后 response-letter.tex 静默保留旧内容）。

### 4c. 编译验证

执行修改后显式运行（不依赖编辑器 hook 的自动编译）：

```bash
latexmk -pdf -interaction=nonstopmode "{MAIN_TEX}"
latexmk -pdf -interaction=nonstopmode response-letter.tex
tools/make-diff.sh
```

任一编译/diff 失败，或出现 LaTeX Error、undefined citation、duplicate label、Float too large、Emergency stop → Audit Gate = `FAIL-BLOCKED`。报告错误且不自动扩大修改范围；不得宣布 Comment 完成或进入 commit。

### 4d. 条件式 focused checkpoint（不再次确认）

这是 `rev-respond` 的 skill-specific named-checkpoint auto-commit policy：

- 仅当 `conditional_commit_authorized == true` 时，Round 3 最终综合确认卡才构成对卡片内**精确列出的** stage 范围和 commit message 的一次性条件授权；不得根据用户输入数字脱离该变量重新推断权限。
- 只有 Audit Gate = `PASS` 或 `PASS-WITH-LOG` 时，该授权才生效。
- 用户输入 `2`、Audit Gate = `FAIL-BLOCKED`、写入范围变化、commit message 变化或 staged diff 无法与确认卡精确对应时，均不得 stage/commit。

授权生效后的执行顺序：
1. 运行 `git status --short` 并记录执行前的完整 staged snapshot。
2. 仅 stage 最终综合确认卡列出的文件或 hunks。目标文件含有其他未提交修改时，必须使用 partial-hunk staging 排除它们。
3. 运行 `git diff --cached --check` 并审阅完整 staged diff。
4. staged diff 出现未授权内容、遗漏本条必要内容或无法安全拆分 → 只撤销本次新增的 staged hunks，使 index 恢复到执行前 snapshot，然后 `FAIL-BLOCKED`；不得影响用户原有 staged 状态。
5. 使用确认卡中展示的 commit message 创建 checkpoint。
6. 提交后报告 commit hash，并确认无关工作区修改保持执行前原有的 staged/unstaged 状态。

此条件授权永远不包含 `git push`、branch 操作、restore、clean 或其他 Comment 的修改。

### 4e. 独立 Revision Package Closeout（仅 `finalize` 触发）

普通单条 Comment 运行结束时，扫描 `response-letter.tex` 中所有 `\response{[TO BE FILLED]}` 的数量：

- **仍有 `[TO BE FILLED]`** → 跳过此步骤，直接进入 4f 下一步提示
- **全部填完（0 个 `[TO BE FILLED]`）** → 不在当前 Comment 运行中自动启动行号回填或新增确认；仅提示用户另行运行 `/rev-respond finalize`

只有用户显式运行 `/rev-respond finalize` 时才执行以下收尾流程。进入后先确认 `[TO BE FILLED] = 0`；否则停止并列出未完成 Comment。

**报告生成**：

1. **确认 baseline 文件**：读取 `.revision-baseline` 获取基准文件名（如 `manuscript-R0.tex`）；不存在则 fallback 到 `manuscript-original.tex`（遗留格式）
   - 均不存在 → 警告并跳过

2. **逐 section 差异对比**：对比基准文件和当前 `{MAIN_TEX}`
   - 提取每个 `\section{}` 的内容，逐 section diff
   - 统计：新增字数、删除字数、净变化

3. **生成修改摘要**（写入 `revision-R{ROUND}/revision_summary.md`）：

```markdown
# Revision Summary

> Generated: {date}
> Baseline: {BASELINE}（从 .revision-baseline 读取）
> Current: {MAIN_TEX}

## Overview

| 指标 | 数值 |
|------|------|
| 总 Comment 数 | {N} |
| 已回复 | {N} |
| 涉及稿件修改的 Comment | {M} |
| 纯解释（无修改） | {N-M} |

## Changes by Section

| Section | 新增 | 删除 | 净变化 | 涉及 Comment |
|---------|------|------|--------|-------------|
| Introduction | +{n} | -{n} | {±n} | R1-2, R2-1 |
| Literature Review | +{n} | -{n} | {±n} | R1-3 |
| ... | ... | ... | ... | ... |

## Comment → Modification Mapping

| Comment | 修改位置 | 修改类型 | 简述 |
|---------|---------|---------|------|
| R1-1 | Section 3, L120-135 | Rewrite | {从 Comment 草稿提取} |
| R1-2 | Section 1, L45-50 | Insert | {从 Comment 草稿提取} |
| R2-3 | — | 无修改 | 纯解释 |
| ... | ... | ... | ... |
```

4. **回填 `\lineref{}` 行号**：
   - 保留 `\lineref{Lines [TBD]}`，根据最终编译后的 manuscript PDF 逐条定位
   - 展示 Comment → 引文 → PDF 行号映射，等待用户确认
   - 通过单独 Write Gate 批量写入 `response-letter.tex` 和对应 `Comment_*.md`
   - 未确认或仍有 `[TBD]` → `FAIL-BLOCKED`，不得把 `???` 当作完成状态

5. **日期检查（规格 §4.6）**：按下文"日期检查"规则核对；有补分析类意见时，D4 / D5 / D7 不应再触发。触发条目只提醒，并列入 Audit Gate 报告，由用户决定先回流还是继续。

6. **Revision Package Audit Gate**：
   - 读取 `~/.claude/skills/rev-init/references/reference.md` 的“预提交检查清单”
   - 检查全部 E/AE/Reviewer 回复、引文逐字一致性、行号、图表编号、bib 完整性、三份 PDF 和可选补充材料
   - 检查每个来源部分均以独立的整体感谢结束；原始 Recommendation 位于全部实质性 Comments 之后，closing courtesy 作为独立 `Closing comment` 保留，且这些来源级收尾 block 不含稿件引文或行号
   - `PASS` 后才允许提示运行 `/pre-submit`；`pre-submit` 只补充主稿与通用投稿文件检查，不能替代本 Gate

7. **展示报告** 给用户，提示：
```
Revision Package Audit：PASS
修改摘要已保存至 revision-R{ROUND}/revision_summary.md

下一步：
- 检查 response-letter.pdf 和 manuscript.pdf
- 运行 /pre-submit 做投稿前终检
- 确认后重新提交
```

### 4f. 下一步提示（仍有未完成 Comment 时）

展示：
- 当前 Cluster 剩余情况（从 revision-guide.md 获取 Cluster 成员列表，grep response-letter.tex 中对应 Comment 的 `[TO BE FILLED]` 计数）
- 当前 Comment 是该来源最后一个未完成的实质性 Comment 时，核对来源级 closing response 是否已经存在；缺失时将其列入本次最终写入包，不能在完成提示中静默遗漏
- 推荐下一条 Comment（Cluster 内：锚点优先；Cluster 间：按 revision-guide.md 执行顺序）
- 依赖警告（如有）
- 如全部 Comment 已完成，改为提示 `/rev-respond finalize`；不要在本次 Comment 运行中直接进入 4e

---

## 日期检查

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

---

## 科技写作纪律（指导 Round 2 起草）

> **定位**：此纪律指导 Round 2 内容起草的语言质量基线。Round 3 的 language-polisher agent 提供最终语言润色（Chinglish 消除、搭配校正、句式优化等）。起草阶段语言质量越高，润色阶段改动越小、风险越低。

**每一句**回复和修改文本必须通过以下检查：

| # | 规则 | 要求 | ❌ → ✅ |
|---|------|------|---------|
| 1 | 简单主动句式 | 一句一意，主语做动作 | "X was revised" → "We revised X" |
| 2 | 逻辑清晰 | 开场不编号；实质回应使用 First/Second/Third | "First, we agree..." → "We agree... First, we revised..." |
| 3 | 短句 | 目标 15-20 词，上限 25 | 长句 → 拆分 |
| 4 | 克制修饰 | 删除不传递信息的副词/形容词 | "significantly improved" → "improved" |
| 5 | 中式英语防治 | 检查动宾搭配 | "improve the level" → enhance |
| 6 | 压缩冗余 | 名词化→动词，删空洞修饰 | "carry out an investigation" → investigate |
| 7 | 破折号纪律 | em dash 每页≤2 | `---such as A, B---` → `, such as A and B,` |

> 感谢语句允许一个描述性形容词（如 "constructive feedback"），正文严格执行。

---

## 质量自检（4 项）

> **执行时机**：Round 2 内容起草完成后、展示给用户之前。AI 内部自检，仅在发现问题时报告给用户。

1. **Part A ↔ Part B 一致性**：`\manuscriptquote{}` 中引用的文本必须与 Part B 的实际修改文本完全一致
2. **跨来源自含性**：不同 Reviewer、Editor、AE 的回复不可依赖对方的 Comment，必须自含式
3. **同 Cluster 一致性**：与同 Cluster 已确认的回复在立场和措辞上保持一致
4. **LaTeX 格式正确**：`\response{}`、`\manuscriptquote{}`、`\lineref{}` 不嵌套；`\response{}` 内无空行
