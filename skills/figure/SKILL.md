---
name: figure
description: Create, redesign, or audit academic figures with method-aware and benchmark-first visual design using TikZ, Python, or R; enforce journal sizing, strict alignment, final-size readability, and cross-figure semantic consistency.
---

# Figure — 学术论文图表全流程

一个入口覆盖所有论文绘图需求：自动判断工具选择、创建新图、美化已有图、跨图一致性检查。整合 Eagle 素材库作为风格参考源。

**输入** `$ARGUMENTS`：格式灵活，示例：
- `/figure` — 交互式选择操作
- `/figure 画一个博弈结构图` — 自动判断 TikZ，进入创建流
- `/figure beautify fig3` — 美化已有的 fig3
- `/figure audit` — 跨图一致性检查
- `/figure eagle 博弈论` — 搜索 Eagle 图库

---

## 设计立场：方法、benchmark 与期刊约束优先

图的专业性首先来自**方法语义正确、视觉语法匹配、严格对齐和最终尺寸可读**，不是来自某套固定色板。执行优先级固定为：

1. 论文中的研究问题、方法和真实数据关系；
2. 相同方法、相同图件功能的 benchmark 论文；
3. 目标期刊的官方尺寸、字体、线宽和可访问性要求；
4. 项目内其他图的跨图一致性；
5. 默认视觉 profile。

新建或重画图时必须读取 `references/method-benchmark-design.md`。TikZ 结构图还必须读取 `references/tikz-semantic-minimal.md`，默认从 `assets/tikz_semantic_minimal.tex` 开始。

### 默认 profile

- **TikZ 结构图、流程图、机制图**：默认 `semantic-minimal`。白底；框、主流程箭头、分区带等结构元素一律灰；颜色只编码已声明的语义类别，最多三组语义色对（浅填 + 深边，token 见 `references/tikz-semantic-minimal.md` 第 2 节），用了就必须有图例或直接标注；可选 / 辅助对象用灰色虚线框；反馈 / 回流用橙色虚线。母版是 zy02 的信息结构图。
- **Python/R 数据图**：沿用同一组 token——中性基线用灰，需要区分的类别依次用 A 蓝、B 橙、C 绿（深色 D 画线 / 点，浅色 F 作填充或置信带）；颜色映射到变量语义并在全篇保持一致。类别超过三个时，先考虑分面、直接标注或线型，不扩色。禁止软件默认色板。
- **journal-minimal-monochrome**：期刊要求黑白或用户指定时使用，见 `references/tikz-journal-minimal.md`。
- **legacy-morandi**：仅当用户明确指定 Morandi，或既有项目已经锁定该视觉语言时使用，见 `references/legacy-morandi.md`。

### 图标题与图注（所有创建、修改和审计路线）

- 图片必须使用简短、描述性的标题，优先采用一个名词短语；英文通常以 3–10 个词为目标，准确性优先，不为凑字数删去必要对象。
- `\caption{}` 只放短标题，不将面板逐项说明、参数设定、方法解释或结果讨论写成标题段落。
- 必须保留的面板说明、符号、单位、情景条件或来源另放图下 Notes；只写读图必需的信息，结果解释放正文。不得因缩短标题而丢失必要信息。
- 图内通常不再重复整图标题；需要面板标题时同样使用短语。具体期刊有明确不同要求时按期刊要求处理。
- 完成时核对正文 caption 与图表注册表标题一致；审计同时检查标题是否简短、解释是否归位。

### 核心禁令

- 不得先选颜色再决定图的结构。
- 颜色只能编码已声明的语义：一种颜色全图只表达一种含义，最多三组；不得为分层、分阶段、分时期或"好看"上色，结构元素一律灰。
- 不得随意混用实线框和虚线框：实线框表示参与主流程的对象；灰色虚线框只表示可选 / 辅助对象；虚线分组框只表示重复或条件性阶段（须在组标题写明）。项目另有语义时必须在设计摘要中声明。
- 不得让同一种虚线同时表示分组、复制、滞后和反馈；每种线型必须保持单一语义，并优先直接标注。
- 不得为了“像 benchmark”复制其装饰；只借鉴与方法和读者任务相匹配的布局、视觉语法和信息层级。
- 不得用箭头暗示未被模型估计的因果、反馈或共同演化关系。
- 不得把不同数据对象画成“多层网络”，除非层间边有明确的数据或模型含义。
- 不得用大面积彩色填充、渐变、阴影、3D、装饰性图标或重复图例制造复杂感。
- 不得在未检查最终印刷尺寸、灰度和嵌入正文效果前宣称完成。

---

## 步骤 0：上下文加载 + 路由判断

### 0.1 读取项目配置 + 项目类型探测（决定 `{FIGURES_DIR}`）

