---
name: lit-pool
description: 文献 pool 阶段：从 tagged_reports/ 按唯一论文去重、生成 citation key，派 worker（主模型）写引用场景，组装 citation_pool/{BG,LR,GAP,METHOD,DISC,COMP}.md 与 master.bib，生成并填写 master_report.md、method_landscape.md，最后校验并写出 literature_manifest.json（下游唯一语料表）。通常由 lit-workflow 调用；单独使用时用于池的修复或刷新。
argument-hint: "[--source-pool（学位论文有源项目时）]"
---

# lit-pool — 引用池与语料表

规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md` §3（冲突时以规格为准）。常规入口是 `/lit-workflow`；本技能也是 pool 阶段的定点修复入口。

- 输入：`tagged_reports/`、`tag_report.md`（lit-tag 产物）、canonical RIS（生成 bib 用）、`structure/0_global/idea.md`。不读 review 报告之外的中间文件。
- 产物：`citation_pool/{BG,LR,GAP,METHOD,DISC,COMP}.md`、`citation_pool/master.bib`、`master_report.md`、`method_landscape.md`（或 `method_landscape_refresh.md`）、`literature_manifest.json`（每篇唯一论文一行，最后写出）。
- 运行目录 `_pool_runs/`（`pool_prepare.json`、worker 模板与格式化结果）。
- 不写任何技术章节 md；不自动 commit；被替换的已有产物（池文件、master.bib、master_report.md）自动移入 `_archive/{日期}/`。

下文 `$L` 指 `structure/2_literature`，命令在论文仓库根目录执行。

## 步骤 0：入口检查

```bash
python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check pool
```

退出码非 0 → 停止并报告（典型：某方向 review/tag 为 FAILED 且未经用户确认跳过、某方向缺带标签副本）。被标 SKIPPED（其后无 CLEARED）的方向由各脚本自动排除。学位论文且项目合同声明了源项目时，先运行：

```bash
python3 ~/.claude/skills/lit-pool/source_bib_to_pool.py --source-bib <源项目.bib> --source-tex <源项目 manuscript.tex> \
  --output $L/_pool_runs/source_pool.json --rq-count <n>
