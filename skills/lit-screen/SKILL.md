---
name: lit-screen
description: 对一个或多个方向的语料 RIS（direction{N}_wos|cnki|openalex.ris）做可选预筛选：XR2026 新锐分区过滤（免费）+ LLM 相关性筛选（付费，需确认）；结果先写入 _screen_runs/，用户确认后才替换 canonical 文件（原文件备份到 _screen_runs/original/），并记录到 lit_status.md。通常由 lit-workflow 调用，也可单独用于定点筛选。
argument-hint: "[方向编号…|all]"
---

# lit-screen — 文献预筛选

规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md` §3。位于 `lit-plan → lit-workflow【输入整理 → [screen] → review → tag → pool】` 中的 screen 阶段。只做预筛选，不做综述、标签或引用池。

**允许只筛部分方向**：未筛选的方向在 `lit_status.md` 显示"未筛选"，属于正常状态。

## 不可违反的规则

- 输入只能是 `structure/2_literature/` 顶层的 canonical 文件（`lit_common.classify_ris` 识别：`direction{N}_{wos|cnki|openalex}.ris`）；CNKI 的 `.enw` 须先由 lit-workflow 转换。
- 所有中间结果只写 `structure/2_literature/_screen_runs/<运行目录>/`，顶层不出现任何 `_zone`/`_llm` 文件。
- **替换 canonical 必须在用户确认 dry-run 计划之后**，且只用 `finalize_screen.py --execute` 完成；不用 `rm`/`mv` 手工收尾。
- 替换前校验：最终 RIS 的 TY = ER > 0；它的每条记录块按原顺序出现在 canonical 中（有序子集，续行原样保留）；LLM 审计与结果逐条一致；运行结果对应的是 canonical 的当前内容。
- 原文件备份到 `_screen_runs/original/<文件名>`；若该处已有更早的原始备份，则当前文件备份为 `<运行目录>/before_<文件名>`。任何备份都不覆盖。
- API key 只从环境变量 `CHATANYWHERE_API_KEY` 读取：不 `echo`、不写进命令行参数（脚本拒绝 `--api-key`）、不开 shell xtrace。
- LLM 有费用：执行前必须确认。API 错误、解析异常一律默认保留。

脚本目录：`~/.claude/skills/lit-screen/`（`screen_xr.py`、`screen_llm.py`、`finalize_screen.py`）。

## Step 0：确定范围

1. 读 `structure/2_literature/literature_search_plan.md` 方向表与 `_quota_result.json`；运行状态脚本查看各方向篇数与配额比：
   ```bash
   python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --no-write
   ```
2. 由参数或用户选择要筛选的 (方向, 来源)。备注列出现"建议筛选"（篇数 > 1.5 × 该来源配额）时一并说明。
3. 每个方向的方向描述 `DIRECTION_TEXT` 取自方向表名称 + 该方向"论文角色"，不得猜测。信息不足时用 AskUserQuestion 询问。

以下 Step 1–5 对每个选中的 canonical 文件**逐个**执行。

## Step 1：XR2026 分区（只读 canonical）

```bash
python3 ~/.claude/skills/lit-screen/screen_xr.py structure/2_literature/direction{N}_{source}.ris --zone 2
```

从 stdout JSON 读取 `run_dir`、`output_path`（`xr_zone2.ris`）、`csv_path`，不要按文件名猜。向用户报告：

| 分区 | 1 区 | 2 区 | 3 区 | 4 区 | 未匹配 | 合计 |
|---|---|---|---|---|---|---|

保留 1–2 区 + 未匹配 → X 篇；过滤 3–4 区 → Y 篇。ISSN/刊名未匹配（新刊、会议、中文刊）默认保留。`output_path` 为 null 表示全部被过滤，此时不能应用分区。

## Step 2：一次性确认筛选选择（用户确认点）

用 AskUserQuestion 一次问清：
- 分区：应用（保留 1–2 区与未匹配）/ 跳过；
- LLM：执行 / 跳过（估算：gpt-4o-mini 约每 1000 篇 0.075 美元，以实际计费为准）。

| 分区 | LLM | LLM 输入 | FINAL_RIS | mode |
|---|---|---|---|---|
| 应用 | 执行 | Step 1 的 `output_path` | LLM 的 `output_path`（`llm.ris`） | `zone+llm` |
| 跳过 | 执行 | canonical | LLM 的 `output_path` | `llm` |
| 应用 | 跳过 | — | Step 1 的 `output_path` | `zone` |
| 跳过 | 跳过 | — | — | 不筛选：canonical 保持不变，结束（状态表显示"未筛选"） |

## Step 3：LLM 相关性（仅在已确认时）

在同一条命令中加载密钥文件并运行，只检查变量非空，不输出值：

```bash
set +x
source "$HOME/Library/CloudStorage/Dropbox/Apps/secrets-vault/email-config.sh"
test -n "${CHATANYWHERE_API_KEY:-}" || { echo "CHATANYWHERE_API_KEY 未配置" >&2; exit 1; }
python3 ~/.claude/skills/lit-screen/screen_llm.py "<LLM 输入>" --direction "<DIRECTION_TEXT>" --threads 20
```

输入是 Step 1 的 `xr_zone2.ris` 时自动沿用同一运行目录；输入是 canonical 时新建运行目录。stdout JSON 给出 `run_dir`、`output_path`、`excluded_output`、`audit_output`（`decisions.jsonl`）与各类计数。

### 必做抽检（发布前）
1. `retain + exclude + error_retain = input`，`decisions.jsonl` 每条输入一行。
2. 抽查至少 10 条：优先 5 条 exclude、3 条 retain、全部 error_retain（多于 2 条则抽 2 条），不足用其他类别补足；对照标题、摘要和理由，确认续行摘要完整。
3. 发现系统性误判、缺行、摘要截断或计数不一致 → 不发布，修正后重跑；不得手改最终 RIS。一个运行目录只容纳一次 LLM 结果：`zone+llm` 分支从 Step 1 重跑（XR 免费，得到新运行目录），`llm` 分支直接重跑 Step 3（自动新建运行目录）。
4. 向用户报告抽检结论与前 10 条被排除标题。错误率异常（如 > 10%）时先暂停，询问是否重跑。

## Step 4：dry-run 替换计划

```bash
python3 ~/.claude/skills/lit-screen/finalize_screen.py \
  --canonical structure/2_literature/direction{N}_{source}.ris \
  --final-ris "<FINAL_RIS>" --run-dir "<run_dir>" --mode <zone|llm|zone+llm> --dry-run
