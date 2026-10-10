# TikZ Semantic-Minimal Profile（默认）

结构图、方法流程图、信息结构图、机制图的默认 profile。母版：zy02 `fig01_info_structure.tex`；模板：`assets/tikz_semantic_minimal.tex`。

一句话：**灰色搭骨架，颜色只说语义，最多三组，必须有图例或直接标注。**

## 1. 视觉立场

- 白底。框、主流程箭头、分区带、时间轴等结构元素一律灰（`ink` 深灰线、白填）。
- 颜色只用来编码图内一个**已声明的语义类别**（如"公开信息 / 私有信息 / 可验证结果"，或"技能 / 需确认 / 产物"）。同一颜色在全图（最好全篇）只表达一种含义。
- 最多三组语义色对（浅填 + 深边）。普通对象保持白底灰边；只有属于某语义类别的对象才上色。
- 强调靠"颜色 + 加粗边 + 粗体关键词"中的一两项，不叠加阴影、渐变、3D、图标。
- 分组靠对齐、留白和极浅灰带（`bandA/bandB`），不用彩色大面积底。
- 每个可见元素都必须承载信息。

## 2. 设计 token

```latex
% 结构灰
\definecolor{ink}{RGB}{64,64,64}       % 普通边框、主流程箭头
\definecolor{muted}{RGB}{120,120,120}  % 可选/辅助对象的虚线边、次要标注
\definecolor{optF}{RGB}{242,242,242}   % 可选/辅助对象填充
\definecolor{bandA}{RGB}{247,247,247}  % 分区带（交替）
\definecolor{bandB}{RGB}{238,238,238}
% 语义色对（F = 浅填，D = 深边/深字）
\definecolor{sAF}{RGB}{226,236,247}\definecolor{sAD}{RGB}{38,84,140}   % A 蓝
\definecolor{sBF}{RGB}{251,229,211}\definecolor{sBD}{RGB}{176,84,26}   % B 橙（最强调）
\definecolor{sCF}{RGB}{224,240,226}\definecolor{sCD}{RGB}{46,110,62}   % C 绿
```

HEX（数据图与审计脚本共用）：ink `#404040`、muted `#787878`、optF `#F2F2F2`、bandA `#F7F7F7`、bandB `#EEEEEE`；A `#E2ECF7/#26548C`、B `#FBE5D3/#B0541A`、C `#E0F0E2/#2E6E3E`。

默认语义分工（可按图改，但须在设计方案里声明）：

| 色 | 默认语义 | 例 |
|---|---|---|
| A 蓝 | 主体 / 公开 / 常规参与对象 | 公开信息；技能节点 |
| B 橙 | 读者必须看到的那一个关键语义；反馈 / 回流 | 私有信息、信息缺口；需用户确认；回流线 |
| C 绿 | 结果 / 可验证 / 产出 | 可验证结果；产物文件 |
| 灰 | 结构、决策、普通流程 | 决策框、主箭头、分区带、时间轴 |

只需要一两种语义时就只用一两组；不得为分层、分阶段、分时期、美观而上色——这些用位置、分区带和标签表达。

## 3. 编码规则

| 元素 | 写法 |
|---|---|
| 普通 / 决策框 | `draw=ink, fill=white`，0.5pt，圆角 2pt |
| 语义框 | `draw=sXD, fill=sXF`，0.5pt；关键语义（通常 B）可加粗到 0.8pt 并在框内粗体关键词 |
| 可选 / 辅助框 | `draw=muted, fill=optF, dashed`（同一图内虚线框只表示"可选/辅助"一种含义） |
| 阶段 / 分组框 | 灰线无填充；实线 = 一次性，虚线 = 重复或条件性（须在标题写明，如 "repeated in each period"） |
| 主流程箭头 | `ink` 实线，约 0.6pt |
| 语义流 | 与源语义同色实线（如私有信息只被一方观测：`sBD` 实线） |
| 反馈 / 回流 | `sBD` 虚线（`dash pattern=on 4pt off 2pt`），约 0.8pt；必须带短标签 |
| 弱依赖 / 共同知识 | 与语义同色的普通虚线，短而直 |
| 箭头标签 | `\scriptsize`，`fill=white, inner sep=1pt`，斜体或与线同色 |

