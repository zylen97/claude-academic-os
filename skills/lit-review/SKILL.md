---
name: lit-review
description: 文献 review 阶段：读取 canonical direction{N}_{wos|cnki|openalex}.ris，按 ≤30 篇分批派 sonnet worker 逐篇筛选（每条记录都有决定与理由），脚本校验后按配额合并为 direction{N}_report.md 与 screening_summary_report.md，并即时提示疑似竞品。通常由 lit-workflow 调用；单独使用时用于某方向的修复或补充后重跑。
argument-hint: "[方向列表，如 1,3；默认全部计划方向]"
---

# lit-review — 逐篇筛选 → 方向报告

规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md` §3（冲突时以规格为准）。常规入口是 `/lit-workflow`；本技能也是 review 阶段的定点修复入口。

- 文件约定、去重口径、RIS 解析全部来自共享模块 `~/.claude/skills/shared/lit_common.py`。
- 运行目录 `structure/2_literature/_review_runs/`（分派计划 `dispatch_plan.json`、批次文件、RIS chunk）。不读、不写 `_tag_runs/`。
- 不自动 commit；不用 `git checkout --` / `git clean` 恢复；覆盖已有方向报告前须用户确认，旧报告自动移入 `structure/2_literature/_archive/{日期}/`。

下文命令均在论文仓库根目录（含 `structure/` 的目录）执行，`L=structure/2_literature`。

## 输入

| 文件 | 说明 |
|---|---|
| `$L/direction{N}_{wos\|cnki\|openalex}.ris` | 语料输入（唯一识别规则 `lit_common.classify_ris`）；其他 `.ris` 只提醒、不读取 |
| `$L/_quota_result.json` | 方向、名称、分轨配额与分级上限（权威）；缺失时退回 `literature_search_plan.md` 的方向表 |
| `structure/0_global/idea.md`、项目 `CLAUDE.md` | 研究背景 |

CNKI `.enw` 的转换属于 lit-workflow 的输入整理阶段（`cnki_enw_to_ris.py` 仍放在本技能目录供其调用）。OpenAlex 补充只能经 lit-workflow 的 `openalex_to_ris.py` 生成 `direction{N}_openalex.ris`，再从 review 重跑。

## 步骤 1：分派

```bash
python3 ~/.claude/skills/shared/dispatch_plan.py --mode ris --lit-dir $L [--directions 1,3]
```

- 必须 `VERIFY: PASS`。阻断（原样报告并停止）：计划方向缺少输入文件或配额要求的来源（OpenAlex 不能替代 WoS）、RIS 的 TY ≠ ER、记录缺标题。提醒（⚠️，继续）：文件名不规范、计划外方向的输入、未转换的 `.enw`。
- 重跑即续跑：记录未变的批次文件原样保留（已填写的不会丢）；源 RIS 变化导致不一致的批次自动移入 `_archive/` 并重建。
- 用以下命令确定需要派发的批次（`EMPTY` / `INVALID` / `MISSING`）：
  ```bash
  python3 ~/.claude/skills/lit-review/format_batches.py --lit-dir $L --json
  ```
- 展示分派表（批次数、篇数、待派发数），用 AskUserQuestion 确认后再派发。

## 步骤 2：子任务（worker）

- 每个待派发批次一个 worker：Agent 工具，`subagent_type: "lit-review-worker"`（定义在 `~/.claude/agents/lit-review-worker.md`，sonnet，只有 Read/Write，只写分配给它的批次文件）。不传 isolation。
- 滚动并发 ≤ 8：完成一个补一个；维护已启动批次清单，不重复派发。
- prompt 只需给：`{RESEARCH_CONTEXT}`（≤800 字：题目、RQ、方法、核心机制、目标期刊；从 idea.md 与 CLAUDE.md 浓缩）、方向编号与名称、论文角色、该方向分级上限（参考）、批次文件路径 `$L/_review_runs/{batch_file}`、chunk 路径 `$L/_review_runs/{chunk_file}`。填写规则在 worker 定义中，不要另写一套。
- **即时竞品预警**：worker 回报“疑似竞品 Z > 0”时，立即在对话中列出（作者、标题、来源方向、一句理由），措辞只说“疑似”，不下“有/无竞品”或“创新性风险低”的结论。

### 失败语义（规格 §3.3）

worker 报错，或其批次在 `format_batches.py` 中不是 `OK`，即为该批次失败：

1. 停止派发新批次 → 等在途 worker 完成 → 对失败批次各重试一次；
2. 仍失败：`python3 ~/.claude/skills/lit-workflow/lit_status.py mark --project-root . --direction N --stage review --state FAILED --note "<原因>"`，用 AskUserQuestion 请用户选择“修复”或“跳过该方向”；
3. 修复成功 → `mark … --state CLEARED`；用户确认跳过 → `mark … --state SKIPPED --note "用户确认跳过"`。脚本读取 `lit_status.md`（经 lit_status.py 的解析）：被标 SKIPPED 且其后无 CLEARED 的方向自动排除在校验、合并之外（汇总报告标“用户确认跳过”），不必重新分派。只标 FAILED 不会解除阻断。

## 步骤 3：校验

```bash
python3 ~/.claude/skills/lit-review/format_batches.py --lit-dir $L
```

阻断项（批次需重做）：记录块与 chunk 不一致、决定缺失或非 include/exclude、include 缺级别、理由为空、入选 + 淘汰 ≠ 记录数、源 RIS 在分派后变化。提醒项（不阻断）：证据不能在摘要中逐字找到、无摘要入选未注明“仅凭标题”。必须 `VERIFY: PASS`。

## 步骤 4：抽检

随机抽 3 条 include（尽量跨方向），打开对应 chunk 核对 AB 与批次中的理由、证据。不符 → 该批次按失败处理（重做后回到步骤 3）。

## 步骤 5：合并

```bash
python3 ~/.claude/skills/lit-review/merge_screening.py --lit-dir $L [--overwrite]
```

- 每方向：WoS + OpenAlex 共用国际配额，CNKI 单独配额；同轨内先按统一去重口径（DOI / WoS UT / 第一作者+年份+标题前80字符）合并重复、保留最高级别，再按级别上限截断。入选文献的 RIS 缺年份或作者 → 阻断（修 RIS 后重跑分派）。
- 方向报告已存在时脚本拒绝覆盖：向用户说明将被替换的方向，确认后加 `--overwrite`（旧报告移入 `_archive/`）。
- 产物：本次方向的 `direction{N}_report.md`（6 列表格 + 疑似竞品 + 竞品判断边界 + 末行 `lit-records` 溯源注释，下游脚本依赖它，不要手改）；`screening_summary_report.md`（按全部方向报告重算）。review 报告此后不再被改写，标签只写进 `tagged_reports/` 副本。
- 预算（`_quota_result.json` 的 `total_budget`）只做提醒。合并输出中“OpenAlex 补充被配额挤掉”的条目要告诉用户。

## 步骤 6：汇报

在对话中给出：各方向入选数（核心/重要/备选）与超配额未入选数；疑似竞品汇总（标“未核实”；没有时说“未标出疑似竞品，不等于不存在竞品”）；方法先例的初步印象（1 行/篇，可选）。然后运行 `python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root .` 刷新状态表。下一步：`/lit-tag`（或 `/lit-workflow` 续跑）。

建议提交范围（由用户确认后提交）：`$L/direction*_report.md`、`$L/screening_summary_report.md`；`_review_runs/` 是否入库由用户决定。

## 阻断与提醒

| 情形 | 处理 |
|---|---|
| 计划方向缺输入 / 配额要求的来源缺失；TY ≠ ER；记录缺标题 | 阻断（分派） |
| 批次未填、不完整或与 chunk 不一致 | 该批次失败 → 重试一次 → FAILED，询问修复或跳过 |
| 入选文献 RIS 缺年份或作者 | 阻断（合并），修 RIS |
| 方向报告已存在 | 需用户确认后 `--overwrite`（旧报告归档） |
| 文件名不规范、计划外输入、证据未逐字命中、超预算 | 提醒 |
| `_review_runs/dispatch_plan.json` 缺失 | 报错，回到步骤 1；不降级 |
