---
name: narrative
description: "叙述型章节写作（section=introduction|literature|discussion；mode=auto|draft|revise|audit|rebuild）：Introduction 与 Literature Review 先更新 blueprint md（structure/1_introduction/introduction.md、structure/2_literature/literature.md）并经用户确认再写 manuscript.tex；Discussion 按项目合同「## 技术章节」的角色定位技术章节（不按字面标题），要求 technical 已完成，逐 RQ 三卡确认后写入。引用池外文献须先回到 lit-workflow 入池。"
---

# Narrative — 叙述型章节写作

唯一规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（§2 目录、§4.5 术语表、§4.6 日期检查、§4.7 本技能要点、§5 确认点）。冲突以规格为准。

在规划、生成或审计任何正文前，完整读取并执行 `~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`：内部审计可以穷尽风险，但只有通过 minimum-sufficient qualification gate 的边界、让步或 limitation 才能进入正文；该规则适用于 Introduction、Literature Review、Discussion 及 implications。

**核心原则**：
1. **blueprint-first for Introduction / LR**：`structure/1_introduction/introduction.md` 与 `structure/2_literature/literature.md` 是逻辑合约；先更新 blueprint 并经用户确认，再生成或替换 tex。`manuscript.tex` 是唯一正文。
2. **tex-in / tex-out for Discussion**：Discussion 只锚定当前正文的技术章节（按项目合同 `## 技术章节` 定位），不建中间 md。
3. **直接生成英文句子**，不走"中文要点 → 翻译"。
4. **功能块 review**：默认按完整段落或假设族确认；用户可随时指定句子级修改。
5. **claim-role evidence**：按外部事实、既有发现、理论命题、方法能力和情境机制配置引用；不以句子引用率代替 claim fit。
6. **引用只来自文献池**：项目 bib 或 `citation_pool/master.bib` 中都没有的文献，必须先回到 `/lit-workflow` 入池（OpenAlex 补充经 `openalex_to_ris.py` 生成 `direction{N}_openalex.ris`，再从 review 续跑到 pool），入池前不得引用。
7. **文献定位是功能而非固定表格**：先搜索正文、附录、label/ref 与图表注册表；确需新建或更新 literature landscape 时，转入 `/build-intro-lit-table` 与 `/latex-table`。

**与相关技能的边界**：
- `/analysis` = 计划、执行、登记结果；本技能不补分析。
- `/technical` = 技术章节 Map 与正文；本技能不动技术章节。
- `/build-intro-lit-table` = Introduction literature landscape 表；本技能只决定正文需要何种定位功能。
- `/polish` = 语言专用；Discussion 每个 RQ 候选在展示前调用其嵌入模式（`POLISH_EMBEDDED_CANDIDATE_ONLY`，只返回候选文本，不写文件）。
- `/finalize` = Conclusion / Abstract / Cover Letter。

**输入** `$ARGUMENTS`：`section=introduction|literature|discussion`（必须）；`mode=auto|draft|revise|audit|rebuild`（可选，默认 `auto`）；`lr_profile=review_only|review_plus_theory|review_theory_hypothesis`（仅 LR；未指定且无已确认选择时请用户选择）。

---

## 步骤 0：前置准备

### 0.1 参数解析

- `section` 必须为 `introduction` / `literature` / `discussion` 之一；不在范围 → AskUserQuestion 让用户选择。
- `mode` 默认 `auto`：目标 section 空白 / TODO → `draft`；已有成熟正文 → `revise`；用户只要求检查或评估 → `audit`。`rebuild` 仅在用户明确要求整节重写时使用；`revise` 不等于整节重写。
- 设 `{SECTION_TYPE}` ∈ {`intro`, `litrev`, `discussion`}；`{NARRATIVE_MODE}` ∈ {`draft`, `revise`, `audit`, `rebuild`}；`{SECTION_QUERY}`：intro → `Introduction`，litrev → `Literature Review`，discussion → `Discussion`。

### 0.2 项目文件路径

- 从项目合同 `CLAUDE.md` 取 `manuscript.tex` 与 `.bib` 路径；fallback：Glob 根目录含 `\documentclass` 的 `.tex`（排除 supplementary / appendix / *.cls）。记 `{TEX_PATH}`、`{BIB_PATH}`。
- 读取项目合同的 `## 项目阶段`、"方法 profile"、`## 技术章节`。

### 0.3 Section tree 解析

创建本次运行的临时目录 `{RUN_TMP}`（会话 scratchpad 或系统临时目录，不在项目根目录）；所有 JSON、候选正文与审计输出只写入该目录。

```bash
python3 ~/.claude/skills/shared/tex_section.py section-tree --tex {TEX_PATH} --output {RUN_TMP}/section_tree.json
```

VERIFY 必须为 PASS。

### 0.4 Section 匹配（不在 preflight 修改正文）

```bash
python3 ~/.claude/skills/shared/tex_section.py match-section \
  --tree {RUN_TMP}/section_tree.json --query "{SECTION_QUERY}" \
  --require-unique --output {RUN_TMP}/section_match.json
```

读取唯一的顶层 `{SECTION_NODE}`。`Literature Review` 允许匹配 `Literature review and hypothesis development` 等包含式标题，不得匹配 Appendix 或重复标题。

**匹配失败**（VERIFY: FAIL）：preflight 不得修改正文。`audit` / `revise` 直接 BLOCK 并列出候选；`draft` / `rebuild` 在步骤 4 的写入确认中把"新建 section 骨架"列为明确写入动作，锚点：

