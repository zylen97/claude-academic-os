# FUND PROTOCOL — 纵向项目申报协议

> 所有 fund-* skill（/fund-mine、/fund-init、/fund-outline、/fund-draft、/fund-polish、/fund-result、/fund-hub）的唯一规格。skill 正文与本文件冲突时，以本文件为准。
> 原则同 Academic OS Lite：骨架统一，机器砍掉。数据都是 Markdown，唯一的脚本是台账生成器。

根目录：`FUNDINGS=/Users/zylen/Library/CloudStorage/Dropbox/02-Research/fundings`

## 1. 目录与命名

```
fundings/
├── PORTFOLIO.md        生成文件，不手改
├── _profiles/          基金档案，每种基金一页（{基金简称}.md）
├── _assets/{代码}/     申请人素材库：成果清单.md、申请人信息卡.md、代表作/、简历/、证书/、刊物封面/
├── _library/           参考库：他人课题/ 与 README.md 索引
├── _scripts/build_portfolio.py
├── _drafts/            /fund-mine 产出的 fund-idea_{YYYYMMDD}_{代码}_{slug}.md
└── {年度}_{代码}_{基金简称}/   项目文件夹
```

- 项目文件夹：`{年度}_{申请人代码}_{基金简称}`，如 `2026_zy_NSFC青年`、`2027_xy_浙江教科规划`。
  - 年度 = 基金自己标的年度（浙江 2027 年度课题在 2026 年 10 月申报，年度写 2027）。
  - 基金简称 = `_profiles/` 里的档案文件名（不含 `.md`）。
  - 文件夹名**不写结果**，中没中只记在 FUND.md。
- 以 `_` 开头的目录是公共目录，不是项目。
- 同一申请人同年度同基金申两项（极少见）时，在简称后加 `_2`。

## 2. 申请人登记

| 代码 | 姓名 | 关系 | 研究项目目录（/fund-mine 挖选题用） |
|---|---|---|---|
| zy | 王子伦 | 本人 | `02-Research/papers`（zy 编号）、`02-Research/_GYM group dropbox/_gym paper` |
| xy | 张晓妍 | 协助（工商管理方向） | 待填 |

新增申请人：在这张表加一行，建 `_assets/{代码}/`（复制 xy 的空模板），再建项目。

**硬规则**：写谁的本子，研究基础、前期成果、代表作只读 `_assets/{申请人代码}/`。两人的成果不得混用；合作成果按实际署名位次写。一个申请人的选题、正文不得挪给另一个申请人用（"相同或相近内容不得以不同申请人名义申报"）。

## 3. 项目卡片 FUND.md

每个项目根目录一份，是**项目阶段与结果的唯一记录**（项目 CLAUDE.md 不再写阶段）。格式为 `- 字段：值`，字段按下列顺序：

| 字段 | 取值 |
|---|---|
| 年度 | 四位年份 |
| 基金 | 全称（含类别，如"一般课题"） |
| 档案 | `_profiles/` 里的文件名，如 `NSFC青年.md` |
| 题目 | 申报题目；未定写"待填" |
| 申请人 | `代码（姓名）`，如 `zy（王子伦）` |
| 角色 | 从 zy 的角度：申请人 / 协助 / 项目组成员 |
| 项目组成员 | 姓名，逗号分隔；台账用它统计成员参与限额 |
| 阶段 | 见第 4 节 |
| 结果 | 立项 / 未中 / — |
| 提交日期 | `YYYY-MM-DD`；未提交时写"截止 YYYY-MM-DD" |
| 结果日期 | `YYYY-MM-DD` |
| 经费 | 申请或批准金额 |
| 正文正本 | 项目内相对路径 |
| 提交版 | 项目内相对路径（一般为 `submitted/`） |
| 前序申请 | 重申时填上一轮的项目文件夹名，否则"无" |
| 后续申请 | 被重申时填下一轮的项目文件夹名，否则"无" |
| 源论文 | 支撑本项目的论文或研究项目 |
| 评审意见 | 摘要一句；全文放 `reviews/评审意见_{年度}.md` |

卡片末尾的 `## 复盘` 写自由文本（中没中的原因、下次怎么改）。

未知值写"待填"，推断值加"（待核）"。台账会把这两种列进"待补信息"。

**改了任何 FUND.md 后，运行一次** `python3 "$FUNDINGS/_scripts/build_portfolio.py"`。

## 4. 阶段

| 阶段 | 含义 | 写入方 |
|---|---|---|
| `init` | 已建项目骨架 | /fund-init |
| `literature` | 在做文献（可选） | /fund-init（用户选择先做文献时） |
| `outlining` | 写大纲 | /fund-outline 入场 |
| `drafting` | 写正文 | /fund-draft 入场 |
| `polishing` | 润色、自检、生成交付稿 | /fund-polish 入场 |
| `submitted` | 已提交，提交版已冻结 | /fund-result submit |
| `awarded` / `rejected` | 已出结果 | /fund-result result |
| `未申报` | 建了项目但没交 | /fund-result abandon |

