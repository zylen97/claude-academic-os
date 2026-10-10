---
name: lit-workflow
description: 文献条线唯一常规入口：在 lit-plan 产出检索方案与 direction{N}_wos|cnki RIS/ENW 之后，依次执行 输入整理（命名校验、CNKI .enw→.ris）→ [screen] → review → tag → pool，可用 from/through 从任一阶段续跑，并维护 structure/2_literature/lit_status.md。也用于 OpenAlex 补充文献（openalex_to_ris.py）后从 review 重跑。不设计检索式（那是 lit-plan）。
argument-hint: "[status] [from=screen|review|tag|pool] [through=screen|review|tag|pool] [screen=ask|off]"
---

# lit-workflow — 文献流水线编排

规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md` §3（与本文件冲突时以规格为准）。

```
lit-plan → lit-workflow：输入整理 → [screen] → review → tag → pool
```

- 本技能只编排。进入某阶段时，**完整读取该阶段技能的 SKILL.md 并按其执行**（不嵌套调用技能）：
  `~/.claude/skills/lit-screen/SKILL.md`、`~/.claude/skills/lit-review/SKILL.md`、`~/.claude/skills/lit-tag/SKILL.md`、`~/.claude/skills/lit-pool/SKILL.md`。阶段技能同时是定点修复入口。
- 状态只来自文件扫描：`~/.claude/skills/lit-workflow/lit_status.py` 生成/更新 `structure/2_literature/lit_status.md`（方向 × 来源 × {输入篇数, 筛选, review, tag, pool, 备注}）。不靠记忆判断阶段。
- **阻断只用于真实研究风险**（规格 §3.3）：计划方向缺输入、RIS 损坏（TY≠ER）、未确认跳过的 FAILED、pool 后 JUDGE 占位符或键不在 master.bib。文件名不规范、上游比下游新只提醒（⚠️）。
- 不自动 commit / push；不用 `git checkout --`、`git clean` 恢复；删除或覆盖用户文件一律先移入 `_archive/` 或备份目录。

## 参数

| 参数 | 默认 | 含义 |
|---|---|---|
| `status` | — | 只运行状态扫描并汇报，不执行任何阶段 |
| `from` | 自动（`lit_status.md` 的"下一步"） | 从指定阶段开始；该阶段的 `--check` 必须通过 |
| `through` | `pool` | 执行到该阶段为止 |
| `screen` | `ask` | `ask`：输入整理后询问是否筛选及筛哪些方向；`off`：不筛选 |

用户只说"继续 / 跑文献 / 完成文献流程" → `from=自动, through=pool, screen=ask`。

## 步骤 1：状态扫描

```bash
python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root .
```

向用户报告：下一步、阻断、提醒、状态表要点。`status` 模式到此结束。

## 步骤 2：输入整理（每次运行都做，在筛选之前）

1. **命名**：`lit_status.md`「提醒」中列出的不规范文件（如 `5-主题.ris`、`savedrecs.ris`、`cnki_combined.ris`）不会被识别。确认其对应方向后，经用户同意改名为 `direction{N}_{wos|cnki|openalex}.ris`；无法对应的移入 `structure/2_literature/_archive/{YYYY-MM-DD}/`。不删除。
2. **CNKI 转换**：对每个只有 `direction{N}_cnki.enw`、没有 `direction{N}_cnki.ris` 的方向，执行 `lit_status.md`「待执行的 CNKI 转换」中的命令（复用 lit-review 的 `cnki_enw_to_ris.py`），形如：
   ```bash
   python3 ~/.claude/skills/lit-review/cnki_enw_to_ris.py \
     --input structure/2_literature/direction{N}_cnki.enw --output structure/2_literature/direction{N}_cnki.ris
   ```
   如需排除报纸可加 `--skip-newspaper`（先问用户）。`.enw` 比已有 `.ris` 新时（⚠️）：用户同意重转后，先把旧 `.ris` 移入 `_archive/{YYYY-MM-DD}/` 再转换。
3. 重新扫描并检查：
   ```bash
   python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check review
   ```
   退出码 2 = 存在阻断（缺输入、RIS 损坏、未转换）→ 停止，列出缺失方向或坏文件，等待用户补齐。

## 步骤 3：[screen]（可选，用户确认点）

- `screen=off` 或 `from` 晚于 screen → 跳过。
- 否则展示各 (方向, 来源) 的篇数与配额比（备注"建议筛选"= 篇数 > 1.5 × 配额），用 AskUserQuestion 询问：筛哪些方向（可多选）/ 都不筛。**只筛部分方向是正常的**，其余在状态表显示"未筛选"。
- 对选中的方向完整读取 `~/.claude/skills/lit-screen/SKILL.md` 并逐个执行；该技能在用户确认后替换 canonical，并自动写入「筛选记录」。
- `through=screen` → 结束。

## 步骤 4：review

1. `python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check review` 必须 PASS。
2. 完整读取 `~/.claude/skills/lit-review/SKILL.md` 并执行。约定：分派计划 `_review_runs/dispatch_plan.json`（缺失即报错，不降级）；产物 `direction{N}_report.md`（review 后不再改写）与 `screening_summary_report.md`。
3. 入选上限按 `_quota_result.json` 的每方向、每轨配额执行；总预算（`total_budget`，双轨时为 WoS 与 CNKI 两轨之和）只做提醒，不阻断。

## 步骤 5：tag

1. `python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check tag` 必须 PASS（每个计划方向都有 review 报告，或已标 FAILED/SKIPPED）。
2. 完整读取 `~/.claude/skills/lit-tag/SKILL.md` 并执行。约定：分派计划 `_tag_runs/dispatch_plan.json`（与 review 的互不覆盖）；产物 `tagged_reports/direction{N}_report.md`（带标签副本，不改 review 报告）与 `tag_report.md`。

## 步骤 6：pool

1. `python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check pool` 必须 PASS：每个计划方向都有 tag 副本或已确认跳过；**存在未确认跳过的 FAILED 时阻断**。
2. 完整读取 `~/.claude/skills/lit-pool/SKILL.md` 并执行。产物：`citation_pool/{BG,LR,GAP,METHOD,COMP,DISC}.md`、`citation_pool/master.bib`、`literature_manifest.json`、`master_report.md`、`method_landscape.md`（首行含 `<!-- curated -->` 时 lit-pool 不覆盖，改写 `method_landscape_refresh.md`）。
3. 完成判定：
   ```bash
   python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check final
   ```
   阻断：pool 产物缺失、master_report.md 的 JUDGE 占位符 ≠ 0、文献池的键不在 master.bib → 回到 lit-pool 修复。
   池文件 / manifest / master.bib 的完整一致性以 lit-pool SKILL.md 中的 `finalize_pool.py --check-only` 复核为准。

## 子任务失败（review / tag，规格 §3.3）

阶段技能用子 agent 分派方向任务（Claude：Agent 工具；review/tag worker 用 sonnet，worker 定义在 `~/.claude/agents/lit-*-worker.md`，并发 ≤ 8）。某方向失败时：

1. 停止派发新任务 → 等在途任务完成 → 对失败方向重试一次；
2. 仍失败 → 记录并询问：
   ```bash
   python3 ~/.claude/skills/lit-workflow/lit_status.py mark --project-root . --direction N --stage review --state FAILED --note "失败原因"
   ```
   用 AskUserQuestion 请用户选择"修复（重跑该方向）"或"跳过该方向"。
3. 用户确认跳过 → `mark … --state SKIPPED --note "用户确认跳过"`；修复成功 → `mark … --state CLEARED`。
4. 其余方向可以继续本阶段与下一阶段，但 pool 前若仍有 FAILED（未确认跳过），`--check pool` 阻断。

## 续跑规则

- 每个阶段开始前都用对应 `--check` 重新判定，阶段结束后重新扫描（状态表即刷新）。
- `from=X` 只能从 `--check X` 通过的阶段开始；不通过就报告阻断，不越过。
- 状态表中的 ⚠️（上游比下游新，如补充了输入、重筛了某方向）不阻断；向用户说明哪些下游结果可能过期，建议从受影响的最早阶段重跑。
- 连续三次在同一阻断上修复失败 → 停下，向用户说明阻断与已尝试的办法。

## OpenAlex 补充

只能从已核验的 DOI 或 OpenAlex JSON 生成补充语料（OpenAlex 请求一律同时带 `api_key` 与 `mailto`，凭证由脚本从 `~/Library/CloudStorage/Dropbox/Apps/secrets-vault/openalex.env` 读取，不打印）：

```bash
python3 ~/.claude/skills/lit-workflow/openalex_to_ris.py --direction N --doi 10.xxxx/yyyy 10.xxxx/zzzz      # 或 --json works.json
# 文件已存在时：--append（按 DOI 去重追加）或 --replace（旧文件先归档到 _archive/）
```

输出 `structure/2_literature/direction{N}_openalex.ris`（TY/TI/AU/PY/DO/JO/AB，TY = ER 校验）。然后运行 `/lit-workflow from=review`（是否先 screen 由用户决定）。提醒用户：OpenAlex 与 WoS 共用国际文献配额，补充可能挤掉原入选论文。**进入文献池之前不得在正文或表格中引用这些文献。**

## 交付

- **结果**：执行到哪个阶段；`lit_status.md` 的"下一步"。
- **语料**：方向数、各来源输入篇数、筛选情况、review/tag/pool 篇数（来自状态表）。
- **阻断与提醒**：原样列出；FAILED / 跳过的方向单独列出。
- **产物路径**：`structure/2_literature/lit_status.md`、`literature_manifest.json`、`citation_pool/master.bib`、`master_report.md`。
- **建议提交范围**（由用户确认后提交，本技能不 commit）：`structure/2_literature/` 下的 `lit_status.md`、`direction*_*.ris`、`direction*_report.md`、`screening_summary_report.md`、`tagged_reports/`、`tag_report.md`、`citation_pool/`、`literature_manifest.json`、`master_report.md`、`method_landscape.md`；`_screen_runs/`、`_review_runs/`、`_tag_runs/`、`_pool_runs/` 是否入库由用户决定。
