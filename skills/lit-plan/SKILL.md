---
name: lit-plan
description: 根据研究 idea 规划 5-7 个文献检索方向、功能标签与配额；默认经 web-access CDP 在已登录的 WoS 上实测命中数并抽样判断相关率，迭代检索式后导出 direction{N}_wos.ris；--plan-only 只出待实测方案；--cnki 额外给出 CNKI 专业检索式（用户手动导出 direction{N}_cnki.enw）。
---

# lit-plan — 文献检索规划

根据研究纲领（idea.md）规划 5-7 个承担配额的检索方向，计算配额，并默认通过 CDP 在 WoS 上实测、校准检索式、导出并即时命名 RIS。规格见 `~/.claude/skills/shared/ACADEMIC-OS-LITE.md` §3。

**输入** `$ARGUMENTS`：可选总预算（纯数字，默认 360）及模式标志。示例：`/lit-plan 360`（默认执行 WoS CDP）、`/lit-plan 360 --plan-only`、`/lit-plan 300 --cnki`。

**用户确认点**：检索方案与配额（写入 `literature_search_plan.md` 前）；CDP 账号风险提示；文件冲突处理。
**Git**：本技能不 commit / push；结束时给出建议提交范围。

---

## 全局约束

- **输出语言**：所有描述性文本用中文（方向名称、层面、角色、设计说明、配额理由）；WoS 检索式用英文。
- **文件命名**（规格 §3.2，由 `lit_common.classify_ris` 统一识别）：
  - WoS 导出：`structure/2_literature/direction{N}_wos.ris`
  - CNKI 导出：`structure/2_literature/direction{N}_cnki.enw`（lit-workflow 输入整理阶段转换为 `direction{N}_cnki.ris`）
  - 方向名称**只写在** `literature_search_plan.md` 的「方向表」中，不写进文件名。
- `_quota_result.json` 是长期产物，任何清理都不删除它。

---

## 步骤 0：解析输入与前置检查

### 0.1 解析预算
- 从 `$ARGUMENTS` 提取数字 → `{TOTAL_BUDGET}`（默认 360）；有效范围 100-500，超出时用 AskUserQuestion 确认。

### 0.1b CNKI 双轨（仅 `--cnki`）
- `--cnki` 是唯一触发方式，不自动检测项目类型。
- 检测到后用 AskUserQuestion 确认中英文配额：
  > 英文文献（WoS）预计多少篇？中文文献（CNKI）预计多少篇？（参考：申请书/学位论文通常英文 150-250 + 中文 80-150）
- 设置 `{WOS_BUDGET}`、`{CNKI_BUDGET}`、`{TOTAL_BUDGET}=两者之和`、`{SEARCH_PLATFORMS}=wos+cnki`。纯 WoS 模式不触发交互。

### 0.1c WoS 执行模式
- 默认 `{WOS_EXECUTION}=cdp`；仅 `--plan-only` 时为 `plan-only`。`--wos-cdp` 是兼容别名；与 `--plan-only` 同时出现 → 停止并提示参数冲突。
- CDP 只自动执行 WoS，不自动执行 CNKI。
- CDP 前加载 web-access（`~/.claude/skills/web-access/SKILL.md`），运行其依赖检查，并展示该技能规定的账号风险提示，取得用户接受。
- 新建后台标签页，不操作用户原有标签页；各方向**串行**校准和导出。

### 0.2 工作流类型与路径

| `$PWD` 包含 | `{WORKFLOW}` | `{IDEA_SOURCE}`（降级链，首个存在且 ≥100 字者） | `{LIT_DIR}` |
|:---|:---|:---|:---|
| `papers/` 或 `_gym paper/` | `paper` | `structure/0_global/idea.md` | `structure/2_literature/` |
| `dissertations/` | `diss` | `structure/0_global/idea.md` → `../源论文_latexfile/structure/0_global/idea.md` → `CLAUDE.md § 章节规划` | `structure/2_literature/` |
| `fundings/` | `fund` | `structure/0_global/idea.md` → `fund-idea.md` → `_drafts/fund-idea_*.md`（最新） | `structure/2_literature/` |