| `{SECTION_TYPE}` | 新建位置 |
|:--|:--|
| `intro` | `\begin{document}` 之后（abstract / frontmatter 之后，如有） |
| `litrev` | 项目合同 `## 技术章节` 所列第一个技术 `\section` 之前；该节为占位时放在 `\section{Introduction}` 之后 |
| `discussion` | `## 技术章节` 所列最后一个技术 `\section` 之后；技术章节未完成 → 按 3.1 BLOCK |

### 0.5 上下文加载

按以下权威层级加载：

1. **项目合同** — 正文正本、写入范围、图表注册规则、阶段、方法 profile、`## 技术章节`。
2. **`structure/0_global/idea.md`** — 研究主题、Gap、RQ、理论框架、目标期刊、贡献意图。
3. **`manuscript.tex`** — 当前 section 正文（修改基线）；Introduction / LR / 技术章节 / Discussion 中的 RQ、H、构念、分析层级、时间与结论措辞；`\journal{}` 或 abstract 中的期刊信息。
4. **术语表** — `structure/0_global/technical_map.md` 第 2 节（存在时读取；md 文件，允许读取），作为术语合同的输入（见 3.3.4 第 6 项）。
5. **`structure/2_literature/citation_pool/`** — BG / GAP / METHOD / LR / DISC / COMP 池与 `master.bib`。
6. **`{BIB_PATH}`** — 验证 citation key；key 存在不等于 claim fit。
7. **section 特异源**：
   - **intro**：`structure/1_introduction/introduction.md`；完整读取 `references/introduction-literature-workflow.md`。
   - **litrev**：`structure/2_literature/literature.md`；完整读取 `references/introduction-literature-workflow.md`；读取 `tagged_reports/`、`master_report.md`、`literature_search_plan.md`（如存在）作为文献溯源；读取当前技术章节中 role=method 的 section 以锁定构念、机制与分析层级；有假设时再核对统计量 / 编码，不得用结果反推假设方向。
   - **discussion**：按 3.1 定位的技术章节正文（结果唯一权威）。
8. **结果权威边界**：Discussion 的结论与数值只以当前 `manuscript.tex` 技术章节为准。`analysis_plan.md`、`results_register.md`、`technical_map.md` 只读取规格 §4.6 所需的日期与第 2 节术语表，不用来补写、纠正或替换正文结果。正文技术章节缺失或内部矛盾 → 停止并转回 `/technical`。

显示加载状态：
```
📂 上下文加载完成：
- 纲领: structure/0_global/idea.md
- manuscript.tex: section "{title}" 现有 {N} 字符；模式 {draft/revise/audit/rebuild}
- blueprint: {路径} {状态: 不存在 / TODO 模板 / draft / confirmed（日期）}  [intro/litrev]
- 术语表: technical_map.md 第 2 节 {已加载 N 条 / 不存在}
- 引用池: {citation_pool 文件列表}；期刊: {journal}
[litrev]: - LR 类型: {用户已确认的类型 / 待选择}
[discussion]: - 技术章节: {标题（角色）列表}；技术正文完成: {日期}
```

### 0.6 路由

`intro` → 步骤 1；`litrev` → 步骤 2；`discussion` → 步骤 3。各子模式完成后进入步骤 4（写入）。

---

## 步骤 1：Introduction 子模式

### 1.0 Blueprint（必须先于正文）

目标文件 `structure/1_introduction/introduction.md`（模板结构见 `~/.claude/skills/paper-init/common/introduction.md.tmpl`）。

1. 读取 blueprint：
   - **不存在**：阶段为 `foundation` / `analysis` / `drafting` → 按模板结构新建；阶段为 `submitted` / `revision-R{N}`（定稿后脚手架可能已归档）→ 不新建文件，改用会话内 Function Map，并在写入确认中注明"blueprint 已归档，本次以会话内合约为准"。
   - **TODO 模板或与 idea.md 的 Gap / RQ 明显不一致** → 需要更新。
   - **revise 模式**：先从现稿生成 reverse Function Map，与 blueprint 对照，只更新用户要改的功能块。
2. 按 `references/introduction-literature-workflow.md` §3 建立 Function Map，写入 blueprint 的对应节：
   - 真实实践难题及其行动者；
   - 从伙伴 / 关系到网络、组合或其他正确分析层级的桥接；
   - 每个 `Gap → So what → declarative Aim → RQ` 语义链；
   - actor、context、sample boundary、time、method 与 focal theory；
   - 方法和理论不直接支持的推断（受保护边界）；
   - paper organization，以及是否需要独立 contribution preview（仅目标期刊或用户要求时）。
3. **Blueprint 确认**：展示 blueprint 拟写入的变更（新建则展示全文），AskUserQuestion：`(1) 写入 blueprint (2) 修改 (3) 取消`。写入后把状态行改为 `confirmed（{今天}）`。
4. `audit` 模式：只输出 Function Map 与 gate 结果，不写 blueprint、不写 tex，结束。

blueprint 未确认前不得生成正文。

### 1.1 连续段落架构与软预算

Introduction 默认不设 `\subsection{}`，按已确认的 blueprint 功能链写作：

`实践难题 → 关系/网络层级 → Gap–Aim 单元 × N → 研究对象/设计 → 方法适配 → focal theory 及边界 → RQs → remainder`

2–4 个 RQ 的论文以约 950–1200 词为软起点；按 RQ 数量、证据负担、目标期刊和全文预算调整。不得为凑字数压缩 gap、边界或方法适配逻辑，也不强制独立 Contributions 段。

