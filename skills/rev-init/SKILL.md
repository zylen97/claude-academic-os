---
description: "一次性初始化修改工作流：确认并冻结提交基准 → 解析决定信（Editor / AE / Reviewer，E/AE 编号）→ 交互式分类与聚类 → 搭追踪文件与回复信骨架 → 概括性回复 → 项目阶段写为 revision-R{N}"
---

# Rev-Init — 修改工作流初始化

> 规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（冲突以规格为准）。
> 子 agent：可以在需要时使用子 agent（定义在 `~/.claude/agents/`），并在执行前告诉用户将派出哪些。
> Git：本技能不自动 commit / push；各 Checkpoint Card 只是建议的提交范围与信息，用户确认后才执行。
> 阶段：本技能是 `revision-R{N}` 的唯一写入者（Step 10b）。修改期间的补分析与设计调整都在 revision 阶段内完成：`/idea-refine`、`/analysis`、`/technical` 只在 `analysis_plan.md` 第 7 节记变更或修复正文，不改阶段。

一次性初始化论文修改项目：冻结基准稿件、解析审稿决定信、交互式分类与聚类、生成追踪文件骨架、构建回复信骨架、生成概括性回复。

**核心原则**：所有分类和聚类决策必须经用户确认后才执行。AI 提方案，用户拍板。

## 输入说明

`$ARGUMENTS` 可选，通常为空。如提供，视为附加指令（如 `审稿人编号从 #2 开始`）。

---

## Step 0: 前置检查

### 0a. 项目环境

- 确认主文件存在（优先读取 `.revision-main`；否则 Glob `manuscript.tex` 或 `main.tex`）。不存在 → 停止，提示用户
- 将检测结果暂存为 `{MAIN_TEX}`；通过 Step 1 Write Gate 后才写入 `.revision-main`
- 确认当前目录是 git 仓库（`git status`）。不是 → 停止，提示用户初始化

### 0b. 冷启动检测（遗留项目适配）

读取项目 CLAUDE.md → 检查是否包含关键字段（期刊名、模板类型、bib 文件名）。

**如果 CLAUDE.md 不存在或缺少关键字段** → 进入冷启动模式：

```
📋 检测到项目尚未完整配置。请确认以下信息：

1. 主文件: [自动检测结果，如 manuscript.tex 或 main.tex]
2. Bib 文件: [自动检测结果]
3. 目标期刊: ?
4. 出版社: [Elsevier / ASCE / Emerald / SAGE / IEEE / Wiley / 其他]
5. 编译方式: [从 latexmkrc 或文件头检测，如 pdflatex / xelatex]
6. 补充材料: [自动检测 supplemental-materials.tex / supplementary-materials.tex]
7. 作者信息（用于 Cover Letter 署名）: ?
```

用户确认后，生成或更新 CLAUDE.md 的 `## 项目信息` 和 `## 核心配置` 部分。不生成 `structure/` 目录——遗留项目不需要写作阶段的脚手架。

### 0c. 轮次检测

自动推断当前修改轮次 `{ROUND}`：

```
检测逻辑（按优先级）：
1. CLAUDE.md 的 `## 项目阶段` 字段中有 `revision-R{N}` →
   - 检查 `revision-R{N}/revision-guide.md` 是否存在：
     → 存在（R{N} 已初始化完成）→ ROUND = N + 1
     → 不存在（R{N} 初始化未完成或被清理）→ ROUND = N
   - 当 ROUND > 1 时，向用户确认："检测到 R{N} 已初始化，即将创建 R{ROUND} 修改结构，是否继续？"
2. 统计已有的 revision-R*/ 归档目录 → ROUND = 最大编号 + 1
3. 存在 manuscript-original.tex（旧格式）且无 revision-R*/ 归档 → ROUND = 1（遗留项目首次使用新系统）
4. 以上都没有 → ROUND = 1（全新项目）
```

展示检测结果并 AskUserQuestion 确认：

```
🔍 检测到当前应为第 {ROUND} 轮修改（R{ROUND}）。

