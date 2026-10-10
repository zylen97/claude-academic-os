---
description: "仅对已有学术 LaTeX 文本做英文语言润色。用于用户要求 polish、润色、简化或提升英文自然度时；也可被 technical / narrative 以嵌入模式调用（只返回候选文本）。不得修改研究逻辑、结构、论断强度、引用、数据、公式、标签或段落顺序。目标章节唯一时自动校验、写回并编译，不展示 diff，不要求二次确认。"
---

# Polish — 自动化 language-only 润色

> 规格：`~/.claude/skills/shared/ACADEMIC-OS-LITE.md`（冲突以规格为准）。正文精简规则：`~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。
> 子 agent：可以在需要时使用子 agent（定义在 `~/.claude/agents/`），并在执行前告诉用户将派出哪些。
> Git：本技能不 stage、不 commit、不 push。

Polish 只改善作者已经定稿的学术英文，不承担 peer review、理论修改、结构重组或期刊定位。

生成或审计候选文本前读取 `~/.claude/skills/shared/MANUSCRIPT-ECONOMY.md`。Polish 不得新增 hedge、caveat、concession、limitation 或防御性句子；只有删除严格不改变含义时才可去掉重复，否则保留原文并把实质性精简问题报告给调用方。

## 范围

仅可修改：

- grammar、articles、punctuation、agreement 和 tense consistency；
- collocation、concision、sentence length、readability 和 local flow；
- pronoun clarity、parallelism、terminology consistency；
- Chinglish、冗余 nominalization / passive voice、em-dash misuse 和 lexical hyphenation。

绝对不得修改：

- RQ、hypothesis、theory、mechanism、interpretation、contribution 或 claim strength；
- 段落顺序/边界、标题、列表、表图、caption、footnote 或 LaTeX environment；
- citation command/key/order、label、reference、formula、symbol、number、year、sample size、coefficient 或 p-value；
- 已定义术语、model name、code identifier、data boundary 或 analytical decision。

不运行任何 reviewer agent 或 `journal-scout`，不生成或依赖 Writing Brief。目标期刊和项目规范从项目合同 `CLAUDE.md` 与 manuscript 中读取。

## 术语表（canonical terminology contract）

若项目存在 `structure/0_global/technical_map.md`，读取其第 2 节"术语表"（术语｜定义｜不得混用的近义词），作为本次润色的约束性术语合同：

- 每个术语按表中写法原样保留，不为词汇多样性替换；
- 表中"不得混用的近义词"不得出现在候选文本中；源文本已经出现的，只报告，不在润色中替换（替换可能改变含义，属于调用方或作者的决定）；
- 两个权威位置（术语表与 manuscript 正式定义）含义冲突时，停止并报告，不按文风择一。

嵌入模式下若调用方已提供术语合同，以调用方提供的为准；未提供时同样读取上述术语表。文件不存在时，以 manuscript 中的正式定义与用户确认的措辞为准。

## 使用的子 agent

- `~/.claude/agents/language-polisher.md`：生成 language-only candidate；
- `~/.claude/agents/language-auditor.md`：三个并行 audit groups。

调用方式：Agent 工具，`subagent_type` 取角色名（如 `language-polisher`、`language-auditor`）。执行前告诉用户本次将派出 1 个 language-polisher 与 3 个 language-auditor（两轮审计）。

处理 lexical hyphenation 前，主 agent 与两个角色均须完整读取 `~/.claude/skills/polish/references/hyphenated-compound-policy.md`，并把该绝对路径写入 prompt。

## 授权与交互

用户明确要求润色一个可唯一定位的章节或精确 passage，即授权在全部 gates 通过后自动写回该目标。不展示 diff、不逐条征求意见、不要求第二次写入确认。

仅在下列情况暂停：

- target file/section 无法唯一定位；
- 输入无法与 source 唯一匹配；
- output protocol 或 protected-content gate 连续两次失败；
- 写入后的 manuscript 无法编译；
- 修复语言必须先做实质性研究判断。

### 嵌入模式（`POLISH_EMBEDDED_CANDIDATE_ONLY`）

`technical` 或 `narrative` 在已完成语义审计的内存草稿上，可以携带 token `POLISH_EMBEDDED_CANDIDATE_ONLY` 调用本流程。此模式下：

- 所给草稿即 exact source block；调用方保留全部研究内容、用户确认、展示与写回决定；
- 调用方标明来源为 Results 或 Discussion 时，生成候选前先做下文"空洞表述预检"；语法正确不等于读者可读；
- 调用方提供的术语合同与用户保护片段是约束性输入；保留每个首选术语，遇到含义冲突时报告，不自行选同义词；
- 生成候选前用 `mktemp -d` 建一个本次专用临时目录，供步骤 4 存放 source/candidate；`EMBEDDED-PASS` 或安全报告失败后删除；若校验状态无法安全恢复，保留并报告路径；
- 跳过目标定位、baseline 编译、写回、写后编译与独立收尾；只执行步骤 2–4（候选生成、语言审计、fidelity 校验）；
- 向 polisher 与 auditors 传 `POLISH_AUTOMATED_LANGUAGE_ONLY`，使全部 protected-content 规则继续生效；
- 向调用方返回完整候选、原/新字数、语言审计状态、术语合同状态与 fidelity 状态，编译报告为 `N/A`；
- 不回调调用方、不递归调用 /polish、不创建持久产物，也不把嵌入调用视为编辑任何项目文件的授权。

嵌入失败时把控制权交还调用方，不展示也不写入候选。若修复需要理论、构念、估计量或其他实质选择，返回 `FAIL-BLOCKED`，不得当作语言问题处理。

### 空洞表述预检（仅嵌入模式的 Results / Discussion）

**定义**：熟悉该领域、但不熟悉建模或估计软件的读者，读一遍后仍无法说出"谁（主体/单位）、什么结果或过程、方向如何、相对于什么比较"，因为句子的主要结论由模型内部对象、符号或谓词承载——这类句子是"空洞表述"（只有符号没有含义）。

**信号词来源**：读取项目所用 analysis profile 的"空洞表述信号"小节：

1. profile 名称取自项目合同 `CLAUDE.md` 的"方法 profile"字段；缺失时取 `structure/0_global/analysis_plan.md` 状态行的 `profile: <name>`；
2. 读取 `~/.claude/skills/analysis/profiles/<name>.md` 的"空洞表述信号"小节；
3. 找不到对应 profile 文件或小节时，改用 `~/.claude/skills/analysis/profiles/_generic.md` 的同名小节，并在返回给调用方的状态中提醒"未找到 profile <name>，已使用 _generic"；`_generic.md` 也不可用时，只按上面的定义判断，并同样提醒。不因此停止流程。

信号词只是线索，不是全局禁用词：Methodology 中的定义与紧凑的技术限定语照常润色。不得在 polish 内把空洞句"翻译"成实质句——这可能改变估计量、条件、时间范围或命题边界。发现空洞表述时返回：

`FAIL-BLOCKED: SOURCE-OPAQUE — <exact sentence>; missing/obscured reader-facing elements: <actor/unit, outcome/process, direction, comparator>. Caller must rewrite the semantic source.`

调用方须先写出"实质在前"的语义源文本，并核对它与 results_register 中对应条目的含义一致，才可重新提交。若源文本已清楚、模型内部用语只是限定语，则正常继续。

## Workflow

### 1. 定位目标（独立模式）

1. 读取项目合同 `CLAUDE.md`，获得 main TeX、target journal 和编译命令。
2. 接受 section title、exact selected passage 或可唯一匹配的 LaTeX block。除非 section title 能唯一定位，否则少于 50 characters 的输入停止。
3. section 定位使用 `~/.claude/skills/shared/tex_section.py`：先用 `mktemp -d` 创建临时目录，再运行 `section-tree` 与 `match-section`，显式传入 `--output "$tmp/_section_tree.json"` 和 `--output "$tmp/_section_match.json" --require-unique`；不得在项目中创建 section JSON、`final.md` 或 polish 工作目录。helper 返回的 match 只是候选，不是唯一性证明；枚举同一匹配优先级的全部标题，只有一个候选时才继续。
4. 捕获 exact source block。可读取相邻上下文判断 transition，并读取 manuscript 中正式定义目标所用理论、构念、主体、时期、估计量和缩写的位置；结合上文"术语表"组装本次术语合同。editable scope 不得越出该 block。
5. project-connected 目标先编译一次未修改的 manuscript，检查 baseline log 中的 LaTeX errors、undefined citations/references、duplicate labels、`Float too large` 和 `Emergency stop`。存在任一问题则停止润色，因为无法区分写回后的 regression 与既有故障。

raw text 不对应项目文件时，跳过 source matching、baseline 编译、写回和写后编译；执行相同的 language / fidelity gates；未给期刊时按 general academic English 处理，只返回文本，编译报告为 `N/A`。

### 2. 生成候选

嵌入模式的 Results / Discussion 输入，先完成空洞表述预检；失败立即交还控制权，不生成、不展示候选，也不得因 fidelity 保持而给出 `EMBEDDED-PASS`。

调用一个 `language-polisher`，提供：

- mode token `POLISH_AUTOMATED_LANGUAGE_ONLY`；
- exact source block、section title 和 position；
- target journal；
- language-only scope 与全部 protected-content rules；
- 术语合同（首选术语、需区分的含义、不得混用的近义词、用户保护片段），如有；
- hyphenated-compound policy 与 `MANUSCRIPT-ECONOMY.md` 的绝对路径，以及"不得新增防御性限定"的禁令；
- 默认 word-count tolerance ±10%。

输出必须包含：一个完整非空的 `latex` code block、简短的内部 Change Summary、policy 要求的 Hyphenated Compound Ledger、candidate word count。解析失败时只重试一次输出协议；再次失败为 `FAIL-BLOCKED`。

### 3. 并行语言审计

对同一 source、candidate、ledger 与术语合同并行调用三个 `language-auditor`，每次都传入 `POLISH_AUTOMATED_LANGUAGE_ONLY`：

- Group 1：grammar and sentence mechanics；
- Group 2：structural language patterns、dashes 和 lexical hyphenation；
- Group 3：terminology、reference clarity、consistency 和 local flow。

Group 3 必须对照所给术语合同，而不是只以最近一次出现为准。使用了不得混用的近义词、改变理论角色或合并了需区分的构念，即使语法正确，也记为 `SOURCE-DRIFT`。

Auditors 不审查研究逻辑，不建议修改 protected content。每条 issue 必须包含 location、Exact、Replacement、confidence 和 semantic-risk。主 agent 只自动应用 `HIGH` confidence、`semantic_risk: no`、其 `Exact` 能在当前 candidate 中唯一匹配、且 Replacement 不与其他已接受修复重叠或冲突的建议。相同建议去重；冲突时保留 polisher candidate。其余保留原文，不询问用户。

每个 auditor 先比较 source 与 candidate：scope、modality、causality、temporal meaning、construct meaning、claim strength 或 protected artifact 的附着关系任何漂移，以 `SOURCE-DRIFT` 报告并给出 source 中的 exact restoration；主 agent 必须先恢复。

合并已接受建议并恢复 drift 后，对 merged candidate 再并行运行一次三个 auditor。任一轮中某个输出格式错误，只允许该 auditor 修复一次 output protocol；第二次仍错为 `FAIL-BLOCKED`。final audit 后不再自动应用新建议；final audit 存在 `SOURCE-DRIFT` 或仍未修复的 `HIGH`、`semantic_risk: no` defect 时阻断写回。MEDIUM / LOW 的风格偏好不阻断，也不开启开放式审稿循环。

### 4. Fidelity gate

将 source 与 final candidate 写入临时目录，执行：

```bash
python3 ~/.claude/skills/polish/scripts/validate_fidelity.py \
  --before <source.tex> --after <candidate.tex> --max-word-change 0.10