- 读取 `CLAUDE.md` → 提取 `{PUBLISHER}`、`{TARGET_JOURNAL}`、`{METHOD_TYPE}`、`{PAPER_TITLE}`
- **项目类型探测**（决定图目录 `{FIGURES_DIR}`）：
  - IF `$PWD` 包含 `dissertations/` → `{FIGURES_DIR}=structure/figures_tables/figures/`（学位论文也用同一结构，但主 tex 位置不同，见下）
  - IF `structure/figures_tables/figures/` 存在 → `{FIGURES_DIR}=structure/figures_tables/figures/`（`/finalize` 前的小论文）
  - IF `figures/` 在项目根目录存在 且 `structure/` 不存在 → `{FIGURES_DIR}=figures/`（`/finalize` 后的小论文，脚手架已清理）
  - 其他（新项目）→ 默认 `{FIGURES_DIR}=structure/figures_tables/figures/`
- **LaTeX 路径契约**：建议主 tex 文件 preamble 添加 `\graphicspath{{structure/figures_tables/figures/}{figures_tables/figures/}{figures/}}`（paper-init 的 manuscript.tex.tmpl 应含此行），这样 `\includegraphics{fig1_foo.pdf}` 使用纯文件名即可，不受 `/finalize` 前后目录迁移影响。
- 扫描 `{FIGURES_DIR}` 目录 → 列出已有图文件 → `{FIGURE_INVENTORY}`
- 读取主 tex 文件 → 找所有 `\includegraphics` 和 `\input{fig*}` → 了解图在论文中的位置

### 0.1.1 方法与 benchmark 证据门（创建和重大重画时强制）

在讨论颜色和盒子前，先完成一页以内的设计证据摘要：

1. **Figure role**：该图在论文中承担 overview、method mechanism、data construction、identification、results、robustness 或其他什么任务？
2. **Method semantics**：哪些对象、方向、时间顺序、层级和不对称关系必须被准确画出？哪些连线会构成方法论误读？
3. **Reader task**：读者看图后必须能回答哪一个问题？
4. **Benchmark set**：优先读取项目 `structure/**/benchmark/`、参考论文 PDF 和已提取图片；不足时用 `figure-harvest` 或 `web-access` 获取 2--5 张相同方法且相同图件功能的参考图。
5. **Visual grammar extraction**：记录 benchmark 的布局骨架、阅读方向、面板层级、对齐方式、节点/边语义、标签密度、图例策略和正文配合，而不只记录颜色。
6. **Borrow / reject**：明确借鉴什么、拒绝什么，以及拒绝原因。

若没有足够 benchmark，使用 `semantic-minimal` 保守设计，并明确这是默认推断。详细模板和常见方法映射见 `references/method-benchmark-design.md`。

### 0.2 解析 `$ARGUMENTS`

从 `$ARGUMENTS` 中识别操作类型：

| 关键词/模式 | 路由 |
|:-----------|:-----|
| `beautify` / `美化` / `polish` + 图编号 | Route B（美化流） |
| `audit` / `检查` / `一致性` | Route D（审计） |
| `eagle` + 标签 | Eagle 搜索（独立功能） |
| 含"框架""流程""概念""结构""关系""博弈树""决策树""时序" | Route A（TikZ 创建） |
| 含"分布""回归""系数""热力图""网络图""散点""柱状""折线""数据" | Route C（Python/R 创建） |
| 空 / 无法判断 | 交互询问 |

**无法判断时** → AskUserQuestion：
```
你要做什么？
(1) 创建新图 — 概念图/框架图/流程图/博弈树（TikZ）
(2) 创建新图 — 数据图/统计图/网络图（Python/R）
(3) 美化已有的数据图
(4) 跨图一致性检查
(5) 搜索 Eagle 图库找参考
```

### 0.3 自动判断 TikZ vs Python/R（仅 create 场景）

**核心原则：有没有真实数据驱动？**

```
图的内容由数据决定？（坐标、大小、颜色由数值映射）
├─ 是 → Python/R（Route C）
│   示例：度分布、回归系数图、热力图、网络力导向图、弦图、散点图
└─ 否（每个元素的位置由作者手动设计）→ TikZ（Route A）
    示例：研究框架图、理论模型图、博弈时序图、流程图、概念关系图
```

判断结果展示给用户确认：
```
🔍 判断结果：这张图适合用 {TikZ / Python / R}
理由：{一句话}

确认？或指定其他工具。
```

### 0.4 确定图编号

- 扫描 `{FIGURES_DIR}` 中已有的 `fig{N}_*` 文件
- 下一个可用编号 = max(N) + 1
- 用户指定的编号优先
- 文件命名规范：`fig{N}_{description}.{tex|py|R}`（description 为 snake_case 英文，≤30 字符）

---

## 步骤 1：Benchmark 优先，Eagle 补充（Routes A/B/C 共享）

学术 benchmark 是首要参考：先找相同方法和相同图件功能，再看相邻领域的顶刊图。Eagle 仅用于补充构图和视觉细节，不能替代方法 benchmark。也可通过 `/figure eagle {标签}` 独立运行。

### 1.1 询问参考来源