确认？或输入正确的轮次编号。
```

### 0c2. 基准来源确认

明确展示当前 `{MAIN_TEX}` 的 Git 状态，并让用户确认它是否与投稿系统中的实际提交稿一致。若不一致，要求用户提供真实提交稿路径，复制该文件作为 `{BASELINE}`；不得默认用当前工作稿代替提交稿。

### 0d. Checkpoint Card — 归档前快照

在任何文件移动或覆盖之前，先展示 focused Checkpoint Card，等待用户明确确认后才执行 staging / commit：

```text
📌 Checkpoint Card — R${ROUND} pre-init snapshot

目的：
  在归档旧 revision 文件、覆盖 response-letter.tex 或冻结 baseline 之前保存安全快照。

拟 stage：
  - CLAUDE.md（如本轮冷启动或阶段信息有更新）
  - 当前已存在且将被归档/覆盖的 revision 文件（如有）

建议 commit message：
  R${ROUND} pre-init: snapshot before archiving R$((ROUND-1)) files

确认后我再执行 git add / git commit。
```

用户不同意提交时：AskUserQuestion「**1** = 不提交、继续（后续移动只做重命名 / 归档，不删除任何文件）/ **2** = 停止」。

### 0e. 已有文件处理（基于轮次）

任何 `mv` / `cp` 前先检查目标路径。目标已存在 → 停止并让用户选择新名称或取消；禁止静默覆盖历史归档、备份或 baseline。

**检查 `revision-R{ROUND}/` 是否已存在**（可能是上次 rev-init 中断留下的）：
- 已存在 → AskUserQuestion：「`revision-R{ROUND}/` 目录已存在：**1** = 移入 `_archive/rev-init-{TODAY}/revision-R{ROUND}/` 后重新初始化 / **2** = 停止」（不硬删）
- 不存在 → 继续

**如果 `revision/` 存在**（遗留项目的旧格式目录）：
- `ROUND == 1` → `mv revision revision-R0`（归档为 R0）
- `ROUND >= 2` → 警告用户存在旧格式目录，建议手动处理

**如果 `response-letter.tex` 已存在**：
- `ROUND >= 2` → 归档：`mv response-letter.tex response-letter-R$((ROUND-1)).tex`
- `ROUND == 1` 且已有实质内容 → 归档为 `response-letter.tex.bak` 后重建（保留备份，避免"保留不覆盖"分支下 Step 8 仍重写骨架的歧义）

**遗留兼容**：如果存在 `manuscript-original.tex`（旧格式）且 `ROUND == 1`：
- 不重复冻结，直接复用为 R0 基准
- 创建 `.revision-baseline` 指向它

---

## Step 1: 冻结基准

先展示 Write Gate，列出 `{BASELINE}`、`.revision-baseline`、`.revision-main`、`tools/` 和 `revision-R${ROUND}/`；用户明确批准后，冻结已确认的提交稿为本轮 diff 基准：

```bash
# 基准文件名：manuscript-R{ROUND-1}.tex
BASELINE="manuscript-R$((ROUND-1)).tex"
MAIN_TEX="{Step 0a 已确认的工作主文件}"
BASELINE_SOURCE="{Step 0c2 已确认的实际提交稿}"

# 遗留兼容：如果已有 manuscript-original.tex 且 ROUND=1，复用它
if [ "$ROUND" = "1" ] && [ -f "manuscript-original.tex" ]; then
    BASELINE="manuscript-original.tex"
else
    # 目标存在时必须停止；不得覆盖
    cp "$BASELINE_SOURCE" "$BASELINE"
fi
```

随后用 Edit 工具 写入 `.revision-baseline` 和 `.revision-main`（各一行），供 make-diff.sh 读取；不得使用 shell 重定向覆盖现有文件。

告知用户：`{BASELINE}` 已冻结，此后**永远不得修改**。随后展示 focused Checkpoint Card：

```text
📌 Checkpoint Card — R${ROUND} baseline frozen

拟 stage：
  - {BASELINE}
  - .revision-baseline
  - .revision-main

建议 commit message：
  R${ROUND}: Freeze baseline ({BASELINE}) for latexdiff