```

向用户完整展示：canonical、替换前后篇数、有序子集校验、XR/LLM 运行校验、备份位置、写入筛选记录的方法说明（`method`）。

## Step 5：确认后执行（用户确认点）

用户明确同意上一步的具体计划后，把 `--dry-run` 换成 `--execute`，其余参数逐字不变。脚本依次：备份原文件 → 原子替换 canonical → 复核篇数 → 在 `lit_status.md`「筛选记录」追加一行并刷新状态表。

若输出含 `warning`（状态记录失败），canonical 已替换成功；按提示中的 `lit_status.py record-screen …` 命令补记即可。

任何校验失败：canonical 不变，`_screen_runs/` 中的结果保留供排查；修正后重跑相应步骤。

## 结束汇报

```
D{N}/{source}：原始 X 篇 → [XR≤2区] Y 篇 → [LLM] Z 篇（已替换 canonical）
原文件备份：structure/2_literature/_screen_runs/original/direction{N}_{source}.ris
运行目录：structure/2_literature/_screen_runs/<run>/
```

- 未筛选的方向保持"未筛选"，可直接进入 review。
- 若由 lit-workflow 调用，回到 lit-workflow 继续；单独调用时建议接着运行 `/lit-workflow from=review`。
- 不自动 commit。建议提交范围：`structure/2_literature/direction{N}_{source}.ris`、`lit_status.md`；`_screen_runs/` 是否入库由用户决定（体积可能较大）。
