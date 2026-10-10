# Legacy Morandi Profile（仅在用户明确指定或项目已锁定时使用）

> 2026-10-10 起默认 profile 改为 semantic-minimal（`tikz-semantic-minimal.md`）。本文件保留旧版 Morandi 色板与分层流程图手册，供已锁定该风格的旧项目延续使用。几何与路由经验已并入 semantic-minimal 第 7–8 节。

## 1. Morandi 色板

启用 legacy-morandi 时，该项目所有图使用此色板。

| 名称 | 深色 | 浅色 | 用途 |
|:-----|:-----|:-----|:-----|
| Steel Blue | `#576fa0` | `#a7b9d7` | 主色系 |
| Gold | `#e3b87f` | `#fadcb4` | 辅助色/对比 |
| Rose | `#b57979` | `#dea3a2` | 强调/警示 |
| Gray | `#7c7c7c` (dark) / `#b5b5b5` (mid) | `#cfcece` (light) | 结构/次要元素（三档灰） |

> **Gray 三档**：TikZ 结构色（层容器虚线边、结构箭头、文本）用 `#7c7c7c`（深，实战中 `#9f9f9f` 太淡看不清）；I/O 盒/日志带等背景块用 `#b5b5b5` 的 !45~!55；浅色辅助区域用 `#cfcece`。

**TikZ 定义**：
```latex
\definecolor{steelblue}{HTML}{576fa0}
\definecolor{steelbluelight}{HTML}{a7b9d7}
\definecolor{gold}{HTML}{e3b87f}
\definecolor{goldlight}{HTML}{fadcb4}
\definecolor{rose}{HTML}{b57979}
\definecolor{roselight}{HTML}{dea3a2}
\definecolor{morandigray}{HTML}{7c7c7c}       % 结构色（深）
\definecolor{morandigraymid}{HTML}{b5b5b5}    % I/O 盒 / 日志带（中）
\definecolor{morandigraylight}{HTML}{cfcece}  % 辅助区域（浅）
```

**Python**：
```python
MORANDI = {
    "steel_blue": "#576fa0", "steel_blue_light": "#a7b9d7",
    "gold": "#e3b87f", "gold_light": "#fadcb4",
    "rose": "#b57979", "rose_light": "#dea3a2",
    "gray": "#7c7c7c", "gray_mid": "#b5b5b5", "gray_light": "#cfcece",
}
```

**R**：
```r
morandi <- c("#576fa0", "#e3b87f", "#b57979", "#7c7c7c",
             "#a7b9d7", "#fadcb4", "#dea3a2", "#b5b5b5", "#cfcece")
```

## 2. 分层流程图手册



---

##### A. legacy-morandi 内部原则

1. **自顶向下阅读**：层编号 1→N 从上到下；输入盒在顶、输出盒在底；主信息流向下
2. **三色点睛 + 其余全灰**：整图最多 3 种语义色，结构性元素（容器、流程、I/O、日志、普通箭头）一律 `morandigray`
3. **主/反差异**：主流程 = 实线 + 结构灰；反馈/回流 = 虚线 + 语义色。靠线型和颜色双重区分

---

##### B. 色彩体系

**色板**（仅在显式启用 legacy-morandi 时使用）：
```latex
\definecolor{steelblue}{HTML}{576fa0}       \definecolor{steelbluelight}{HTML}{a7b9d7}
\definecolor{gold}{HTML}{e3b87f}            \definecolor{goldlight}{HTML}{fadcb4}
\definecolor{rose}{HTML}{b57979}            \definecolor{roselight}{HTML}{dea3a2}
\definecolor{morandigray}{HTML}{7c7c7c}     \definecolor{morandigraymid}{HTML}{b5b5b5}
\definecolor{morandigraylight}{HTML}{cfcece}
```

**语义分配示例**（需结合论文主题选定）：
| 色 | 典型语义 | 示例 |
|:---|:---------|:-----|
| Steel blue | 知识/检索/显性/默认主体 | RAG / explicit_RAG / Stage-1 知识类 |
| Gold | 执行/计算/隐性/工具调用 | FC / tacit_FC / Stage-2 评估 |
| Rose | 人工/干预/反馈/警示 | Human review / Override / Key principle callout |
| Gray(morandigray) | 结构/流程/日志/辅助 | 容器、主流程箭头、DTT 带、I/O 盒 |

