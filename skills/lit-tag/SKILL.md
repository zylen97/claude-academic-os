---
name: lit-tag
description: 文献 tag 阶段：为 direction{N}_report.md 中每篇入选文献标功能标签（BG/LR/GAP-RQx/METHOD-基础/METHOD-先例/DISC-RQx/COMP），按 ≤30 篇分批派 sonnet worker，脚本校验后写入 tagged_reports/ 带标签副本（不改 review 报告），按唯一论文统计 tag_report.md。通常由 lit-workflow 调用；单独使用时用于某方向的重标或修复。
argument-hint: "[方向列表，如 1,3；默认全部已有 review 报告的方向]"
---

# lit-tag — 功能标签

规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md` §3（冲突时以规格为准）。常规入口是 `/lit-workflow`；本技能也是 tag 阶段的定点修复入口。

- 输入：`structure/2_literature/direction{N}_report.md`（review 产物，**只读，永不改写**）、`structure/0_global/idea.md`。
- 产物：`tagged_reports/direction{N}_report.md`（与 review 报告逐行对应，多一列“功能标签”）、`tag_report.md`。
- 运行目录 `_tag_runs/`（分派计划 `dispatch_plan.json` 与标签模板）；与 review 的 `_review_runs/` 互不覆盖。计划缺失即报错，不降级。
- 不自动 commit；已存在且内容不同的带标签副本被替换前自动移入 `_archive/{日期}/`。

下文 `$L` 指 `structure/2_literature`，命令在论文仓库根目录执行。

## 步骤 0：RQ

从 idea.md 读出 RQ 列表，得到 RQ 数 n（GAP-RQx / DISC-RQx 只允许 x = 1…n）。识别不出 RQ → 停止，请用户先在 idea.md 中明确 RQ，不默认 RQ1–RQ5。

## 步骤 1：分派

```bash
python3 ~/.claude/skills/shared/dispatch_plan.py --mode report --lit-dir $L [--directions 1,3]
python3 ~/.claude/skills/lit-tag/insert_tags.py --lit-dir $L --rq-count <n> --check --json   # 哪些批次待派发
```

- 必须 `VERIFY: PASS`。每个模板 `_tag_runs/d{N}_b{M}_tags.md` 首行记录该批文献的 tier:row 与标题。
- 重跑即续跑：未变的模板原样保留；review 报告变化后的模板自动归档重建，**标题相同的文献沿用已填标签**，只需补新文献。
- 展示分派表，用 AskUserQuestion 确认后派发 `EMPTY` / `INVALID` / `MISSING` 的批次。

## 步骤 2：子任务（worker）

- 每批一个 worker：Agent 工具，`subagent_type: "lit-tag-worker"`（`~/.claude/agents/lit-tag-worker.md`，sonnet，只写分配的模板）。滚动并发 ≤ 8，不重复派发，不传 isolation。
- prompt 给：`{RESEARCH_CONTEXT}`（≤800 字）、RQ1…RQn 原文、投稿年份（BG 窗口 = 投稿年及前两年）、模板路径、方向报告路径。标签定义在 worker 定义中，不要另写一套。
- 失败语义同 lit-review：worker 报错或其批次 `--check` 不是 OK → 停止派发 → 等在途完成 → 重试一次 → 仍失败则 `lit_status.py mark --project-root . --direction N --stage tag --state FAILED --note …`，询问“修复 / 跳过”；修复成功 `--state CLEARED`，确认跳过 `--state SKIPPED`。review 或 tag 被标 SKIPPED（其后无 CLEARED）的方向自动排除在分派、写入、汇总与 pool 之外。

## 步骤 3：写入带标签副本

```bash
python3 ~/.claude/skills/lit-tag/insert_tags.py --lit-dir $L --rq-count <n>
```

全有或全无：计划中任一批次缺失/未填/含非法标签（不在定义表、RQ 编号越界、分隔符不是 `+`）/行号与报告不符，或 review 报告在分派后变化 → 不写任何文件，`VERIFY: FAIL`，按失败语义重做对应批次。通过后写入计划中各方向的 `tagged_reports/direction{N}_report.md`。

## 步骤 4：汇总

```bash
python3 ~/.claude/skills/lit-tag/tag_aggregate.py --lit-dir $L --rq-count <n>
```

阻断：`tagged_reports/` 与 review 报告不一一对应（缺副本、多副本、副本行与报告不一致——提示对该方向重跑本技能）；有文献无合法标签。统计按唯一论文（与 review 同一去重口径：DOI / WoS UT / 第一作者+年份+标题前80字符），重复出现的文献合并标签、保留最高级别；方向贡献表按出现次数计。达标率只做提醒。

## 步骤 5：抽检与汇报

- 随机抽 2–3 篇（跨级别）核对标签与入选理由是否相符；明显不符 → 重做该批次。
- 汇报：唯一论文数与出现次数、各标签组达标情况（⚠️/❌ 的标签给出补检方向建议，补检只能经 lit-workflow 回流）、COMP 篇数（为 0 时说“当前语料未标出竞品”，不说“不存在竞品”）。
- 运行 `python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root .` 刷新状态。下一步：`/lit-pool`（或 `/lit-workflow` 续跑）。
- 建议提交范围（用户确认后提交）：`$L/tagged_reports/`、`$L/tag_report.md`。

## 阻断与提醒

| 情形 | 处理 |
|---|---|
| idea.md 无可识别 RQ | 停止，请用户明确 RQ |
| `_tag_runs/dispatch_plan.json` 缺失 | 报错，回到步骤 1；不降级 |
| 批次缺失/未填/非法标签 | 该批次失败 → 重试一次 → FAILED，询问修复或跳过 |
| review 报告在分派后变化；带标签副本与 review 报告不一致 | 阻断，对该方向重跑本技能 |
| 标签达标率低、COMP = 0 | 提醒 |
