#!/usr/bin/env python3
"""文献条线状态（lit-workflow）：扫描 structure/2_literature/，生成/更新 lit_status.md。

子命令
  scan  [--check screen|review|tag|pool|final] [--no-write] [--json]
        扫描文件、重写状态表；--check 指定"准备开始的阶段"，存在阻断时退出码 2。
  record-screen --direction N --source S --method TEXT --before X --after Y --run-dir P [--backup P]
        在「筛选记录」追加一行（lit-screen 的 finalize_screen.py 会自动调用）。
  mark --direction N --stage review|tag --state FAILED|SKIPPED|CLEARED [--note TEXT]
        在「失败与跳过记录」追加一行。SKIPPED 只能在用户确认跳过后写入。

公共参数 --project-root（默认当前目录；语料目录为 <root>/structure/2_literature）。

阻断（规格 §3.3，只用于真实研究风险）
  screen/review：无检索计划；计划方向缺少输入；CNKI .enw 未转换；RIS 损坏（TY≠ER 或 0 条）
  tag：计划方向没有 review 报告且未标 FAILED/SKIPPED
  pool：计划方向没有 tag 副本且未确认跳过；存在未确认跳过的 FAILED
  final：pool 产物缺失；master_report.md 的 JUDGE 占位符 ≠ 0；文献池（literature_manifest.json）的键不在 master.bib
        （完整的池文件/manifest/bib 一致性校验由 lit-pool 的 finalize_pool.py --check-only 负责）
提醒（不阻断）：文件名不规范、上游比下游新、计划外方向、配额与计划不一致、筛选记录与当前篇数不符。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _cand in (_HERE.parent / "shared", _HERE.parent.parent / "_academic-shared" / "scripts"):
    if (_cand / "lit_common.py").is_file():
        sys.path.insert(0, str(_cand))
        break
import lit_common  # noqa: E402

STATUS_FILE = "lit_status.md"
POOL_GROUPS = lit_common.POOL_FILES
STAGES = ("screen", "review", "tag", "pool", "final")
SCREEN_HEAD = "## 筛选记录"
MARK_HEAD = "## 失败与跳过记录"
SCREEN_LINE = re.compile(
    r"^- (\d{4}-\d{2}-\d{2}) D(\d+)/(wos|cnki|openalex)：(.+?)，(\d+) → (\d+)(.*)$")
MARK_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) D(\d+) (review|tag) (FAILED|SKIPPED|CLEARED)(?:：(.*))?$")
BIB_KEY = re.compile(r"^@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)


# ----------------------------------------------------------------- 路径与日志区

def lit_dir_of(root: Path) -> Path:
    return root / "structure" / "2_literature"


def read_logs(lit_dir: Path) -> tuple[list[str], list[str]]:
    """返回 (筛选记录行, 失败与跳过记录行)，保持文件中顺序。"""
    path = lit_dir / STATUS_FILE
    if not path.exists():
        return [], []
    screen, marks, current = [], [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = {SCREEN_HEAD: screen, MARK_HEAD: marks}.get(line.strip())
            continue
        if current is not None and line.startswith("- ") and line.strip() != "- 无":
            current.append(line.rstrip())
    return screen, marks


def latest_screens(lines: list[str]) -> dict[tuple[int, str], dict]:
    out: dict[tuple[int, str], dict] = {}
    for line in lines:
        m = SCREEN_LINE.match(line)
        if m:
            out[(int(m.group(2)), m.group(3))] = {
                "date": m.group(1), "method": m.group(4),
                "before": int(m.group(5)), "after": int(m.group(6)),
            }
    return out


def latest_marks(lines: list[str]) -> dict[tuple[int, str], dict]:
    out: dict[tuple[int, str], dict] = {}
    for line in lines:
        m = MARK_LINE.match(line)
        if m:
            key = (int(m.group(2)), m.group(3))
            if m.group(4) == "CLEARED":
                out.pop(key, None)
            else:
                out[key] = {"date": m.group(1), "state": m.group(4), "note": m.group(5) or ""}
    return out


# ----------------------------------------------------------------- 计划与配额

def read_plan(lit_dir: Path) -> tuple[dict[int, str], list[int]]:
    """literature_search_plan.md：优先「## 方向表」，回退「## 方向N：名称」标题。返回 (名称, 方向号)。"""
    path = lit_dir / "literature_search_plan.md"
    if not path.exists():
        return {}, []
    names: dict[int, str] = {}
    in_table = False
    text = path.read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        if line.startswith("## "):
            in_table = line.strip().startswith("## 方向表")
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            m = re.fullmatch(r"D?(\d+)", cells[0]) if cells else None
            if m and len(cells) > 1:
                names[int(m.group(1))] = cells[1]
    if not names:
        for m in re.finditer(r"(?m)^##\s*方向\s*(\d+)\s*[：:]\s*(.+?)\s*$", text):
            names[int(m.group(1))] = m.group(2)
    return names, sorted(names)


