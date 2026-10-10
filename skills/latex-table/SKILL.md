---
name: latex-table
description: "LaTeX 表格模板与格式规范：项目类型自适应输出路径 + caption 宏包预检 + label 防冲突；结果表数值只取 results_register 登记来源；表注遵守正文精简规则"
user-invocable: true
auto-invoke: true
---

# LaTeX 表格规范

当用户要求创建、修改或格式化 LaTeX 表格时，遵循以下模板和规则。

写作或审计 table note 前，完整读取
`~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。表格必须可独立正确解读，
但 note 只承担解码功能，不承担替正文预先答辩的功能。

**文献综述 landscape table 特例**：如果表格用于总结 prior studies、related research、literature landscape、literature positioning、Appendix literature table 或 Supplemental evidence map，先读取并遵循 `~/.claude/skills/shared/LITERATURE-LANDSCAPE-TABLE-PREFERENCE.md`。这类表格默认按 substantive research streams 组织，并使用 related studies + representative studies 的结构；方法列只作为辅助信息，除非论文主题本身是方法比较。

## 输出位置（按项目类型分流）

Step 0 — 项目类型探测 + 确定 `{TABLES_FILE}`：

| 项目类型（按 `$PWD` 探测） | `{TABLES_FILE}` |
|:---|:---|
| `papers/` / `_gym paper/`（英文小论文） | `structure/figures_tables/tables.tex` |
| `dissertations/`（学位论文） | `structure/figures_tables/tables_{章号}.tex`（按章分文件，避免所有表堆在一起） |
| `fundings/`（基金） | `structure/figures_tables/tables.tex` |
| `$PWD` 不在上述目录 | AskUserQuestion 确认路径，不默认写入 |

**学位论文章号推断**：
1. 若调用上下文是 `/diss-draft` 串行调用 → 从当前正在处理的 `chapters/ch{XX}_*.md` 提取 `XX`（2 位数字）
2. 若上下文无法推断 → 读取 `$PWD` 下 `chapters/` 目录最近编辑的 `ch{XX}_*.md`，默认该章号
3. 都不行 → AskUserQuestion 询问用户："当前表格归属第几章（如 3）？"

- 每次创建/修改表格后，**必须同步更新** `structure/figures_tables/index.md` 的 Tables 表格（不存在则 mkdir + touch）
- **数据来源**（规格 §4.7；仅英文论文项目，学位论文与基金项目不适用）：结果表（估计值、命题 / 数值结果、检验统计、描述统计）的数值只能取自 `structure/0_global/results_register.md` 中登记条目的"来源"文件，并在 `index.md` 的"来源"列写对应 register ID。register 已存在但所需结果未登记 → 停止，提示先经 `/analysis` Release 登记；register 尚不存在（分析阶段的草表）→ 可制作，`index.md` 来源写脚本输出路径、状态不得高于 drafted，并提醒进入正文前须登记。文献表、符号表、参数设定表等非结果表不受此限（来源写"文献 / 设定"）。
- 集成方式（二选一）：
  - **A. 写作时引用**（推荐）：`/technical` 写作时在 manuscript.tex 中用 `\input{structure/figures_tables/tables.tex}` 引入，或单个表用 `Table~\ref{tab:xxx}` 引用
  - **B. 定稿时贴入**：`/finalize` 时把 `tables.tex` 内容贴到 manuscript.tex 末尾

## Step 1 — 主 tex 文件发现 + Caption/threeparttable 宏包预检（写入前必做）

**主 tex 发现**（不写死 `main.tex` / `manuscript.tex`——dissertations 常用 `thesis.tex`、`main_dissertation.tex` 等）：

```bash
# 找项目根目录下含 \documentclass 的单文件（行首匹配，避开 % 注释行；dissertations 常用 thesis.tex）
MAIN_TEX=$(grep -lE '^\s*\\documentclass' *.tex 2>/dev/null | head -n 5)
```

- 找到 0 个 → 🔴 报错退出，提示用户主 tex 不在项目根
- 找到 1 个 → `MAIN_TEX` 即该文件
- 找到多个 → AskUserQuestion 让用户选择

**Caption 宏包预检**（对 `$MAIN_TEX` 的 preamble）：

```bash
grep -E '\\usepackage(\[[^\]]*\])?\{caption\}' "$MAIN_TEX"
```

- ✅ 命中 → 继续
- ❌ 未命中：
  - 若 documentclass 是 `elsarticle / sagej / WileyNJDv5 / ctexart` → cls 自带可继续
  - 其他（如 `article / IEEEtran / ASCE`）→ 🟡 告警 + AskUserQuestion (1) 添加宏包 (2) 用简化模板 (3) 继续（自行承担风险）

## Step 2 — Label 冲突检查（写入前必做）

扫描 `{TABLES_FILE}` 已有的 `\label{tab:XXX}`，若新表的 label 已存在：
- 🔴 阻断，报告冲突："已存在 `\label{tab:xxx}`（第 N 行）。请选择：(1) 覆盖原表 (2) 改名（如 `tab:xxx_v2`）(3) 取消"
- 禁止静默追加导致 LaTeX 编译警告 `multiply defined labels`

## 标准模板（完整版，适用于支持 caption + threeparttable 的项目）

下列 `tablenotes` 块是条件块：只有至少一条说明通过语义准入时才保留；否则从
`\begin{tablenotes}` 到 `\end{tablenotes}` 整块省略。

```latex
\begin{table}[!htbp]
\centering
\captionsetup{font=normalsize, labelsep=period}
\setlength{\abovecaptionskip}{5pt}
\setlength{\belowcaptionskip}{0pt}
\caption{表格标题}
\label{tab:label_name}
\small
\begin{threeparttable}
\begin{tabular*}{0.9\textwidth}{@{\extracolsep{\fill}}lccccccc}
\toprule
\textbf{列标题1} & \textbf{列标题2} & ... \\
\midrule
\textit{变量1} & 数据 & ... \\
\textit{变量2} & 数据 & ... \\
\bottomrule
\end{tabular*}
\begin{tablenotes}[flushleft]
\small\linespread{1}\selectfont
\item \textit{Note}: 注释内容...
\end{tablenotes}
\end{threeparttable}
\end{table}
\vspace{-15pt}
```

## 简化模板（当 caption/threeparttable 不可用时的降级）

下列 `flushleft` Note 同样是条件块；无必要说明时整块省略。

```latex
\begin{table}[!htbp]
\centering
\caption{表格标题}
\label{tab:label_name}
\small
\begin{tabular}{lccccc}
\toprule
\textbf{列标题1} & \textbf{列标题2} & ... \\
\midrule
\textit{变量1} & 数据 & ... \\
\bottomrule
\end{tabular}
\begin{flushleft}
\small \textit{Note}: 注释内容...
\end{flushleft}
\end{table}
```

## 核心规则

- 统一 `\small` 字体，**禁止** `\footnotesize`、`\Large` 等
- 表头 `\textbf{}`，第一列 `\textit{}`，数据列居中 `c`
- 宽度 `0.9\textwidth`，浮动 `[!htbp]`
- Caption 使用 `\captionsetup{font=normalsize, labelsep=period}`（若 caption 可用）
- 支持时使用 `threeparttable`；只有至少一条说明通过 Table note 语义准入时才加入 `tablenotes`，不得保留空 note 或为模板完整性制造说明
- **Label 命名约定**：`tab:{chapter}_{semantic}` 或 `tab:{section}_{semantic}`，避免纯数字命名冲突
- 文献综述 landscape table 应优先使用 `Research stream / Related studies / Representative study / Research focus / Empirical or theoretical context / Main purpose or contribution`，并避免以 Method 作为默认分类主轴。

## Table note 语义边界

只在读者正确解释单元格确有需要时写入：非显然缩写/符号、caption 或表头未说明的样本/模型范围、
标准误/置信区间/显著性约定，以及必要的 reference category、transformation 或 data source。

禁止写入：结果解释、通用 noncausal disclaimer、正文已有的方法说明、稳健性辩护、与读数无关的 limitation，
以及 caption、表头或相邻正文的复述。同一边界已在正文建立时不因“更保险”而重复；仅当表格作为独立对象会被
实质误读时保留一个最短限定。

**删除测试**：删除某句不会导致熟悉领域的读者误读任何单元格，就删除该句。Note 不设目标句数或目标长度，
需要什么写什么，不需要时省略整个 `tablenotes` / `flushleft Note` block，不得为填充模板制造说明。