**配对硬规则**：
- **B.1 Fill ≥ !50 饱和度**：低于 !45 的填充在 PDF 里几乎看不见，盒子"消失"。常用 `!50-!60`
- **B.2 Fill XOR Draw**：盒子要么填彩色（边默认无/灰），要么只描彩边（填白）；不要同时 `fill=彩色 + draw=同色`（双装饰污染）
- **B.3 稳定模式 = 灰边 + 彩填**：`draw=morandigray + fill=accent!50` 是**唯一**能保证任何色都能渲染的组合
- **B.4 xcolor 冲突警告**：`draw=steelblue, fill=white` 经常**边框画不出**（xcolor 有同名预定义色可能占用解析），换用 B.3 方案或改用灰边

---

##### C. 元素手册（逐个元素的稳定模式）

###### C1. 层容器（Layer container）

```latex
layerbox/.style={draw=morandigray, thick, fill=none,
    rounded corners=8pt, dash pattern=on 3pt off 2pt},
\node[layerbox, minimum width=15.6cm, minimum height=3.3cm] (L1) at (7.5, 5.5) {};
```

硬规则：
- 圆角 `rounded corners=8pt` 必须（无圆角生硬）
- dash pattern 必须显式写 `on 3pt off 2pt`（默认 `dashed` 在圆角处 dash 不规律，看起来像斜线）
- `fill=none` 必须（填色 + 虚线双重装饰污染）
- **用显式坐标放置**：`at (center_x, y)` + `minimum width/height` 指定。**绝不用 `fit`**（fit 按内容 bounding box 算，不同层边界不同会算出偏心，上下层对不齐）
- 多层容器同宽（同 `minimum width`） + 同中心 x（统一 `center_x`）

###### C2. 层标签（Layer label）

```latex
layerlabel/.style={font=\footnotesize\bfseries, text=morandigray},
\node[layerlabel, anchor=south west] at ($(L1.north west)+(0.1,0.08)$)
    {Layer 1: Dual knowledge base};
```

- 放容器**外部顶部**（`anchor=south west` + 向上 0.08cm 偏移），避免被虚线边框切过
- 不放容器内部（除非容器有填色能遮挡虚线）
- **如果容器顶部外侧还要走 backtrack/overflow 弧线** → label 会和弧线 label 抢位置 → 把 layer label 换到右上角：`anchor=south east @ container.north east`

###### C3. 内容盒 —— 空容器 + 独立子节点模式（C3 是本手册最重要的 recipe）

**禁止**单节点内 `\\` 多行，因为 `\\` 在不同 style 下会静默失效（症状："Chunking117 chunks" 同一行）。

**稳定模式**：盒子是**空容器**，内部每个元素用**独立节点**，相对 `(B.north)` 用 `yshift` 定位。

```latex
% style 定义
stageblue/.style={draw=morandigray, fill=steelbluelight!50,
    rounded corners=4pt, thick,
    minimum width=2.9cm, minimum height=2.6cm},
title/.style={font=\small\bfseries, anchor=center},
sub/.style  ={font=\scriptsize, anchor=center},
body/.style ={font=\scriptsize, text=black!75, align=left,
    anchor=north west, text width=2.4cm},  % text width 比 minimum width 小 0.4-0.5cm

% 使用（假设 B 的宽度为 2.9cm，半宽 1.45cm）
\node[stageblue] (B) at (x, y) {};                              % 空容器
\node[title] at ($(B.north)+(0, -0.30)$) {Stage 1};             % 距顶 0.30cm
\node[sub]   at ($(B.north)+(0, -0.62)$) {Identification};      % 距顶 0.62cm（与 title 间隔 0.32cm）
\draw[steelblue!40, thick]                                       % 分隔线：跨盒内部 2/3 宽
    ($(B.north)+(-1.20, -0.85)$) -- ($(B.north)+(1.20, -0.85)$);
\node[body] at ($(B.north)+(-1.15, -0.97)$) {%                  % body 从分隔线下 0.12cm 开始
    RAG: cases, contracts\\[1pt]
    FC: ---\\[1pt]
    Out: type, precedents};
```

**在 body 节点里**，`\\[Npt]` 行间距还算稳定（因为有 `align=left` + 显式 `text width`），但避免超过 3 行；超过 3 行建议拆多个 body 节点。

**盒内元素垂直预算**（高度 2.6cm 的盒子）：
| 元素 | 垂直占用 |
|:-----|:---------|
| title (距顶 0.3) | 0.3 cm 偏移 |
| sub (距顶 0.62) | 0.3 cm 偏移 |
| 分隔线 (距顶 0.85) | 0.2 cm |
| body (从 0.97 起 + 4 行 + 行距) | ~1.3 cm |
| 底部留白 | ≥ 0.3 cm |
| **总** | ~2.6 cm ✓ |