def read_quota(lit_dir: Path) -> tuple[dict[int, dict] | None, str | None]:
    path = lit_dir / "_quota_result.json"
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        out = {}
        for row in data.get("directions", []):
            if row.get("direction_type", "corpus") != "corpus":
                continue
            out[int(row["id"])] = {
                "name": row.get("name", ""),
                "wos": int(row.get("wos_quota", row.get("quota", 0)) or 0),
                "cnki": int(row.get("cnki_quota", 0) or 0),
            }
        return out, None
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return None, f"_quota_result.json 无法解析：{exc}"


# ----------------------------------------------------------------- 产物读取

def count_report_rows(path: Path) -> int:
    """报告三级表格中的论文行数（与 lit-review/lit-tag 共用 lit_common 的解析）。"""
    try:
        return len(lit_common.report_papers(path))
    except (OSError, ValueError):
        return 0


def manifest_papers(path: Path) -> list[dict] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    papers = data.get("papers") if isinstance(data, dict) else data
    return papers if isinstance(papers, list) else None


def paper_directions(paper: dict) -> set[int]:
    raw = paper.get("directions", paper.get("direction", []))
    if not isinstance(raw, list):
        raw = [raw]
    out = set()
    for item in raw:
        m = re.search(r"\d+", str(item))
        if m:
            out.add(int(m.group()))
    return out


def bib_keys(path: Path) -> set[str]:
    return set(BIB_KEY.findall(path.read_text(encoding="utf-8"))) if path.exists() else set()


def mtime(path: Path) -> float:
    return path.stat().st_mtime


def converter_path() -> Path | None:
    for cand in (_HERE.parent / "lit-review", _HERE.parent.parent / "lit-review"):
        for sub in ("", "scripts"):
            p = cand / sub / "cnki_enw_to_ris.py"
            if p.is_file():
                return p
    return None


# ----------------------------------------------------------------- 扫描

@dataclass
class Status:
    lit_dir: Path
    rows: list[dict] = field(default_factory=list)
    blockers: dict[str, list[str]] = field(default_factory=lambda: {s: [] for s in STAGES})
    reminders: list[str] = field(default_factory=list)
    conversions: list[str] = field(default_factory=list)
    next_step: str = ""
    current: str = "review"
    pool_started: bool = False

    def block(self, stages: tuple[str, ...], msg: str) -> None:
        for s in stages:
            if msg not in self.blockers[s]:
                self.blockers[s].append(msg)