AskUserQuestion：
```
参考来源：
(1) 项目 benchmark / 论文 PDF（默认）
(2) 从 Eagle 图库补充搜索
(3) 我直接提供参考图
(4) 暂无参考，使用 semantic-minimal 保守设计
```

只有用户选 (4) 且本地也无可用 benchmark 时，才跳过参考提取。

### 1.2 Eagle 标签搜索

```bash
python3 ~/.claude/skills/shared/eagle_search.py search --tags "{用户输入的标签}"
```

VERIFY: PASS → 继续。FAIL → 展示可用标签列表，让用户换标签重试或跳过。

### 1.3 展示搜索结果

```
🔍 Eagle 搜索结果（标签: "{tags}"）— 共 {N} 张

[1] {name}
    标签: {tags}
    来源: {annotation}
    尺寸: {width}×{height}

[2] ...

选择参考图（输入编号，可多选如 "1,3"），或 "skip" 跳过
```

### 1.4 读取并分析参考图

对用户选中的每张参考图：
1. 用 Read 工具查看图片（多模态视觉分析）
2. 从 Eagle metadata 提取 `palettes`（自动色板）
3. 记录视觉分析结果：
   - `{REF_LAYOUT}`：整体布局模式（网格/流程/层级/对称...）
   - `{REF_STYLE}`：视觉风格（线条粗细、框形状、间距、标注方式）
   - `{REF_PALETTE}`：色板信息

这些信息传递给后续的创建/美化步骤。

---

## Route A：TikZ 概念图创建

### 2A.1 收集图内容规格

AskUserQuestion（如 `$ARGUMENTS` 未提供足够信息）：
```
描述你要画的概念图：
- 图的目的/标题
- 包含哪些元素（概念、变量、参与者...）
- 元素之间的关系（因果、流程、层级、对比...）
- 特殊要求（子图、注释、数学符号...）
```

同时读取项目上下文：
- `structure/0_global/idea.md` → 研究框架理解
- 项目合同 `CLAUDE.md` 的 `## 技术章节` 中角色为 method 的 manuscript 章节；analytical-model 项目另读 `structure/3_analysis/derivation/` 中的模型设定文件 → 模型结构（如果画模型图）
- `manuscript.tex` 目标章节 → 图前后正文
- `structure/**/benchmark/` 与 benchmark 论文图片 → 提取相同方法、相同图件功能的视觉语法
- 目标章节正文与图注上下文 → 确认该图前后文字分别承担什么解释
- 已有 `fig*.tex` → 风格一致性参考

### 2A.2 提议设计方案

用中文文字描述布局方案（**不写代码**）：

```
📐 Fig {N} 设计方案: {title}

布局: {描述整体结构，如"左右两列，左列为外部环境，右列为资源-策略映射"}

元素关系示意:
┌─────────┐    ──→    ┌─────────┐
│  元素 A  │          │  元素 B  │
└─────────┘    ←──    └─────────┘
       ↓
  ┌──────────┐
  │  元素 C   │
  └──────────┘

方法语义:
- 必须可见: {对象、时间、层级、方向、不对称关系}
- 禁止暗示: {未估计的因果、反馈、多层关系或阶段}

Benchmark 证据:
- 参考图: {论文 + figure 编号}
- 借鉴: {布局、视觉语法、信息层级、对齐方式}
- 不照搬: {装饰或不适用于本文方法的元素}

布局与对齐契约:
- 目标成稿宽度: {mm / 单栏 / 双栏}
- 固定列 x: {...}
- 固定行 y: {...}
- 主阅读路径: {...}

视觉 profile:
- 默认 semantic-minimal: 白底 + 灰色结构 + ≤3 组语义色
- 语义色分配: A 蓝 = {...}；B 橙 = {读者必须看到的关键语义}；C 绿 = {...}（不用的删掉）
- 虚线框语义: {可选 / 辅助；或重复阶段}
- 连线语义: 灰实线 = 主流程；同色实线 = {语义流}；橙虚线 = {反馈 / 回流}
- 图例: {图底一行 / 直接标注}

确认方案？可以调整布局、元素、配色。
```

**循环**：用户不满意 → 修改方案 → 再次展示 → 直到用户确认。

### 2A.3 生成 standalone .tex

按照已确认的 method/benchmark 设计摘要生成代码。项目既有风格只有在不损害方法语义、最终尺寸可读性和专业性时才继承；旧图风格存在缺陷时不得机械复制。

