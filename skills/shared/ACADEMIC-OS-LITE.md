# Academic OS Lite — 唯一规格（Claude 与 Codex 共用）

> 版本 1.0 · 2026-10-10
> 本文件在两处保持**逐字相同**：
> - Claude：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`
> - Codex：`~/.codex/skills/_academic-shared/ACADEMIC-OS-LITE.md`
> 任何技能与本文件冲突时，以本文件为准；修改本文件必须同步两处。

---

## 0. 设计原则：骨架照搬 Codex，机器砍掉

**保留（骨架）**
1. 阶段与职责边界：`lit-workflow` 统一编排文献；`analysis` 独立成阶段（Plan → Run → Release）；`technical` 先 Map 再写 Tex；`manuscript.tex` 是唯一正文。
2. 设计先于结果：分析计划由用户确认后才执行；看过结果后改设计必须写变更记录。
3. 设计基准与报告基准分离：报告基准只决定"怎么写"，不能反过来改模型、变量或主设定。
4. 正文中每个技术结论都能指回结果登记表中的一条。
5. 不存在长期并存的技术章节正文草稿（methodology.md/results.md/simulation.md 一律不建）。

**砍掉（机器）**：YAML 契约、SHA 哈希链、Ruby/Python 契约校验器、逐项 evidence ID 的 schema、阶段 manifest 的哈希绑定、stage 字符串状态机、每个技能自带的 agent prompt 副本。

**三条判断标准**（以后改技能也按此执行）
1. 单人项目，git 就是版本追溯；不要再造哈希与清单去做 git 已经做的事。
2. 每个产物必须有人会读；只给脚本读的文件不要。
3. "阻断"只用于真实研究风险（改设计未记录、缺证据、引用键不存在、RIS 损坏）；格式、命名、时间先后不一致只提醒。

---

## 1. 项目阶段（唯一枚举与负责人）

阶段只写在项目合同（Claude：项目 `CLAUDE.md`；Codex：项目 `AGENTS.md`）的 `## 项目阶段` 一处，格式：

```
## 项目阶段
- 状态: foundation
- 更新时间: YYYY-MM-DD
```

| 阶段 | 含义 | 谁写入 | 写入条件 |
|---|---|---|---|
| `foundation` | idea、文献、研究设计 | `paper-init`（初始化）；`idea-refine`（设计被改动时回退到此） | — |
| `analysis` | 执行已批准的分析计划 | `analysis`（Plan 阶段） | 用户批准 `analysis_plan.md`（状态行改为 approved） |
| `drafting` | 技术章节与叙述章节写作、定稿 | `analysis`（Release 阶段） | 用户确认 `results_register.md` 完整（发布行写入日期） |
| `submitted` | 已投稿 | `pre-submit` | 全部 🔴 项清零，用户确认投稿 |
| `revision-R{N}` | 第 N 轮修改 | `rev-init` | 解析决定信后 |

其他技能只读阶段、不写阶段。`resume` 依据阶段给建议。

**回退规则**：`idea-refine` 只在当前阶段为 `analysis` 或 `drafting` 时把阶段回退为 `foundation`；当前阶段为 `submitted` 或 `revision-R{N}` 时**不改阶段**，只在 `analysis_plan.md` 第 7 节记变更（修改期的补分析与设计调整都在 revision 阶段内完成）。`analysis` 在 `submitted`/`revision-R{N}` 阶段执行 Plan/Release 时同样不写阶段。

**项目合同字段格式**（paper-init 写入；analysis、technical、narrative、resume 等按此读写）：
```
- **方法 profile**: <saom | panel-regression | survey-sem | analytical-model | _generic>

## 技术章节
| \section 标题 | 角色 |
|:--|:--|
| （technical Map 写入） | method / results / simulation |
```

---

## 2. 项目目录（paper-init 生成，所有技能按此读写）

```
{OUTER_DIR}/
├── raw literature/                 ← 原文 PDF（不入 git）
└── {ID}_latexfile/                 ← git 仓库
    ├── CLAUDE.md | AGENTS.md       ← 项目合同（含 ## 项目阶段、## 技术章节）
    ├── manuscript.tex  {ID}.bib  latexmkrc  *.cls *.bst
    ├── submission/
    ├── structure/
    │   ├── 0_global/
    │   │   ├── idea.md             ← 纲领（为什么、方向）
    │   │   ├── analysis_plan.md    ← 分析计划（含设计基准、变更记录）
    │   │   ├── results_register.md ← 结果登记表（Release 的产物）
    │   │   ├── technical_map.md    ← 技术章节结构 + 段落任务 + 术语表
    │   │   └── background/         ← 情景与政策资料（可选）
    │   ├── 1_introduction/introduction.md   ← Intro blueprint
    │   ├── 2_literature/                    ← 文献流水线全部产物（见 §3）+ literature.md（LR blueprint）
    │   ├── 3_analysis/
    │   │   └── derivation/         ← 仅 analytical-model：推导工作区，长期保留
    │   └── figures_tables/{index.md, tables.tex, figures/}
    └── data/{raw, processed, scripts, models, results, robustness, notes}
```