### 1.2 Gap–Aim–RQ 对齐

每个 RQ 必须回溯到一个 defensible gap 与一个 declarative aim，不强制一一对应。逐链核对 construct、分析层级、context、时间限定、结论措辞与 claim strength；RQ 不得扩大为 aim 未承诺的机制、因果或绩效问题。

### 1.3 英文正文生成与 review

严格依据已确认的 blueprint 直接生成英文正文。先完成内部 semantic gates，再按功能块展示：实践问题与层级桥接、各 Gap–Aim 段、研究设计 / 理论镜头 / RQ、remainder。用户可确认整块或指定任一句修改。

`revise` 模式只生成用户选定功能块的候选替换；没有 `rebuild` 授权时不得从零生成整节。正文修改若改变了 blueprint 中的论证（Gap、Aim、RQ、边界），先回到 1.0 更新并确认 blueprint。

### 1.4 Gap、Aim 与 RQ 措辞

- 禁绝对性声明：❌ "X is unexplored" / "no prior research" / "the first study to..." / "completely absent" / "本文是首个..." / "完全空白"。
- 从已引文献的适用边界推出精确未知项：`Prior studies have ... However, ...`、`These findings leave unclear ...`、`It remains unclear whether ...`；不把 `to the best of our knowledge`、`few studies` 当作无需证据的套话。
- 每个 Gap–Aim 单元以陈述句收束（如 `Therefore, the first aim of this study is to examine ...`）；RQ 问号统一放在研究设计与理论镜头之后的列表中。

**RQ 列表写入硬约定**（Discussion 的 RQ 解析依赖此约定）：
```latex
\begin{itemize}
  \item \textbf{RQ1:} How does X affect Y under condition Z?
  \item \textbf{RQ2:} What mechanisms explain the relationship between X and Y?
\end{itemize}
```
（`\begin{itemize}` 或 `\begin{enumerate}`；每条 `\item` 以 `\textbf{RQ\d:}` 开头并含字面问号。）

### 1.5 Claim-role evidence 与语义审计

不计算句子引用率，不自动给无引句补文献。外部事实、行业统计、既有发现、理论命题和方法能力均须有 claim-fit 证据；作者综合、gap、so what、aim、RQ、本研究设计陈述、边界句和 remainder 通常无需机械加引。

展示前执行 `references/introduction-literature-workflow.md` §4 的 Introduction gates（practice-to-network、gap-evidence、Gap–Aim–RQ、design-fit、theory-scope、setting-boundary、hedge、no-premature-results）。

### 1.6 功能块 review 完成 → 步骤 4

---

## 步骤 2：Literature Review 子模式

### 2.0 用户选择 LR 类型

类型由用户决定；可推荐并说明依据，但不得自行确定或切换。本次指令、会话、项目合同或 `literature.md` 已记录用户的明确选择时直接沿用，否则说明选项并请用户选择。

| 类型 | 任务 | 默认总词数 | 默认允许区间 |
|---|---|---:|---:|
| `review_only` | 按研究问题组织主题，综合已有知识、概念、机制与研究定位 | 1,400 | 1,200–1,600 |
| `review_plus_theory` | 在主题综述基础上，明确采用某种理论解释研究问题 | 1,700 | 1,400–2,000 |
| `review_theory_hypothesis` | 进一步形成方向性论证和可检验假设 | 2,200 | 1,800–2,600 |

以上是个人写作默认值，不是期刊规定。预算覆盖完整 LR（含理论阐释、假设推导与假设句），以英文单词计，排除标题、图表、参考文献与括号式引文。用户明确篇幅或已确认的项目预算优先。局部修订不为凑字数扩改全节；确需超出预算时说明原因，由用户调整。

### 2.1 从 Introduction、RQ 与范文形成思路

读取当前 Introduction / RQ、LR 与 role=method 技术章节，明确读者进入模型或分析前需要理解的主题、概念和机制；不用结果预设文献结论。

用户指定范文时先读其完整 LR 与 Introduction 的研究问题，总结小节与 RQ 的关系、段落功能、文献比较方式，以及理论、gap 和方法说明的位置；无法获取全文时如实说明。未指定时可复用已有 benchmark，不强制新搜。缺少合适范文全文时通过 web-access skill 获取（若存在 `~/.claude/skills/web-access/references/benchmark-fulltext-workflow.md` 则按其执行），核验后归档到项目已有 benchmark 目录再阅读。范文只迁移组织原则，不照搬标题或论断。

### 2.2 Blueprint（必须先于正文）

目标文件 `structure/2_literature/literature.md`（模板结构见 `~/.claude/skills/paper-init/common/literature.md.tmpl`）。不存在时的处理同 1.0 第 1 项。

把以下内容写入 blueprint 并展示为 LR Architecture Card：
- 用户选择的类型、总词数及分配；
- 候选小节标题、顺序、每节核心问题与段落推进；与 RQ 的关系及所需证据类型；
- 当前稿保留 / 替换范围及受保护内容；
- 仅理论类：focal theory 与相邻理论的角色；仅假设类：H 清单、机制与对应的模型含义（Argument Packet 摘要）。

思路可用中文讨论，英文正文直接成稿。AskUserQuestion：`(1) 写入 blueprint (2) 修改 (3) 取消`；写入后状态行改为 `confirmed（{今天}）`。`audit` 模式只输出适用检查与修改建议，不写 blueprint、不写 tex。

### 2.3 文献检索、阅读与思路校正

