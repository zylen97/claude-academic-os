---
name: paper-init
description: "初始化论文项目骨架：选出版社 + 方法 profile（saom / panel-regression / survey-sem / analytical-model / other），按 Academic OS Lite §2 生成目录、项目合同、idea.md、analysis_plan.md 骨架与 manuscript.tex；可建 GitHub 私有仓库，初始提交前展示文件清单并经用户确认"
---

# Paper Init — 论文项目初始化

唯一规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（§1 阶段、§2 目录、§4.7 本技能要点）。与本文件冲突时以规格为准。

## 核心使命

从零搭建一个标准化的 LaTeX 论文项目：多出版社（Elsevier / ASCE / Emerald / SAGE / IEEE / Wiley）× 方法 profile（saom / panel-regression / survey-sem / analytical-model / other）。生成规格 §2 的目录、项目合同（`CLAUDE.md`，含 `## 项目阶段` 与 `## 技术章节`）、`idea.md`、`analysis_plan.md` 骨架（状态 draft）、Introduction / Literature Review blueprint 和按方法类型生成的 manuscript 章节骨架。

**不生成**：`methodology.md`、`results.md`、`simulation.md` 或任何技术章节 md；`6_discussion/` 等 Discussion 目录；`results_register.md` 与 `technical_map.md`（分别由 `/analysis` Release 与 `/technical` Map 生成）。

## 参数解析

从 `$ARGUMENTS` 提取论文编号 `{ID}`（如 `zy15`）。为空时用 AskUserQuestion 询问。`{ID}` 用于所有命名：`{ID}.bib`、`paper_{ID}`（GitHub 仓库名）、`{ID}_latexfile/`（内层目录名）。

再用 AskUserQuestion 询问**外层项目文件夹名** `{OUTER_DIR}`（如 `zy18_供应链数字化转型溢出_IJPE`）。

## 项目目录结构（两层嵌套，规格 §2）

```
{OUTER_DIR}/
├── raw literature/                 ← 原文 PDF（不入 git）
└── {ID}_latexfile/                 ← git 仓库
    ├── CLAUDE.md                       ← 项目合同（含 ## 项目阶段、## 技术章节）
    ├── manuscript.tex  {ID}.bib  latexmkrc  *.cls *.bst
    ├── submission/
    ├── structure/
    │   ├── 0_global/
    │   │   ├── idea.md             ← 纲领（为什么、方向）
    │   │   └── analysis_plan.md    ← 分析计划骨架（状态 draft）
    │   ├── 1_introduction/introduction.md   ← Intro blueprint
    │   ├── 2_literature/literature.md       ← LR blueprint（文献流水线产物后续也写在此目录）
    │   ├── 3_analysis/
    │   │   └── derivation/README.md   ← 仅 analytical-model：推导工作区说明
    │   └── figures_tables/{index.md, tables.tex, figures/}
    └── data/{raw, processed, scripts, models, results, robustness, notes}
```

- `structure/0_global/results_register.md`、`technical_map.md` 由后续技能生成；`structure/0_global/background/`（情景与政策资料）可选，用户需要时自建。
- 后续所有步骤（Step 2–5）的工作目录均为 `{ID}_latexfile/`。

### 项目创建位置 `{PROJECT_PARENT_DIR}`

- **当前在 idea-mine 批次目录**（同时存在 `ideas/`、`idea-review/`、`papers/`）：不在此建项目，按全局CLAUDE.md的科研项目目录推导：
  - 路径包含 `papers` → `{PROJECT_PARENT_DIR}` = 路径中 `papers` 对应的完整目录；
  - 路径包含 `_gym paper` → 对应 `_gym paper` 目录；
  - 其他 → AskUserQuestion 询问。
- **不在 batch 目录**：`{PROJECT_PARENT_DIR}` = 当前工作目录。

## 前置检查