项目合同中的 `## 技术章节` 列出 manuscript 中技术章节的 `\section` 标题及其角色（method / results / simulation），由 `technical` Map 阶段写入；`narrative` 用它定位技术章节，**不按字面标题匹配**。

---

## 3. 文献条线

### 3.1 技能与职责

| 技能 | 职责 | 用户确认点 |
|---|---|---|
| `lit-plan` | 检索方向、WoS 检索式（实测命中数 + 抽样相关率闭环）、配额 | 检索方案与配额 |
| `lit-workflow` | 唯一常规入口：输入整理 → [screen] → review → tag → pool；可从任一阶段续跑；维护 `lit_status.md` | 是否筛选；失败方向是否跳过 |
| `lit-screen` / `lit-review` / `lit-tag` / `lit-pool` | 各阶段的实现，也是定点修复入口 | 见各技能 |
| `build-intro-lit-table` | 基于文献池生成 Introduction 文献表与一般性 gap | 表结构 |
| `idea-mine` | 从论文 PDF 挖掘可迁移 idea | — |
| `cnki-scout`（仅 Codex） | CNKI 期刊池扫描（发现用，不进入语料） | — |
| `idea-scout`（仅 Codex，定时任务也只在 Codex 侧） | 顶刊日报 | — |

### 3.2 文件约定（所有脚本必须共用 `lit_common.py` 中的同一个函数识别）

- 语料输入：`structure/2_literature/direction{N}_{wos|cnki|openalex}.ris`，正则 `^direction(\d+)_(wos|cnki|openalex)\.ris$`。方向名称只写在 `literature_search_plan.md` 的方向表中，不写进文件名。
- CNKI 原始导出：`direction{N}_cnki.enw`，由 `lit-workflow` 在输入整理阶段转换为 `direction{N}_cnki.ris`（在筛选之前）。
- OpenAlex 补充：只能经 `openalex_to_ris.py` 从已核验 JSON 生成 `direction{N}_openalex.ris`，然后从 review 重新走流程；未进入文献池前不得引用。
- OpenAlex 补充文献与 WoS 共用该方向的国际配额，同台竞争入选（不设独立配额）；review 合并时若补充文献挤掉了原入选论文，打印提示并在方向报告中注明被挤出的条目。
- 配额：`_quota_result.json`（lit-plan 产出，长期保留，清理时豁免）。
- 运行目录（不参与输入识别）：`_screen_runs/`、`_review_runs/`、`_tag_runs/`、`_pool_runs/`。review 与 tag 的分派计划分别为 `_review_runs/dispatch_plan.json` 与 `_tag_runs/dispatch_plan.json`，互不覆盖；缺失即报错，不降级。
- 阶段产物：
  - review：`direction{N}_report.md`（review 后不再被改写）、`screening_summary_report.md`
  - tag：`tagged_reports/direction{N}_report.md`（带标签副本）、`tag_report.md`
  - pool：`citation_pool/{BG,LR,GAP,METHOD,COMP,DISC}.md`、`citation_pool/master.bib`、`literature_manifest.json`（每篇唯一论文一行，供下游读取；不含哈希）、`master_report.md`、`method_landscape.md`
- `method_landscape.md`：若文件首行含 `<!-- curated -->`（由 idea-refine 或 analysis 在人工整理后加入），lit-pool 不覆盖，改写 `method_landscape_refresh.md`。
- 状态：`lit_status.md`，表格为 方向 × 来源 × {输入篇数, 筛选, review, tag, pool, 备注}。时间先后不一致（上游比下游新）只标 ⚠️，不阻断。

### 3.3 阻断与提醒

| 情形 | 处理 |
|---|---|
| 计划中的方向缺少输入文件；RIS 的 TY 数 ≠ ER 数 | 阻断 |
| 某方向 review/tag 子任务失败 | 停止派发 → 等在途完成 → 重试一次 → 仍失败则在 `lit_status.md` 标 FAILED，询问用户"修复或跳过"；pool 前若存在 FAILED 且未获用户确认跳过，阻断 |
| 只筛选了部分方向 | 正常；未筛选方向在状态表标"未筛选" |
| pool 后 JUDGE 占位符 ≠ 0、池内键不在 master.bib 中 | 阻断 |
| 文件名不规范、上游比下游新 | 提醒 |

### 3.4 子 agent 与模型