确认后我再执行 git add / git commit。
```

---

## Step 2: 创建目录 + 复制工具

```bash
mkdir -p tools revision-R${ROUND}/drafts
```

从 `~/.claude/skills/rev-init/` 读取以下文件并写入项目：
- `scripts/make-diff.sh` → `tools/make-diff.sh`（`chmod +x`）
- `assets/latexdiff-preamble.tex` → `tools/latexdiff-preamble.tex`

> 不需要项目级 hook。rev-init 只安装 `tools/make-diff.sh` 与 `tools/latexdiff-preamble.tex`；需要 track-changes PDF 时，由主 agent 或用户显式运行 `tools/make-diff.sh`（/rev-respond 每次写入后会运行）。`tools/make-diff.sh` 读取 `.revision-main` 与 `.revision-baseline`。

---

## Step 3: 获取决定信

AskUserQuestion：

```
请提供审稿决定信的来源：
  [1] 已粘贴到 revision-R${ROUND}/comment-letter.md
  [2] 直接在此处粘贴原文
  [3] 从文件路径读取
```

- 选 1 → 读取 `revision-R${ROUND}/comment-letter.md`，确认非空
- 选 2 → 用户粘贴内容 → 写入 `revision-R${ROUND}/comment-letter.md`
- 选 3 → 用户提供路径 → 读取 → 写入 `revision-R${ROUND}/comment-letter.md`

---

## Step 4: 解析决定信（主 Agent）

### 4a. 通读原始决定信

主 Agent 读取 `revision-R${ROUND}/comment-letter.md` 全文，理解整体结构。不同期刊/投稿系统的格式差异极大，需要 LLM 的语义理解能力来正确识别结构，不可使用硬编码脚本。

### 4b. 结构识别

识别并分离以下角色：
- **Editor / Handling Editor**：决定信正文、编辑要求
- **Associate Editor**（如有）：AE 综合评价
- **Reviewer #N**：每位审稿人的意见

注意：
- 审稿人编号保留原始编号（如 #2, #3, #4，不重编为 #1, #2, #3）
- 识别 Q&A 区域（如 ASCE EM 的标准化问答表），提取含实质性反馈的回答

### 4c. 编号处理

对 Editor、AE 和每位 Reviewer 的实质性意见进行编号：
- Editor 的独立可执行要求 → `E-1`, `E-2`, ...
- Associate Editor 的独立可执行要求 → `AE-1`, `AE-2`, ...
- 审稿人已分 Major/Minor → `RN-K` / `RN-mK`
- 审稿人未分 Major/Minor → 连续编号 `RN-1, RN-2, ...`（不强行分类）
- 保留原始编号；一个独立关切 = 一条 Comment
- 同一段落内多个独立问题 → 拆分为独立 Comment
- 保留完整原始英文文本，不改写不缩减
- 纯决定通知、感谢或无执行要求的 Editor/AE 文本保留为 General，不强行编号
- 识别来源末尾的礼貌收尾语，如 ``Hope the comments might help''、``Thank you for considering these comments''。将其保留为独立的 `Closing comment`，不得并入最后一条实质性 Comment，也不得计入 actionable comment 数量
- 识别位于全部 Major/Minor Comments 之后的 `Recommendation`、总体建议或总结性评估。将其保留在来源末尾作为不编号的 `Recommendation` block，不得移入 General Assessment，也不得计入 actionable comment 数量

### 4d. 生成 comment-letter-clean.md

读取 `~/.claude/skills/rev-init/assets/comment-letter-clean.md.tmpl` 模板格式，生成 `revision-R${ROUND}/comment-letter-clean.md`，包含：
- 头部元信息（决定类型、日期、截止日期、编辑姓名）
- Editor / AE / 每位 Reviewer 各有独立标题
- 每条实质性意见有 ID 前缀（`**E-1.**`、`**AE-1.**`、`**R1-1.**`、`**R1-m1.**`）
- 每个来源的 General Assessment、Recommendation 与 Closing comment（如原文存在）分别保留为不编号的来源级文本，并保持它们在原信中的前后位置
- Q&A 区域提取（如有实质性反馈）
- 末尾的初步分类工作区表格（供 Step 5 填写）

### 4e. 展示并确认

展示统计摘要：
- 识别到 N 位审稿人
- 每位审稿人 N 条 Major / M 条 Minor
- 是否有 Q&A 提取
- 审稿人编号是否连续

AskUserQuestion：

```
解析结果如上。请检查：
- 审稿人数量和编号是否正确？
- 意见拆分是否合理？
- 有无遗漏的实质性意见？