按已确认的段落任务检索文献池：`citation_pool/`、`tagged_reports/`、`master_report.md`、`master.bib` 与项目 bib；用全文判断核心概念、机制和最近邻研究。每段在会话中建立证据对应：核心判断 → 代表研究及来源位置 → 共识 / 差异 / 适用边界 → 与本文关系；包含有意义的反例。证据不足时修正、收窄或删除判断，不能先写结论再装饰引用。

**池内证据不足**：先收窄或删除该判断；确需新文献时暂停本 section，告知用户需要补充的主题与检索方向，转 `/lit-workflow` 的 OpenAlex 补充流程（已核验 JSON → `openalex_to_ris.py` → `direction{N}_openalex.ris` → 从 review 续跑到 pool）。新文献进入 `citation_pool/master.bib` 后再回到本步骤；入池前不得引用。

普通引用选择与局部证据校正无需逐条确认；改变类型、整体架构、focal theory、RQ / H 或论断方向时，先回到 2.2 更新 blueprint 并由用户确认。

### 2.4 按类型成稿与审计

按证据校正后的思路直接写英文，以完整 subsection / 假设族供用户审阅（展开方式与检查见 reference §5–§7）：

- `review_only`：主题判断 + 代表研究比较与综合 + 必要的概念 / 情境机制解释；不强制独立理论节、H 或每节末尾的 gap。
- `review_plus_theory`：在主题综述上建立理论解释及其与研究问题的联系；不自动增加方向性假设。
- `review_theory_hypothesis`：按 reference §6 建立假设论证，核对理论前提、情境机制、方向与模型含义；不能用结果反推假设。

共同检查主题覆盖与区分、文献综合、证据匹配、与 Introduction / 方法的分工、构念与分析层级一致、正文经济性与总词数。引用服从论断角色，不以固定引用密度或逐篇摘要排列代替综合。

### 2.5 文献定位资产

先检查正文、附录和图表注册表中已有的定位资产；已有合格表格或正文定位即可，不为形式对称另造表或固定添加 Literature positioning 小节。确需新建或更新时转 `/build-intro-lit-table` 与 `/latex-table`。候选小节审阅后进入步骤 4。

---

## 步骤 3：Discussion 子模式

### 3.1 技术章节定位与前置检查

**定位**（不按字面标题匹配）：读取项目合同 `## 技术章节` 表，忽略以"（待"开头的占位行，得到 `{TECH_SECTIONS}` = [(标题, 角色)]，角色 ∈ {method, results, simulation}。对每个标题，在 `{RUN_TMP}/section_tree.json` 中只取 `cmd` 为 `section` 的节点（顶层 `\section`），标题去首尾空白后与表中标题比较（忽略大小写），要求恰好匹配一个。不要用 `match-section`：它也会匹配同名的 `\subsection`（如 analytical-model 骨架中 `\section{Equilibrium analysis}` 下的 `\subsection{Equilibrium analysis}`）而报歧义。

**前置检查**（任一不满足 → 🔴 BLOCK）：
1. `{TECH_SECTIONS}` 非空，且至少含 1 个角色为 `results` 的 section；
2. 每个列出的标题都在 manuscript 中唯一匹配到顶层 `\section`，且正文（去掉注释与 `% TODO`）≥ 300 字符；
3. `structure/0_global/technical_map.md` 表头"技术正文完成"已填日期；
4. `\section{Introduction}` 中能按 1.4 的约定提取至少 1 条 RQ。

BLOCK 提示：
```
⚠️ Discussion 需要已完成的技术章节：
  - ## 技术章节 为空/占位，或缺 results 角色 → 先运行 /technical（Map 会写入 ## 技术章节）
  - 标题在 manuscript 中找不到或重复 → 先运行 /technical 修复，使 ## 技术章节 与正文标题逐字一致
  - technical_map.md 无"技术正文完成"日期 → 先完成 /technical Tex
  - RQ 缺失 → 先运行 /narrative section=introduction
```

**日期检查**（规格 §4.6，提醒不阻断）：比较 `analysis_plan.md` 第 7 节最后一条日期、`results_register.md` 发布日期与 `technical_map.md` 技术正文完成日期。前两者任一晚于完成日期 →
```
⚠️ 技术正文可能已过期：{变更记录 / register} 日期 {X} 晚于技术正文完成日期 {Y}
  回流：register 变了 → /technical 修复；设计变了 → /idea-refine / /analysis Plan
  (1) 先回流（推荐） (2) 了解风险，继续写 Discussion
```

通过后额外读取：
- Introduction 的 RQ 列表 → `{RQ_LIST}`；
- Literature Review 全文中的 `\citep{}` / `\citet{}` keys → `{LR_CITED_REFS}`；
- 角色 `method` 的 section → 模型设定、关键假设、构念与结论目标；
- 角色 `results` / `simulation` 的 section → 关键发现、命题、Fig / Table 编号、统计或数值结果；
- `citation_pool/DISC.md`（如存在）。

```
📂 Discussion 上下文：
- 技术章节: {标题（角色）…}；技术正文完成 {日期}
- RQ 列表: {N} 个；LR 已用文献: {M} 个 keys
- 关键发现: {N} 个（含 Fig/Table/Proposition 编号）；DISC 池: {K} 个候选
```

### 3.2 子节结构

| 子节 | 字数 | 引用 | 写作格式 |
|:--|:--:|:--:|:--|
| Discussion on the research questions（按 RQ 切 `\subsubsection`） | 1000–1500 | 按角色 | 段落式深度讨论 |
| Theoretical implications | 400–500 | **≤3 个 `\citep`** | 总起句 + First / Second /（Third） |
| Practical implications | 按期刊与决策负担；独立子节常以 300–500 为软起点 | **尽量 0，上限 1** | 结果锚定的 decision translation |