**强制规范**：
- `\documentclass[tikz, border=6pt]{standalone}`，从 `assets/tikz_semantic_minimal.tex` 起步。
- 字体：英文图 `\usepackage{newtxtext,newtxmath}`（pdflatex）；中文图首行 `% !TEX program = xelatex`，`fontspec` + `xeCJK`，`\setmainfont{Times New Roman}`、`\setCJKmainfont{Songti SC}[BoldFont=Heiti SC]`。目标期刊另有字体要求时按期刊。
- `\usetikzlibrary{positioning, arrows.meta, calc}` 为基础；需要底层分区带时加 `backgrounds`；**不用 `fit`**（见 2A.3.1）。
- 箭头 `Stealth`。
- 颜色只用模板 token：结构灰 `ink/muted/optF/bandA/bandB`，语义色对 `sAF/sAD`、`sBF/sBD`、`sCF/sCD`；不新增其他颜色。
- 每种语义色、虚线框、反馈虚线都要在图例或直接标注中说明含义。
- 线宽按最终尺寸：框边 0.5pt，主箭头 0.6pt，反馈虚线 0.8pt，关键语义框 ≤ 0.9pt。
- 文本按最终嵌入尺寸检查，通常 7–8pt；阶段 / 面板标题 `\small\bfseries`，句首大写。
- 多行文字的 style 必须同时有 `align` 和 `text width`。
- 开发阶段先写坐标账本（注释，ASCII），同列同 x、同行同 y。

写入 `{FIGURES_DIR}fig{N}_{description}.tex`。

#### 2A.3.1 布局几何、路由与常见陷阱

坐标账本、间距公式、路由规则见 `references/tikz-semantic-minimal.md` 第 7–8 节。出 bug 先查：

| 症状 | 原因 | 修复 |
|:-----|:-----|:-----|
| 多行文字挤成一行 | style 缺 `align` 或 `text width`，`\\` 静默失效 | style 同时写 `align=center, text width=…` |
| 相邻框肉眼难辨的重叠 | 布局前没算 | 注释里写每个框 [x_min, x_max] 与 gap（≥ 0.4cm） |
| 上下分组框不对齐 / 偏心 | 用了 `fit` | 显式坐标 + `minimum width/height` |
| 跨行垂直箭头歪斜 | 不同大小框的 anchor 偏差 | 显式 `(x,y1) -- (x,y2)` |
| `-\|`/`\|-` 配 rounded corners 出怪弧 | TikZ 圆角算法 | 改显式 polyline |
| 反馈线穿过框或标签 | 没留路由通道 | 在账本里预留通道，走图外侧 |
| 两个文本节点叠印 | 同 y 且 x 范围重叠 | 分开 y（约 0.4cm） |
| 写 .tex 被 unicode-guard 拦 | 注释或正文里有 `±` `−` `·` `—` 等 | 改 ASCII 或 LaTeX 命令（`$\pm$`、`--`、`$\cdot$`） |

### 2A.3.2 Figure Flywheel 图表飞轮审查模式（强制）

**适用范围**：Route A/B/C 的新建、修改、美化，以及用户连续多轮提出修改意见时的每一轮。任何一轮图表修改后，都不能只看代码或只看编译结果，必须进入“修改 → 渲染 → 严格看图 → 修复 → 再渲染”的飞轮，直到没有问题。

**本轮意见台账**：
- 先把用户这一轮提出的每条修改意见列成台账，不合并、不省略。
- 渲染后逐条核对：`已落实` / `未落实` / `因技术或学术原因暂不落实`。
- 如果有 `未落实`，必须继续修改；如果暂不落实，必须向用户说明原因，不能假装已经完成。

**严格看图清单**（每轮都查，不只查用户点名的问题）：
1. 文本框、标签、图例、坐标轴标题、面板编号是否有重叠、截断、溢出、压线。
2. 箭头、连线、虚线、反馈线是否穿过文本或框体，是否与其他线混在一起导致阅读歧义。
3. 文本框之间、子图之间、层容器与内部元素之间是否留有足够间距，是否存在肉眼不明显但实际重叠的边界。
4. 阅读顺序是否自然，层级结构是否清楚，视觉重心是否偏移，是否因为局部改动破坏了整体结构。
5. 字号、线宽、边距、留白、图例位置、坐标刻度密度是否达到出版图质量。
6. 视觉语法是否与方法和 benchmark 匹配；颜色是否只承担已声明的语义，黑白/灰度下是否仍能理解。
7. 行列中心、基线、面板边界和重复单元是否严格对齐；对齐是否主要由网格和留白实现，而不是靠装饰框补救。
8. 在 manuscript 最终嵌入尺寸下，正文、数学符号、箭头标签和图例是否仍可读。
9. 上一轮已经修好的问题是否被新改动重新引入。

**飞轮规则**：
- 发现任何一个问题，就在已确认的目标图源文件范围内修改、重新渲染、重新看图。
- 不允许以“差不多”“应该可以”结束；终止条件是本轮意见台账全部关闭，且严格看图清单没有剩余问题。
- 每轮优先修最影响阅读的 1-3 个问题，避免一次性大改引入新错误。
- 如果超过 5 轮仍不收敛，停止局部微调，回到布局方案阶段重新设计；重写图结构或影响其他文件前必须再次确认。

### 2A.4 编译验证 + 视觉自查闭环（强制）

**核心原则**：编译通过不等于图对。必须编译 → Read PDF → 视觉诊断 → 修 → 再编译，并执行 Figure Flywheel，**自循环**直到视觉无缺陷，再交给用户。不要写完就甩给用户说"改好了"。