**1** = 确认无误，或直接输入需要调整的地方。
```

用户输入调整意见 → 修改后重新展示 → 再次 AskUserQuestion。**迭代直到用户输入 1**。

---

## Step 5: 交互式分类

读取 `~/.claude/skills/rev-init/references/reference.md` 获取分类规则。

AI 对每条可执行 Comment（含 E/AE）提出分类建议：
- **类型**：Modify / Explain / Supplement
- **优先级**：Highest / High / Medium / Low

展示完整分类表：

```
| ID | 核心问题（5-8词） | 类型 | 优先级 | 备注 |
|----|-------------------|------|--------|------|
| R1-1 | 核心概念定义模糊 | Modify | Highest | R2-1 也提到 |
| R1-2 | 方程符号不一致 | Modify | Highest | R3-4 类似 |
| ...  | ... | ... | ... | ... |
```

AskUserQuestion：

```
以上是 AI 建议的分类结果。请逐条确认或修改：
- 修改某条：如 "R1-3: 优先级改为 High"
- 全部接受：**1**
```

**迭代直到用户输入 1**。

---

## Step 6: 交互式聚类（核心交互点）

读取 `~/.claude/skills/rev-init/references/reference.md` 获取聚类决策树和主题类别。

基于分类结果提出 Cluster 方案：

```
## 聚类方案

### C1: [名称] (Highest)
- 涉及: R1-1, R2-1, R3-1
- 锚点: R1-1（最详细，3个具体要求）
- 核心问题: [一句话提炼]
- 理由: [为什么这些意见归为一组]

### C2: [名称] (Highest)
- 涉及: R1-2, R3-4
- 锚点: R1-2
- 理由: [...]

...

### 依赖关系
C2 → C1（C1 需要 C2 的符号统一结果）

### 推荐执行顺序
1. C2（全局影响，无依赖）
2. C1（依赖 C2）
3. ...
```

AskUserQuestion：

```
以上是 AI 建议的聚类方案。请审阅并调整：
- 合并：如 "合并 C3 和 C5"
- 拆分：如 "C2 拆为 C2a 和 C2b"
- 调整归属：如 "R2-3 从 C1 移到 C4"
- 调整锚点：如 "C1 锚点改为 R2-1"
- 修改方向：如 "C3 重点改 Methods 而非 Introduction"
- 全部接受：**1**
```

**迭代直到用户输入 1**——这是整个初始化最关键的交互点。

### Checkpoint Card — 分类聚类确认后

分类和聚类方案用户确认后立即保存（这是最昂贵的交互产物）：

```text
📌 Checkpoint Card — R${ROUND} classification and clustering confirmed

拟 stage：
  - revision-R${ROUND}/comment-letter.md
  - revision-R${ROUND}/comment-letter-clean.md

建议 commit message：
  R${ROUND} rev-init: parsed comments + confirmed classification & clustering

