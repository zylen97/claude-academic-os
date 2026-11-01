---
description: "初始化基金申请项目：按 年度_申请人代码_基金简称 建项目（或在已有文件夹里就地初始化），章节结构从基金档案生成，写 FUND.md 卡片与项目 CLAUDE.md；支持重申模式（继承上一轮正文，把评审意见整理成修改清单）"
---

# /fund-init — 初始化基金申请项目

**规格**：`~/.claude/skills/shared/FUND-PROTOCOL.md`（下称"协议"）。开始前先读协议第 1、3、4、5、6 节。

**输入** `$ARGUMENTS`：
- 无参数 → 新申模式，从 fund-idea.md 读选题
- `重申 {前序项目文件夹名}` → 重申模式

全程中文。

## Step 1：读选题来源

**新申模式**，来源按顺序找：
1. `$ARGUMENTS` 里给出的 fund-idea 路径
2. `$FUNDINGS/_drafts/fund-idea_*.md` 中最新的一份（`ls -t | head -1`），AskUserQuestion 确认是否用它
3. 都没有 → 提示先跑 `/fund-mine`；用户坚持直接建，则逐项询问申请人代码、基金档案、年度、题目、研究方向

**重申模式**：
1. 读 `$FUNDINGS/{前序项目}/FUND.md`。阶段不是 `rejected` → 停止并说明（只有未中的项目能重申）。
2. 申请人代码、基金档案沿用前序卡片；年度询问用户（通常为前序年度 +1）；题目先沿用，Step 6 再确认是否修改。
3. 有新的 fund-idea.md（`_drafts/` 里该申请人、该档案的最新一份）时，AskUserQuestion 是否合并使用。

## Step 2：确认项目信息

读 `_profiles/{档案}`，从中取交付类型、正文结构、匿名要求、申报窗口。AskUserQuestion 一次确认：

```
1. 申请人：{代码}（{姓名}）
2. 基金档案：{档案}　年度：{年度}
3. 项目文件夹：{年度}_{代码}_{基金简称}
4. 题目：
5. 交付类型：{档案给出的值；多个值时请用户选定}
6. 截止日期：{按档案申报窗口推断，请用户核对}
7. 拟申请经费、研究周期（不知道写"待填"）
8. 项目组成员（不知道写"待填"）
```

申请人代码不在协议第 2 节登记表里 → 停止，提示先登记。

## Step 3：建项目文件夹

路径：`$FUNDINGS/{年度}_{代码}_{基金简称}/`

- **不存在** → 新建。
- **已存在且没有 FUND.md**（用户已经把官方通知、模板放进去）→ 就地初始化：只新增文件，**不移动、不覆盖**已有文件。
- **已存在、有 FUND.md、但没有 CLAUDE.md 和 `sections/`**（只建了卡片，如 /fund-hub backfill 补的卡）→ 就地初始化：卡片里已有的值作为 Step 2 的预填，Step 5.1 只补全"待填"字段，不覆盖已有值。
- **已存在且有 FUND.md 和 CLAUDE.md 或 `sections/`** → 停止，提示该项目已初始化；要改信息直接编辑 FUND.md。

按协议第 5 节建子目录：`sections/`、`structure/0_global/`、`structure/2_literature/`、`structure/figures_tables/figures/`、`deliverables/`、`submitted/`、`reviews/`、`reference/`。

## Step 4：从档案生成章节规划

读档案的"正文结构"（或"活页结构""申报书结构"），拆成 `sections/{NN}_{章节名}.md` 列表。每章确定：

- **文件名**：两位编号 + 档案原标题的简写，如 `01_选题.md`、`02_研究内容.md`
- **角色**：按协议第 5 节的角色词表标注（如 `立项依据`、`目标内容+创新点`）
- **字数上限**：档案写了就照抄；档案只给总字数或页数时，按章节分量提出分配建议
- **状态**：`待写`

只给表格栏目、不写正文的项（经费、基本信息、成员表）标角色 `表格`。

把列表展示给用户，AskUserQuestion 确认或调整（合并、拆分、改字数）。**章节以档案为准，不套用其他基金的结构。**

## Step 5：写文件

### 5.1 FUND.md

按协议第 3 节字段顺序写入。申请人 `{代码}（{姓名}）`；角色：代码为 zy 写"申请人"，否则写"协助"（zy 同时是项目组成员时写"项目组成员"）；项目组成员取 Step 2 的答案；阶段 `init`；结果 `—`；提交日期写 `截止 {日期}`；正文正本写 `sections/`（交付类型含 latex 时写 `main.tex`）；提交版写 `submitted/`；前序申请：重申模式写前序文件夹名，否则"无"；后续申请"无"；评审意见"待填"；`## 复盘` 写"待填"。

### 5.2 CLAUDE.md

