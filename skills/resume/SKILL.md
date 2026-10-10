---
name: resume
description: "新 session 快速加载项目上下文：读项目阶段、analysis_plan 状态、register 发布日期、technical_map 完成日期、lit_status.md，按规格 §1 阶段与 §4.6 日期检查给出下一步（Project Context Loader）"
---

# Resume — 项目上下文加载

在新会话开始时快速读取项目关键文件，生成一段简洁的项目简述，让 Claude 立即理解"这篇论文在干嘛、做到哪了"。只读，不写任何文件。

唯一规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（§1 阶段、§4.6 日期检查、§4.7）。

**输入** `$ARGUMENTS`：无参数。

---

## 步骤 0：前置检查

当前目录不存在 `CLAUDE.md` → 停止，提示用户切换到项目根目录。

## 步骤 0.5：项目类型检测

1. `structure/` + `manuscript.tex` → **英文论文项目**（步骤 1–8）
2. `chapters/` + `CLAUDE.md` 含 `## 撰写进度` → **学位论文项目**：读合同阶段 + 撰写进度表、`chapters/*.tex` 结构、源项目信息（如有）
3. `sections/` + `CLAUDE.md` 含 `## 章节规划` → **基金项目**：读合同阶段 + 章节规划、`sections/*.md` 进度
4. 都不匹配 → **通用模式**：只读 `CLAUDE.md` + git log 后输出简述

学位论文与基金项目走各自的简化流程，然后直接跳到步骤 7、8。

---

## 步骤 1：项目元数据与阶段

从 `CLAUDE.md` 提取：项目编号、英文标题、一句话概括、方法、**方法 profile**（`## 核心配置`）、目标期刊、模板类型、`## 技术章节` 表（占位行以"（待"开头，视为未写入）。

`## 项目阶段` 的 `状态` 字段（规格 §1）：
- `foundation`：idea、文献、研究设计
- `analysis`：执行已批准的分析计划
- `drafting`：技术章节与叙述章节写作、定稿
- `submitted`：已投稿
- `revision-R{N}`：第 N 轮修改
- `accepted`：已录用（用户手动设置，无提醒）

缺少阶段字段（遗留项目）→ 从下列文件推断，并在简述中注明"阶段字段缺失"。

## 步骤 2：研究纲领

读取 `structure/0_global/idea.md` **全文**：版本（`> **版本**: vX.Y`）、§2 Gap → Objective → RQ、§3 方法、§4 贡献。

## 步骤 3：状态文件（只读）

| 文件 | 读取内容 |
|---|---|
| `structure/2_literature/lit_status.md` | 各方向 × 来源的筛选 / review / tag / pool 进度、FAILED 与 ⚠️ 标记 |
| `structure/0_global/analysis_plan.md` | 状态行（draft / approved + 批准日期、profile）；第 2 节设计基准条数；第 7 节最后一条日期与内容 |
| `structure/0_global/results_register.md` | 发布行日期、条目数、必报条目数、null 条目数 |
| `structure/0_global/technical_map.md` | 表头"依据"日期与"技术正文完成"日期 |
| `structure/1_introduction/introduction.md`、`structure/2_literature/literature.md` | 状态行（draft / confirmed）；前 30 行 |
| `structure/3_analysis/derivation/`（analytical-model） | 文件列表与已标 ID 的结论块数 |

不存在的文件记为"无"。`structure/1_introduction/` 等已被 `/finalize` 归档时注明"已完成定稿清理，manuscript.tex 为唯一正文"。

## 步骤 4：manuscript.tex

Grep 全部 `\section` / `\subsection`，判断每节是 `% TODO` 还是有实质正文。技术章节按 `## 技术章节` 表的标题定位（不按字面猜）；该表为占位时只报告"技术章节结构尚未经 /technical Map 确认"。

## 步骤 5：Git 历史

```bash
git log -15 --date=short --format="%ad %s"
```

## 步骤 6：修改阶段检测（条件执行）

存在 `revision-R*/` 或阶段为 `revision-R*` 时，额外读取最新轮次的 `comment-letter-clean.md`、`revision-guide.md`（如有）、`.revision-baseline`（如有）、历史轮次数、`response-letter.tex` 中 `[TO BE FILLED]` 数量。

## 步骤 6.5：日期检查（规格 §4.6）

记 `C` = `analysis_plan.md` 第 7 节最后一条日期，`R` = register 发布日期，`T` = 技术正文完成日期。`T` 存在且 `C > T` 或 `R > T` → 记为"技术正文可能过期"，在步骤 8 中给出回流路线（register 变了 → `/technical` 修复；设计变了 → `/idea-refine` / `/analysis` Plan）。只提醒，不阻断。

---

## 步骤 7：项目简述

一段自然语言（中文，≤500 字，不用表格与状态符号）：
1. 项目概况：研究什么、用什么方法（profile）、投什么期刊
2. 研究问题：RQ 列表
3. 当前进度：文献、分析计划、结果登记、技术章节、叙述章节分别到了哪里
4. 最近动态：从 git log 概括
5. 修改阶段：审稿意见概况（如适用）

## 步骤 8：下一步建议（一句话，非强制）

先报告步骤 6.5 的过期提醒（如有），再按阶段：

- **foundation**：
  - 无 `literature_search_plan.md` → `/lit-plan`；有检索方案但 `lit_status.md` 显示未完成或有 FAILED → `/lit-workflow`
  - 文献池已完成、`analysis_plan.md` 第 2 节设计基准不足 5 条，或 idea.md 近期有较大改动 → `/idea-refine`
  - 计划状态 draft 且第 1、3、4、5 节已基本填写，或计划 approved 但阶段为 foundation（设计改动后待重新批准）→ `/analysis` Plan
  - Introduction / LR 可在本阶段提前写：对应 section 为空 → 可选 `/narrative section=introduction|literature`
- **analysis**：
  - register 不存在 → `/analysis` Run → Release
  - 运行中需要改 RQ、模型族或主设定 → `/idea-refine`
- **drafting**：
  - `technical_map.md` 不存在，或 `## 技术章节` 仍为占位 → `/technical`（Map）
  - map 存在但无"技术正文完成"日期 → `/technical`（Tex）
  - Introduction / LR 为空 → `/narrative section=introduction|literature`
  - 技术正文已完成、Discussion 为空 → `/narrative section=discussion`
  - 正文已写但需要语言打磨 → `/polish section={…}`
  - 全部 section 已写入 → `/finalize`，之后 `/pre-submit`
- **submitted**：无主动提醒
- **revision-R{N}**：`revision-R*/` 不存在 → `/rev-init`；`response-letter.tex` 有 `[TO BE FILLED]` → `/rev-respond`
- **学位论文**：init → `/diss-init`；literature → `/lit-plan` / `/lit-workflow`；drafting → 未 outlined 的章节 `/diss-outline`，已 outlined 未 drafted `/diss-draft`；polishing → 未 polished `/diss-polish`，全部 polished `/diss-finalize`
- **基金项目**：init → `/fund-init`；literature → `/lit-plan` / `/lit-workflow`；outlining → `/fund-outline`；drafting → `/fund-draft`；reviewed / polishing → `/fund-polish`

最后一句问用户："需要从哪里继续？"