一种线型在一张图里只表达一种关系；非常规关系必须直接标注。

## 4. 图例与标注

- 用了语义色就必须有图例（图底一行，色块 + 一句话）或在图内直接标注；图例条目同时说明虚线框、反馈虚线的含义（如果图里有）。
- 图例只列图里真实出现的编码，顺序与默认语义表一致。
- 长定义放 caption 的 Notes，不塞进图里。

## 5. 字体与尺寸

- 英文图：`newtxtext,newtxmath`（pdflatex），与 Elsevier / Times 系正文一致；目标期刊另有字体要求时按期刊。
- 中文图：XeLaTeX + `fontspec` + `xeCJK`，`\setmainfont{Times New Roman}`、`\setCJKmainfont{Songti SC}[BoldFont=Heiti SC]`；文件首行写 `% !TEX program = xelatex`。中文图中英文标签照常用 Times，代码类标签用 `\texttt`。
- 最终尺寸：正文标签 7–8pt（TikZ 里 `\footnotesize` / `\scriptsize` 按成稿缩放核算），注释不低于 6.5pt，面板 / 阶段标题 `\small\bfseries`。
- 句首大写（sentence case），不在每个框里用 Title Case。

## 6. 线宽与形状

| 元素 | 默认 |
|---|---:|
| 框边 | 0.5pt |
| 关键语义框边 | ≤ 0.9pt |
| 主箭头 | 0.6pt |
| 反馈虚线 | 0.8pt |
| 分组框 / 分隔线 | 0.4–0.6pt |
| 圆角 | 2pt（分组框 4pt） |

箭头统一 `Stealth`。形状变化必须有含义，默认全部矩形。

## 7. 对齐契约

画之前在 .tex 注释里写坐标账本：

```text
target width = ... mm
columns x = ...      rows/lanes y = ...
standard node width/height = ...
gutters: horizontal ..., vertical ...
routing lanes for feedback lines = ...
```

- 同列复用同一个 x，同行复用同一个 y；同角色框同宽同高同内边距。
- 相邻框间距 `gap = x_B - w_B/2 - (x_A + w_A/2) ≥ 0.4cm`，在注释里写出每个框的 [x_min, x_max]。
- 分组框 / 分区带用显式坐标画，不用 `fit`（不同内容会算出偏心，上下对不齐）。
- 注释只用 ASCII（`-`、`+/-`），否则 unicode-guard 会拦。

## 8. 路由规则

1. 垂直连线用显式坐标 `(x,y1) -- (x,y2)`，不靠不同大小框的 `.south/.north` anchor。
2. 多段折线写成显式 polyline；不要 `-|`/`|-` 叠 `rounded corners`（单次 90° 折角除外）。
3. 反馈线走图外侧或预留的路由通道，绝不穿过框体和文字。
4. 标签放在线的同一侧（全图一致的上/下/右侧），不压其他线。
5. 多行框文字：style 必须同时有 `align=center` 和 `text width`，否则 `\\` 会静默失效；超过 4 行就拆框或把细节移到 caption。

## 9. 颜色检验（加色前四问）

1. 它编码的语义是什么？能用一句话写进图例吗？
2. 全图（和全篇）是否同一种含义？
3. 位置、线型、直接标签能否更干净地表达？能 → 不加色。
4. 灰度打印下，语义框是否仍能靠图例文字 / 粗边 / 标签区分？

四问都过才保留。

## 10. 成稿检查

1. 编译 standalone PDF 并读图。
2. 按目标栏宽检查字号与线宽；嵌入正文后再看实际页面。
3. 100% 和 50% 缩放各看一遍；做一次灰度预览。
4. 查重叠、截断、穿框连线、行列对齐、数学基线。
5. 语义色数 ≤ 3，结构元素全灰，图例与实际编码一一对应。

## 11. 何时不用本 profile

- 期刊要求黑白或用户指定 → `references/tikz-journal-minimal.md`（journal-minimal-monochrome）。
- 用户明确要 Morandi 或项目已锁定 → `references/legacy-morandi.md`。
- 数据图不套本 profile 的框线规则，但沿用同一组 token（见 SKILL.md Route B/C）。