def scan(root: Path) -> Status:
    lit_dir = lit_dir_of(root)
    st = Status(lit_dir)
    if not lit_dir.is_dir():
        st.block(STAGES, f"语料目录不存在：{lit_dir}")
        st.next_step = "先运行 lit-plan"
        return st

    names, plan_ids = read_plan(lit_dir)
    quota, quota_err = read_quota(lit_dir)
    if quota_err:
        st.reminders.append(quota_err)
    if quota:
        planned = sorted(quota)
        if plan_ids and set(plan_ids) != set(planned):
            st.reminders.append(f"方向表 {plan_ids} 与 _quota_result.json {planned} 不一致；以配额文件为准")
        for d, q in quota.items():
            names.setdefault(d, q["name"])
    else:
        planned = plan_ids
    if not planned:
        st.block(STAGES, "找不到检索计划（literature_search_plan.md 方向表 / _quota_result.json）；先运行 lit-plan")

    inputs = lit_common.canonical_inputs(lit_dir)
    for p in lit_common.nonconforming_ris(lit_dir):
        st.reminders.append(f"文件名不规范，不会作为语料输入：{p.name}（应为 directionN_wos|cnki|openalex.ris）")
    enws: dict[int, Path] = {}
    for p in sorted(lit_dir.glob("*.enw")):
        d = lit_common.classify_enw(p)
        if d is None:
            st.reminders.append(f"文件名不规范的 CNKI 导出：{p.name}（应为 directionN_cnki.enw）")
        else:
            enws[d] = p
    for p in sorted(lit_dir.glob("direction*_report.md")):
        if lit_common.classify_report(p) is None:
            st.reminders.append(f"review 报告文件名不规范，不会被识别：{p.name}（应为 directionN_report.md）")

    screens = latest_screens(read_logs(lit_dir)[0])
    marks = latest_marks(read_logs(lit_dir)[1])
    conv = converter_path()
    manifest_path = lit_dir / "literature_manifest.json"
    papers = manifest_papers(manifest_path) if manifest_path.exists() else None
    if manifest_path.exists() and papers is None:
        st.reminders.append("literature_manifest.json 无法解析（无 papers 列表）")

    all_dirs = sorted(set(planned) | {d for d, _ in inputs} | set(enws))
    for d in all_dirs:
        in_plan = d in planned
        if planned and not in_plan:
            st.reminders.append(f"D{d} 不在检索计划中（计划外方向的输入不会被下游当作正式方向）")
        q = (quota or {}).get(d)
        required = set()
        if in_plan:
            if q is None or q["wos"] > 0:
                required.add("wos")
            if q is not None and q["cnki"] > 0:
                required.add("cnki")
        sources = sorted(required | {s for (dd, s) in inputs if dd == d} | ({"cnki"} if d in enws else set()),
                         key=lit_common.SOURCES.index)

        # 方向级阶段状态
        review_md = lit_dir / f"direction{d}_report.md"
        tagged_md = lit_dir / "tagged_reports" / f"direction{d}_report.md"
        rmark, tmark = marks.get((d, "review")), marks.get((d, "tag"))
        input_mtimes = [mtime(inputs[(d, s)]) for s in sources if (d, s) in inputs]
        notes_dir: list[str] = []

        if rmark:
            review_cell = "FAILED" if rmark["state"] == "FAILED" else "跳过（用户确认）"
        elif review_md.exists():
            n = count_report_rows(review_md)
            review_cell = f"{n} 篇" if n else "✅"
            if input_mtimes and max(input_mtimes) > mtime(review_md):
                review_cell += " ⚠️"
                notes_dir.append("输入比 review 报告新")
        else:
            review_cell = "—"
        review_skipped = bool(rmark and rmark["state"] == "SKIPPED")

        if review_skipped:
            tag_cell = "跳过"
        elif tmark:
            tag_cell = "FAILED" if tmark["state"] == "FAILED" else "跳过（用户确认）"
        elif tagged_md.exists():
            n = count_report_rows(tagged_md)
            tag_cell = f"{n} 篇" if n else "✅"
            if review_md.exists() and mtime(review_md) > mtime(tagged_md):
                tag_cell += " ⚠️"
                notes_dir.append("review 报告比 tag 副本新")
        else:
            tag_cell = "—"
        tag_skipped = review_skipped or bool(tmark and tmark["state"] == "SKIPPED")

        if papers is not None:
            n = sum(d in paper_directions(p) for p in papers if isinstance(p, dict))
            pool_cell = f"{n} 篇"
            if tagged_md.exists() and mtime(tagged_md) > mtime(manifest_path):
                pool_cell += " ⚠️"
                notes_dir.append("tag 副本比文献池新")
        else:
            pool_cell = "—"

        if in_plan:
            if not review_md.exists() and not rmark:
                st.block(("tag",), f"D{d} 尚无 review 报告（direction{d}_report.md）")
            if rmark and rmark["state"] == "FAILED":
                st.reminders.append(f"D{d} review FAILED：{rmark['note'] or '见失败记录'}；pool 前必须修复或由用户确认跳过")
                st.block(("pool", "final"), f"D{d} review FAILED 且未确认跳过")
            if tmark and tmark["state"] == "FAILED":
                st.block(("pool", "final"), f"D{d} tag FAILED 且未确认跳过")
            if not tag_skipped and not tagged_md.exists() and not tmark:
                st.block(("pool",), f"D{d} 尚无 tag 副本（tagged_reports/direction{d}_report.md）")

        for s in sources:
            path = inputs.get((d, s))
            notes = list(notes_dir)
            if path is None:
                count_cell = "—"
                if s == "cnki" and d in enws:
                    count_cell = "待转换"
                    cmd = (f"python3 {conv or '<lit-review>/cnki_enw_to_ris.py'} "
                           f"--input {enws[d]} --output {lit_dir / f'direction{d}_cnki.ris'}")
                    st.conversions.append(cmd)
                    st.block(("screen", "review"), f"D{d} CNKI 尚未转换：{enws[d].name} → direction{d}_cnki.ris")
                elif s in required:
                    st.block(("screen", "review"), f"D{d} 缺少输入文件 direction{d}_{s}.ris")
                    notes.append("缺少输入")
            else:
                n, errors = lit_common.check_ris(path)
                count_cell = str(n)
                if errors:
                    count_cell = f"{n} ❌"
                    st.block(("screen", "review"), f"RIS 损坏：{'; '.join(errors)}")
                if s == "cnki" and d in enws and mtime(enws[d]) > mtime(path):
                    notes.append(".enw 比 .ris 新 ⚠️")
                    st.reminders.append(f"D{d} {enws[d].name} 比 direction{d}_cnki.ris 新；如需重转，先把旧 .ris 移入 _archive/")
                if q and s in ("wos", "cnki") and q[s] > 0 and n > 1.5 * q[s] and (d, s) not in screens:
                    notes.append(f"{n / q[s]:.1f}× 配额 {q[s]}，建议筛选")
            scr = screens.get((d, s))
            if scr:
                screen_cell = f"{scr['method']} {scr['before']}→{scr['after']}（{scr['date']}）"
                if path is not None and lit_common.check_ris(path)[0] != scr["after"]:
                    screen_cell += " ⚠️"
                    notes.append("当前篇数与筛选记录不符")
                    st.reminders.append(f"D{d}/{s} 当前篇数与筛选记录不符（文件可能已被替换）")
            else:
                screen_cell = "未筛选" if path is not None else "—"
            st.rows.append({
                "direction": d, "name": names.get(d, ""), "source": s, "input": count_cell,
                "screen": screen_cell, "review": review_cell, "tag": tag_cell, "pool": pool_cell,
                "note": "；".join(notes) + ("" if in_plan else ("；" if notes else "") + "计划外"),
            })

    _check_final(st, lit_dir, papers, manifest_path)
    reviewed = [d for d in planned if (lit_dir / f"direction{d}_report.md").exists() or (d, "review") in marks]
    tagged = [d for d in planned if (lit_dir / "tagged_reports" / f"direction{d}_report.md").exists()
              or (d, "tag") in marks or (d, "review") in marks]
    if st.blockers["review"] or len(reviewed) < len(planned) or not planned:
        st.current = "review"
        st.next_step = "修复输入（见阻断）" if st.blockers["review"] else "review（可先 screen）"
    elif len(tagged) < len(planned):
        st.current, st.next_step = "tag", "tag"
    elif st.blockers["pool"]:
        st.current, st.next_step = "pool", "处理 FAILED 方向（修复或由用户确认跳过）后再 pool"
    elif not st.pool_started or st.blockers["final"]:
        st.current, st.next_step = "final", "pool"
    else:
        st.current, st.next_step = "done", "完成（文献池可供下游使用）"
    st.reminders = list(dict.fromkeys(st.reminders))
    return st


