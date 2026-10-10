---
description: "投稿前终检：引用键可解析、图表已登记且被引用、术语表一致、正文精简规则、日期检查（规格 §4.6）、格式与投稿附件；红黄绿三级报告，通过并经用户确认后把项目阶段写为 submitted（Pre-submission Checklist）"
---

# Pre-Submit — 投稿前终检

> 规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（冲突以规格为准）。正文精简规则：`~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。
> 子 agent：可以在需要时使用子 agent（定义在 `~/.claude/agents/`），并在执行前告诉用户将派出哪些。
> Git：本技能不 stage、不 commit、不 push。

自动扫描 manuscript.tex 与关联文件，生成红黄绿三级检查报告。**不修改稿件与任何项目文件**；只写两处：检查报告 `submission/pre_submit_report.md`，以及（全部 🔴 清零且用户确认后）项目合同中的项目阶段。

分级原则（规格 §0）：🔴 只用于真实研究风险或投稿必然被退回的问题（引用键不存在、引用了不存在的图表、登记的证据不存在、占位符残留、编译错误、缺必需文件）；格式、命名、时间先后不一致记 🟡 并给出回流路线。精简检查保持严格，但不把通用 caveat、可选扩展或审稿人口味伪装成缺陷。

**输入** `$ARGUMENTS`：无参数。直接运行 `/pre-submit`。

---

## 步骤 0：上下文加载

### 0.1 读取项目配置

读取项目合同 `CLAUDE.md`，提取：
- `{MAIN_TEX}`（通常为 `manuscript.tex`）、`{BIB_FILE}`、`{TARGET_JOURNAL}`、`{PUBLISHER}`
- 方法类型、"方法 profile"、`## 技术章节` 表、`## 项目阶段`

Fallback：查找含 `\documentclass` 的 `*.tex` 作为主文件；查找 `*.bib`。

### 0.2 读取文件

- `{MAIN_TEX}` 全文、`{BIB_FILE}` 全文；
- `submission/` 下全部 `.tex`（coverletter、titlepage、highlights、declaration 等）；
- `structure/0_global/` 下的 `idea.md`、`analysis_plan.md`、`results_register.md`、`technical_map.md`（存在的都读；只是 md，不做任何哈希或 schema 校验）；
- `structure/figures_tables/index.md`（如存在）。

---

## 步骤 1：引用完整性

### 1.1 正文 → bib（幽灵引用）

提取 `{MAIN_TEX}` 中全部 `\cite`、`\citep`、`\citet` 及其变体（含 `\citealp`、`\citeauthor`、`\citeyear`，含可选参数与多 key 逗号分隔）的 key。对每个 key 检查是否存在于 `{BIB_FILE}`：
- 存在 → ✅
- 不存在 → 🔴 幽灵引用：正文引了但 bib 里没有

### 1.2 bib → 正文（孤立条目）

`{BIB_FILE}` 中未被正文引用的条目 → 🟡 孤立条目。

### 1.3 bib 条目质量

- 缺少必填字段（title、author、year、journal/booktitle）→ 🔴
- 年份格式异常（非 4 位数字、与 key 中年份不一致）→ 🟡
- 重复条目（相同 title+year 或相同 DOI）→ 🟡
- article 缺 DOI → 🟢

### 1.4 bib 深度清洗

- **期刊名一致性**：同一期刊缩写与全称混用、大小写不一致 → 🟡，列出变体组供统一；
- **Citation key 格式**：不符合 `auth.lower + year + shorttitle(1,1)` → 🟢（外部导入条目可能如此，不阻断）；
- **年份分布**：报告近 5 年占比、最早与最晚年份；近 5 年占比 < 30% → 🟡。

---

## 步骤 2：格式合规

### 2.1 字数统计

```bash
texcount -1 -sum -merge {MAIN_TEX} 2>/dev/null || echo "texcount not available"
```

不可用时用正则粗估（去除 LaTeX 命令后的单词数）。报告：正文字数、参考文献数量、图表数量（`\begin{figure}` + `\begin{table}`）。

### 2.2 结构完整性

| 检查项 | 匹配模式 | 缺失级别 |
|--------|---------|---------|
| Abstract | `\begin{abstract}` | 🔴 |
| Keywords | `\begin{keyword}` 或 `\keywords` | 🔴 |
| Introduction | `\section{Introduction}` 或类似 | 🔴 |
| Conclusion | `\section{Conclusion` | 🔴 |
| References | `\bibliography` 或 `\begin{thebibliography}` | 🔴 |
| Acknowledgments | `\section*{Acknowledg` 或类似 | 🟡 |
| CRediT / Author contributions | `CRediT` 或 `Author contribution` | 🟡（部分期刊必须） |
| Declaration of interest | `declaration` 或 `conflict` | 🟡 |

### 2.3 TODO / 占位符残留

扫描 `{MAIN_TEX}` 与 `submission/` 下全部 `.tex`：`TODO`（不区分大小写）、`XXX`、`FIXME`、`TBD`、`\textcolor{red}`、`???`、作为占位数字的 `000`。每处命中 → 🔴。

