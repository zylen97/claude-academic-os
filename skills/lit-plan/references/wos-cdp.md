# WoS CDP 自动检索与导出

## 使用边界

`lit-plan` 默认运行本流程；只有用户显式指定 `--plan-only` 时跳过。运行前仍须展示 web-access 的账号风险提示并获得接受。使用用户现有 Chrome 登录态，新建后台标签页，不操作或关闭用户原有标签页。

运行前执行：

```bash
node ~/.claude/skills/web-access/scripts/check-deps.mjs
```

## 脚本入口

脚本从标准输入读取一条 WoS 高级检索式：

```bash
node ~/.claude/skills/lit-plan/wos_cdp_export.mjs \
  --mode count <<'WOS_QUERY'
TS=(...)
WOS_QUERY
```

最终导出：

```bash
node ~/.claude/skills/lit-plan/wos_cdp_export.mjs \
  --mode export \
  --output structure/2_literature/direction5_wos.ris \
  --limit 1000 <<'WOS_QUERY'
TS=(...)
WOS_QUERY
```

抽样校准时把 `--limit` 设为 20–50，并将输出放在 `/tmp/lit-plan-{project}/D{id}-v{round}-probe.ris`。每个抽样文件同样必须有明确名称。

## 固定操作规则

脚本按以下顺序执行：

1. 进入 WoS Core Collection 高级检索。
2. 执行 Query Builder 检索式。
3. 展开 `Web of Science Index`，只勾选 SCIE 与 SSCI；某索引为零而不显示时记录为 absent。
4. 应用筛选后的数量才是 `actual_hits`。
5. 设置 `Usage (last 180 days): most first`。
6. 选择 `RIS (other reference software)`。
7. 必须选择 `Records from 1 to N`；禁止保留默认的 `All records on page`，后者通常只导出当前页 50 条。
8. 选择 `Full Record`。
9. 等待下载完成并稳定，核验 `TY`、`ER` 数量。
10. 立即移动并重命名到 `--output`；完成后不遗留新的 `savedrecs*.ris`。

## 命名与覆盖安全

- Corpus direction 最终文件固定为 `structure/2_literature/direction{N}_wos.ris`（规格 §3.2；方向名只写在 `literature_search_plan.md` 方向表）。
- 串行导出；禁止并行触发多个 WoS 下载，否则无法可靠绑定下载文件与方向。
- 目标文件已存在时硬停止，禁止静默覆盖、自动追加 `(1)` 或产生第二个同义文件。
- 下载数量不符时，脚本把下载文件改名为 `direction{N}_wos.FAILED-x-of-y.ris` 并报错（该名不会被识别为语料输入），不遗留模糊的 `savedrecs*.ris`。
- 成功标准：输出文件存在且非空，`TY = ER = min(actual_hits, limit, 1000)`。

## 页面变化

WoS 是动态站点，选择器可能变化。脚本失败时先检查页面文字、元素语义和当前 URL；不要在同一失效选择器上反复重试。若页面结构变化，更新脚本并重新做真实小样本测试。