- 读取项目 `CLAUDE.md` → 项目编号、英文标题、一句话概括、方法、目标期刊。
- 判断成熟度 `{IDEA_MATURITY}`：`mature`（有明确 Gap/RQ → 方向围绕 Gap/方法论精准设计）或 `exploratory`（主题明确但 Gap/RQ 不明 → 方向偏探索、覆盖面更广）。写入方案文件头供下游参考。
- 降级链全部失败 → 停止，提示至少提供研究主题和大致方向（fund 先跑 `/fund-mine`；diss 先跑 `/diss-init`）。
- `{LIT_DIR}` 只是内部变量；向用户展示或写入文件时一律展开为字面路径 `structure/2_literature/`。

### 0.3 已有检索方案
- `structure/2_literature/literature_search_plan.md` 已存在 → 用 AskUserQuestion 询问覆盖还是增量更新。覆盖时旧方案先移入 `structure/2_literature/_archive/{YYYY-MM-DD}/`。

### 0.4 既有输入文件清点与编号冲突
列出 `structure/2_literature/` 顶层的 `*.ris`、`*.enw`。设计完方向（步骤 1）后自检：
- **编号复用**：已有 `direction{N}_*.ris|.enw` 而新方案的方向 N 主题已改变 → 写方案前用 AskUserQuestion 请用户选择：旧文件移入 `_archive/{YYYY-MM-DD}/`（移动，不删除），或把新方向换一个编号。
- **旧命名**：如 `5-媒介选择.ris`、`savedrecs.ris`、`cnki_combined.ris` 不会被识别为语料输入。确认它们对应的方向后，经用户同意改名为 `direction{N}_wos.ris`（或移入 `_archive/`）；跨方向合并的 CNKI 文件无法映射，需按方向重新导出。
- 处理完毕才进入步骤 2。

---

## 步骤 1：设计检索方向

设计 5-7 个承担正式配额的 **corpus** 方向；另可设计 0-3 个不承担配额的 **targeted probe**（窄 gap、竞品、反例核查），单独列出，不进入配额计算。

### 功能标签体系

| 标签 | 全称 | 含义 | 对应章节 |
|:-----|:-----|:-----|:---------|
| `BG` | Background | 近 3 年发表且与研究主题相关（沾边即可） | Introduction §1 |
| `LR` | Literature Review | 落在 LR 讨论主题范围内 | Literature Review §2 |
| `GAP-RQx` | Gap Support | 同一大主题但视角/维度/方法与 RQx 不同；按实际 RQ 数生成 | Intro / LR |
| `METHOD-基础` | Methodology | 定义/提出本文方法的文献 | Methodology |
| `METHOD-先例` | Methodology | 本文方法在其他领域的应用 | Methodology |
| `DISC-RQx` | Discussion | 与 RQx 相关（宽泛纳入）；按实际 RQ 数生成 | Discussion |
| `COMP` | Competitor | 做了高度相似研究的论文 | 跨章节（决定能不能做） |

### 每个方向必须包含
1. 方向编号与名称　2. 层面（核心理论/理论基础/方法论/行业背景等）　3. 论文角色（1-2 句）　4. 功能标签（5 问清单）　5. 优先级 P1/P2/P3　6. 一条可直接粘贴的 WoS 检索式　7. 检索式设计说明（对应哪些母文献流、为何用 TI/TS/AK、主要噪声风险）　8. 方向类型 `corpus` / `targeted_probe`

### 功能标签分配（5 问清单）

| # | 问题 | 是 → 标签 | 说明 |
|:-:|:-----|:---------|:-----|
| 1 | 该方向文献会在 LR 中被专门讨论（占一个 subsection 或一段）？ | **LR** | 纯工具型方法方向（如 SEM、回归）不标 LR |
| 2 | 方向是关于行业/应用领域的？ | **BG** | 且方向内有近 3 年文献 |
| 3 | 方向是关于方法本身的理论来源？ | **METHOD-基础** | 如 Biform Game 理论、Shapley 值定义 |
| 4 | 方向是关于方法在其他领域的应用？ | **METHOD-先例** | 如 Biform Game 在供应链中的应用 |
| 5 | 检索主题与 RQx 重叠？（逐个 RQ 判断） | **GAP-RQx + DISC-RQx** | 重叠则同时标 |

> 方法本身是理论框架（博弈论、信号博弈）→ 标 LR + METHOD；只是计算工具（SEM、DEA）→ 只标 METHOD。COMP 不分配给特定方向，所有方向自然扫描。