1. 判定是否为 idea-mine 批次目录，确定 `{PROJECT_PARENT_DIR}`。
2. `{PROJECT_PARENT_DIR}/{OUTER_DIR}` 已存在 → **停止并询问**，不覆盖。
3. `gh --version` 与 `gh auth status` 通过；GitHub 上不存在同名 `paper_{ID}` 仓库（`gh repo view paper_{ID}` 应失败）。同名仓库已存在 → 停止，让用户选择复用或改名，不覆盖、不删除。`gh` 不可用或未认证 → 只跳过远程仓库创建，本地骨架照常生成，并在摘要中说明。
4. `latexmk --version` 可用。

## GitHub 私有仓库

用户调用 `/paper-init` 即授权创建**且仅创建**一个名为 `paper_{ID}` 的 GitHub **private** 仓库并设为本地 `origin`（命令必须显式含 `--private`，不得带 `--push`）。`git add`、`git commit`、`git push` 不在此授权内，见 Step 5。

## 出版社选择

AskUserQuestion：

```
目标出版社？
  [1] elsevier — Elsevier期刊（AiC, IJPM, JCP, SCS等）· elsarticle · 双盲
  [2] asce — ASCE期刊（JME, JCEM等）· ascelike · 单盲
  [3] emerald — Emerald期刊（ECAM等）· standard article + natbib · 双盲
  [4] sage — SAGE期刊（Urban Studies, PMJ等）· sagej · 双盲
  [5] ieee — IEEE期刊（IEEE TEM等）· IEEEtran · 双盲
  [6] wiley — Wiley期刊（BSE等）· WileyNJDv5 · 双盲/三盲
```

记为 `{PUBLISHER}`。出版社决定 manuscript.tex 文档类、cls/bst 与 submission/ 文件组成。

## 方法类型选择

AskUserQuestion：

```
研究方法类型？
  [1] saom — 纵向网络 + 随机行动者模型（RSiena）
  [2] panel-regression — 二手数据 + 面板回归
  [3] survey-sem — 问卷调查 + SEM / PLS
  [4] analytical-model — 解析建模（博弈 / 合同 / 运营模型，可含数值研究或随机规划）
  [5] other — 其他方法（使用通用 profile）
```

记为 `{METHOD_TYPE}`，并确定方法 profile `{PROFILE}`：

| `{METHOD_TYPE}` | `{PROFILE}` | `{METHOD_LABEL}` |
|---|---|---|
| saom | `saom` | 纵向网络 + 随机行动者模型（SAOM） |
| panel-regression | `panel-regression` | 二手数据 + 面板回归 |
| survey-sem | `survey-sem` | 问卷调查 + SEM |
| analytical-model | `analytical-model` | 解析建模 |
| other | `_generic` | 其他方法（TODO: 写明具体方法） |

**profile 存在性检查**（规格 §4.2，提醒而非阻断）：检查 `~/.claude/skills/analysis/profiles/{PROFILE}.md`。不存在时把 `{PROFILE}` 改为 `_generic` 并提醒用户；`_generic.md` 也不存在时仍写入 `_generic`，提醒"profile 文件尚未安装，/analysis 将按通用规则执行"，流程不停止。

方法类型决定：manuscript 技术章节骨架、项目合同中的数据命名规范、是否生成 `structure/3_analysis/derivation/`。

## Idea-mine 导入（可选）

**自动检测**：前置检查已判定当前目录为 idea-mine 批次目录 → 自动启用导入，`{BATCH_DIR}` = 当前工作目录。

**手动触发**：否则 AskUserQuestion：

```
是否从 idea-mine 批次导入源材料？
  [1] 是 — 从 idea-mine 批次复制源论文、paper note、idea 文件和审稿评分
  [2] 否 — 跳过，从空白 idea.md 开始
```

选"是"且不在 batch 目录时，再询问 `{BATCH_DIR}` 的绝对路径。启用导入时收集：

- `{PAPER_ID}`：源论文编号（如 `12`，对应 P12）
- `{IDEA_SHORT}`：idea 简称（匹配 `idea_{PAPER_ID}_{IDEA_SHORT}_*.md`）
- `{TARGET_JOURNAL}`：选中的期刊版本（决定读取哪个 idea 文件）