总字数约束：1800–2500 词。

### 3.3 Discussion on RQ（逐 RQ 三卡）

进入本步骤前完整读取 `references/discussion-workflow.md`（分阶段确认、结果优先级、解释论证、本地语料检索、文献关系、Contribution Seed、claim ladder、理论落地与 punchline 的详细规范）。

```
FOR each RQ IN {RQ_LIST}:
  1. 从技术章节抽取全部相关发现，标记 unsupported/unexpected、异质性、divergence/asymmetry、
     expected/background；先把模型内部表述转译为"研究对象—结果构念—方向—比较对象"的
     substantive pattern，形成 RQ Answer Card
  2. 等用户确认"结果回答"；未确认不得进入解释或文献检索
  3. 围绕优先结果形成 1–3 个 Interpretive Arguments（结果锚点、理论逻辑、情境、解释类型、
     Contribution Seed、边界），形成 Interpretive Arguments Card
  4. 等用户确认"解释主线"；未确认不得为该论点配置引用
  5. 展示 Subagent Run Board；派只读子 agent（Agent 工具，`subagent_type: "Explore"`，只读）在本地语料内定向检索 manuscript LR
     与文献池；主 agent 合并并核对 claim fit。子 agent 不写 Discussion 正文
  6. 形成 Literature Dialogue Card：consistent with / extends / qualifies / contrasts with /
     contextualizes 关系，及 Contribution Seed 的 novelty verdict
  7. 等用户确认"文献对话"；未确认不得生成段落
  8. 建立 RQ 范围的 theory hierarchy 与术语合同（3.3.4），内部生成约 300–500 词初稿，
     以 reader-facing substantive answer 开头并执行 semantic gates
  9. 调用 /polish 嵌入模式（POLISH_EMBEDDED_CANDIDATE_ONLY），再做 regression-only claim lock；
     全部 gate 通过后才展示候选
  10. 用户句子级确认后展示 RQ-scoped 写入确认；批准后仅写入该 RQ，审计通过后把 validated
      seeds 记入 {CONTRIBUTION_LEDGER}
END FOR
```

三张卡不得合并跳过，除非用户已在当前对话中明确给出并确认三类内容（fast path 只压缩展示，不降低确认与 claim-fit 标准）。状态回退：RQ Answer 改变 → 作废后续 argument、检索、literature、draft、polished candidate；Argument 改变 → 作废检索、literature、draft、polished candidate；Literature relation 改变 → 作废 draft 与 polished candidate。仅措辞变化不作废三张卡，但须重新通过嵌入语言 / 忠实性 gate；用户明确要求保留的文字是 protected span。

theory-role 或术语合同的实质变化会作废 draft、polished candidate、语言 / 忠实性结果和受影响的 Contribution Seed，并退回产生该判断的确认卡。用户反馈某结果句"看不懂"或过于技术化 → 视为 semantic-source readability failure：保留三张卡，作废该句与 polished candidate，回到 substantive-first 结果转译后再走嵌入润色。

#### 3.3.1 RQ Answer Card

```
🧾 RQ{i} Answer Card
- Reader-facing direct answer: {一到两句，以研究对象、结果构念、方向和比较对象回答 RQ}
- Essential findings: {方向、条件 / 时期、关键对比；默认不写系数 / SE / p 值}
- Technical fidelity lock (not intended prose): {该回答如何逐项映射回技术章节的结论目标、条件、范围和正式对比}
- Priority: {P1=unsupported/unexpected、异质或分化；P2=对比或 punchline 所需；P3=次要的预期发现}
- Joint contrast: {多个结果共同呈现的核心差异；没有写 none}
- Prohibited inference: {结果不支持的因果、替代、绩效或生成过程推断}

请确认结果回答；此处不讨论原因。
```

analytical-model 的"发现"是命题、比较静态、阈值与数值结果：直接回答写成"在什么条件下、谁的什么决策 / 收益如何变化、相对于什么基准"，参数条件放进 fidelity lock，不让符号充当主语。

#### 3.3.2 Interpretive Arguments Card

优先解释未符合预期、异质、相反 / 不对称结果与综合 punchline；符合预期的结果只在对比需要时展开。

| ID | 对应结果 | 理论逻辑 | 研究情境（行动者 / 能力 / 接口 / 决策） | 类型 | Contribution Seed | Claim boundary |
|:--|:--|:--|:--|:--|:--|:--|
| A1 | {result} | {pathway} | {…} | theory-based meaning / possible contextual interpretation | {潜在 conceptual move，非成品贡献} | {不得推导什么} |

Contribution Seed 至少包含理论基线、可能的 conceptual move、证据锚点和情境到理论的抽象；行业事实本身不是理论贡献。每个 RQ 默认 0–2 个 seed。

#### 3.3.3 本地语料检索与 Literature Dialogue Card

解释主线确认后，按 reference §5 展示 Subagent Run Board，并只在本地语料内定向检索：
- Agent A：manuscript LR 的已引文献及邻近原句中可对话的 claim；
- Agent B：`citation_pool/DISC.md`、`COMP.md`、`LR.md`，必要的 `BG.md` / `GAP.md`，`master_report.md`、`tagged_reports/`、`master.bib`；
- Agent C（仅在强 extension / contrast、目标期刊贡献或 claim fit 含混时）：Claim-Fit & Contribution 审计。