- Claude：Agent 工具；review/tag worker 用 sonnet，pool 写作用主模型；并发 ≤ 8。worker 定义在 `~/.claude/agents/lit-*-worker.md`，工具仅 Read/Write，只写分配给它的文件。
- Codex：worker 继承当前模型；并发 ≤ 6；worker 提示词统一放 `_academic-shared/agents/`。
- 两侧失败语义相同（见 3.3）。

---

## 4. 写作与论文条线

### 4.1 主流程

```
paper-init（出版社 + 方法 profile）
 → lit-plan → WoS → lit-workflow
 → idea-refine【确认】→ idea.md
 → analysis Plan【确认】→ analysis_plan.md（approved）→ 阶段 analysis
 → analysis Run → 推导/脚本/结果
 → analysis Release【确认】→ results_register.md → 阶段 drafting
 → technical Map【确认】→ technical_map.md
 → technical Tex → manuscript.tex（审计 + 嵌入式润色 + 编译）
 → narrative（Intro/LR 可在 technical 之前；Discussion 在 technical 之后）
 → [polish] → finalize → pre-submit → 阶段 submitted
 → rev-init → rev-respond
回流：设计层改动 → analysis_plan.md 变更记录 → idea-refine / analysis Plan
```

### 4.2 方法 profile（一页纸检查清单，不是阻断器）

位置：Claude `~/.claude/skills/analysis/profiles/`；Codex `~/.codex/skills/analysis/profiles/`（内容相同）。
文件：`saom.md`、`panel-regression.md`、`survey-sem.md`、`analytical-model.md`、`_generic.md`。
每个 profile 固定八个小节：适用范围｜输入（数据包 / 模型设定）｜结论目标（效应 / 命题）｜证据类型｜必做检验｜报告顺序｜解读边界｜空洞表述信号（供润色识别"只有符号没有含义"的句子）。
项目使用的 profile 写在项目合同"方法 profile"字段与 `analysis_plan.md` 状态行。**找不到对应 profile 时使用 `_generic.md` 并提醒用户，不停止流程。**

### 4.3 `analysis_plan.md`（一页；模板见 analysis 技能）

```
# 分析计划 — {ID}
状态: draft | approved（批准日期 YYYY-MM-DD）｜profile: <name>
## 1 RQ → 结论目标        （每个 RQ 要证明 / 估计什么）
## 2 设计基准              （5–8 篇；每篇一句话：借什么）
## 3 模型与输入            （模型设定或数据边界）
## 4 任务清单              （T1…；内容；产出文件）
## 5 检验与稳健性          （profile 必做项 + 项目特有项）
## 6 解读边界              （不得声称什么）
## 7 变更记录              （只追加：日期｜改了什么｜原因｜影响 register/technical/narrative 的哪些部分）
```

规则：
- `approved` 之后，第 1、3、4、5 节的任何改动都必须先在第 7 节追加一行，并由用户确认；属于 RQ、模型族、主设定变化的，回到 `idea-refine`，阶段回退为 `foundation`。
- 在计划中登记过的空结果、失败检验必须进入 register，不得静默删除。

### 4.4 `results_register.md`（Release 产物）

```
# 结果登记表 — {ID}
发布: YYYY-MM-DD（对应 analysis_plan 批准日期 YYYY-MM-DD）
| ID | 类型 | 内容（一句话） | 来源（文件#锚点 / 脚本→输出） | RQ | 必报 | 解读边界 |
```
- ID 用 `F1, F2…`（finding；不用 R，避免与审稿意见编号 R1-1 混淆）；重新发布时已有 ID 不改号，删除的编号不复用。
- 类型取自 profile 的证据类型（如 proposition / equilibrium / estimate / robustness / null / figure / table）。
- analytical-model 的来源是 `structure/3_analysis/derivation/*.md#锚点` 与复核脚本输出；实证类是 `data/results/` 下的输出。
- "必报"=是 的条目在 technical 中必须恰好出现一次；"否"的条目可省略但需在 technical_map 中写一句原因。

### 4.5 `technical_map.md`（technical Map 产物）

```
# 技术章节结构 — {ID}
依据: results_register 发布 YYYY-MM-DD｜技术正文完成: （technical Tex 结束时写入日期）
## 1 章节结构   | section/subsection 标题 | 角色(method/results/simulation) | 段落任务 | register ID | 表/图 |
## 2 术语表     | 术语 | 定义 | 不得混用的近义词 |
## 3 报告基准   （默认复用设计基准，另加 1–2 篇目标期刊样例；只决定组织与披露）
## 4 省略说明   （非必报条目的省略原因）
```
- 写完结构后，把章节标题与角色同步写入项目合同 `## 技术章节`。
- `narrative` 与 `polish` 读取第 2 节术语表（这是 md，允许读取）。

### 4.6 失效与回流（替代哈希链）