### 2.4 LaTeX 编译检查（编译到临时目录，不改项目产物）

```bash
tmp=$(mktemp -d)
latexmk -interaction=nonstopmode -outdir="$tmp" {MAIN_TEX} > "$tmp/run.txt" 2>&1
grep -nE "^!|Error|Emergency stop" "$tmp"/*.log | head -20
grep -nE "undefined|multiply defined" "$tmp"/*.log | head -20
grep -nE "Warning" "$tmp"/*.log | head -20
grep -nE "Overfull \\\\hbox \(([2-9][0-9]|[1-9][0-9]{2,})" "$tmp"/*.log | head -20
```

latexmk 读取项目 `latexmkrc` 决定编译引擎。判定：
- `!` / Error / Emergency stop → 🔴
- undefined citation / undefined reference / duplicate label → 🔴
- 其他 Warning → 🟡（列前 10 条）
- `Overfull \hbox` 超过 20pt → 🟡
- 编译成功且无 Error → ✅

检查结束后删除临时目录。

---

## 步骤 3：符号与术语一致性

### 3.1 符号一致性（启发式）

提取全部行内公式（`$...$`、`\(...\)`），按 section 分组比较符号集合：同一概念在不同位置使用不同符号、符号首次使用时无定义 → 🟡，提醒人工确认。

### 3.2 术语表一致性（`technical_map.md` 第 2 节）

`technical_map.md` 存在时，读取第 2 节"术语表"（术语｜定义｜不得混用的近义词）：
- 对每一行，在 `{MAIN_TEX}` 正文（不含注释、公式、`\cite`/`\ref`/`\label` 参数）中按词边界、不区分大小写搜索"不得混用的近义词"；
- 命中 → 🟡，列出位置、命中词与应使用的术语；同一近义词在多个章节命中时合并成一条；
- 术语表中的术语在正文从未出现 → 🟢（可能是表过时，提醒复核术语表）。

`technical_map.md` 不存在 → 跳过本项并在报告中注明。

### 3.3 通用术语一致性

- 同一概念的不同写法（如 "game-theoretic" vs "game theoretic"，"decision-making" vs "decision making"）→ 🟡；
- 缩写首次出现时无全称定义 → 🟡；
- 定义缩写后又混用全称 → 🟡。

---

## 步骤 4：图表检查

### 4.1 引用完整性

扫描全部 `\label{fig:*}` 与 `\label{tab:*}`：
- 有 label 无 `\ref` / `\autoref` / `\cref` → 🟡 未被正文引用的图表
- 有 ref 无 label → 🔴 引用了不存在的图表

### 4.2 登记（`structure/figures_tables/index.md`）

`index.md` 存在时：
- 正文中每个图表应在 `index.md` 中有一行（图按 `\includegraphics` 文件名匹配"文件名"列；表按 caption 标题或编号匹配"标题" / "编号"列——注册表没有 label 列）→ 缺失 🟡；
- `index.md` 中登记、但正文未使用的图表 → 🟢；
- `index.md` 中为数据图 / 结果表记录的 register ID（如有）必须在 `results_register.md` 中存在 → 不存在 🔴（登记的证据不存在）；`results_register.md` 不存在时该项记 🟡 并注明无法核对。

`index.md` 不存在 → 🟡 "图表未登记"。

### 4.3 编号连续性

Figure 与 Table 编号是否连续，有无跳号。

### 4.4 图片文件

`\includegraphics{}` 的文件不存在 → 🔴；格式不推荐（线图用 `.jpg`、`.bmp`）→ 🟡（建议 PDF/EPS 或 300dpi PNG）。

---

## 步骤 5：submission/ 文件

### 5.1 Cover letter

`submission/coverletter.tex`：不存在 → 🔴；含 TODO → 🔴；否则 ✅。

### 5.2 其他投稿附件

按 `{PUBLISHER}` 检查必需文件：
- **elsevier**：coverletter、declaration、highlights、titlepage
- **asce**：coverletter
- **emerald**：coverletter、titlepage
- **sage**：coverletter
- **ieee**：coverletter
- **wiley**：coverletter、titlepage

缺少必需文件 → 🔴。

---

## 步骤 6：贡献一致性与正文精简

### 6.1 提取贡献点

- Introduction 中含 "contribut" 的段落 → 声称的贡献列表；
- Discussion 中含 "contribut" / "implicat" 的段落 → 展开的贡献列表；
- `idea.md` 贡献点（如存在）。

### 6.2 一致性（语义级，均记 🟡）

- Introduction 声称、Discussion 未展开 → 空头支票；
- Discussion 展开、Introduction 未预告 → 突兀；
- 贡献数量不一致；关键短语严重不一致。

### 6.3 正文精简规则（`MANUSCRIPT-ECONOMY.md`）

只检查已经存在的防御性冗余，不发明"可能缺少"的通用 caveat：
- 同一 noncausal、sample、context、temporal、proxy 或 limitation 边界跨 section 重复；
- 已确认的结果被连续 `may / might / could / perhaps` 弱化；
- table note 超出单元格解码，重复 Methodology、Results、Discussion 或稳健性辩护；
- 内部流程语言泄漏进正文（register、profile、map、release、gate、audit、validation、hash 等）；
- caveat 压过其保护的实质 claim。