def _check_final(st: Status, lit_dir: Path, papers: list[dict] | None, manifest_path: Path) -> None:
    """完成判定的要点（完整校验以 lit-pool 的 finalize_pool.py --check-only 为准）。"""
    pool_dir = lit_dir / "citation_pool"
    st.pool_started = pool_dir.exists() or manifest_path.exists()
    required = [pool_dir / f"{g}.md" for g in POOL_GROUPS] + [
        pool_dir / "master.bib", manifest_path, lit_dir / "master_report.md"]
    missing = [p.relative_to(lit_dir).as_posix() for p in required if not p.exists()]
    if missing:
        st.block(("final",), f"pool 产物缺失：{', '.join(missing)}")
    if st.pool_started and not (lit_dir / "method_landscape.md").exists():
        st.reminders.append("method_landscape.md 不存在")
    report = lit_dir / "master_report.md"
    judge = report.read_text(encoding="utf-8").count("JUDGE") if report.exists() else 0
    if judge:
        st.block(("final",), f"master_report.md 仍有 {judge} 处 JUDGE 占位符")
    if (pool_dir / "master.bib").exists() and papers is not None:
        bib = bib_keys(pool_dir / "master.bib")
        orphan = {str(p.get("citation_key")) for p in papers if isinstance(p, dict) and p.get("citation_key")} - bib
        if orphan:
            st.block(("final",), f"{len(orphan)} 个池内键不在 master.bib：{', '.join(sorted(orphan)[:8])}")
    if manifest_path.exists():
        newest_tag = max((mtime(p) for p in (lit_dir / "tagged_reports").glob("direction*_report.md")), default=0)
        if newest_tag > mtime(manifest_path):
            st.reminders.append("tag 副本比 literature_manifest.json 新：文献池可能需要重跑 pool")
    if (lit_dir / "tagged_reports").is_dir():
        for err in lit_common.compare_tagged_to_review(lit_dir):
            if not err.startswith("TAGGED_COPY_MISSING"):
                st.reminders.append(f"tag 副本与 review 报告不一致（上游已变，需重跑 tag）：{err}")