```

## 步骤 1：准备

```bash
python3 ~/.claude/skills/lit-pool/pool_prepare.py --lit-dir $L [--source-pool $L/_pool_runs/source_pool.json]
```

- 阻断：缺 `tag_report.md`；`tagged_reports/` 与 review 报告不一一对应或有行不一致（回到 lit-tag 重跑该方向）；非法标签；占位作者；citation key 格式错误或重复。
- 唯一论文口径与 review/tag 相同（DOI / WoS UT / 第一作者+年份+标题前80字符）；重复出现的合并标签、理由与来源方向，保留最高级别。
- citation key：`姓氏小写 + 年份 + 标题首个实词首字母`（中文姓转拼音），冲突追加 b/c…；**已有 `literature_manifest.json` 时，同一篇论文沿用原 key**（刷新语料不会让正文已引用的 key 变化）。
- 写出 `_pool_runs/pool_prepare.json` 与预填模板 `_pool_runs/pool_agent{N}_raw.md`（每个 ≤30 个“标签 × 文献”条目，书目信息已预填）。分配不变时已填模板保留；分配变化时旧模板归档，相同“标签 × key”的引用场景自动沿用。

## 步骤 2：子任务（worker，主模型）

- 先查哪些模板待填：`python3 ~/.claude/skills/lit-pool/format_pool_agents.py --lit-dir $L --check --json`。
- 每个 `EMPTY` / `INVALID` / `MISSING` 模板一个 worker：Agent 工具，`subagent_type: "lit-pool-worker"`（`~/.claude/agents/lit-pool-worker.md`，不指定 model 即继承主模型，只写分配的模板）。滚动并发 ≤ 8，不传 isolation。
- prompt 给：`{RESEARCH_CONTEXT}`（≤800 字，含 RQ、方法、贡献意图）与模板路径。写法规则在 worker 定义中。
- 失败语义：停止派发 → 等在途完成 → 重试一次 → 仍失败则停止本阶段并报告（不合并部分结果）。

## 步骤 3：格式化与组装

```bash
python3 ~/.claude/skills/lit-pool/format_pool_agents.py --lit-dir $L     # 每个条目恰好一次且引用场景非空
python3 ~/.claude/skills/lit-pool/pool_merge.py --lit-dir $L            # 写 6 个池文件
```

六个池文件总是全部生成；COMP 或 METHOD 为空是需要报告的风险，不是错误。

## 步骤 4：master.bib

```bash
python3 ~/.claude/skills/lit-pool/ris2bib.py --lit-dir $L [--extra-bib <源项目.bib>]
```

逐篇匹配 RIS：先用 review 记录的原始记录，再按 DOI，再按年份 + 第一作者；任何候选都必须通过标题高相似度检查。任一篇匹配失败 → 阻断，不写 TODO 占位条目（修 RIS 或回到 review）。

## 步骤 5：master_report.md

```bash
python3 ~/.claude/skills/lit-pool/generate_master_report.py --lit-dir $L --idea-file structure/0_global/idea.md
```

输出 `DATA PASS — JUDGMENT PENDING`。主 agent（不开 worker）逐个填写全部 `<!-- JUDGE … -->`：

- 竞品：依据 COMP 池与 `screening_summary_report.md` 的疑似竞品汇总；COMP = 0 写“当前语料未发现直接竞品”并说明残余检索风险，不得声称不存在竞品。
- Gap：逐条给出 ✅真实 / ⚠️需关注 / ❌已被填补 + 文献支撑（citation key）+ 理由。
- 方法论：核心/重要级 METHOD = 0 时写明方法论证风险与可能的补检。
- 补检建议：只能经 lit-workflow（OpenAlex → `openalex_to_ris.py` → 从 review 重跑）回流，不得把池外文献直接写进池或正文。
- 已存在的 master_report.md 被归档到 `_archive/`；其中仍成立的判断可以搬回。

完成后 `grep -c JUDGE $L/master_report.md` 必须为 0。

## 步骤 6：method_landscape.md

- 若 `$L/method_landscape.md` 首行含 `<!-- curated -->`（idea-refine 或 analysis 人工整理过）：**不覆盖**，把本次文献视角写到 `$L/method_landscape_refresh.md`。
- 否则写（或重写）`$L/method_landscape.md`。主 agent 综合 `citation_pool/METHOD.md`、idea.md 的方法部分与相关方向的带标签报告，结构：
  1. 建模策略综述；2. 变量选取共性与差异；3. 数据与样本通行做法；4. 方法创新空间（结合本研究情境）；5. 与本研究方法设计的逐条对照。
  每节引用具体 citation key；中文 1000–2000 字；CNKI 文献注明“（国内学者）”。

## 步骤 7：收尾校验，写出语料表

```bash
python3 ~/.claude/skills/lit-pool/finalize_pool.py --lit-dir $L
```

阻断：master_report.md 缺失或仍有 JUDGE；池内键不在 master.bib；6 个池文件的键与准备好的语料不一致（语料表的行必须等于池内唯一键集合）。提醒：method_landscape 缺失；准备之后 tagged_reports 又有变化（应从步骤 1 重跑）。通过后写出 `literature_manifest.json`（citation_key、书目、tier、tags、pools、directions、reasons、source_origin、溯源记录；不含哈希）。

下游只读复验（build-intro-lit-table 等）：`python3 ~/.claude/skills/lit-pool/finalize_pool.py --lit-dir $L --check-only`。

## 步骤 8：汇报与清理

- 汇报：唯一论文数与分级、各池条目数、COMP/METHOD 风险、master_report 结论要点、method_landscape 写到哪个文件。运行 `python3 ~/.claude/skills/lit-workflow/lit_status.py --project-root . --check final`。
- 下一步：`/idea-refine`（审 idea 与方法方向）；Introduction 文献表见 `/build-intro-lit-table`。
- 清理（可选，须用户确认）：只处理运行目录 `_review_runs/`、`_tag_runs/`、`_pool_runs/`，确认后移入 `$L/_archive/{日期}/`。**永不处理** `_quota_result.json`、`lit_status.md`、`_screen_runs/`（筛选备份）、任何 `direction*` 文件、`tagged_reports/`、报告与池文件。禁止 `rm _*.json` 一类通配删除。清理后 `finalize_pool.py` 只能用 `--check-only`。
- 建议提交范围（用户确认后提交）：`$L/citation_pool/`、`$L/literature_manifest.json`、`$L/master_report.md`、`$L/method_landscape*.md`。

## 阻断与提醒

| 情形 | 处理 |
|---|---|
| 存在未确认跳过的 FAILED 方向；缺带标签副本 | 阻断（步骤 0） |
| 带标签副本与 review 报告不一致；非法标签；key 冲突/格式错误 | 阻断（步骤 1） |
| worker 重试后仍失败 | 停止，报告 |
| RIS 匹配失败（会产生 TODO 条目） | 阻断（步骤 4） |
| JUDGE ≠ 0；池内键不在 master.bib；语料表与池键不一致 | 阻断（步骤 7） |
| COMP/METHOD 为空、达标率低、上游比下游新 | 提醒 |