```

必须通过 citations、references、labels、headings、environment order、protected table/figure environments、captions、footnotes、math、numbers、acronyms、protected identifiers、paragraph count、brace balance 和 word-count tolerance。

失败时仅允许同一 polisher 做一次 fidelity repair；随后完整重复步骤 3 的有界审计序列并重跑 validator。仍失败则不写入。

嵌入模式到此把已校验的候选返回调用方，跳过步骤 5–6；调用方须在展示或写入前运行自己的语义 / 技术回归审计。

### 5. 自动写回与编译（独立模式）

全部 gates 通过后：

1. 用 Edit 工具 仅替换捕获的 source block；
2. 立即运行项目要求的 LaTeX 编译；
3. 检查 LaTeX errors、undefined citations/references、duplicate labels、`Float too large` 和 `Emergency stop`。

编译失败时只恢复本次捕获的 exact source block（同样用 Edit 工具 ），不使用 `git restore` 等大范围回滚；随后重新编译一次确认恢复成功，并报告 `FAIL-BLOCKED`。exact restoration 或 recovery 编译失败时，明确报告并停止。

### 6. 收尾（独立模式）

只报告：target file/section、原/新字数、语言审计结果、术语合同状态、fidelity 校验结果、编译结果、是否完成自动写回或已在失败后恢复、git actions（`none`）、未解决的 blocker。

不展示 diff，不保留持久 polish 产物。只有在 `PASS` 或确认恢复成功后，才清理本次创建的临时目录；若 restoration 或 recovery 编译失败，保留 source snapshot 并报告其绝对路径。

## 通过标准

独立 `PASS`：英文自然度提升、protected content 完全不变、修改未越出授权范围、manuscript 无新增编译硬错误。

`EMBEDDED-PASS`：所给候选满足相同的语言、术语与 fidelity 条件；编译与写回为 `N/A`，由调用方负责。未通过空洞表述预检的 Results / Discussion 源文本不得获得 `EMBEDDED-PASS`，即使语法正确且零修改候选能通过 fidelity 校验。