```bash
cd {project_root}/{FIGURES_DIR} && pdflatex -interaction=nonstopmode fig{N}_{description}.tex 2>&1 | tail -5
# 中文图用 xelatex
```

**编译层**：
- 编译成功 → 进入视觉自查
- 编译失败 → 解析错误，修复，重试（最多 3 次）
- 3 次仍失败 → 展示错误给用户，等待指示

**视觉自查层**（强制，不得跳过）：

每次编译成功后，**主 agent 必须用 Read 工具打开 PDF** 视觉检查。检查 checklist（每一条都要确认）：

1. **节点边界、留白和文字是否清楚？**
   - 普通框白底灰边；语义框浅填深边清晰可见；分区带足够浅，不抢框。
   - 只有 `legacy-morandi` 才沿用旧版高饱和度填充规则。
2. **节点内多行文本是否换行？**
   - 常见坑：`\\` 在某些 style 下没生效，title 和 subtitle 挤在一行（如 "Chunking117 chunks"）
   - **修复**：style 必须显式含 `align=center`，或者用**独立的 title 节点 + 独立的 sub 节点**相对盒子 center 做 yshift 定位
3. **箭头是否和其他元素重叠/穿过？**
   - 常见坑：反馈箭头垂直上升穿过下游输出盒；`|-` / `-|` 与 `rounded corners` 产生不工整圆弧
   - **修复**：用显式 3 段 polyline `(x1,y1) -- (x2,y1) -- (x2,y2) -- (x3,y2)`；把被穿过的节点移到别的 x 坐标
4. **层容器边框是否有内部元素溢出？**
   - 检查每个容器的 `minimum width/height` 能否包住所有子元素 + 0.3cm 内边距
   - Backtrack / 回流弧线是否压到容器上边框（通常因为容器高度不够给弧线留空间）
5. **标签位置是否被其他元素遮挡？**
   - 分组 / 阶段标题是否被虚线边框穿过？（放在框外上方，`anchor=south`）
   - 箭头 midway label 是否被另一条线覆盖？
6. **方法与 benchmark 视觉语法是否守住？**
   - 图是否准确表达方法中的对象、方向、时间、层级和不对称关系？
   - 是否出现 benchmark 没有、模型也没有的装饰性层、反馈箭头或因果暗示？
   - 语义色是否 ≤ 3 组、每组单一含义、都有图例或直接标注？结构元素是否全灰？
   - 实线框、虚线框、实线箭头、虚线箭头是否各自保持单一且一致的语义？
7. **对齐是否严格？**
   - 同一"带"内的盒子中心 y 是否一致？同一列的 x 是否一致？
   - 上下两带的对应列 x 是否对齐（方便垂直连接）？
   - 重复结构是否复用同一组坐标、尺寸和间距，而不是逐个目测摆放？
8. **最终尺寸是否通过？**
   - 将图嵌入 manuscript 后重新渲染对应页；不得只检查 standalone PDF。
   - 在目标栏宽下检查字号、线宽、断词、图例和 caption 占用；必要时做灰度预览和 50% 缩放检查。

**循环规则**：
- 发现 ≥1 条缺陷 → 立刻修代码，重编译，再 Read PDF，再查 checklist
- **不要**一次集齐所有缺陷再改——每次只改 1-2 处，避免引入新问题
- **不要**只凭视觉"看起来差不多"就收工——每条 checklist 条目都要明确 ✓ 或确认不适用
- 单个图的迭代次数不设上限，但如果 > 5 轮还没收敛，回到草稿阶段重新想布局

**终止条件**：checklist 8 条全过 → 才能把图交给用户 / 进入下一张图。

### 2A.5 展示结果

用 Read 工具展示生成的 PDF 给用户。

```
✅ TikZ 图生成成功

📄 源文件: {FIGURES_DIR}fig{N}_{description}.tex
📊 PDF: {FIGURES_DIR}fig{N}_{description}.pdf

[展示 PDF 预览]

需要修改吗？指出具体调整（位置、大小、颜色、文字...）
```

**循环**：用户提出修改 → 建立本轮意见台账 → Edit .tex → 重新编译 → 执行 Figure Flywheel → 再次展示 → 直到用户确认。

---

## Route B：Python/R 数据图美化

### 2B.1 定位目标图

- 根据用户指定的图编号/路径，定位：
  - 输出图片（PDF/PNG）→ 用 Read 工具查看
  - 源脚本（.py / .R）→ 读取代码
- 如果只有 PDF 没有源脚本 → AskUserQuestion 询问源脚本路径或数据文件路径
- 也检查 `data/scripts/`、`scripts/`、`code/` 目录下的脚本
- **数据来源核对**（英文论文项目）：脚本读取的数据文件应是 `structure/0_global/results_register.md` 中某条目的"来源"。未登记 → 提醒用户经 `/analysis` Release 登记（美化只改视觉，不阻断）；`index.md` 的"来源"列写 register ID

### 2B.2 八维度诊断