### 导入内容与目标位置

全部放入 `{ID}_latexfile/structure/0_global/idea-mine-ref/`（纳入 git）：

```
structure/0_global/idea-mine-ref/
├── source_paper.pdf          ← 源论文 PDF 副本（固定名）
├── paper_note.md             ← 源论文精读报告（固定名）
├── migration_analysis.md     ← 迁移方向预判（固定名）
├── idea_{PAPER_ID}_{IDEA_SHORT}_*.md   ← 各期刊版本（保留原名）
└── review_*_P{PAPER_ID}.md             ← 各期刊审稿评分（保留原名）
```

> 文件命名契约（与 `/idea-mine`、`/idea-refine`、idea-reviewer 对齐）：`source_paper.pdf`、`paper_note.md`、`migration_analysis.md` 必须是固定名；`idea_*.md`、`review_*.md` 保留原名。

### 导入操作

1. **源论文 PDF（双份）**：按 `{BATCH_DIR}/idea-raw/_step3_matching.md` 的 P{NN} → PDF 文件名映射，在 `{BATCH_DIR}/papers/` 找到源论文：
   - 复制到 `{OUTER_DIR}/raw literature/`（保留原文件名）；
   - 再复制一份到 `idea-mine-ref/source_paper.pdf`。
2. **paper note**：`{BATCH_DIR}/paper-notes/{原文件名}.md` → `idea-mine-ref/paper_note.md`。
3. **migration_analysis.md**：优先 `cp {BATCH_DIR}/idea-raw/migration_analysis_P{PAPER_ID}.md`；不存在时从 `_step3_matching.md` 提取 `### P{PAPER_ID}:` 小节写入。
4. **idea 文件**：`{BATCH_DIR}/ideas/idea_{PAPER_ID}_{IDEA_SHORT}_*.md` 全部复制（保留原名）。
5. **review 文件**：`{BATCH_DIR}/idea-review/review_*_P{PAPER_ID}.md` 全部复制（保留原名）。
6. **重组写入 idea.md**（在 Step 3 生成 idea.md 骨架之后执行）：读取 `idea_{PAPER_ID}_{IDEA_SHORT}_{TARGET_JOURNAL}.md`，按下表覆盖写入 `structure/0_global/idea.md`，版本号设为 `v0.1`：

| idea 文件章节 | → idea.md 章节 | 处理方式 |
|:--|:--|:--|
| §1 灵感来源 | §1 灵感来源 & 参考论文 | 保留主论文摘要 + 迁移动机 + 迁移方向选择 |
| §2 行业背景 | §2 行业背景与实践难题 | 直接迁移 |
| §2 Gap 分析 | §2 文献不足（简述） | 每个 Gap 压缩为 1–2 句 |
| §2 RQ | §2 Gap→Objective→RQ 表格 | 重组为表格，从每个 Gap 提炼 Objective |
| §3 方法论 | §3 方法论选择论证 | 只保留方法选择论证与总体框架；具体设计属于 `analysis_plan.md`，不放公式和推导 |
| §4 贡献意图 | §4 贡献意图 | 拆分理论贡献与实践贡献，要点式 |
| §5 风险评估 | §5 风险评估 | 表格（风险 / 等级 / 应对） |

## 模板目录

```
~/.claude/skills/paper-init/
├── CLAUDE.md.tmpl                    # 项目合同
├── idea.md.tmpl
├── bib.tmpl
├── gitignore.tmpl
├── common/
│   ├── introduction.md.tmpl        # Intro blueprint
│   └── literature.md.tmpl          # LR blueprint
├── analytical-model/
│   └── derivation_README.md.tmpl   # 推导工作区说明（仅 analytical-model）
└── publishers/{elsevier,asce,emerald,sage,ieee,wiley}/
    ├── manuscript.tex.tmpl
    └── coverletter / titlepage / declaration / highlights（按出版社）
```

`analysis_plan.md` 骨架**不在本目录**：直接复制 analysis 技能的模板 `~/.claude/skills/analysis/templates/analysis_plan.md`（唯一来源，不另写副本）。