子 agent 只读、输出结构化证据表、不写正文、不决定最终关系；主 agent 负责合并、去重、核验 citation key。子 agent 不可用时顺序执行同样的检索并在卡片中注明。本地语料不足 → 先收窄或删除 argument；确需新文献 → 按 2.3 的"池内证据不足"流程回到 `/lit-workflow`，入池前不得引用。

Literature Dialogue Card 至少展示：argument、候选文献、文献实际 claim、关系类型、相同 / 不同边界、拟写法、Contribution implication、novelty verdict（supported / duplicate / overstated / insufficient evidence）。`contextualizes` 只能支持背景，不能冒充对结果机制的直接验证。

#### 3.3.4 成稿内审、嵌入润色与 Contribution Ledger

第一版不直接展示。先按 reference §10 执行：

1. **Result-compression + substantive-first readability gate**：结果摘要只保留实质模式，统计检验名、稳健性与方法细节留在技术章节；RQ 开头先用"研究对象—结果构念—方向—比较对象"的领域语言陈述结果，模型内部对象只能随后限定或核验。成句反向映射到结论目标，确认条件、范围、方向与正式对比未变；不通过时修复 semantic source，不交给 `/polish`。
2. **Integration gate**：同一 RQ 的多个结果共享一条解释主线，保留各自理论角色。
3. **Claim-strength gate**：结果事实直接陈述；理论含义用 `can / suggests / is consistent with`；未检验的情境机制只用一个总括性限定。
4. **Domain-grounding gate**：解释落到项目实际行动者、能力与接口；换一个行业名称仍完全成立 → 重写。
5. **Theory-hierarchy gate**：focal lens 来自 Introduction / LR；其余来源标为相邻文献或情境证据。Discussion 不得引入 LR 未定位的新理论标签，不得把相邻文献写成主理论的组成或延伸，不得从单篇情境研究制造新领域名称；确需新理论 → 停止并返回 LR。
6. **Canonical-terminology gate**：建立本 RQ 的术语合同，覆盖理论角色、行动者 / 分析单位、构念、结论目标、时期 / 条件和行业术语。优先级：当前流程中用户明确批准的措辞 → `technical_map.md` 第 2 节术语表 → manuscript 正式定义 → 技术章节中的结论含义 → 一致的局部用法。技术章节提供必须保持的语义与推断边界，不要求照搬模型内部句法。记录 preferred term、须区分的近义词与禁用的歧义同义词；实质冲突 → 停止并请用户裁决，不以润色方式解决。
7. **Citation-role gate**：每组引用承担明确且不重复的角色；目标期刊身份只用于内部选文，正文按研究领域、议题或机制称注文献，不写 "[Journal] research"。
8. **Punchline gate**：综合段说明多个结果共同增加了什么认识，不宣称未经检验的替代、因果或绩效。
9. **Economy gate**：删除相邻段落中的重复理论句、方法边界与防御性让步；不连续堆叠 `may / could / perhaps`。
10. **Contribution-seed gate**：只保留可追溯到已确认结果、解释与文献关系的 seed。

Semantic gates 通过后，将该版本冻结为 `{SEMANTIC_SOURCE}`，调用 `/polish` 嵌入模式：参数以 `POLISH_EMBEDDED_CANDIDATE_ONLY` 开头，传入 `{SEMANTIC_SOURCE}`、术语合同、protected spans、section 位置与目标期刊；该调用只改语言、不写文件。返回 `FAIL-BLOCKED: SOURCE-OPAQUE` → 回到第 1 项重写 semantic source。取得 `EMBEDDED-PASS` 后，主 agent 对候选做一次 regression-only claim lock（结果方向、统计 / 推导支持含义、条件与时间限定、模态 / 因果、情境 hedge、构念边界、引用挂载、段落数、300–500 词）。实质漂移 → 恢复 `{SEMANTIC_SOURCE}` 并最多重跑一次；第二次漂移为 `FAIL-BLOCKED`，不得展示或写入。

展示格式：
```
### RQ{i}: {简短主题}

[完整英文段落，约 300–500 词]

📊 字数: {N}
🔗 Citation roles: theory={…}; comparison={…}; context={…}; extension={…}
🔬 Results coverage: {essential findings 全覆盖 / 缺失项}
👁 Result readability: SUBSTANTIVE-FIRST PASS / BLOCK
🧭 Claim calibration: observed / theory-based / contextual 已区分
🧩 Theory hierarchy: PASS / BLOCK
🔤 Terminology alignment: PASS / BLOCK
✨ Language polish + fidelity: EMBEDDED-PASS / BLOCK

确认 / 修改某句 / 全段重写？
```

RQ-scoped 写入确认获批并写入后，回读目标 block，要求与用户批准文本完全一致，再运行：

```bash
python3 ~/.claude/skills/narrative/scripts/audit_discussion.py --tex {TEX_PATH} --rq "RQ{i}" --bib {BIB_PATH}
```

PASS 后显示 `✓ RQ{i}/{N} done`。WARN 由主 agent 做语义判断并记录；FAIL 必须修复后才能进入下一个 RQ。脚本不替代理论、情境与 claim-fit 的语义审核。

同时更新会话内 `{CONTRIBUTION_LEDGER}`：只记录 Literature Dialogue Card 判定为 `supported` 的 seed（字段见 reference §9）；`duplicate` 合并，`overstated` 降级，`insufficient evidence` 不进入。

### 3.4 Theoretical implications

#### 3.4.1 从 Contribution Ledger 综合，不独立发明贡献

