#!/usr/bin/env python3
"""已核验的 OpenAlex 文献 → direction{N}_openalex.ris（lit-workflow 补充入口）。

输入二选一：
  --json FILE [FILE ...]   OpenAlex work 对象 / work 列表 / {"results": [...]}（已人工核验）
  --doi DOI [DOI ...]      逐个按 DOI 调 OpenAlex API（每次请求同时带 api_key 与 mailto，
  --doi-file FILE          凭证经 lit_common.openalex_credentials 读取，不打印）

输出：<lit-dir>/direction{N}_openalex.ris（默认 lit-dir = structure/2_literature）
  每条记录含 TY/TI/AU/PY/DO/JO/AB（JO、AB 缺失时提醒），另写 SN/VL/IS/SP/EP/KW/UR/AN。
  缺 TI/AU/PY/DO 的记录直接报错，不写文件。写出后用 lit_common.check_ris 校验 TY = ER = 记录数。
  目标文件已存在时：--append 追加（按 DOI 去重，原记录原样保留）；--replace 先把旧文件移入
  <lit-dir>/_archive/<日期>/ 再写新文件；都不给则拒绝。
写完后需从 review 重新运行 lit-workflow；进入文献池之前不得引用这些文献。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _cand in (_HERE.parent / "shared", _HERE.parent.parent / "_academic-shared" / "scripts"):
    if (_cand / "lit_common.py").is_file():
        sys.path.insert(0, str(_cand))
        break
import lit_common  # noqa: E402

API = "https://api.openalex.org/works/"
SELECT = ("id,doi,title,display_name,publication_year,type,authorships,primary_location,"
          "locations,biblio,abstract_inverted_index,keywords,language")
TYPE_MAP = {
    "article": "JOUR", "review": "JOUR", "letter": "JOUR", "editorial": "JOUR", "erratum": "JOUR",
    "book": "BOOK", "book-chapter": "CHAP", "dissertation": "THES", "report": "RPRT",
    "preprint": "UNPB", "dataset": "DATA", "proceedings-article": "CPAPER",
}


def norm_doi(raw: str | None) -> str:
    if not raw:
        return ""
    doi = raw.strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.IGNORECASE)
    return doi.strip().lower()


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def abstract_text(inverted: dict | None) -> str:
    if not inverted:
        return ""
    slots: dict[int, str] = {}
    for word, positions in inverted.items():
        for pos in positions:
            slots[int(pos)] = word
    return clean(" ".join(slots[i] for i in sorted(slots)))


def ris_author(name: str) -> str:
    name = clean(name)
    if not name or "," in name:
        return name
    parts = name.split(" ")
    return name if len(parts) == 1 else f"{parts[-1]}, {' '.join(parts[:-1])}"


def source_of(work: dict) -> dict:
    for loc in [work.get("primary_location")] + list(work.get("locations") or []):
        if isinstance(loc, dict) and isinstance(loc.get("source"), dict) and loc["source"].get("display_name"):
            return loc["source"]
    host = work.get("host_venue")
    return host if isinstance(host, dict) else {}


def work_to_ris(work: dict) -> tuple[list[str], list[str], list[str]]:
    """返回 (RIS 行, 阻断错误, 提醒)。"""
    errors, warnings = [], []
    doi = norm_doi(work.get("doi"))
    title = clean(work.get("title") or work.get("display_name"))
    year = work.get("publication_year")
    authors = [ris_author((a.get("author") or {}).get("display_name") or a.get("raw_author_name") or "")
               for a in work.get("authorships") or [] if isinstance(a, dict)]
    authors = [a for a in authors if a]
    label = doi or work.get("id") or title[:60] or "(未知记录)"
    if not title:
        errors.append(f"{label}: 缺少标题")
    if not authors:
        errors.append(f"{label}: 缺少作者")
    if not isinstance(year, int):
        errors.append(f"{label}: 缺少出版年")
    if not doi:
        errors.append(f"{label}: 缺少 DOI")
    src = source_of(work)
    journal = clean(src.get("display_name"))
    abstract = abstract_text(work.get("abstract_inverted_index"))
    if not journal:
        warnings.append(f"{label}: 缺少期刊/来源名（JO）")
    if not abstract:
        warnings.append(f"{label}: 缺少摘要（AB），review 只能依据标题判断")

    lines = [f"TY  - {TYPE_MAP.get(str(work.get('type') or ''), 'GEN')}"]
    if title:
        lines.append(f"TI  - {title}")
    lines += [f"AU  - {a}" for a in authors]
    if isinstance(year, int):
        lines.append(f"PY  - {year}")
    if journal:
        lines.append(f"JO  - {journal}")
        lines.append(f"T2  - {journal}")
    issns = [clean(x) for x in (src.get("issn") or []) if clean(x)]
    if not issns and src.get("issn_l"):
        issns = [clean(src["issn_l"])]
    lines += [f"SN  - {x}" for x in dict.fromkeys(issns)]
    biblio = work.get("biblio") or {}
    for tag, key in (("VL", "volume"), ("IS", "issue"), ("SP", "first_page"), ("EP", "last_page")):
        if clean(biblio.get(key)):
            lines.append(f"{tag}  - {clean(biblio.get(key))}")
    if abstract:
        lines.append(f"AB  - {abstract}")
    for kw in work.get("keywords") or []:
        text = clean(kw.get("display_name") if isinstance(kw, dict) else kw)
        if text:
            lines.append(f"KW  - {text}")
    if work.get("language"):
        lines.append(f"LA  - {clean(work['language'])}")
    if doi:
        lines.append(f"DO  - {doi}")
        lines.append(f"UR  - https://doi.org/{doi}")
    if work.get("id"):
        lines.append(f"AN  - {clean(str(work['id']).rsplit('/', 1)[-1])}")
    lines.append("DB  - OpenAlex")
    lines.append("ER  - ")
    return lines, errors, warnings


def load_json_works(paths: list[str]) -> list[dict]:
    works: list[dict] = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            data = data["results"]
        works.extend(data if isinstance(data, list) else [data])
    bad = [w for w in works if not isinstance(w, dict)]
    if bad:
        raise ValueError("JSON 中存在非对象的 work 记录")
    return works


def fetch_by_doi(dois: list[str]) -> list[dict]:
    key, _mail = lit_common.openalex_credentials()
    works = []
    for doi in dois:
        url = API + "doi:" + urllib.parse.quote(doi, safe="/") + "?" + urllib.parse.urlencode(
            lit_common.openalex_params(select=SELECT))
        work = None
        for attempt in range(3):  # 网络抖动（如 SSL EOF）重试，404 不重试
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    work = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    raise ValueError(f"OpenAlex 中找不到 DOI：{doi}") from None
                last = f"HTTP {exc.code}"
            except Exception as exc:  # 任何错误信息都不得带出 api_key
                last = str(exc).replace(key, "[REDACTED]")
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
        if work is None:
            raise RuntimeError(f"OpenAlex 请求失败（DOI {doi}）：{last}")
        if norm_doi(work.get("doi")) != doi:
            raise ValueError(f"OpenAlex 返回的 DOI 与请求不符：请求 {doi}，返回 {work.get('doi')}")
        works.append(work)
    return works


def existing_dois(path: Path) -> set[str]:
    out = set()
    for rec in lit_common.split_ris_records(lit_common.read_text(path)):
        m = re.search(r"(?m)^DO  - (.+)$", rec)
        if m:
            out.add(norm_doi(m.group(1)))
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="已核验的 OpenAlex 记录 → direction{N}_openalex.ris")
    p.add_argument("--direction", type=int, required=True)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--json", nargs="+", help="已核验的 OpenAlex work JSON 文件")
    src.add_argument("--doi", nargs="+", help="DOI 列表（调用 OpenAlex API）")
    src.add_argument("--doi-file", help="每行一个 DOI 的文本文件")
    p.add_argument("--lit-dir", default="structure/2_literature")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--append", action="store_true", help="目标已存在时追加（按 DOI 去重）")
    mode.add_argument("--replace", action="store_true", help="目标已存在时先归档旧文件再重写")
    p.add_argument("--dry-run", action="store_true", help="只转换和校验，不写文件")
    args = p.parse_args(argv)

    lit_dir = Path(args.lit_dir).expanduser().resolve()
    if not lit_dir.is_dir():
        print(f"ERROR: 语料目录不存在：{lit_dir}", file=sys.stderr)
        return 1
    target = lit_dir / f"direction{args.direction}_openalex.ris"
    assert lit_common.classify_ris(target) == (args.direction, "openalex")
    if target.exists() and not (args.append or args.replace):
        print(f"ERROR: {target.name} 已存在；用 --append 追加或 --replace 归档后重写", file=sys.stderr)
        return 1

    try:
        if args.json:
            works = load_json_works(args.json)
        else:
            raw = args.doi or Path(args.doi_file).read_text(encoding="utf-8").split()
            dois = list(dict.fromkeys(d for d in (norm_doi(x) for x in raw) if d))
            if not dois:
                raise ValueError("没有可用的 DOI")
            works = fetch_by_doi(dois)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    seen = existing_dois(target) if (target.exists() and args.append) else set()
    blocks, errors, warnings, skipped = [], [], [], []
    for work in works:
        doi = norm_doi(work.get("doi"))
        if doi and doi in seen:
            skipped.append(doi)
            continue
        lines, errs, warns = work_to_ris(work)
        errors += errs
        warnings += warns
        if doi:
            seen.add(doi)
        blocks.append("\n".join(lines))
    if errors:
        print("ERROR: 以下记录未通过核验，未写任何文件：\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1
    if not blocks:
        print("没有新记录需要写入" + (f"（{len(skipped)} 条 DOI 已存在）" if skipped else ""))
        return 0

    new_text = "\n\n".join(blocks) + "\n"
    if target.exists() and args.append:
        old = lit_common.read_text(target).rstrip("\n")
        payload = old + "\n\n" + new_text
    else:
        payload = new_text
    expected = len(lit_common.split_ris_records(payload))

    tmp = lit_dir / f".{target.name}.tmp"
    tmp.write_text(payload, encoding="utf-8")
    count, errs = lit_common.check_ris(tmp)
    if errs or count != expected:
        tmp.unlink(missing_ok=True)
        print(f"ERROR: 生成的 RIS 校验失败：{errs or f'TY={count} ≠ 预期 {expected}'}", file=sys.stderr)
        return 1
    if args.dry_run:
        tmp.unlink(missing_ok=True)
        print(f"[dry-run] 将写入 {target}：共 {count} 条（新增 {len(blocks)}，跳过重复 {len(skipped)}）")
    else:
        if target.exists() and args.replace:
            archive = lit_dir / "_archive" / date.today().isoformat()
            archive.mkdir(parents=True, exist_ok=True)
            dest = archive / target.name
            if dest.exists():
                dest = archive / f"{target.stem}_{datetime.now().strftime('%H%M%S')}.ris"
            shutil.move(str(target), dest)
            print(f"旧文件已归档：{dest}")
        tmp.replace(target)
        print(f"已写入 {target}：共 {count} 条（新增 {len(blocks)}，跳过重复 {len(skipped)}），TY = ER = {count}")
    for w in warnings:
        print(f"提醒：{w}")
    print("下一步：从 review 重新运行 lit-workflow；进入文献池之前不得引用这些文献。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