如果 body 内容更多 → 增加 `minimum height` 到 3.0+ cm。

###### C4. I/O 盒（输入 / 输出 / 数据带）

```latex
iobox/.style={draw=none, fill=morandigraymid!55, rounded corners=3pt,
    minimum width=2.6cm, minimum height=0.8cm, align=center,
    font=\small\bfseries, text=black!85},
\node[iobox] (cr) at (center_x, top_y)    {CR Input};
\node[iobox] (ar) at (center_x, bottom_y) {AR Output};
```

- 固定灰色无边框，和彩色盒子视觉区分
- 位置：图顶（输入）和图底（输出），在层容器**外部**
- I/O 和层容器之间用短垂直箭头（0.5-1.0cm 长）连接

###### C5. 主流程箭头（实线灰）

```latex
arrow/.style={->, thick, morandigray},
\draw[arrow] (A.east) -- (B.west);                         % 水平
\draw[arrow] (center_x, y_from) -- (center_x, y_to);       % 垂直（显式坐标，不用 anchor）
```

- 水平：用 `.east -- .west`
- **垂直：必须用显式坐标** `(center_x, y1) -- (center_x, y2)`，不要用 `A.south -- B.north`（不同大小盒子 anchor 点计算可能偏差）
- 箭头长度 0.5-1.5cm（外观最清爽）
- midway label：`node[chanlabel, midway, above] {text}`，`chanlabel/.style={font=\scriptsize, text=morandigray!90!black}`

###### C6. 反馈 / 回流路径（虚线语义色）

```latex
rosepath/.style={->, thick, rose, dash pattern=on 3pt off 2pt},
```

**绝对禁止** `-|` / `|-` 搭配 `rounded corners`（TikZ 圆角算法画出的弧不工整，经常比预期大或歪）。

**场景 a：单个锐角拐弯**（可以不用圆角）：
```latex
\draw[rosepath]
    (src.east) -- ++(0.5, 0) -- ++(0, -2.1) -- (dst.east);    % 三段显式 polyline
```

**场景 b：必须圆角**（比如 backtrack 弧上去再左折下来）：
```latex
\draw[rosepath, rounded corners=4pt]
    (pm.north) -- ++(0, 0.45) -| (s1.north)
    node[chanlabel, text=rose, pos=0.3, above] {Backtrack};
```
`-|` 在这里可用，因为弧线不和其他 rounded corner 图形相交，视觉上圆角弧够小够工整。如果路径多次拐弯 → 拆成多段手写 polyline。

**场景 c：绕过其他盒子**：
如果 A→B 的直线路径天然穿过盒 C（或 C 的 y 范围）：
- 方案 1：把 C 挪走
- 方案 2：路径多绕一段（从 A 向外走足够距离，再拐向 B）
- **不让路径穿过任何盒体**

###### C7. 跨层索引 / 依赖虚线（小短路径）

```latex
\draw[->, thick, morandigray, dash pattern=on 3pt off 2pt]
    (src.south) -- (dst.north);
```

- 用**灰虚线**而非玫瑰色（玫瑰留给"反馈/干预"语义）
- 短、直、少拐弯
- 用于 DTT source_id 依赖、vector store → retrieve 的 index 连接等

###### C8. 标题 + metadata（图顶部元数据）

**硬规则：两行分开 y，不同 y 坐标**：
```latex
\node[font=\small\bfseries, text=black!85] at (center_x, y1)
    {Case A30 (P2 laboratory) --- DTT excerpt};
\node[font=\scriptsize, text=morandigray!90!black] at (center_x, y1 - 0.4)
    {KCR = 1.00 \quad ETR = 0.32 (S2, S3) / 1.94 (S4)};
```

- y 间距约 0.4cm
- 字号对比清晰：主 `\small\bfseries`，副 `\scriptsize`
- 若同 y 放两 node 且 x 跨度重叠 → 文字会叠印（典型 bug）

###### C9. 关键原则 callout（rose 边 + 白填）

```latex
notebox/.style={draw=rose, thick, fill=white, rounded corners=3pt,
    font=\scriptsize, text=rose, text width=8cm, align=center, inner sep=5pt},
\node[notebox] (principle) at (center_x, top_y) {%
    \textbf{Key principle}: the LLM does not compute;
    all quantitative reasoning is performed by FC functions.};
```