### 占位符替换

读取 `.tmpl` 后替换以下占位符，再写入目标路径。**先替换 `{DATA_NAMING}`**（其文本内含 `{ID}`），再替换其余占位符：

| 占位符 | 值 |
|---|---|
| `{ID}` | 论文编号 |
| `{TODAY}` | 当前日期 YYYY-MM-DD |
| `{METHOD_TYPE}` / `{PROFILE}` / `{METHOD_LABEL}` | 见"方法类型选择"表 |
| `{TEMPLATE_CLASS}` | elsevier → `Elsarticle (preprint)`；asce → `ascelike (Journal)`；emerald → `Standard article + natbib`；sage → `sagej (Harvard)`；ieee → `IEEEtran (journal, onecolumn)`；wiley → `WileyNJDv5 (APA, Times1COL)` |
| `{SUBMISSION_FILES}` | elsevier → `coverletter.tex, declaration.tex, highlights.tex, titlepage.tex`；asce / sage / ieee → `coverletter.tex`；emerald / wiley → `coverletter.tex, titlepage.tex` |
| `{DATA_NAMING}` | 见下方"数据命名规范"中 `{METHOD_TYPE}` 对应的整块文本 |

替换后 grep 目标文件中的 `{ID}`、`{TODAY}`、`{PROFILE}`、`{METHOD_LABEL}`、`{TEMPLATE_CLASS}`、`{SUBMISSION_FILES}`、`{DATA_NAMING}`、`{profile}`，必须为 0 处残留（`.bib` 文件名中的 `{ID}` 已替换为实际编号）。

### 数据命名规范（`{DATA_NAMING}` 替换内容）

