#!/usr/bin/env python3
"""
LLM 相关性批量筛选（lit-screen Step 3）

用法:
  python3 screen_llm.py <input_ris> --direction "方向描述" [--threads 20] [--run-dir DIR]

API key 只从进程环境变量 CHATANYWHERE_API_KEY 读取；--api-key 参数被拒绝。
输入可以是 canonical RIS，也可以是同一运行目录下的 xr_zone{N}.ris。
输出全部写入运行目录（输入在 _screen_runs/<run>/ 内时沿用该目录，否则新建）：
  - llm.ris           保留记录（retain + error_retain），原记录块有序子集
  - excluded.ris      被排除记录的原始块
  - decisions.jsonl   每条输入记录一行：ordinal / title / decision / reason / error
  - run.json          本次运行摘要（输入路径、方向、模型、各类计数）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from screen_xr import RUNS_DIRNAME, default_run_dir, parse_ris, write_ris  # noqa: E402

API_BASE = "https://api.chatanywhere.tech/v1"
MODEL = "gpt-4o-mini"

# 基于六非博 Literature Review Software 7B prompt 改进：允许方法论关联
SYSTEM_PROMPT = """你的任务是解读文献摘要，判断其是否与用户的研究观点相关。判断标准：
1. **主题相关**：摘要研究的行业、情境或问题与用户研究直接相关，标注为 1
2. **方法相关**：摘要使用的理论框架、模型或分析方法与用户研究相同或高度相似，标注为 1
3. **无关**：主题和方法均无关联，标注为 0
请仅基于摘要本身的信息进行判断。请严格按照以下格式提供结果：标注. 理由（中文）"""


def screen_one(index: int, title: str, abstract: str, direction: str, api_key: str) -> dict:
    """筛选单篇论文。返回 {index, relevant, reason} 或 {index, error}。"""
    user_msg = f"以下是用户感兴趣的研究观点：{direction}\n\n标题：{title}\n摘要：{abstract}"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            payload = json.dumps({
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0,
            }, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(
                f"{API_BASE}/chat/completions",
                data=payload,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                resp = json.loads(response.read().decode("utf-8"))
            answer = resp["choices"][0]["message"]["content"].strip()
            relevant, reason = _parse_answer(answer)
            return {"index": index, "relevant": relevant, "reason": reason}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                return {"index": index, "error": str(e)}
    return {"index": index, "error": "max retries exceeded"}


def _parse_answer(answer: str) -> tuple[bool, str]:
    """解析 '标注. 理由'。宁留勿删：格式异常默认保留。"""
    answer = answer.strip()
    match = re.match(r"^\s*([01])\s*[.。:：]\s*(.*)$", answer, re.DOTALL)
    if match:
        return match.group(1) == "1", match.group(2).strip()
    if answer.startswith("1"):
        return True, answer
    if answer.startswith("0"):
        return False, answer
    # "不相关" 含 "相关"，排除词必须优先
    if re.search(r"不相关|无关|标注[为:：]?\s*0", answer):
        return False, answer
    if re.search(r"标注[为:：]?\s*1|直接相关|方法相关|主题相关|高度相似|匹配", answer):
        return True, answer
    return True, f"[parse_fallback_retain] {answer}"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as handle:
            tmp_name = handle.name
            handle.write(text)
            handle.flush()
        Path(tmp_name).replace(path)
    except Exception:
        if tmp_name:
            Path(tmp_name).unlink(missing_ok=True)
        raise


def _redact(error: object, api_key: str) -> str:
    text = str(error)
    return text.replace(api_key, "[REDACTED]") if api_key else text


def _field(rec: dict, *tags: str) -> str:
    for tag in tags:
        value = rec.get(tag)
        if value:
            return " ".join(value) if isinstance(value, list) else value
    return ""


def resolve_run_dir(input_path: Path, run_dir: str | None) -> Path:
    if run_dir:
        out = Path(run_dir).expanduser().resolve()
    elif input_path.parent.parent.name == RUNS_DIRNAME:
        out = input_path.parent  # XR 结果所在的同一运行目录
    else:
        out = default_run_dir(input_path)
    if (out / "llm.ris").exists():
        raise ValueError(f"运行目录已有 LLM 结果，请换新目录：{out}")
    lit_dir = input_path.parent.parent.parent if input_path.parent.parent.name == RUNS_DIRNAME else input_path.parent
    if out == lit_dir.resolve():
        raise ValueError("运行目录不能是语料顶层目录")
    return out


def screen(ris_path: str, direction: str, threads: int = 20, run_dir: str | None = None) -> dict:
    api_key = os.environ.get("CHATANYWHERE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("需要通过 CHATANYWHERE_API_KEY 环境变量提供 API Key")
    if not direction.strip():
        raise ValueError("研究方向不能为空")
    if threads < 1:
        raise ValueError("threads 必须至少为 1")

    input_path = Path(ris_path).expanduser().resolve()
    records = parse_ris(input_path)
    total = len(records)
    if total == 0:
        raise ValueError(f"RIS contains no complete records: {input_path}")
    out_dir = resolve_run_dir(input_path, run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: dict[int, dict] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {}
        for i, rec in enumerate(records):
            title, abstract = _field(rec, "TI", "T1"), _field(rec, "AB", "N2")
            if not title and not abstract:
                results[i] = {"index": i, "relevant": True, "reason": "无标题和摘要，默认保留"}
                done += 1
                continue
            futures[executor.submit(screen_one, i, title, abstract, direction, api_key)] = i
        for f in as_completed(futures):
            try:
                result = f.result()
            except Exception as exc:  # 任何记录都不能从审计中消失
                result = {"index": futures[f], "error": _redact(exc, api_key)}
            results[result["index"]] = result
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  进度: {done}/{total}", file=sys.stderr)

    kept, removed, rows = [], [], []
    for i, rec in enumerate(records):
        r = results.get(i)
        error_text = ""
        if r is None:
            decision, reason, error_text = "error_retain", "筛选任务无返回，默认保留", "missing_worker_result"
        elif "error" in r:
            decision, reason, error_text = "error_retain", "API 调用失败，默认保留", _redact(r["error"], api_key)
        elif r["relevant"]:
            decision, reason = "retain", r.get("reason", "")
        else:
            decision, reason = "exclude", r.get("reason", "")
        (removed if decision == "exclude" else kept).append(rec)
        rows.append({
            "ordinal": i + 1,
            "title": _field(rec, "TI", "T1"),
            "decision": decision,
            "reason": reason,
            "error": error_text,
            "has_abstract": bool(_field(rec, "AB", "N2").strip()),
        })

    output_path = out_dir / "llm.ris"
    excluded_path = out_dir / "excluded.ris"
    audit_path = out_dir / "decisions.jsonl"
    if kept:
        write_ris(kept, output_path)
    write_ris(removed, excluded_path)
    _atomic_write_text(audit_path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))

    stats = {
        "input_path": str(input_path),
        "input": total,
        "relevant": sum(r["decision"] == "retain" for r in rows),
        "irrelevant": len(removed),
        "errors": sum(r["decision"] == "error_retain" for r in rows),
        "output": len(kept),
        "direction": direction,
        "model": MODEL,
        "run_dir": str(out_dir),
        "output_path": str(output_path) if kept else None,
        "excluded_output": str(excluded_path),
        "audit_output": str(audit_path),
    }
    _atomic_write_text(
        out_dir / "run.json",
        json.dumps({"created_at": datetime.now().isoformat(timespec="seconds"), **stats},
                   ensure_ascii=False, indent=2) + "\n",
    )
    stats["removed_titles"] = [_field(r, "TI", "T1") or "unknown" for r in removed[:30]]
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return stats


if __name__ == "__main__":
    if any(arg == "--api-key" or arg.startswith("--api-key=") for arg in sys.argv[1:]):
        print("错误: --api-key 已禁用；请仅通过 CHATANYWHERE_API_KEY 环境变量提供凭证", file=sys.stderr)
        sys.exit(2)
    parser = argparse.ArgumentParser(description="LLM 文献相关性筛选（只写运行目录）")
    parser.add_argument("ris_path", help="输入 RIS（canonical 或运行目录中的 xr_zone{N}.ris）")
    parser.add_argument("--direction", required=True, help="方向描述（取自 literature_search_plan.md）")
    parser.add_argument("--threads", type=int, default=20, help="并发线程数 (默认 20)")
    parser.add_argument("--run-dir", help="运行目录（默认：输入在 _screen_runs/<run>/ 内则沿用，否则新建）")
    args = parser.parse_args()
    if not os.environ.get("CHATANYWHERE_API_KEY", "").strip():
        print("错误: 需要 API Key，请通过 CHATANYWHERE_API_KEY 环境变量提供", file=sys.stderr)
        sys.exit(1)
    try:
        screen(args.ris_path, args.direction, args.threads, args.run_dir)
    except Exception as exc:
        print(f"错误: {_redact(exc, os.environ.get('CHATANYWHERE_API_KEY', ''))}", file=sys.stderr)
        sys.exit(1)