全部 RQ 完成后，只从 `{CONTRIBUTION_LEDGER}` 生成理论贡献候选：删除无理论基线 / 无 RQ 证据 / 只有行业描述的 seed；按理论问题而非 RQ 编号聚类并合并；区分结果、情境解释与 theoretical move；保留最强且互不重叠的 2–3 个；把目标期刊 relevance 写成"为什么该理论认识对本领域重要"。

```
🎯 Contribution Synthesis Card
| # | 来源 seeds/RQs | Theoretical baseline | Confirmed evidence | Conceptual move | Scope/boundary | Target-journal relevance |
|:--|:--|:--|:--|:--|:--|:--|
| C1 | … | … | … | extend / qualify / differentiate / temporalize / integrate | … | … |
- Coverage / Non-overlap / Traceability: …
请确认贡献组合；未确认不得成稿。
```

用户调整贡献时同步回查 seed、RQ 证据与文献关系。ledger 为空 → 🔴 BLOCK：返回对应 RQ 的 Interpretive Arguments / Literature Dialogue Card 收窄重审，不得独立发明贡献。候选可能重叠或 novelty 含混时，派一个只读 Claim-Fit & Contribution Auditor（Agent 工具，`subagent_type: "Explore"`，只读）做跨 RQ 审计后再形成卡片。

#### 3.4.2 英文段落

每项贡献按 `theoretical baseline → confirmed RQ evidence → conceptual move → scope/boundary → relevance` 书写；理论贡献是跨 RQ 的升华，不按 RQ 顺序复述。格式：总起句 + First / Second /（Third），每点 2–3 句、0–1 个 `\citep`；400–500 词，全节 ≤3 个 `\citep`。ledger 只支持两个不重叠贡献时只写两点。

#### 3.4.3 用户句子级 review

展示 + AskUserQuestion：确认 / 修改 / 重写，循环至确认。

### 3.5 Practical implications

进入本步骤前完整读取 `references/practical-implications-workflow.md`。

#### 3.5.1 Practical Decision Map

只从当前技术章节的已确认发现建立候选，不从常识独立发明建议。默认"一个不重叠的管理决策变化 = 一个 implication unit"；RQ 与管理决策自然一一对应时可按 RQ 排列，但不把 RQ 数量机械转换成建议数量。

```
🎯 Practical Decision Map
组织逻辑: {按管理决策 / 按相互依赖的工作流 / 按 RQ；说明理由}
Implication unit {i}:
- Result anchor: {哪项已确认发现，含方向/比较/不对称或条件}
- Manager/owner: {谁能采取行动}
- Focal decision: {其反复面对的哪项决策}
- Default to revise: {研究结果改变了什么常规判断}
- Action/design lever: {可调整的流程、资源配置、结构或控制}
- Trigger/trade-off: {何时采取；何时不应泛化}
- Optional illustration: {只在能澄清管理对象或实施顺序时保留}
Traceability verdict: {PASS/REVISE}
```

AskUserQuestion 确认。

#### 3.5.2 英文段落

每个 unit 采用最小充分链条：`non-obvious finding → focal managerial decision → changed action/design lever → trigger or trade-off → optional compact illustration`。不设固定建议数、句数或案例数；`First/Second/Third` 只在帮助识别独立决策时使用。引用尽量 0，上限 1 个 `\citep`；不得用新引文为超出本研究结果的处方补授权。生成后执行 workflow 中的 decision-change、specificity、example-role、evidence-distance、non-SOP、anti-laundry-list 与 economy gates；不通过时收窄或删除建议，不以增加例子、工具、KPI 或限定词修补。

#### 3.5.3 用户句子级 review

展示 + AskUserQuestion：确认 / 修改 / 重写，循环至确认。

### 3.6 Discussion 完成 → 步骤 4（各 RQ 已增量写入；implications 在此写入）

---

## 步骤 4：写入 manuscript.tex

Introduction / LR 按已批准的写作单元写入：`draft` / `rebuild` 在完整候选获批后创建或填充整节；`revise` 只替换明确批准的 paragraph / subsection / hypothesis-family blocks。Discussion 按 3.3 逐 RQ 增量写入（只替换目标 `\subsubsection`）；Theoretical / Practical implications 在各自确认后写入。所有写入都先过 4.0。

### 4.0 Citation hard gate（写入前）

提取拟写入文本（整节或目标 RQ block）中的全部 `\citep{}` / `\citet{}` keys，逐一检查：
1. 在项目 `{BIB_PATH}` → 通过；
2. 不在项目 bib、但在 `structure/2_literature/citation_pool/master.bib`（已入池）→ 列入 `{BIB_SYNC_ENTRIES}`，写入时从 master.bib 复制完整条目；
3. 两处都没有 → 🔴 BLOCK：列出 key，返回对应子节的引用选择；需要的新文献按 2.3 流程回到 `/lit-workflow` 入池。不得生成 `(ref)` 占位，不得手写或从外部直接粘贴 BibTeX 绕过文献池。

Introduction / LR 还须完成 claim-role audit：key 存在只证明可解析，不证明支持该论断；claim fit 不通过时不得靠换引用形式或加引用数量修复。

### 4.1 写入确认

Discussion 单个 RQ：
```
📝 RQ-scoped 写入确认
- Target: {TEX_PATH} → \subsubsection{RQ{i}: …} only
- Change: replace this RQ block; preserve every other Discussion subsection
- Words/citations: {N} words; {citation keys}
- Bib sync from master.bib: {list or none}
- Validation: citation hard gate + audit_discussion.py + LaTeX compile
确认仅写入这个 RQ？
```