读取图片（视觉分析）+ 读取源代码（代码分析），对照 8 个维度评估：

```
📋 Fig {N} 诊断报告

| # | 维度 | 状态 | 问题 | 建议 |
|:-:|:-----|:----:|:-----|:-----|
| 1 | 视觉编码 | 🔴 | 使用默认色且颜色无统计语义 | 按变量类型与 benchmark 重建设计 |
| 2 | 字体 | 🟡 | 最终栏宽下低于期刊字号 | 按目标期刊与全篇图件统一 |
| 3 | 标注 | ✅ | 轴标签完整 | — |
| 4 | 布局 | 🟡 | 图例位置遮挡数据 | 移至底部水平排列 |
| 5 | 子图 | ⬜ | 单图，不适用 | — |
| 6 | 分辨率 | 🔴 | PNG 72dpi | 改为 PDF 300dpi |
| 7 | 尺寸 | 🟡 | 未按最终栏宽设计 | 锁定目标宽度与最终字号 |
| 8 | 细节 | 🟡 | 刻度标签过密 | 减少刻度数量 |
```

**状态定义**：
- 🔴 必须修复（严重影响出版质量）
- 🟡 建议修复（提升美观度）
- ✅ 无问题
- ⬜ 不适用

### 2B.3 与 Eagle 参考图对比（如有）

如果步骤 1 中选了 Eagle 参考图：

```
📊 与参考图对比

参考图: {name}（{annotation}）

| 方面 | 当前图 | 参考图 | 建议调整 |
|:-----|:-------|:-------|:---------|
| 视觉编码 | 默认蓝橙 | 一组中性色 + 一个信号色 | 按数据语义重设编码 |
| 布局 | 单面板 | 左右双面板 | 考虑拆分为 (a)(b) |
| 字号 | 偏小 | 10pt 正文 | 放大标签字号 |
```

### 2B.4 提议美化方案

```
🎨 美化方案（共 {N} 处调整）

优先级高:
1. [视觉编码] 按变量类型、统计关系和 benchmark 重设颜色/线型/形状
2. [分辨率] 输出格式改为 PDF 300dpi

优先级中:
3. [字体] 按目标期刊与项目统一字体，并在最终栏宽下校验字号
4. [布局] 图例移至右下角

优先级低:
5. [细节] 减少 X 轴刻度密度

确认？可以增删调整。
```

AskUserQuestion，循环直到确认。

### 2B.5 修改源脚本

根据确认的美化方案，修改 Python/R 脚本。关键注入模板：

> ⚠️ **占位符替换契约**：下方模板中的 `{FIGURES_DIR}`、`{N}`、`{desc}` 是**写盘前**必须由主 agent Edit 替换为实际字符串的占位符——Python/R 运行时**不会**展开它们。例如 `{FIGURES_DIR}` → `structure/figures_tables/figures/`、`{N}` → `3`、`{desc}` → `network_topology`。忘记替换会生成字面量名为 `{FIGURES_DIR}fig{N}_{desc}.pdf` 的文件。

**Python (matplotlib，示意；颜色和尺寸必须由 figure spec 替换)**：
```python
import matplotlib.pyplot as plt
# semantic-minimal token（与 TikZ 同一组；只取需要的语义）
INK, MUTED = "#404040", "#787878"
SEM = {"A": ("#26548C", "#E2ECF7"), "B": ("#B0541A", "#FBE5D3"), "C": ("#2E6E3E", "#E0F0E2")}  # (线/点, 填充/置信带)
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.serif": ["Times New Roman", "TeX Gyre Termes", "Times"],
    "pdf.fonttype": 42, "svg.fonttype": "none",
})
# 输出
plt.savefig("{FIGURES_DIR}fig{N}_{desc}.pdf", bbox_inches="tight", dpi=300)
```

**R (ggplot2，示意；theme 与 palette 必须由 figure spec 替换)**：
```r
ink <- "#404040"; muted <- "#787878"
sem <- c(A = "#26548C", B = "#B0541A", C = "#2E6E3E")        # 线 / 点
sem_fill <- c(A = "#E2ECF7", B = "#FBE5D3", C = "#E0F0E2")   # 填充 / 置信带
theme_journal <- theme_classic(base_family = "Times New Roman") +
  theme(text = element_text(family = "Times New Roman"),
        panel.grid.minor = element_blank())
ggsave("{FIGURES_DIR}fig{N}_{desc}.pdf",
       width = target_width_mm / 25.4,
       height = target_height_mm / 25.4,
       device = cairo_pdf)
```

### 2B.6 运行脚本 + 视觉自查闭环（强制）

**与 2A.4 同一原则**：运行通过不等于图对，必须 Read PDF 视觉确认。

```bash
cd {project_root} && python3 {FIGURES_DIR}fig{N}_{desc}.py 2>&1 | tail -20
# 或
cd {project_root} && Rscript {FIGURES_DIR}fig{N}_{desc}.R 2>&1 | tail -20
```