- 放图最顶或图中醒目位置
- 内容短而关键（一句话原则）
- 作为视觉锚点，吸引读者第一眼看到

###### C10. 图例（legend）

- 底部一行水平列出，左对齐或均分
- 每项：`\node[font=\scriptsize, text=<accent>, anchor=west] at (x, y) {\textbullet\ 说明}`
- 条目间 x 间距 ≥ 3cm 防挤
- 最后一条通常是 arrows 含义说明（灰色文本）

```latex
\node[font=\scriptsize, text=steelblue!85!black, anchor=west]
    at (0.2, -4.3) {\textbullet\ explicit\_RAG (retrieved)};
\node[font=\scriptsize, text=gold!75!black, anchor=west]
    at (4.8, -4.3) {\textbullet\ tacit\_FC (computed)};
\node[font=\scriptsize, text=morandigray, anchor=west]
    at (8.9, -4.3) {arrows: source\_id $\rightarrow$ dependent node};
```

---

##### D. 坐标布局公式（布局前必须手算）

###### D1. 盒子间距公式

对每对相邻盒 A、B（中心 x_A、x_B，宽度 w_A、w_B）：
```
gap(A, B) = x_B - w_B/2 - (x_A + w_A/2)
必须  gap ≥ 0.4 cm，建议 0.5-0.7 cm
```

**在 .tex 开头用注释写出所有 x 位置**，作为自检：
```latex
% Row positions (all gaps = 0.5 cm):
%   s1 center=0.85  w=2.6  span [-0.45, 2.15]
%   s2 center=3.95  w=2.6  span [ 2.65, 5.25]   gap to s1 = 0.50 OK
%   pm center=6.50  w=1.5  span [ 5.75, 7.25]   gap to s2 = 0.50 OK
%   s3 center=9.05  w=2.6  span [ 7.75,10.35]   gap to pm = 0.50 OK
%   s4 center=12.15 w=2.6  span [10.85,13.45]   gap to s3 = 0.50 OK
%   hd center=14.70 w=1.5  span [13.95,15.45]   gap to s4 = 0.50 OK
```

若编辑 .tex 时注释里出现 Unicode `−` (U+2212) 或 `±` → unicode-guard 会拦下写入 → **注释只用 ASCII `-` 和 `+/-`**。

###### D2. 容器宽度 / 高度

```
container_width  ≥ Σ(box_widths) + Σ(gaps) + 2 × padding      (padding ≥ 0.3 cm)
container_height = box_height + top_space + bottom_space       (top/bottom ≥ 0.3 cm)
```

若容器顶部要走 backtrack 弧线：`top_space` 再加 0.5-0.6cm。

###### D3. 多带图的上下带对齐

上下两个 layerbox 同宽 + 同 center x + 对应列 x 相同。这样跨带垂直连线才能笔直。

例（fig2 RAG pipeline）：
- 上带 indexing：Chunk / Embed / Store 在 x=6.4 / 10.0 / 13.6
- 下带 query：Cosine-top-k / Rerank 在 x=10.0 / 13.6（与上带同列）
- index 虚线从 Store.south 直接垂直下到 Cosine-top-k.north，完全笔直

###### D4. 多行堆叠（DTT 样式）

每行一个背景带 + 固定行高：
```
row_y_step = box_height + row_gap    (row_gap ≥ 0.3cm)
背景带 minimum_height = box_height + 0.25 cm  (盒子高度 + 小内边距)
```

例（fig5 DTT）：盒高 1.05cm + 行间距 0.35cm → row_y_step = 1.4cm。

###### D5. 同列对齐（列 x 锁定）

一旦确定某图用 N 列布局（N = 3/4/5），**所有行共享同一组列 x**。某行盒子数 < N 则右侧留空。不要重新均分（否则列错位）。

---

##### E. 路径路由硬规则

1. **E.1 垂直箭头用显式坐标**，不用 `.south / .north` anchor（不同大小盒子 anchor 计算会偏）
2. **E.2 禁止** `-|` / `|-` 配 `rounded corners`（除非单次 90° 折角，场景 C6.b）
3. **E.3 多段折线用显式 3 段 polyline**：`(x1,y1) -- (x2,y1) -- (x2,y2) -- (x3,y2)`
4. **E.4 反馈路径绕图外部**，不穿越任何盒体
5. **E.5 Backtrack 弧**：从 PM 顶 → 向上出容器 → 向左 → 向下入 S1 顶。容器高度要给弧线留 0.5cm+
6. **E.6 Override feedback**：从 HD → 向右出容器 → 向下到 DTT 高度 → 向左入 DTT 东边。走右侧，不穿过中间内容
7. **E.7 Index/依赖短链接**：纯灰虚线，`.south -- .north` 或显式坐标，不加 label 除非必要