其他写入：
```
📝 即将写入 {TEX_PATH} 的 \section{…}：
- 总字数: {N} 词（目标: {target}）；总引用: {citep} \citep + {citet} \citet
- 从 master.bib 同步到项目 bib: {list}
- 写作单元预览（每单元首句）: …
- [intro/litrev]: blueprint {路径} 状态 confirmed（{日期}） / 已归档（会话内合约）
- [revise]: 批准替换的 block；受保护的 RQ/H/labels/refs/figures/tables/macros；结构与字数 delta
- [新建 section 骨架]: {位置}
确认写入？(1) 写入 (2) 回退到某子节修改 (3) 取消
```

AskUserQuestion 等待最终确认。"继续 / ok" 只对当前展示的这一次写入生效。

### 4.2 写入（bib 先、tex 后）

1. 把 `{BIB_SYNC_ENTRIES}` 从 master.bib 原样追加到项目 bib，回读确认所有拟写入 keys 已存在；失败则停止，tex 不动。
2. `draft` / `rebuild` 替换或创建确认中列出的 section block；`revise` 只替换获批 block；RQ 增量写入只替换目标 block。
3. 保留目标 heading 行及其 `\label{}`。
4. 写入前后比较并保护 RQ、H、labels、refs、figures、tables、macros、environments 与未批准正文；任何未批准删除 → BLOCK。

**Introduction**：默认连续叙事，不自动插入 `\subsection{}`；Gap–Aim 段、研究设计 / 理论边界、RQ 列表和 remainder 按 blueprint 排列；独立 contribution preview 仅在 blueprint 要求时写入。

**LR**：subsection / subsubsection 来自 blueprint 中确认的主题 / 理论 / 假设架构，不从引用池方向机械生成；保留已有理论框架图与已登记定位资产的位置与引用；不自动创建 Literature positioning 小节或内嵌表。

**Discussion**：`\subsection{Discussion on the research questions}` 下按 RQ 用 `\subsubsection{RQ{i}: …}`；RQ 增量写入只替换目标 `\subsubsection` 到下一个 `\subsubsection` / `\subsection` / `\section` 之前的 block；`\subsection{Theoretical implications}`、`\subsection{Practical implications}`。

### 4.3 bib 回归

写入后重新提取本次 section 或 RQ block 的 keys，确认全部在项目 bib；不一致立即修复 bib/tex，不留 orphan citation。

### 4.4 编译与写后审计

```bash
latexmk -pdf -interaction=nonstopmode {TEX_PATH}
```

检查 undefined citation、LaTeX Error、duplicate label、Float too large、Emergency stop。Discussion RQ 增量写入还须运行 3.3 的 `audit_discussion.py`；只有引用回归、编译与 RQ 审计全部通过，才更新 `{CONTRIBUTION_LEDGER}` 或进入下一个 RQ。失败时只修复本次写入引入的问题；修复会改变研究逻辑时停止并返回对应确认卡。

---

## 步骤 5：完成提示

```
✅ /narrative section={SECTION_TYPE} 完成
- {section title}: {N} 词；功能块/子节 {M}；引用 {citep} \citep + {citet} \citet；bib 同步 {K} 条
[intro/litrev]: - blueprint: {路径} confirmed（{日期}）
[discussion]: - LR 文献回扣 {K}/{L}；结果锚点 {P} 处

💡 后续:
- 可在 manuscript.tex 中亲自再改一轮；改后需要语言打磨可运行 /polish section={…}
- 三节叙述型完成后 → /finalize
📦 建议提交（需你确认后才执行）: manuscript.tex {BIB_PATH} {blueprint 路径}；信息: narrative {section}
```

本技能不自动 commit。

---

## 共享约束

### 引用规则
- 生成时内部用 `[citep]/[citet]/[—]` 标识，最终 tex 只保留 `\citep{}` / `\citet{}`。
- 每个引用必须通过 4.0；池外文献先回 `/lit-workflow`。
- Claim fit 优先于密度；`\citet{}` 用于突出某研究的具体设计或发现，`\citep{}` 用于主题综合；不为形式交替换写。
- Discussion 优先复用 LR 已用文献。
- Hedge：已确认事实直接陈述；理论解释只用一个校准后的 modal；未检验机制只用一个总括限定。
- Minimum-sufficient qualification 与 one-risk-one-home：见 `MANUSCRIPT-ECONOMY.md`。

### 交互节奏
- 先确认完整合约：Introduction 先确认 blueprint（Function Map）；LR 先选类型再确认 blueprint；Discussion 维持 RQ 三卡。
- 功能块 review，可指定句子级修改；成熟稿定点修订，整节 rebuild 须明确授权。
- 写入 blueprint、写入 tex、git 操作分别确认（规格 §5）。

### 失败模式
- section 匹配失败：`draft` / `rebuild` 在写入确认中列出新建骨架；`audit` / `revise` BLOCK。
- citation key 缺失：写入前 BLOCK，回到引用选择或 `/lit-workflow`。
- Discussion 前置条件不满足：3.1 BLOCK。
- 日期检查发现技术正文过期：提醒并给回流路线，由用户决定。

### 与 /polish 的接力

Discussion 每个 RQ 候选在展示前已通过 `/polish` 嵌入模式（不写文件）。作者写入后另行修改并需要再次打磨时，独立调用 `/polish section={section title}`；未被作者再次改动的 RQ block 不重复自动润色。