每个阶段只由表中的写入方修改。写作阶段（init → polishing）前进不跳步，回改随时允许（如 polishing 中回去改 drafting 的章节，阶段不回退）。`submitted` 和 `未申报` 记录的是事实，/fund-result 可以从任何未提交的阶段登记。

## 5. 项目内部结构

```
{项目}/
├── FUND.md               卡片
├── CLAUDE.md             项目说明：交付类型、合规要点、源项目、章节规划（含状态）、写作注意
├── fund-idea.md          选题方案
├── structure/0_global/idea.md   fund-idea.md 的副本，供 /lit-plan 读取
├── structure/2_literature/      /lit-* 工作目录
├── structure/figures_tables/    /figure、/latex-table 输出
├── sections/{NN}_{章节名}.md    正文写作稿；{NN}_{章节名}_outline.md 为大纲；synthesis_summary.md
├── deliverables/         /fund-polish 生成的交付稿（Word、填报稿、main.tex 的 PDF）
├── submitted/            /fund-result 冻结的提交版，提交后不再改
├── reviews/              真实评审意见、重申修改清单、提交前自检报告
├── reference/            官方模板、往年版本等参考
├── {slug}.bib            参考文献
└── main.tex              仅交付类型为 latex 时存在
```

官方文件（通知、模板）可以留在项目根目录，skill 不移动、不覆盖它们。

### CLAUDE.md 的章节规划表

```
| 章节 | 文件 | 角色 | 字数上限 | 状态 |
```

- 章节和顺序来自基金档案的"正文结构"，由 /fund-init 与用户确认后写入。
- **角色**决定 /fund-outline 和 /fund-draft 用哪套写法，取值：
  `立项依据`（意义、现状、述评）／`目标内容`（目标、内容、关键问题、重点难点）／`研究方案`（思路、方法、技术路线）／`创新点`／`可行性`／`研究基础`（前期成果、条件、简历）／`预期成果`（成果形式、去向、考核指标）／`进度安排`／`表格`（经费、基本信息等填表项，不写大纲）
  一个章节可以有多个角色，用"+"连接，如 `目标内容+创新点`。
- **状态**：待写 → 大纲 → 初稿 → 定稿。/fund-outline 写"大纲"，/fund-draft 写"初稿"，/fund-polish 写"定稿"。不再使用 `sections/progress.md`。

## 6. 基金档案 `_profiles/{基金简称}.md`

每份档案必须有：

- 头部字段：级别、**交付类型**、交付格式、匿名要求、申报窗口
- `## 正文结构`（或"活页结构""申报书结构"）：章节、每节字数或页数限制
- `## 合规与限项`
- `## 评审要点`
- `## 来源文件`

**交付类型**只取以下值，决定 /fund-polish 生成什么交付稿：

| 交付类型 | 含义 | /fund-polish 产出 |
|---|---|---|
| `latex` | 正文可自行排版成 PDF（如 NSFC 正文） | 灌入 main.tex 并编译 |
| `word` | 交官方 Word 模板 | `deliverables/` 里的 docx 正文稿 + 回填清单；项目里有回填脚本时用脚本 |
| `word-macro` | 带宏的官方 .doc，只能在 Windows Word 里填（如教育部） | 按栏目拆好的纯文本填报稿 + 操作提醒 |
| `system` | 在申报系统里逐栏填写（如浙江教科规划） | 按系统栏目的填报稿，逐栏标字数和上限 |

可以写多个，如 `latex | word`，由 /fund-init 和用户确认后写进项目 CLAUDE.md。

标"待核"的内容用前提醒用户以当年通知为准。拿到新年度通知时，由 /fund-hub profile 更新档案。

## 7. 合规硬检查（/fund-polish 提交前必做，/fund-hub check 随时可做）

1. **匿名**：档案要求匿名的部分，不得出现申请人姓名、单位、学校、所在地区，也不得出现能指向申请人的团队成员姓名。比对来源：`_assets/{代码}/申请人信息卡.md` 的姓名、单位、通讯地址。档案规定了替代写法（如"××"）的按档案写。
2. **限项**：按档案"合规与限项"逐条核对，重点是同年度申请人限报项数、在研项目冲突、成员参与上限。
3. **跨申请人**：读 PORTFOLIO.md 的"跨申请人检查"；题目相近要向用户报告，由用户决定。
4. **成果归属**：研究基础里的每一项成果都要能在该申请人的 `成果清单.md` 找到。

## 8. 评审意见

- NSFC 等会返回专家评审意见的基金，结果出来后由 /fund-result 存进 `reviews/评审意见_{年度}.md`，这是最有价值的数据。
- 重申时 /fund-init 把上一轮评审意见整理成 `reviews/重申修改清单.md`（每条意见对应一条修改动作）。
- 不存在独立的模拟评审 skill。提交前的评审视角自检在 /fund-polish 里做，口径为档案"评审要点"加上往年真实评审意见。