# ----------------------------------------------------------------- 输出

def render(st: Status, screen_lines: list[str], mark_lines: list[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    out = [
        "# 文献条线状态",
        "",
        f"> 生成时间：{now}｜由 lit-workflow 的 lit_status.py 扫描文件生成。状态表、阻断、提醒每次重写；"
        "「筛选记录」「失败与跳过记录」只追加。",
        f"> 下一步：{st.next_step}",
        "",
        "## 状态表",
        "",
        "review / tag / pool 是方向级结果，同一方向各来源行显示相同值；⚠️ = 上游文件比下游新（只提醒）。",
        "",
        "| 方向 | 名称 | 来源 | 输入篇数 | 筛选 | review | tag | pool | 备注 |",
        "|---|---|---|---:|---|---|---|---|---|",
    ]
    for r in st.rows:
        out.append(f"| D{r['direction']} | {r['name']} | {r['source']} | {r['input']} | {r['screen']} | "
                   f"{r['review']} | {r['tag']} | {r['pool']} | {r['note']} |")
    if not st.rows:
        out.append("| — | — | — | — | — | — | — | — | 无输入 |")
    out += ["", "## 阻断", ""]
    labels = {"screen": "screen/review 前", "review": "screen/review 前", "tag": "tag 前",
              "pool": "pool 前", "final": "完成判定"}
    order = ("review", "tag", "pool", "final", "done")
    shown = {"screen", "review"}
    if order.index(st.current) >= 1:
        shown.add("tag")
    if order.index(st.current) >= 2:
        shown.add("pool")
    if st.pool_started:
        shown.add("final")
    seen, any_block = set(), False
    for stage in (s for s in STAGES if s in shown):
        for msg in st.blockers[stage]:
            if msg in seen:
                continue
            seen.add(msg)
            any_block = True
            out.append(f"- [{labels[stage]}] {msg}")
    if not any_block:
        out.append("- 无")
    out += ["", "## 提醒", ""] + ([f"- {m}" for m in st.reminders] or ["- 无"])
    if st.conversions:
        out += ["", "待执行的 CNKI 转换：", ""] + [f"    {c}" for c in st.conversions]
    out += ["", SCREEN_HEAD, ""] + (screen_lines or ["- 无"])
    out += ["", MARK_HEAD, ""] + (mark_lines or ["- 无"])
    return "\n".join(out) + "\n"


def write_status(root: Path, st: Status | None = None) -> Status:
    lit_dir = lit_dir_of(root)
    st = st or scan(root)
    if lit_dir.is_dir():
        screen_lines, mark_lines = read_logs(lit_dir)
        tmp = lit_dir / f".{STATUS_FILE}.tmp"
        tmp.write_text(render(st, screen_lines, mark_lines), encoding="utf-8")
        tmp.replace(lit_dir / STATUS_FILE)
    return st


def _append_log(lit_dir: Path, head: str, line: str) -> None:
    screen_lines, mark_lines = read_logs(lit_dir)
    (screen_lines if head == SCREEN_HEAD else mark_lines).append(line)
    # 先写入日志区，再整体重算状态表
    path = lit_dir / STATUS_FILE
    body = render(Status(lit_dir, next_step="（待刷新）"), screen_lines, mark_lines)
    path.write_text(body, encoding="utf-8")


def record_screen(lit_dir: Path, *, direction: int, source: str, method: str, before: int, after: int,
                  run_dir: Path | str, backup: Path | str | None = None, day: str | None = None) -> None:
    lit_dir = Path(lit_dir)
    if source not in lit_common.SOURCES:
        raise ValueError(f"未知来源：{source}")
    method = method.replace("，", ",").replace("|", "/").strip() or "筛选"

    def _rel(p: Path | str) -> str:
        p = Path(p)
        try:
            return p.resolve().relative_to(lit_dir.resolve()).as_posix()
        except ValueError:
            return str(p)

    extra = f"（运行目录 {_rel(run_dir)}" + (f"；原文件备份 {_rel(backup)}" if backup else "") + "）"
    line = f"- {day or date.today().isoformat()} D{direction}/{source}：{method}，{before} → {after}{extra}"
    _append_log(lit_dir, SCREEN_HEAD, line)
    write_status(lit_dir.parent.parent)


def mark(lit_dir: Path, *, direction: int, stage: str, state: str, note: str = "") -> None:
    if stage not in ("review", "tag") or state not in ("FAILED", "SKIPPED", "CLEARED"):
        raise ValueError("stage 必须是 review|tag，state 必须是 FAILED|SKIPPED|CLEARED")
    note = note.replace("\n", " ").strip()
    line = f"- {date.today().isoformat()} D{direction} {stage} {state}" + (f"：{note}" if note else "")
    _append_log(Path(lit_dir), MARK_HEAD, line)
    write_status(Path(lit_dir).parent.parent)


# ----------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-"):
        argv.insert(0, "scan")
    p = argparse.ArgumentParser(description="文献条线状态：扫描并维护 structure/2_literature/lit_status.md")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--check", choices=STAGES, help="准备开始的阶段；该阶段有阻断时退出码 2")
    s.add_argument("--no-write", action="store_true", help="只打印，不写 lit_status.md")
    s.add_argument("--json", action="store_true")
    r = sub.add_parser("record-screen")
    r.add_argument("--direction", type=int, required=True)
    r.add_argument("--source", choices=lit_common.SOURCES, required=True)
    r.add_argument("--method", required=True)
    r.add_argument("--before", type=int, required=True)
    r.add_argument("--after", type=int, required=True)
    r.add_argument("--run-dir", required=True)
    r.add_argument("--backup")
    m = sub.add_parser("mark")
    m.add_argument("--direction", type=int, required=True)
    m.add_argument("--stage", choices=("review", "tag"), required=True)
    m.add_argument("--state", choices=("FAILED", "SKIPPED", "CLEARED"), required=True)
    m.add_argument("--note", default="")
    for sp in (s, r, m):
        sp.add_argument("--project-root", default=".")
    args = p.parse_args(argv)
    root = Path(args.project_root).expanduser().resolve()
    lit_dir = lit_dir_of(root)

    if args.cmd == "record-screen":
        record_screen(lit_dir, direction=args.direction, source=args.source, method=args.method,
                      before=args.before, after=args.after, run_dir=args.run_dir, backup=args.backup)
        print(f"已记录筛选：D{args.direction}/{args.source} {args.before} → {args.after}")
        return 0
    if args.cmd == "mark":
        mark(lit_dir, direction=args.direction, stage=args.stage, state=args.state, note=args.note)
        print(f"已记录：D{args.direction} {args.stage} {args.state}")
        return 0

    st = scan(root)
    if not args.no_write:
        write_status(root, st)
    if args.json:
        print(json.dumps({"next": st.next_step, "rows": st.rows, "blockers": st.blockers,
                          "reminders": st.reminders, "conversions": st.conversions},
                         ensure_ascii=False, indent=2))
    else:
        print(render(st, *read_logs(lit_dir)) if args.no_write or not lit_dir.is_dir()
              else (lit_dir / STATUS_FILE).read_text(encoding="utf-8"))
    if args.check:
        blockers = st.blockers[args.check]
        print(f"=== CHECK {args.check}: {'BLOCKED' if blockers else 'PASS'} ===")
        return 2 if blockers else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