### 检索式设计原则

执行前完整读取 `references/query-design.md`。核心：
- 每个 corpus 方向内部生成宽式、平衡式、严式三个候选，最终只保留一条。
- 正式方向必须对应一个成熟学术社群；不要把本文完整创新组合当作唯一检索交集。
- 优先 `TS`；需要提高精度时用 `TI` 或 `(TI=(...) OR AK=(...))`。同义词用 `OR`，不同母概念用 `AND`，相邻母文献流可用 `(A AND B) OR (A AND C)`。
- 不写未经验证的命中量预测；`--plan-only` 方案标 `provisional`，CDP 实测通过后才标 `frozen`。
- `<50` 通常放宽；`>1000` 不自动收紧，相关性合格时按近 180 天使用量保留前 1000。

### 建筑工程领域术语规范
研究涉及建筑工程管理时，禁止单独使用 `"construction"` 或 `"building*"`（歧义极大），改用：

| 禁用 | 替代为（OR 连接） |
|:-----|:-----------------|
| `"construction"` | `"construction industry"` OR `"construction project*"` OR `"construction sector"` OR `"construction firm*"` OR `"construction company"` |
| `"building*"` | `"built environment"` OR `"building sector"` OR `"building industry"` |

可补充 `"AEC"`、`"civil engineering"`、`"infrastructure project*"`。固定短语（`"modular construction"`、`"off-site construction"`、`"prefabricated construction"`）语义已明确，无需替换。

### CNKI 专业检索式（仅 wos+cnki）

每个方向在 WoS 检索式后再给一条 CNKI 专业检索式（与 WoS 一一对应）：
- 字段：`SU`=主题、`TI`=题名、`KY`=关键词、`AB`=摘要、`FT`=全文、`AU`=作者、`AF`=机构、`JN`=文献来源、`YE`=年、`FU`=基金、`CLC`=分类号。推荐 `SU %=`（内置同义词扩展）。
- 同字段组合用 `*`(与) `+`(或) `-`(非)，检索词用英文单引号，如 `SU %= '供应链韧性 * 制造业'`；跨字段用 `AND/OR/NOT`（前后空格）；年份 `YE BETWEEN ('2020', '2026')`。CNKI 不支持 `*` 截断，用 `%` 模糊匹配。
- 关键词按中文学术界通行表达翻译，不做机械翻译；`SU %=` 已扩展同义词，可比 WoS 更简洁；中文文献量通常更大，可适当收紧。

格式：WoS 块后紧跟

```cnki
SU %= '供应链韧性 * 制造业' AND YE BETWEEN ('2020', '2026')
```
> CNKI 检索说明：{与 WoS 的差异，如术语选择、范围调整}

**CNKI 导出由用户手动完成**：每个方向在 CNKI 导出 EndNote 格式，保存为 `structure/2_literature/direction{N}_cnki.enw`。分批导出时把多个 `.enw` 首尾拼接为一个文件（记录间空行分隔）。不得跨方向合并。

### 方向覆盖性检查

| 标签 | 至少覆盖 | 理想覆盖 |
|:-----|:---------|:---------|
| `BG` | 1 个方向 | 1-2 个 |
| `LR` | 2 个方向 | 3-5 个 |
| `GAP-RQx` | 1 个方向 | 2-3 个 |
| `METHOD-基础/先例` | 1 个方向 | 1-2 个 |
| `DISC-RQx` | 1 个方向 | 1-2 个 |
| `COMP` | 不单设方向 | 各方向自然扫描 |

有标签未被覆盖 → 增加方向或调整功能标签。

---

## 步骤 2：分配配额（脚本计算，不心算）

### 2.1 准备输入
把 corpus 方向写入临时文件 `structure/2_literature/_directions.json`（targeted probe 不写入）：

```json
{"directions": [{"id": 1, "name": "方向名称", "tags": ["BG", "LR", "GAP-RQ1", "DISC-RQ1"], "priority": "P1", "direction_type": "corpus"}]}
```

### 2.2 运行配额脚本

```bash
# 纯 WoS
python3 ~/.claude/skills/lit-plan/quota_calc.py --directions structure/2_literature/_directions.json --budget {TOTAL_BUDGET}
# wos+cnki
python3 ~/.claude/skills/lit-plan/quota_calc.py --directions structure/2_literature/_directions.json \
  --budget-wos {WOS_BUDGET} --budget-cnki {CNKI_BUDGET}
```