- 运行失败 → 展示错误，修复重试
- 运行成功 → **必须 Read PDF** 自查 checklist：
  1. 坐标轴标签是否被截断？（`bbox_inches="tight"` 是否生效）
  2. 图例是否遮挡数据？位置是否合理？
  3. 字号在最终正文栏宽下是否可读？（按目标期刊规范；不得用 standalone 放大预览代替最终尺寸检查）
  4. 颜色、线型和形状是否与变量类型、统计语义、benchmark 及全篇语义映射一致？
  5. 多面板 (a)(b) 标签是否一致、对齐？
  6. Y 轴数值范围是否合理（不应有过多空白或刻度标签溢出）？

发现缺陷 → 改脚本 → 重跑 → 再 Read PDF → 再查。自循环直到 checklist 全过，才展示给用户。

**用户确认轮**：自查通过后展示给用户，接受用户的语义反馈 → 改 → 再自查 → 直到用户确认。

**飞轮补充**：用户每提出一轮反馈，都必须先建立本轮意见台账，再修改脚本、运行、Read PDF，并按 Figure Flywheel 检查反馈落实、重叠/截断/拥挤、结构美观、配色一致性。仍有问题就继续修，不得把有明显视觉缺陷的图交给用户确认。

---

## Route C：Python/R 数据图创建

### 2C.1 收集图规格

AskUserQuestion：
```
描述你要创建的数据图：
- 图类型（散点图/柱状图/热力图/网络图/系数图/弦图/...）
- 数据来源（data/ 下的文件？脚本生成？手动输入？）
- X/Y 轴变量
- 分组/面板变量（如有）
- 特殊要求（误差线、置信区间、子图拼接...）
```

同时扫描项目的 `data/` 目录了解可用数据文件。

**数据来源门**（规格 §4.7；英文论文项目的数据图，概念图不适用）：
- 读取 `structure/0_global/results_register.md`。图的数据必须来自其中登记条目的"来源"（`data/results/`、`data/robustness/` 下的输出，或 analytical-model 的 `structure/3_analysis/derivation/checks/` 复核输出与数值研究输出）；脚本只读这些文件，不手工录入数值、不从历史报告或正文中抄数。
- register 已存在但所需结果未登记 → 停止，提示先经 `/analysis` Release 登记后再画。
- register 尚不存在（分析阶段的探索图）→ 可以画，`index.md` 来源写脚本输出路径、状态不得高于 drafted，并提醒进入正文前须登记。
- 完成后在 `index.md` 的"来源"列写 register ID。

### 2C.2 推荐语言 + 设计方案

**语言推荐逻辑**：
- 网络图、弦图 → R（igraph / circlize 生态更强）
- 复杂 ggplot 风格统计图 → R
- 机器学习可视化、地理空间图 → Python
- 简单柱状/折线/散点 → 如项目已有 R 脚本则 R，否则 Python
- 用户指定 → 覆盖推荐

```
📊 Fig {N} 设计方案: {title}

类型: {coefficient plot with 95% CI}
数据: {data/model_results.csv}
语言: R（推荐理由：项目已有 R 脚本，ggplot2 生态适合此类图）
布局: {单面板 / 双面板 (a)(b)}
视觉编码:
  - 参考 benchmark: {论文 + figure}
  - 中性基线: {灰 #404040 / #787878}
  - 语义色: {A 蓝 = …；B 橙 = 核心信号；C 绿 = …}（≤3，全篇同义）
  - 不确定性: {interval / alpha / hatch}
目标尺寸: {single/double column, width_mm × height_mm}

确认？可以调整。
```

AskUserQuestion，循环直到确认。

### 2C.3 生成脚本

生成完整的 Python/R 脚本，预配置：
- semantic-minimal token 下、与变量类型、统计语义、benchmark 和目标期刊一致的视觉编码
- 项目统一字体；无项目约束时默认 Times New Roman
- PDF/SVG 矢量输出，必要时附 300--600 DPI 预览
- 按目标期刊最终栏宽反推尺寸与字号，而不是固定 7"×5"
- 完整的坐标轴标签和图例

写入 `{FIGURES_DIR}fig{N}_{description}.{py|R}`。

### 2C.4 运行 + 验证

同 Route B 的步骤 2B.6。

---

## Route D：跨图一致性审计

### 2D.1 扫描所有图源文件

```bash
python3 ~/.claude/skills/shared/figure_audit.py inventory --figures-dir {FIGURES_DIR}
```

脚本提取每个图的：颜色定义、字体设置、输出格式、DPI、尺寸，并标出 semantic-minimal token 之外的颜色。
输出 `_figure_audit.json` + stdout 汇总表。

VERIFY: PASS = 全部一致。FAIL = 有不一致项。

### 2D.2 主 Agent 语义分析