确认后我再执行 git add / git commit。
```

### 特殊情况

**矛盾意见**：两位审稿人要求互相矛盾 → 放入同一 Cluster，标注 "⚠️ 矛盾"，要求用户做取舍决策。

**AI 使用披露**：审稿人质疑 AI 使用 → Highest 优先级合规问题。此条回复策略**必须由用户亲自确认**，AI 不得自行起草 AI 使用声明。

**需要补分析的意见**：要求新增 / 重跑分析、补稳健性检验、补数据图表的意见，在聚类方案中给所属 Cluster 标注 `需补分析`。这类 Cluster 在推荐执行顺序中靠前，并在 revision-guide 中注明回流路线：`/analysis`（计划第 7 节追加变更记录 → Run → Release 重新发布 results_register）→ `/technical` 修复受影响的技术段落 → 再由 `/rev-respond` 写回复。若意见要求改变 RQ、模型族或主设定（设计层），单独标注 `⚠️ 设计层`，交由用户决定是否接受。

---

## Step 7: 生成追踪文件

先展示 Write Gate，列出 `revision-guide.md`、`response-letter.tex`、General-response drafts 和 CLAUDE.md 的具体改动及编译验证。用户批准后，基于确认的聚类方案生成：

1. **`revision-R${ROUND}/revision-guide.md`**：读取 `~/.claude/skills/rev-init/assets/revision-guide.md.tmpl`，填充全部 9 个 Section
   - Section 3 行号表：用 `grep -n "\\section\|\\subsection" "{MAIN_TEX}"` 获取
   - Section 4 意见清单：从 comment-letter-clean.md 导入，回填 Cluster 列
   - Section 5 Cluster 分析：从确认的聚类方案填充

**进度追踪说明**：不单独生成进度文件。回复完成状态直接通过 `response-letter.tex` 中的 `[TO BE FILLED]` 占位符判断——有占位符 = 未完成，无占位符 = 已完成。

---

## Step 8: 构建 response-letter.tex 骨架

读取 `~/.claude/skills/rev-init/assets/response-letter.tex.tmpl`，填入：

1. 标题 `[MANUSCRIPT-ID]` → 实际稿件编号
2. 开篇段落 `[N]` → 审稿人数量（two/three）；无 AE 删除 "the Associate Editor, and"
3. 目录 → 按实际审稿人编号生成
4. Editor → 粘贴意见原文
5. AE（如有）→ 粘贴意见原文
   - Editor/AE 的 General 文本先生成概括性回复
   - 每条已编号的 `E-K` / `AE-K` 实质性意见单独生成 `[TO BE FILLED]` 块，后续通过 `/rev-respond` 处理
6. 每位 Reviewer：
   - General Assessment 原文
   - 每条 Comment → `\reviewercomment{Comment \#N-K.}` + 换行 + 审稿人原文（不加粗） + `\responseheader` + `\response{[TO BE FILLED]}` + `\bigskip`
     - `\reviewercomment{}` 内**只放编号**（如 `Comment \#2-1.`），不要自编标题
     - 如果原文自带标题/编号（如 "Major Comment 1: ..."），仍保留系统 Comment ID；原始标题和正文作为普通文本（不加粗）另起一行
7. 每个 Editor / AE / Reviewer 来源结束处：
   - 若原文在全部实质性意见之后含 `Recommendation` 或总结性评估，单独生成 `\reviewercomment{Recommendation.}`，保留原文，添加 `\responseheader` 和 `\response{[RECOMMENDATION RESPONSE TO BE FILLED]}`
   - 若原文含礼貌收尾语，单独生成 `\reviewercomment{Closing comment.}`，保留原文，添加 `\responseheader` 和 `\response{[CLOSING RESPONSE TO BE FILLED]}`
   - 若原文没有礼貌收尾语，仍为该来源预留独立的整体感谢段；不得把整体感谢塞入最后一条实质性 Comment

写入 `response-letter.tex`。

验证：`grep -c "TO BE FILLED" response-letter.tex` = 需填写的总条目数。

---

## Step 9: 生成 General Responses

### 9a. 生成规则

对 Editor General、AE General（如有）、R1-0、R2-0、...、RN-0 生成概括性回复；已编号的 `E-K` / `AE-K` 不在此处填充：
- 每个回复 3-6 句话（80-150 words）
- 使用 `\response{}` 包裹，不用 `\manuscriptquote{}` 和 `\lineref{}`
- **每个对象的感谢措辞必须不同**（限一个描述性形容词）
- 引用格式：纯文本 `(Author et al., Year)`，不用 natbib
- 科技写作纪律：短句（≤25词）、主动语态、克制修饰、无中式英语

### 9b. 回复要点

- **Editor**：感谢安排审稿 + 概述修改方向 + 针对编辑特别要求的概括性回应
- **AE**：感谢协调和综合评价 + 简要说明已做对应改进
- **Reviewer #X-0**：感谢时间和专业评审 + 对总体评价回应 + 引导到逐条回复

### 9b2. 来源级收尾感谢（强制）

在每个 Editor、AE 或 Reviewer 部分的最后一条实质性 Comment 之后生成一段整体感谢：
- 若原文含来源级 `Recommendation`，在该 block 中直接回应总结性要求，并以整体感谢收尾；不要再机械添加第二段 closing thanks
- 若原文含 closing courtesy，保留独立的 `\reviewercomment{Closing comment.}` 和原文，并用该块下的 `\response{}` 表达整体感谢
- 若原文没有 closing courtesy，直接添加独立的 `\response{}` 整体感谢
- 收尾感谢为 2--3 句，概括该来源意见带来的主要改进；不使用 First/Second/Third，不添加 `\manuscriptquote{}` 或 `\lineref{}`
- 分别保存到 `revision-R${ROUND}/drafts/`：`Comment_Editor-closing.md`、`Comment_AE-closing.md` 或 `Comment_RN-closing.md`
- 来源级 Recommendation 分别保存为 `Comment_Editor-recommendation.md`、`Comment_AE-recommendation.md` 或 `Comment_RN-recommendation.md`
- 填完后确认 `response-letter.tex` 中不存在 `[RECOMMENDATION RESPONSE TO BE FILLED]` 或 `[CLOSING RESPONSE TO BE FILLED]`

### 9c. 展示 + 确认

一次性展示所有 general responses → AskUserQuestion 确认。

确认后 → 填入 `response-letter.tex`，并分别保存到 `revision-R${ROUND}/drafts/`：
- `Comment_Editor-0.md`
- `Comment_AE-0.md`（如有）
- `Comment_RN-0.md`（每位 Reviewer 一份）

> 命名对齐：前缀统一为 `Comment_`（与 Cluster-specific proposals/comments 一致），让 `/rev-respond` 的 `drafts/Comment_*.md` glob 自动涵盖 General responses，避免成为孤儿文件。旧的 `Response_*.md` 前缀已弃用。

---

## Step 10: 更新 CLAUDE.md

### 10a. 追加/更新修改工作流配置

AskUserQuestion：是否自动追加修改工作流配置到项目 CLAUDE.md？

如用户选是，追加：修改工作流节（上下文文件、skills、闭环步骤）+ Response Letter 格式规范。

### 10b. 更新项目阶段字段

在 CLAUDE.md 中查找 `## 项目阶段` 部分：
- 已存在 → 更新 `状态` 和 `更新时间`
- 不存在 → 在文件末尾追加

```markdown
## 项目阶段
- 状态: revision-R{ROUND}
- 更新时间: {TODAY}
- 基准文件: {BASELINE}
- 轮次历史:
  - R{ROUND}: {TODAY}（{DECISION_TYPE}）
```

如果是 R2+，保留之前的轮次历史记录，追加新行。

---

## Step 11: 编译 + Checkpoint Card（最终）+ 摘要

1. 编译验证：`latexmk -pdf -interaction=nonstopmode response-letter.tex && latexmk -pdf -interaction=nonstopmode "{MAIN_TEX}"`；如需 track-changes，同步运行 `tools/make-diff.sh`
   - 任一编译失败或出现 LaTeX Error、undefined citation、duplicate label、Float too large、Emergency stop → Audit Gate = `FAIL-BLOCKED`，不得宣布初始化完成或进入最终 checkpoint
   - 全部通过 → Audit Gate = `PASS` 或 `PASS-WITH-LOG`
   - 同时确认每个 Editor、AE 和 Reviewer 部分均以独立的来源级感谢结束；原文中的 Recommendation 保持在全部实质意见之后，closing courtesy 未被并入最后一条实质性 Comment
2. 展示最终 focused Checkpoint Card（**使用 `$BASELINE` 变量引用**，避免 legacy ROUND=1 分支下 `manuscript-R0.tex` 不存在导致的 pathspec 错误）：
   ```text
   📌 Checkpoint Card — R${ROUND} rev-init complete

   拟 stage：
     - revision-R${ROUND}/
     - response-letter.tex
     - tools/
     - .revision-baseline
     - .revision-main
     - {BASELINE}

   建议 commit message：
     R${ROUND} rev-init: complete initialization (guide + response skeleton + general responses)

   确认后我再执行 git add / git commit。
   ```
3. 展示摘要：文件树 + 当前轮次 R{ROUND} + Cluster 总览 + 推荐执行顺序 + 下一步指引（`/rev-respond {first anchor ID}`）