脚本按标签池目标（BG=50, LR=150, GAP=75, METHOD=60, DISC=65）计算 tag_share → raw_demand → 等比缩放到预算 → 每方向保底 20（小预算可 `--min-quota`）→ 内部分层（核心 ≤25%、重要 ≤40%、备选 ≤35%）→ 标签覆盖检查；提供 `actual_hits` 后还检查命中量 ≥ 配额、命中量 ≥ 50、抽样相关率 ≥ 40%、`query_status` 已冻结；targeted probe 混入会报 `PROBE_HAS_QUOTA`。

### 2.3 校验
- stdout 末行 `=== VERIFY: PASS|FAIL ===`。**只有 PASS 才写 `_quota_result.json`**；FAIL 时不覆盖已有配额文件，停止并展示错误。
- 配额表用 AskUserQuestion 请用户确认（用户确认点）。后续步骤从 `_quota_result.json` 读取配额。

### 2.4 临时文件
- `--plan-only`：方案写入后删除 `_directions.json`。
- CDP 模式：保留 `_directions.json` 供步骤 2.5 回填实测字段；全部方向冻结且最终复核 PASS 后删除。
- `_quota_result.json` 永久保留。

### 2.5 WoS 实测校准与导出（默认执行；`--plan-only` 跳过）

完整读取 `references/wos-cdp.md`，然后对每个 corpus 方向**串行**执行（增量更新时只处理新增或检索式有改动的方向；未改动的方向沿用已有 `direction{N}_wos.ris` 与实测字段）：

1. `wos_cdp_export.mjs --mode count` 运行候选检索式（自动只保留 SCIE + SSCI，排序固定为 `Usage (last 180 days): most first`）。
2. 导出 20-50 条抽样 RIS 到项目外临时目录（如 `/tmp/lit-plan-{项目编号}/D{N}-v{轮次}-probe.ris`）；读取题名、摘要、关键词，逐条判断相关性并记录噪声类型。
3. 把 `quota`（取 `_quota_result.json` 中该方向 `wos_quota`）、`actual_hits`、`sample_size`、`sample_relevant`、`iteration` 写入临时 JSON，运行：
   ```bash
   python3 ~/.claude/skills/lit-plan/query_audit.py --input /tmp/lit-plan-{项目编号}/D{N}-audit.json
   ```
4. `REVISE` → 按真实噪声修改检索式，最多三轮；`ESCALATE` → 合并方向、降为 targeted probe，或用 AskUserQuestion 请用户决定。
5. `PASS` → 导出全部；`PASS_TRUNCATE_1000` → 导出前 1000：
   ```bash
   node ~/.claude/skills/lit-plan/wos_cdp_export.mjs --mode export --limit 1000 \
     --output structure/2_literature/direction{N}_wos.ris <<'WOS_QUERY'
   TS=(...)
   WOS_QUERY
   ```
6. 下载完成即核验 `TY = ER = 导出数` 并直接落为 `direction{N}_wos.ris`，再开始下一方向。
7. 目标文件已存在 → 停止并显示冲突（回到 0.4 处理）；禁止覆盖、禁止产生 `(1)` 副本、禁止遗留 `savedrecs*.ris`。数量不符时脚本把下载改名为 `direction{N}_wos.FAILED-x-of-y.ris` 并报错——该文件不会被识别为语料输入，核查后移入 `_archive/`。
8. 把 `actual_hits`、`sample_size`、`sample_relevant`、`sample_precision`、`query_status`、`final_ris`（= `direction{N}_wos.ris`）回填 `_directions.json`，重新运行配额脚本，必须 `VERIFY: PASS`。

---

## 步骤 3：列出经典文献

列出 WoS 检索式无法覆盖、必须手动补入的文献（专著、行业报告、工作论文/预印本、年代久远的奠基性文献）：

| 文献 | 论文中的角色 | 功能标签 |
|:-----|:------------|:---------|
| Author (Year). *Title* | 角色说明 | BG/LR/... |

> 这些文献若要进入文献池，须先核验 DOI，再经 `openalex_to_ris.py` 生成 `direction{N}_openalex.ris` 走 lit-workflow（见 lit-workflow「OpenAlex 补充」）。

---