**saom**：
```
- 语言：R + RSiena。脚本 `data/scripts/{ID}_data_pipeline.R`（→ `data/processed/*.rds`）、`data/scripts/{ID}_models.R`（→ `data/models/{ID}_m1.rds` … 与同名 `.txt` 日志到 `data/results/`）。
- 稳健性：`data/robustness/{ID}_rob_{检验名}.R` 与同名 `.rds` / `.txt`。
- RSiena 的 `projname` 必须包含目标目录（如 `"data/results/{ID}_m3"`），禁止输出到项目根目录。
- 执行顺序：data_pipeline → models → robustness（后者依赖前者产物）。
```

**panel-regression**：
```
- 语言不限（R / Stata / Python）。脚本 `data/scripts/{ID}_data_pipeline.{R|do|py}`（→ `data/processed/`）、`data/scripts/{ID}_models.{R|do|py}`。
- 估计对象 `data/models/{ID}_m{N}.{rds|ster|pkl}`；回归表与日志 `data/results/{ID}_m{N}.{csv|txt}`。
- 稳健性：`data/robustness/{ID}_rob_{检验名}.{R|do|py}` 与同名输出。
- 执行顺序：data_pipeline → models → robustness。
```

**survey-sem**：
```
- 问卷工具与量表来源记录在 `data/notes/`；原始回收数据放 `data/raw/`（只读）。
- 脚本 `data/scripts/{ID}_clean.{R|py}`（→ `data/processed/`）、`data/scripts/{ID}_cfa.R`、`data/scripts/{ID}_sem.R`（lavaan）；使用 SmartPLS 等软件时，把导出报告放 `data/results/{ID}_{模型名}_*.{csv|txt|html}` 并在 `data/notes/` 记录软件版本与设置。
- 稳健性（共同方法偏差、替代模型等）：`data/robustness/{ID}_rob_{检验名}.*`。
```

**analytical-model**：
```
- 推导：`structure/3_analysis/derivation/*.md`（长期保留，见该目录 README）。
- 符号 / 数值复核脚本与输出：`structure/3_analysis/derivation/checks/{ID}_check_{对象}.{py|nb|m}` 与同名输出。
- 数值研究：脚本 `data/scripts/{ID}_numeric_{名称}.{py|jl|m}`；参数表 `data/raw/` 或 `data/processed/`；结果 `data/results/{ID}_numeric_{名称}.{csv|txt}`；敏感性 `data/robustness/{ID}_sens_{参数}.*`。
- 求解器名称与版本、随机种子、最优性间隙写入结果日志。
```

**other**：
```
- 所有脚本放 `data/scripts/`，文件名以 `{ID}_` 为前缀；正式输出写入 `data/results/` 或 `data/robustness/`，禁止输出到项目根目录。
- 具体命名在 `analysis_plan.md` 第 4 节任务清单中逐项登记。
```

## 执行步骤

严格按顺序执行，每步确认无误再进入下一步。

---

### Step 1：创建项目目录 + Git 初始化 + 私有仓库

```bash
mkdir -p "{PROJECT_PARENT_DIR}/{OUTER_DIR}/{ID}_latexfile"
mkdir "{PROJECT_PARENT_DIR}/{OUTER_DIR}/raw literature"
cd "{PROJECT_PARENT_DIR}/{OUTER_DIR}/{ID}_latexfile"
git init -b main
# 仅当前置检查第 3 项通过时：
gh repo create paper_{ID} --private --source=. --remote=origin
gh repo view paper_{ID} --json nameWithOwner,isPrivate,url   # 核对 isPrivate=true
```

`isPrivate` 不为 true → 停止并报告，不进行任何推送。

### Step 1.5：Idea-mine 导入（条件步骤）

执行"导入操作"1–5（需要时先 `mkdir -p structure/0_global/idea-mine-ref`）。操作 6 延到 Step 3 末尾。

---

### Step 2：创建目录结构

> 以下命令在 `{ID}_latexfile/` 内执行。

所有方法类型：
```bash
mkdir -p structure/0_global structure/1_introduction structure/2_literature structure/3_analysis \
  structure/figures_tables/figures \
  data/raw data/processed data/scripts data/models data/results data/robustness data/notes \
  submission
```

仅 analytical-model 追加：
```bash
mkdir -p structure/3_analysis/derivation/checks
```

---

### Step 3：创建骨架文件

> 目标路径均相对于 `{ID}_latexfile/`；每个模板都做"占位符替换"。

#### 3.1 项目配置

| 模板 | 目标路径 |
|---|---|
| `CLAUDE.md.tmpl` | `CLAUDE.md` |
| `gitignore.tmpl` | `.gitignore` |

不生成 `.vscode/settings.json`（LaTeX Workshop 由全局 User Settings 管理）与项目级 `.claude/` / `.codex/` 配置目录。

#### 3.2 LaTeX 文件

| 模板 | 目标路径 |
|---|---|
| `publishers/{PUBLISHER}/manuscript.tex.tmpl` | `manuscript.tex` |
| `bib.tmpl` | `{ID}.bib` |

#### 3.3 manuscript 技术章节骨架（写入 manuscript.tex 后立即执行）

所有出版社模板都以 `\section{Methodology}` … `\section{Discussion}` 为统一锚点。用下表对应的块**整体替换** manuscript.tex 中从 `\section{Methodology}` 行起、到 `\section{Discussion}` 行之前（不含）的内容。替换后执行检查：`\section{Discussion}` 恰好出现 1 次，且位于全部技术章节之后。

这些标题是初始建议，最终技术章节结构由 `/technical` Map 确认，并写入项目合同 `## 技术章节`。

**analytical-model**：
```latex
\section{Research method and modeling process}
\subsection{Research method}
% TODO: Write content here

\subsection{Modeling process}
% TODO: Write content here

\section{Equilibrium analysis}
\subsection{Equilibrium analysis}
% TODO: Write content here

\subsection{Comparative analysis}
% TODO: Write content here

\section{Numerical analysis}
\subsection{Numerical simulation}
% TODO: Write content here

\subsection{Simulation results}
% TODO: Write content here

```

**saom**：
```latex
\section{Methodology}
\subsection{Research setting and data}
% TODO: Write content here

\subsection{Network and behavior measures}
% TODO: Write content here

\subsection{Stochastic actor-oriented model specification}
% TODO: Write content here

\section{Results}
\subsection{Descriptive network statistics}
% TODO: Write content here

\subsection{Model estimates}
% TODO: Write content here

\subsection{Goodness of fit and robustness}
% TODO: Write content here

```

**panel-regression**：
```latex
\section{Research methods}
\subsection{Sampling and data collection}
% TODO: Write content here

\subsection{Measures}
% TODO: Write content here

\subsection{Methods of analysis}
% TODO: Write content here

\section{Results}
\subsection{Descriptive statistics and correlations}
% TODO: Write content here

\subsection{Hypothesis testing}
% TODO: Write content here

\subsection{Robustness checks}
% TODO: Write content here

```

**survey-sem**：
```latex
\section{Methodology}
\subsection{Data collection}
% TODO: Write content here

\subsection{Bias mitigation and evaluation}
% TODO: Write content here

\subsection{Questionnaire development}
% TODO: Write content here

\subsection{Measures}
% TODO: Write content here

\subsection{Analytical methods}
% TODO: Write content here

\section{Results}
\subsection{Reliability and validity}
% TODO: Write content here

\subsection{Hypothesis testing}
% TODO: Write content here

\subsection{Robustness checks}
% TODO: Write content here

```

**other**：保留模板中的 `\section{Methodology}` 与 `\section{Results}` 占位，不替换。

#### 3.4 submission/ 投稿附件

| `{PUBLISHER}` | 模板 → `submission/` |
|---|---|
| elsevier | `coverletter.tex`、`declaration.tex`、`highlights.tex`、`titlepage.tex` |
| asce / sage / ieee | `coverletter.tex` |
| emerald / wiley | `coverletter.tex`、`titlepage.tex` |

模板路径为 `publishers/{PUBLISHER}/{文件名}.tmpl`。

#### 3.5 cls/bst 文件

```bash
copy_cls() {
  local name=$1
  local src=$(find ~/Library/CloudStorage/Dropbox -name "$name" -maxdepth 8 -print -quit 2>/dev/null)
  [ -z "$src" ] && src=$(kpsewhich "$name" 2>/dev/null)
  if [ -n "$src" ]; then cp "$src" .; else echo "⚠️ $name 未找到"; fi
}
case "$PUBLISHER" in
  elsevier) copy_cls elsarticle.cls;   copy_cls elsarticle-harv.bst ;;
  asce)     copy_cls ascelike.cls;     copy_cls ascelike.bst ;;
  emerald)  : ;;
  sage)     copy_cls sagej.cls;        copy_cls SageH.bst ;;
  ieee)     copy_cls IEEEtran.cls;     copy_cls IEEEtran.bst ;;
  wiley)    copy_cls WileyNJDv5.cls;   copy_cls wileyNJD-APA.bst ;;
esac
```

#### 3.6 latexmkrc

所有出版社写入 `$pdf_mode = 1;`（pdflatex）。需要 CJK 时改为 `$pdf_mode = 5;`（xelatex）。

#### 3.7 structure/ 文件

| 来源 | 目标路径 | 适用 |
|---|---|---|
| `idea.md.tmpl` | `structure/0_global/idea.md` | 全部 |
| `~/.claude/skills/analysis/templates/analysis_plan.md` | `structure/0_global/analysis_plan.md` | 全部 |
| `common/introduction.md.tmpl` | `structure/1_introduction/introduction.md` | 全部 |
| `common/literature.md.tmpl` | `structure/2_literature/literature.md` | 全部 |
| `analytical-model/derivation_README.md.tmpl` | `structure/3_analysis/derivation/README.md` | 仅 analytical-model |
| 空文件 | `structure/3_analysis/.gitkeep` | 非 analytical-model |
| 空文件 | `structure/3_analysis/derivation/checks/.gitkeep` | 仅 analytical-model |

**analysis_plan.md 骨架**：复制 analysis 模板后，把 `{ID}` 替换为论文编号、`{profile}` 替换为 `{PROFILE}` 的值，并核对状态行为 `状态: draft｜profile: <profile 值>`（保留模板其余结构与注释不变）。模板文件不存在 → 停止本文件的生成并提醒用户"analysis 技能模板未安装"，其余步骤照常，摘要中列为待补项；不得自行编写替代模板。

#### 3.8 图表管理文件

| 操作 | 目标路径 |
|---|---|
| 创建注册表 | `structure/figures_tables/index.md` |
| 创建空表格文件 | `structure/figures_tables/tables.tex` |
| 空目录占位 | `structure/figures_tables/figures/.gitkeep` |

**index.md 初始内容**：
```markdown
# 图表注册表 — {ID}

> 所有图片存放于 `figures/`，所有表格统一写在 `tables.tex`。
> 数据图 / 结果表的"来源"必须填 `results_register.md` 中的条目 ID；概念图填"概念图"。

## Figures

| 编号 | 文件名 | 标题 | 所属章节 | 生成方式 | 来源（register ID / 概念图） | 状态 |
|:--:|:------|:-----|:--------|:---------|:--------|:--:|

## Tables

| 编号 | 标题 | 所属章节 | 来源（register ID / 文献 / 设定） | 状态 |
|:--:|:-----|:--------|:--------|:--:|

## 说明

- 状态：planned → drafted → in-manuscript → finalized
- Figure 文件命名：`figXX_shortname.pdf`
- 新增 / 修改图表时同步更新本注册表
```

**tables.tex 初始内容**：
```latex
% tables.tex -- {ID} all tables in one file
% Paste content to the end of manuscript.tex when finalizing
```

#### 3.9 Idea-mine 内容写入（条件步骤）

执行"导入操作"第 6 步，覆盖写入 `structure/0_global/idea.md`。

---

### Step 4：编译验证

```bash
latexmk manuscript.tex
```

确认生成 `manuscript.pdf` 且无致命错误。cls/bst 缺失导致失败时，报告缺失文件，不改动模板。

---

### Step 5：初始提交（需用户确认）

1. 运行 `git status --short --untracked-files=all`，按出版社列出将要加入的文件：

   ```bash
   git add .gitignore CLAUDE.md manuscript.tex {ID}.bib latexmkrc {本出版社的 cls/bst} structure/ submission/
   ```

   （emerald 无 cls/bst；`data/` 下暂无文件，不加入。）

2. 向用户展示：完整文件清单、提交信息 `Initialize {ID} paper skeleton ({PUBLISHER} + {METHOD_TYPE})`、是否推送到 `origin`（仅当 Step 1 已建仓）。
3. AskUserQuestion：`(1) 提交并推送 (2) 只提交不推送 (3) 暂不提交`。
4. 按选择执行 `git commit` / `git push -u origin main`。未获确认不得执行任何 add / commit / push。

---

### Step 6：输出摘要

1. **创建完成** — 外层文件夹 + `{ID}_latexfile/` 的树状图
2. **GitHub 仓库** — URL 与私有状态（未建仓则说明原因）
3. **出版社 / 方法 profile** — `{PUBLISHER}` / `{METHOD_TYPE}` → `{PROFILE}`（如回退到 `_generic`，说明原因）
4. **编译验证** — 结果
5. **提交状态** — 已提交并推送 / 仅提交 / 未提交
6. **Idea-mine 导入报告**（如有）— 复制到 `raw literature/` 与 `idea-mine-ref/` 的文件；idea.md 版本 v0.1
7. **下一步**（规格 §4.1）：
   - 填写 `CLAUDE.md` 中的 TODO（英文标题、具体方法、目标期刊）并完善 `idea.md`
   - `/lit-plan` → WoS 检索 → `/lit-workflow`
   - `/idea-refine`：审 idea 与方法方向，设计基准写入 `analysis_plan.md` 第 2 节
   - `/analysis`：Plan【确认】→ Run → Release【确认】
   - `/technical`：Map【确认】→ 写入 manuscript.tex
   - `/narrative`：Introduction / Literature Review 可在 technical 之前；Discussion 在 technical 之后
   - `[/polish]` → `/finalize` → `/pre-submit`