- 判断依据只有日期：`analysis_plan.md` 第 7 节最后一条变更日期、`results_register.md` 发布日期、`technical_map.md` 技术正文完成日期。
- `technical`、`narrative`（Discussion）、`finalize`、`pre-submit` 开始前比较日期：若变更记录或 register 晚于技术正文完成日期 → 提醒并给出回流路线（register 变了 → technical 修复；设计变了 → idea-refine / analysis Plan）。
- 正文其他章节被修改不会使技术章节失效（不存在整稿哈希）。

### 4.7 各技能要点

| 技能 | 要点 |
|---|---|
| `paper-init` | 选出版社 + 方法类型（saom / panel-regression / survey-sem / analytical-model / other）；生成 §2 目录；不生成技术章节 md；analytical-model 额外生成 `3_analysis/derivation/README.md`；生成 `analysis_plan.md` 骨架（draft）；初始提交前展示文件清单 |
| `idea-refine` | 审 idea 与方法方向（保留 Claude idea-reviewer 的 Dim5 建模创新、Dim6 假设逐条审查）；产出 idea.md 新版本；设计基准写入 analysis_plan 第 2 节；设计层改动写变更记录并把阶段回退为 foundation；不自动 commit |
| `analysis` | Plan【确认】→ Run → Release【确认】；按 profile；analytical-model 在 derivation/ 中推导命题、证明骨架与比较静态，并用复核脚本（如 SymPy / 数值）验证；不写正文 |
| `technical` | Map【确认】→ 直接写 manuscript.tex → 对照 register 审计（必报项恰好一次、无超出证据的说法、解读边界）→ 嵌入式润色（language-polisher，只改语言）→ 回归审计 → 编译 → 写完成日期 |
| `narrative` | Intro/LR：先更新 blueprint md 并确认，再写 tex；Discussion：按项目合同 `## 技术章节` 定位 results 角色章节，逐 RQ 回应；引用池外文献必须先回到 lit-workflow |
| `polish` | 只做语言；可被 technical / narrative 以"嵌入模式"调用（只返回候选文本，不写文件） |
| `finalize` | Conclusion → Abstract → Cover Letter（只以 manuscript.tex 为事实来源；投稿元数据先确认）→ 清理 |
| `pre-submit` | 引用键全部可解析、图表已登记且被引用、术语表一致、正文精简规则、§4.6 日期检查；通过后写入 submitted |
| `rev-init` / `rev-respond` | 冻结基准 → 解析决定信 → 聚类；回复只设两次确认（策略、最终综合）；需要补分析的意见 → analysis（更新 register + 变更记录）→ technical 修复 |
| `figure` / `latex-table` | 数据图的数据必须来自 register 中登记的来源；概念图不需要 |
| `resume` | 读阶段、analysis_plan 状态、register 与 technical_map 日期，给出下一步 |

### 4.8 正文精简规则（manuscript economy）

见 `MANUSCRIPT-ECONOMY.md`（同目录）。核心：每个限定只在最需要的位置出现一次；表注只用于解读表格；内部流程语言（register、profile、map、gate 等）不得出现在正文。

---

## 5. 交互与安全

- **需要用户确认才写入**：idea.md 修改；analysis_plan 批准与变更；register 发布；technical_map 结构；Intro/LR blueprint；finalize 投稿元数据；任何 git commit/push；删除或覆盖用户文件（一律先备份或移入 `_archive/`，不硬删）。
- "继续 / ok" 只对当前已展示的那一步生效，不代表授权后续写入。
- Git：技能不自动 commit；阶段结束时给出建议的提交范围与信息，由用户确认。禁止 `git checkout --`、`git clean` 作为恢复手段。
- OpenAlex：一律从 `~/Library/CloudStorage/Dropbox/Apps/secrets-vault/openalex.env` 读取 `OPENALEX_API_KEY` 与 `OPENALEX_MAILTO`，每次请求同时带 `api_key` 与 `mailto`。

---

## 6. 平台语法对照

| 概念 | Claude | Codex |
|---|---|---|
| 调用技能 | `/lit-workflow`（Skill 工具） | `$lit-workflow` |
| 项目合同 | 项目 `CLAUDE.md` | 项目 `AGENTS.md` |
| 共享目录 | `~/.claude/skills/shared/` | `~/.codex/skills/_academic-shared/` |
| 共享脚本 | `~/.claude/skills/shared/*.py` | `~/.codex/skills/_academic-shared/scripts/*.py` |
| 子 agent | `~/.claude/agents/*.md` + Agent 工具 | `_academic-shared/agents/*.md` + Codex worker |
| 向用户确认 | AskUserQuestion | 确认卡（对话中列出选项） |

除上表语法差异外，同名技能的流程、文件约定、阻断规则必须一致。