## 步骤 4：生成 `structure/2_literature/literature_search_plan.md`

「方向表」是方向名称的唯一出处，lit-workflow 的 `lit_status.py` 从这里读取方向名；表格首列只写方向编号。

````markdown
# {项目编号} 文献检索方案

> **日期**: {YYYY-MM-DD}
> **检索平台**: {wos: "Web of Science Core Collection（SCIE + SSCI）"；wos+cnki: 再加 "+ CNKI 总库（专业检索）"}
> **总预算**: {TOTAL_BUDGET} 篇
> **目标期刊**: {从项目合同提取}
> **Idea 成熟度**: {mature / exploratory}
> **方案状态**: {provisional（未实测）/ frozen（全部方向实测通过并导出）}

## 方向表

| # | 方向 | 功能标签 | 优先级 | 配额 | 输入文件 |
|:--|:-----|:---------|:------:|:----:|:---------|
| 1 | {方向名} | {标签} | P1 | {纯WoS: N 篇；双轨: WoS X + CNKI Y} | direction1_wos.ris{双轨时加 , direction1_cnki.enw} |
| ... | | | | | |
| | **合计** | | | **{TOTAL_BUDGET} 篇** | |

**建议检索顺序**: {按优先级与依赖关系}

---

## 方向1：{方向名称}
> **层面**: …
> **论文角色**: …
> **功能标签**: …
> **优先级**: **P1**
> **配额**: {N 篇（核心≤x / 重要≤y / 备选≤z）；双轨："WoS X 篇 + CNKI Y 篇"}
> **WoS 实测**: {actual_hits；plan-only 写"待实测"}
> **抽样审计**: {sample_relevant}/{sample_size} = {precision；plan-only 写"待审计"}
> **检索状态**: {provisional / PASS / PASS_TRUNCATE_1000}
> **输入文件**: direction1_wos.ris{双轨: + direction1_cnki.enw}

```wos
{WoS 检索式}
```
> {检索式设计说明}

{双轨时 CNKI 检索式块}

---

{方向 2…N}

## Targeted probes（不承担配额，可选）

| 名称 | 检索式 | 用途 | 实测命中 |
|:-----|:-------|:-----|:--------:|

## 标签覆盖检查

| 标签 | 覆盖方向 | 状态 |
|:-----|:---------|:----:|
| BG | 方向X, 方向Y | ✅ |
| … | … | … |
| COMP | 各方向自然扫描 | ✅ |

## 需手动补入的经典文献

| 文献 | 论文中的角色 | 功能标签 |
|:-----|:------------|:---------|
````

### 对话输出
1. 方向表与配额；2. 标签覆盖检查；3. 建议检索顺序；
4. `--plan-only`：提醒用户实测后回到本技能冻结；CDP 模式：报告每轮命中量、抽样相关率、最终文件名及 TY/ER 校验；
5. 启用 CNKI：提醒按方向导出 `direction{N}_cnki.enw`；
6. 输入到齐后运行 `/lit-workflow`（输入整理 → [screen] → review → tag → pool）；
7. 建议提交范围：`structure/2_literature/literature_search_plan.md`、`_quota_result.json`、`direction*_wos.ris`（由用户确认后提交）。

---

## 边界条件

| 情况 | 处理 |
|:-----|:-----|
| idea 源缺失或 < 100 字 | 停止，提示至少提供研究主题和大致方向 |
| 方向数 < 5 / > 7 | 提醒覆盖不足 / 建议合并相近方向 |
| 某标签未被覆盖 | 提示并建议增加方向 |
| 已存在 literature_search_plan.md | 询问覆盖（旧文件归档）或增量 |
| CDP / 登录态不可用 | 停止自动执行，保留 provisional 方案，提示恢复浏览器连接 |
| corpus 方向命中量 < 配额或 < 50 | 修改检索式；三轮后合并或降为 targeted probe |
| 抽样相关率 < 40% | 按真实噪声继续收紧，不因数量合格而冻结 |
| 目标 RIS 已存在 | 停止；用户选择归档旧文件或换编号；不生成 `(1)` 副本 |
| RIS 的 TY/ER 与预期不一致 | 脚本改名为 `.FAILED-*.ris` 并报错，不进入下一方向 |
| quota_calc VERIFY: FAIL | 不写配额文件，展示错误，修正方向或预算后重跑 |