重复防御与可合并的 caveat 记 🟡，并给出唯一建议保留位置；只有导致 claim 自相矛盾、实质误读或内部流程语言泄漏时记 🔴。只给出聚焦的删除 / 移位建议，不开启新的全稿审稿轮次。

---

## 步骤 7：流程状态与日期检查

**日期检查（规格 §4.6，取代哈希链；只提醒，不阻断）**

读取四个日期（都在 `structure/0_global/` 下）：

| 记号 | 来源 |
|---|---|
| P | `analysis_plan.md` 第 7 节"变更记录"表中最晚的日期（表为空 → 无） |
| R | `results_register.md` 的 `发布:` 行第一个日期（register 发布日期） |
| M | `technical_map.md` 的 `依据: results_register 发布 YYYY-MM-DD` 中的日期 |
| T | `technical_map.md` 的 `技术正文完成:` 日期（technical Tex 结束时写入） |

逐条判定（"晚于" = 严格晚于；同一天不算晚于）：

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

P 或 R 与 T 是同一天时，不判为晚于，但注明"同日，日期无法区分先后，请确认该变更已反映在技术正文中"。

输出格式：先列出触发的条目（编号、涉及的日期、对应变更行原文），再给出**一条合并后的回流路线**（去重并按 idea-refine → analysis Plan → analysis Run/Release → technical → narrative 的顺序排列），最后注明"完成回流后重新运行本技能"。没有触发任何条目时输出"日期检查：通过（P=…，R=…，M=…，T=…）"。日期只用于判断先后，不作为任何正文内容的来源。

在本技能中，D0' 与 D1–D7 每个触发条目记 🟡，并在报告"流程状态"一节给出合并后的回流路线；D0 记 🟢。

另查：

| 检查项 | 方式 | 级别 |
|--------|------|------|
| Conclusion | Conclusion section 词数 ≥ 150 且无占位符 | 🔴 |
| Abstract | Abstract 词数 ≥ 120 且无占位符 | 🔴 |
| Cover Letter | 见 5.1 | — |
| writing brief | `submission/writing_brief.md` 或 `drafts/writing_brief.md` 存在 | 🟢（可选） |

---

## 步骤 8：生成报告

`mkdir -p submission/`，写入 `submission/pre_submit_report.md`（每次覆盖）：

```markdown
# Pre-Submission Checklist — {PAPER_TITLE}

> Generated: {date}
> Target journal: {TARGET_JOURNAL} ({PUBLISHER})
> Manuscript: {MAIN_TEX}

## Summary

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 MUST-FIX | {n} | 投稿前必须修复 |
| 🟡 WARNING | {n} | 建议修复 |
| 🟢 INFO | {n} | 供参考 |

## Statistics

| 指标 | 数值 |
|------|------|
| 正文字数（估算） | {n} |
| 参考文献数量 | {n} |
| 图表数量 | {n} Fig + {n} Tab |

## 流程状态（日期检查）

P={…} R={…} M={…} T={…}
{触发条目与合并回流路线，或"通过"}

## 🔴 MUST-FIX

### 1. [引用] 幽灵引用：{key}
正文 L{行号} 引用了 `{key}`，但 bib 中不存在。
...

## 🟡 WARNING
...

## 🟢 INFO
...

## Verdict

{🔴 = 0}: ✅ READY TO SUBMIT — 未发现必须修复的问题。建议处理 🟡 项后提交。
{🔴 > 0}: ❌ NOT READY — 请先修复 {n} 条 🔴 问题。
```

### 展示报告与阶段写入

完整展示报告。

🔴 > 0：
```
❌ 发现 {n} 条必须修复的问题，请处理后重新运行 /pre-submit。
```

🔴 = 0：用 AskUserQuestion 询问（问题中列出 🟡 数量，并单独列出日期检查的触发条目，若有）：
```
✅ 检查通过（🔴 = 0；🟡 = {n}，其中日期检查提醒 {k} 条）。

更新项目阶段为 submitted？
(1) 确认（CLAUDE.md 中写 状态: submitted、更新时间: {TODAY}）
(2) 暂不更新
```

用户选 (1) → 在项目合同 `## 项目阶段` 中只改 `状态: submitted` 与 `更新时间: {TODAY}` 两行，保留该节其余行（如 rev-init 写入的基准文件与轮次历史）；该节不存在时按规格 §1 格式新建。选 (2) → 不写。修改轮次重投时同样适用：写 submitted 后，下一轮 /rev-init 依据 `revision-R*/` 目录推断轮次。

---

## 全局约束

- **不改稿件**：只扫描、只报告；修改由用户或对应技能完成。
- **幂等**：可反复运行，每次覆盖 `submission/pre_submit_report.md`。
- **容错**：单项检查失败（如 texcount 不可用、图片路径无法访问）不阻断整体流程，标记 `⚠️ 检查跳过：{原因}` 并继续。