---

##### F. 五种常见场景的配方（直接抄）

###### F.1 单行 N 个异构盒（fig4：4 stages + 2 humans）

- 盒子按 D1 公式算好 x，gap 0.5cm
- 水平主流程箭头 `.east -- .west`
- 顶部 CR Input（iobox），底部 AR Output
- 回流弧（Backtrack / Override）走容器上方/右侧外部
- 容器 layer label 放右上角（避开 Backtrack label）

###### F.2 两带平行布局（fig2：indexing + query）

- 两个 layerbox 同宽 + 同 center x + 上下叠放
- 上下带内部各自按 F.1 布局
- 跨带箭头：虚线 3 段 polyline，或 `.south -- .north` 直连
- 带间垂直距离 ≥ 1.5cm（给跨带虚线箭头呼吸空间）
- 底部若有附加信息（preference note），用 rose notebox，dashed 箭头回指相关盒子

###### F.3 上带 generic + 下带 example（fig3：通用 FC loop + S2→F1 实例）

- 上带 3 个 phase box（主要尺寸，比如 4.6cm 宽 × 3.8cm 高）
- 下带 3 个 example box（略小，比如 4.6cm 宽 × 2.6cm 高）
- 两带用单条 "instantiates" 虚线垂直连接，在 center x
- 上带 label "Generic ..."，下带 label "Example: ..."
- 图顶放 Key principle rose callout 吸引注意

###### F.4 多行 stage 堆叠（fig5：DTT 按 S1/S2/S3/S4 四行）

- 每行一个背景色块（`fill=steelbluelight!15` 或 `!18`，低饱和度做分区）
- 行间 y step 1.4cm（盒高 1.05 + 间距 0.35）
- 固定 N 列（如 4 列，x=1.9, 5.0, 8.1, 11.2）
- 每行最多 N 个盒子，少于 N 则右侧留空（不重排）
- 行左侧 stage 标签 `anchor=east` @ 最左侧固定 x（如 0.2）
- 顶部标题 + metadata 两行（C8），底部图例一行（C10）

###### F.5 中心辐射（hub-and-spoke，本手册未实战，仅原则）

- 中心放主体框，周围 4-6 个卫星框
- 所有箭头从中心出发或指向中心（靠近中心的那端用 `.north/.south/.east/.west` 对应方向）
- 卫星间不连线（避免干扰）
- 用角度均布卫星位置：`at ({center_x + r*cos(angle)}, {center_y + r*sin(angle)})`

---

##### G. 致命陷阱速查（出 bug 先查这 10 条）

| # | 症状 | 原因 | 修复 |
|:-:|:-----|:-----|:-----|
| G1 | 盒子"消失"只剩文字 | `fill=color!30` 或更低 | fill 下限 `!45`，常用 `!50-!60` |
| G2 | draw=steelblue 白填盒子边框不出 | xcolor 命名冲突 | B.3：`draw=morandigray + fill=accent!50` |
| G3 | 多行文字挤一行 (如 "Chunking117 chunks") | 节点内 `\\` 静默失效 | C3：空容器 + 独立 title/sub/body 节点 |
| G4 | 相邻盒 0.1-0.3cm 肉眼看不到的重叠 | 布局前没算 | D1：注释里写出 [x_min, x_max] + gap |
| G5 | Backtrack 弧和 layer label 挤顶部 | 同一个容器顶部两元素抢位置 | C2：layer label 换 `anchor=south east` |
| G6 | 标题和 metadata 叠印 | 同 y 放两 node | C8：两行分开 y，间距 0.4cm |
| G7 | `-\|` 或 `\|-` 配 rounded corners 出现诡异圆弧 | TikZ 圆角算法 | E.3：三段显式 polyline |
| G8 | 跨带垂直箭头歪斜 | `.south/.north` anchor 计算偏差 | C5：显式 `(center_x, y1) -- (center_x, y2)` |
| G9 | Write .tex 被 unicode-guard 拦 | 注释里有 Unicode `±` `−` | D1：注释只用 ASCII `+/-` `-` |
| G10 | `pdflatex && rm` 触发权限提示 | Claude Code 复合命令整体匹配 | 两条独立 Bash 调用，或白名单 `Bash(pdflatex * && rm *)` |