```markdown
# {题目}

> 基金申请项目。阶段与结果见 `FUND.md`；规格见 `~/.claude/skills/shared/FUND-PROTOCOL.md`。

## 项目信息

- 申请人：{代码}（{姓名}）
- 基金：{全称}　档案：`_profiles/{档案}`
- 交付类型：{latex / word / word-macro / system}
- 截止：{日期}

## 合规要点（摘自档案，提交前 /fund-polish 会逐条核对）

- 匿名要求：{原文摘要；无则写"无"}
- 篇幅限制：{总字数、页数、图片数等}
- 限项：{与本申请人相关的条款}

## 源项目

| 源项目 | 路径 | 贡献 |
|---|---|---|

研究基础只从 `$FUNDINGS/_assets/{代码}/成果清单.md` 取。

## 章节规划

| 章节 | 文件 | 角色 | 字数上限 | 状态 |
|---|---|---|---|---|
{Step 4 确认的列表}

## 写作注意

- {档案"选题定位"和"评审要点"里与写作直接相关的要求}
- 研究内容、方案用"拟""将"；已有基础用"已"
```

### 5.3 章节骨架

每个 `sections/{NN}_{章节名}.md`：

```markdown
# {章节标题（照抄档案原标题）}

<!-- 角色: {角色} -->
<!-- 字数上限: {N} -->

## 写作要点

{结合 fund-idea.md 和档案评审要点，列 3–5 条，写具体，不写模板话}

---

<!-- 正文从此开始 -->
```

### 5.4 fund-idea.md 与 idea.md

把 Step 1 用到的 fund-idea 复制为项目根目录 `fund-idea.md`，再复制一份到 `structure/0_global/idea.md`（供 /lit-plan 读取）。重申模式且没有新 fund-idea 时，用前序项目的 `fund-idea.md`；前序没有就根据前序正文生成一份精简版。两份内容保持一致，任一处修改后用 `cp` 同步。

### 5.5 main.tex（仅交付类型含 latex）

```bash
TEMPLATE_DIR=~/.claude/skills/fund-init/templates
# 档案为 NSFC 系列用 nsfc.tex.tmpl，其余用 provincial.tex.tmpl
cp "$TEMPLATE_DIR/{模板}.tex.tmpl" main.tex
cp "$TEMPLATE_DIR/latexmkrc.tmpl" latexmkrc
```

用 perl 替换 `{PROJECT_SLUG}`、`{PROJECT_TITLE}`、`{APPLICANT}`、`{AFFILIATION}`、`{PROPOSAL_DATE}`（主 agent 先 export 这些变量）。再把模板里的 `\section{}` 改成与章节规划表一致的标题和顺序，每节下留占位注释 `% 本节正文待灌入自 sections/{NN}_{章节名}.md`。`{slug}.bib` 建空文件，`\addbibresource{{slug}.bib}`。

交付类型不含 latex 时不建 main.tex，`{slug}.bib` 仍然建（引用管理用）。

### 5.6 官方模板

档案"来源文件"列出的本年度官方模板如果在别的项目里，复制一份到本项目 `reference/`（不移动原件）。用户已放进本项目根目录的官方文件保持原位。

## Step 6：重申模式的额外工作

1. **继承正文**：
   - 前序有 `sections/*.md` → 按新章节规划逐章复制为起点，章节对应不上的部分放进 `reference/前序正文_未归位.md`。
   - 前序只有 Word 或 PDF → 用 `textutil -convert txt`（.doc/.docx）或 `pdftotext -layout`（.pdf）把提交版转成 `reference/前序正文.txt`，再按章节拆进各 `sections/*.md` 的正文区，开头标注 `<!-- 继承自 {前序项目}，待按修改清单修改 -->`。
   - 前序是 LaTeX → 复制 `main.tex` 到 `reference/前序_main.tex`；交付类型仍为 latex 时，以它代替模板作为本项目 main.tex。
2. **修改清单**：读前序 `reviews/评审意见_*.md`、FUND.md 的评审意见和 `## 复盘`，写 `reviews/重申修改清单.md`：

   ```markdown
   # 重申修改清单（前序：{前序项目}）

   | # | 评审意见原文（或复盘要点） | 问题归类 | 修改动作 | 涉及章节 | 状态 |
   |---|---|---|---|---|---|
   ```

   前序没有任何评审意见和复盘时，清单只写一行"无真实评审意见，修改方向由用户提供"，并 AskUserQuestion 请用户给出上一轮自己认为的问题。
3. **题目**：AskUserQuestion 确认沿用还是修改题目（同一基金重申，题目改动不宜过大）。
4. **回写前序卡片**：把前序 FUND.md 的"后续申请"改为本项目文件夹名。这是 /fund-init 唯一会改的其他项目文件，改之前告诉用户。

## Step 7：收尾

1. 运行 `python3 "$FUNDINGS/_scripts/build_portfolio.py"`；读 PORTFOLIO.md 的"跨申请人检查"和"命名问题"，有内容就报告。
2. AskUserQuestion：下一步先做文献（阶段写 `literature`，提示运行 `/lit-plan`），还是直接写大纲（阶段保持 `init`，提示运行 `/fund-outline`）。
3. 输出：项目路径、交付类型、章节数、截止日期与剩余天数、重申模式下修改清单的条数。

## 注意事项

- 不修改源项目和素材库的任何文件。
- 文件夹名必须符合协议第 1 节；用户给的名字不合规时，提出合规名字并确认。
- 截止日期少于 30 天时，在每次输出的第一行提醒剩余天数。