在脚本机械检查基础上，主 Agent 补充语义级检查：
- 每张图是否与其方法、图件功能和 benchmark 视觉语法匹配，而非只追求全篇同色
- 跨图共享元素的颜色、形状和线型语义是否一致；不同图件类型是否保留必要的差异
- TikZ 结构图是否遵守 `semantic-minimal`（或有明确理由启用其他 profile）；数据图是否使用同一组 token 且语义一致
- 标签风格一致性（(a)(b)(c) vs A/B/C vs 无标签）
- 坐标轴标注风格（Title Case vs sentence case vs ALL CAPS）
- 图例风格（框内 vs 框外，位置是否统一）
- 最终栏宽下的字号、线宽、灰度可读性与 panel 对齐

### 2D.3 展示审计报告

```
📋 跨图一致性审计 — {PAPER_TITLE}

共 {N} 张图（TikZ: {x}, Python: {y}, R: {z}）

| 维度 | 状态 | 详情 |
|:-----|:----:|:-----|
| 方法/benchmark 匹配 | 🟡 | Fig. 2 的层间箭头可能暗示模型未估计的实时反馈 |
| 视觉 profile | 🟡 | Fig. 2 用了 5 种颜色且无图例；按 semantic-minimal 收到 ≤3 组语义色 |
| 字体一致性 | ✅ | 全部使用项目锁定的 Times New Roman 图内标签 |
| 输出格式 | 🔴 | fig3 为 PNG，其余 PDF |
| 尺寸一致性 | ✅ | 均按目标双栏宽度 183 mm 设计并检查最终字号 |
| 标签风格 | ✅ | 全部 (a)(b)(c) 标签 |
| 对齐与打印可读性 | 🟡 | Fig. 2 重复列未锁定同一坐标，缩放后标签低于目标字号 |

修复建议:
1. Fig. 2: 先按方法语义修正层间关系，再用 benchmark 驱动布局
2. Fig. 2: 切换 semantic-minimal、补图例并锁定行列坐标
3. Fig. 3: 输出格式改为 PDF
```

AskUserQuestion：
```
是否立即修复？
(1) 全部修复
(2) 选择性修复（输入编号，如 "1"）
(3) 暂不修复
```

选 (1) 或 (2) → 按 Route B 的美化流程逐个修复。

---

## 步骤 Final：完成提示

```
✅ Figure 操作完成

{Route A: 📐 创建了 TikZ 概念图}
{Route B: 🎨 美化了数据图}
{Route C: 📊 创建了数据图}
{Route D: 📋 完成了跨图一致性检查}

📂 文件:
- 源文件: {FIGURES_DIR}fig{N}_{description}.{tex|py|R}
- 输出: {FIGURES_DIR}fig{N}_{description}.pdf

📋 index.md 已更新（编号 Fig. {N}）

🔗 在 manuscript.tex 中引用（使用纯文件名，依赖 preamble `\graphicspath{}` 兜底）:
\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{fig{N}_{description}.pdf}
\caption{TODO}
\label{fig:TODO}
\end{figure}

> **注**：如果 preamble 未设置 `\graphicspath{}`，请临时改成绝对路径 `{FIGURES_DIR}fig{N}_{description}.pdf`，并建议把 `\graphicspath{{structure/figures_tables/figures/}{figures_tables/figures/}{figures/}}` 加到主 tex 的 preamble，以免 `/finalize` 清理脚手架后所有图链断裂。

💡 提示:
- 运行 /figure audit 检查所有图的一致性
- 投稿前 /pre-submit 也会检查图表规范
```

---

## 全局约束

### 交互模式
- 所有设计方案都走"中文提议 → 用户确认 → 执行"闭环
- 用户可随时输入 "stop" 中断流程

### 文件规范
- TikZ: standalone 文档，单独编译为 PDF
- Python/R: 独立脚本，输出 PDF 到 `{FIGURES_DIR}`
- 命名: `fig{N}_{snake_case_description}.{tex|py|R}`
- **每次创建/修改图后，必须同步更新 `structure/figures_tables/index.md` 的 Figures 表格**

### 不越界
- 不修改 manuscript.tex（只提供引用代码供用户手动插入）
- 不修改已有图的数据内容（只改视觉呈现）
- 不替代用户的学术判断（图的内容选择由用户决定）
- 数据图的数据只来自 `results_register.md` 登记的来源（见 2C.1 数据来源门）；概念图不受此限

### Eagle 集成
- 库路径: `/Users/zylen/Library/CloudStorage/Dropbox/Apps/Eagle/research.library/`
- 搜索工具: `~/.claude/skills/shared/eagle_search.py`
- Eagle 搜索是可选的，不强制要求
- 建议用户持续向 Eagle 中添加好图并打标签，丰富参考库

### 跨 Skill 关系
- `/pre-submit` 会检查图表规范（分辨率、格式、引用完整性）
- `/paper-init` 创建 `structure/figures_tables/figures/` 目录和 `index.md` 注册表（项目初始默认结构；`/figure` 通过 Step 0.1 类型探测决定最终 `{FIGURES_DIR}` 值）
- `/figure audit` 是 `/pre-submit` 图表检查的前置增强版
- 图表注册表 `structure/figures_tables/index.md` 是图表元数据的唯一索引
