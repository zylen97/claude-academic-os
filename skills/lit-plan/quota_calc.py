#!/usr/bin/env python3
"""
quota_calc.py — 文献检索配额计算（lit-plan §2）

根据各方向的功能标签分配和总预算，计算每个方向的检索配额。
替代主 Agent 的心算，避免算术错误。

用法:
    # 纯英文模式
    python3 quota_calc.py --directions directions.json --budget 360

    # 中英文双轨模式
    python3 quota_calc.py --directions directions.json --budget-wos 200 --budget-cnki 100

输入 JSON 格式 (directions.json):
    {
      "directions": [
        {
          "id": 1,
          "name": "装配式建筑供应链管理",
          "tags": ["BG", "LR", "GAP-RQ1", "DISC-RQ1"],
          "priority": "P1",
          "direction_type": "corpus",
          "actual_hits": 240,
          "query_status": "PASS",
          "sample_size": 20,
          "sample_relevant": 13,
          "sample_precision": 0.65
        },
        ...
      ]
    }

输出:
    1. stdout 结构化摘要（供主 Agent 校验）
    2. 写入 _quota_result.json（供后续步骤使用）
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# 标签 Pool 目标（常量）
# ---------------------------------------------------------------------------

TAG_POOL_TARGETS = {
    "BG": 50,
    "LR": 150,
    "METHOD": 60,  # METHOD-基础 + METHOD-先例 共享
}

# GAP-RQx 和 DISC-RQx 的目标是动态的，按 RQ 数量均分
GAP_TOTAL = 75
DISC_TOTAL = 65

MIN_QUOTA = 20


def normalize_tag(tag: str) -> str:
    """将具体标签归一化到 Pool 目标的 key。
    METHOD-基础 / METHOD-先例 → METHOD
    GAP-RQ1 / GAP-RQ2 → GAP（统一处理）
    DISC-RQ1 / DISC-RQ2 → DISC（统一处理）
    """
    if tag.startswith("METHOD"):
        return "METHOD"
    if tag.startswith("GAP"):
        return "GAP"
    if tag.startswith("DISC"):
        return "DISC"
    return tag


def get_pool_targets(all_tags: set[str]) -> dict[str, int]:
    """根据实际出现的标签，构建 Pool 目标字典。"""
    targets = dict(TAG_POOL_TARGETS)

    # 统计 RQ 数量
    gap_rqs = sorted({t for t in all_tags if t.startswith("GAP-RQ")})
    disc_rqs = sorted({t for t in all_tags if t.startswith("DISC-RQ")})

    # GAP 和 DISC 按 RQ 数量均分目标
    if gap_rqs:
        targets["GAP"] = GAP_TOTAL
    if disc_rqs:
        targets["DISC"] = DISC_TOTAL

    return targets


def calculate_quotas(directions: list[dict], total_budget: int, min_quota: int | None = None) -> dict:
    """
    核心计算逻辑：
    1. tag_share[标签, 方向] = 标签Pool目标 / 服务该标签的方向数
    2. raw_demand[方向] = Σ tag_share（对该方向服务的所有标签求和）
    3. quota[方向] = round(TOTAL_BUDGET × raw_demand / Σ raw_demand)
    4. 保底：每个方向至少 min_quota 篇（默认 20）
    """
    min_quota = MIN_QUOTA if min_quota is None else min_quota
    # 收集所有标签
    all_tags = set()
    for d in directions:
        all_tags.update(d["tags"])

    pool_targets = get_pool_targets(all_tags)

    # 第1步：统计每个归一化标签被多少个方向服务
    tag_direction_count: dict[str, int] = defaultdict(int)
    for d in directions:
        seen_norm = set()
        for tag in d["tags"]:
            norm = normalize_tag(tag)
            if norm not in seen_norm:
                tag_direction_count[norm] += 1
                seen_norm.add(norm)

    # 第2步：计算每个方向的 raw_demand
    raw_demands = {}
    tag_share_details = {}  # 用于展示计算过程

    for d in directions:
        did = d["id"]
        seen_norm = set()
        demand = 0.0
        shares = {}
        for tag in d["tags"]:
            norm = normalize_tag(tag)
            if norm in seen_norm:
                continue  # 同方向同归一化标签只算一次
            seen_norm.add(norm)
            target = pool_targets.get(norm, 0)
            count = tag_direction_count.get(norm, 1)
            share = target / count
            demand += share
            shares[norm] = round(share, 1)
        raw_demands[did] = demand
        tag_share_details[did] = shares

    # 第3步：等比缩放到总预算
    total_demand = sum(raw_demands.values())
    if total_demand == 0:
        print("ERROR: Total raw demand is 0, cannot calculate quotas", file=sys.stderr)
        sys.exit(1)

    # 第4步：保底 min_quota。需要迭代固定低配额方向；一次性重缩放会把
    # 原本未触底的方向重新压到 min_quota 以下，导致 VERIFY 失败。
    quotas = {}
    remaining = set(raw_demands)
    remaining_budget = total_budget

    if total_budget < min_quota * len(raw_demands):
        # 极端情况：预算不足以满足全方向保底。调用方应传 --min-quota
        # 降低保底；这里仍给出确定性均分并让 verify 暴露该问题。
        per_dir = max(1, total_budget // len(raw_demands))
        remainder = total_budget - per_dir * len(raw_demands)
        order = sorted(raw_demands, key=lambda did: raw_demands[did], reverse=True)
        quotas = {did: per_dir for did in raw_demands}
        for did in order[:remainder]:
            quotas[did] += 1
        print(
            f"WARNING: min quota sum ({min_quota * len(raw_demands)}) exceeds "
            f"budget ({total_budget}); pass --min-quota or per-track min quota to lower the floor.",
            file=sys.stderr,
        )
    else:
        while remaining:
            rem_demand = sum(raw_demands[did] for did in remaining)
            tentative = {
                did: round(remaining_budget * raw_demands[did] / rem_demand)
                for did in remaining
            }
            below_min = [did for did, q in tentative.items() if q < min_quota]
            if not below_min:
                quotas.update(tentative)
                break
            for did in below_min:
                quotas[did] = min_quota
                remaining.remove(did)
                remaining_budget -= min_quota

        # 最终调整：确保总和精确等于预算（处理四舍五入误差），且不破坏保底。
        diff = total_budget - sum(quotas.values())
        while diff > 0:
            max_did = max(quotas, key=lambda did: (raw_demands[did], quotas[did]))
            quotas[max_did] += 1
            diff -= 1
        while diff < 0:
            candidates = [did for did, q in quotas.items() if q > min_quota]
            if not candidates:
                break
            max_did = max(candidates, key=lambda did: (quotas[did], raw_demands[did]))
            quotas[max_did] -= 1
            diff += 1

    # 内部分层
    tiers = {}
    for did, q in quotas.items():
        core = math.ceil(q * 0.25)
        important = math.ceil(q * 0.40)
        backup = q - core - important
        if backup < 0:
            backup = 0
            important = q - core
        tiers[did] = {"core": core, "important": important, "backup": backup}

    # 标签覆盖检查
    coverage = {}
    for norm_tag in pool_targets:
        covering = []
        for d in directions:
            norm_tags = {normalize_tag(t) for t in d["tags"]}
            if norm_tag in norm_tags:
                covering.append(d["id"])
        coverage[norm_tag] = covering

    return {
        "quotas": quotas,
        "tiers": tiers,
        "raw_demands": {k: round(v, 1) for k, v in raw_demands.items()},
        "tag_share_details": tag_share_details,
        "pool_targets": pool_targets,
        "coverage": coverage,
        "total_budget": total_budget,
    }


def verify(
    result: dict,
    directions: list[dict],
    min_quota: int | None = None,
    track: str = "wos",
) -> list[str]:
    """内建校验，返回错误列表（空 = PASS）。"""
    errors = []
    min_quota = MIN_QUOTA if min_quota is None else min_quota
    quotas = result["quotas"]
    total_budget = result["total_budget"]
    coverage = result["coverage"]
    tiers = result["tiers"]

    # 1. 总和校验
    actual_sum = sum(quotas.values())
    if actual_sum != total_budget:
        errors.append(f"SUM_MISMATCH: Σ配额={actual_sum}, 预算={total_budget}")

    # 2. 最低配额校验
    for did, q in quotas.items():
        if q < min_quota:
            errors.append(f"MIN_VIOLATION: 方向{did} 配额={q} < {min_quota}")

    # 3. 标签覆盖校验
    for tag, dirs in coverage.items():
        if len(dirs) == 0:
            errors.append(f"TAG_UNCOVERED: 标签 {tag} 未被任何方向覆盖")

    # 4. 分层一致性校验
    for did, q in quotas.items():
        t = tiers[did]
        tier_sum = t["core"] + t["important"] + t["backup"]
        if tier_sum != q:
            errors.append(f"TIER_MISMATCH: 方向{did} 配额={q}, 分层合计={tier_sum}")

    # 5. 每个方向至少有标签
    for d in directions:
        if not d.get("tags"):
            errors.append(f"NO_TAGS: 方向{d['id']} 没有功能标签")

    # 6. WoS 自动校准后的容量与质量门。未提供 actual_hits 时视为
    # provisional plan，不在本脚本里伪造命中量；提供后必须通过。
    if track == "wos":
        passing_statuses = {"PASS", "PASS_TRUNCATE_1000"}
        for d in directions:
            did = d["id"]
            if d.get("direction_type", "corpus") == "targeted_probe":
                errors.append(
                    f"PROBE_HAS_QUOTA: 方向{did} 是 targeted_probe，不应进入正式配额计算"
                )
                continue
            actual_hits = d.get("actual_hits", d.get("wos_actual_hits"))
            if actual_hits is None:
                continue
            try:
                actual_hits = int(actual_hits)
            except (TypeError, ValueError):
                errors.append(f"INVALID_HITS: 方向{did} actual_hits={actual_hits!r}")
                continue
            quota = quotas[did]
            if actual_hits < quota:
                errors.append(
                    f"CAPACITY_VIOLATION: 方向{did} 实际命中={actual_hits} < 配额={quota}"
                )
            if actual_hits < 50:
                errors.append(
                    f"CORPUS_TOO_THIN: 方向{did} 实际命中={actual_hits} < 50；"
                    "应放宽、合并或降为 targeted_probe"
                )
            query_status = d.get("query_status")
            if query_status is None:
                errors.append(f"QUERY_STATUS_MISSING: 方向{did} 缺少 query_status")
            elif query_status not in passing_statuses:
                errors.append(
                    f"QUERY_NOT_FROZEN: 方向{did} query_status={query_status!r}"
                )
            sample_size = d.get("sample_size")
            if sample_size is None:
                errors.append(f"SAMPLE_SIZE_MISSING: 方向{did} 缺少 sample_size")
            else:
                try:
                    sample_size = int(sample_size)
                except (TypeError, ValueError):
                    errors.append(
                        f"INVALID_SAMPLE_SIZE: 方向{did} sample_size={sample_size!r}"
                    )
                else:
                    required_sample = min(20, actual_hits)
                    if sample_size < required_sample:
                        errors.append(
                            f"SAMPLE_TOO_SMALL: 方向{did} 抽样量={sample_size} "
                            f"< 冻结所需={required_sample}"
                        )
            precision = d.get("sample_precision")
            if precision is None:
                errors.append(f"PRECISION_MISSING: 方向{did} 缺少 sample_precision")
            else:
                try:
                    precision = float(precision)
                except (TypeError, ValueError):
                    errors.append(
                        f"INVALID_PRECISION: 方向{did} sample_precision={precision!r}"
                    )
                else:
                    if not 0 <= precision <= 1:
                        errors.append(
                            f"INVALID_PRECISION: 方向{did} sample_precision={precision}"
                        )
                    elif precision < 0.40:
                        errors.append(
                            f"LOW_PRECISION: 方向{did} 抽样相关率={precision:.0%} < 40%"
                        )

    return errors


def main():
    global MIN_QUOTA  # 允许小预算项目降低保底

    parser = argparse.ArgumentParser(description="Calculate literature search quotas")
    parser.add_argument("--directions", required=True,
                        help="JSON file with direction data")
    parser.add_argument("--budget", type=int, default=None,
                        help="Total budget for WoS-only mode (default: 360)")
    parser.add_argument("--budget-wos", type=int, default=None,
                        help="WoS budget (dual-budget mode)")
    parser.add_argument("--budget-cnki", type=int, default=None,
                        help="CNKI budget (dual-budget mode)")
    parser.add_argument("--output", default=None,
                        help="Output JSON path (default: same dir as input / _quota_result.json)")
    parser.add_argument("--min-quota", type=int, default=None,
                        help="Override MIN_QUOTA constant for all tracks (default: 20)")
    parser.add_argument("--min-quota-wos", type=int, default=None,
                        help="Override minimum per-direction quota for WoS track")
    parser.add_argument("--min-quota-cnki", type=int, default=None,
                        help="Override minimum per-direction quota for CNKI track")
    args = parser.parse_args()

    if args.min_quota is not None:
        MIN_QUOTA = args.min_quota

    # 判断模式
    dual_mode = args.budget_wos is not None and args.budget_cnki is not None
    if dual_mode:
        wos_budget = args.budget_wos
        cnki_budget = args.budget_cnki
        total_budget = wos_budget + cnki_budget
    else:
        total_budget = args.budget or 360
        wos_budget = total_budget
        cnki_budget = 0

    # 读取输入
    try:
        with open(args.directions, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Cannot read {args.directions}: {e}", file=sys.stderr)
        sys.exit(1)

    directions = data.get("directions", [])
    if not directions:
        print("ERROR: No directions found in input JSON", file=sys.stderr)
        sys.exit(1)

    wos_min_quota = args.min_quota_wos if args.min_quota_wos is not None else MIN_QUOTA
    cnki_min_quota = args.min_quota_cnki if args.min_quota_cnki is not None else MIN_QUOTA

    # 计算 WoS 配额
    wos_result = calculate_quotas(directions, wos_budget, min_quota=wos_min_quota)
    wos_errors = verify(
        wos_result, directions, min_quota=wos_min_quota, track="wos"
    )

    # 计算 CNKI 配额（双轨模式）
    cnki_result = None
    cnki_errors = []
    if dual_mode:
        cnki_result = calculate_quotas(directions, cnki_budget, min_quota=cnki_min_quota)
        cnki_errors = verify(
            cnki_result, directions, min_quota=cnki_min_quota, track="cnki"
        )

    # 输出 JSON
    output_path = args.output or str(Path(args.directions).parent / "_quota_result.json")
    output_data = {
        "total_budget": total_budget,
        "wos_budget": wos_budget,
        "cnki_budget": cnki_budget,
        "dual_mode": dual_mode,
        "directions": []
    }
    for d in directions:
        did = d["id"]
        wos_q = wos_result["quotas"][did]
        dir_entry = {
            "id": did,
            "name": d["name"],
            "tags": d["tags"],
            "priority": d.get("priority", "P2"),
            "raw_demand": wos_result["raw_demands"][did],
            "wos_quota": wos_q,
            "wos_tiers": wos_result["tiers"][did],
        }
        for field in (
            "direction_type",
            "actual_hits",
            "wos_actual_hits",
            "query_status",
            "sample_size",
            "sample_relevant",
            "sample_precision",
            "final_ris",
        ):
            if field in d:
                dir_entry[field] = d[field]
        if dual_mode:
            cnki_q = cnki_result["quotas"][did]
            dir_entry["cnki_quota"] = cnki_q
            dir_entry["cnki_tiers"] = cnki_result["tiers"][did]
            dir_entry["quota"] = wos_q + cnki_q
        else:
            dir_entry["cnki_quota"] = 0
            dir_entry["quota"] = wos_q
        output_data["directions"].append(dir_entry)
    output_data["pool_targets"] = wos_result["pool_targets"]
    output_data["coverage"] = {k: [f"D{x}" for x in v] for k, v in wos_result["coverage"].items()}


    # ===== stdout 结构化摘要 =====
    print("=== QUOTA CALCULATION ===")
    if dual_mode:
        print(f"Mode: dual (WoS={wos_budget} + CNKI={cnki_budget} = {total_budget})")
    else:
        print(f"Mode: WoS-only (budget={wos_budget})")
    print(f"Directions: {len(directions)}")
    print()

    # Pool 目标
    print("Pool targets:")
    for tag, target in sorted(wos_result["pool_targets"].items()):
        print(f"  {tag}: {target}")
    print()

    # 计算过程
    if dual_mode:
        print("| 方向 | 服务标签 | WoS配额 | CNKI配额 | 合计 | WoS(核/重/备) | CNKI(核/重/备) |")
        print("|:-----|:---------|:------:|:-------:|:---:|:------------:|:-------------:|")
    else:
        print("| 方向 | 服务标签 | raw_demand | 配额 | 核心 | 重要 | 备选 |")
        print("|:-----|:---------|:---------:|:----:|:----:|:----:|:----:|")
    for d in directions:
        did = d["id"]
        tags_str = "+".join(sorted({normalize_tag(t) for t in d["tags"]}))
        wos_q = wos_result["quotas"][did]
        wt = wos_result["tiers"][did]
        if dual_mode:
            cnki_q = cnki_result["quotas"][did]
            ct = cnki_result["tiers"][did]
            print(f"| D{did} {d['name'][:12]} | {tags_str} | {wos_q}篇 | {cnki_q}篇 | {wos_q+cnki_q}篇 | ≤{wt['core']}/{wt['important']}/{wt['backup']} | ≤{ct['core']}/{ct['important']}/{ct['backup']} |")
        else:
            rd = wos_result["raw_demands"][did]
            print(f"| D{did} {d['name'][:12]} | {tags_str} | {rd} | {wos_q}篇 | ≤{wt['core']} | ≤{wt['important']} | ≤{wt['backup']} |")
    if dual_mode:
        tw = sum(wos_result["quotas"].values())
        tc = sum(cnki_result["quotas"].values())
        print(f"| **合计** | | **{tw}篇** | **{tc}篇** | **{tw+tc}篇** | | |")
    else:
        print(f"| **合计** | | | **{sum(wos_result['quotas'].values())}篇** | | | |")
    print()

    # 标签覆盖
    print("Tag coverage:")
    for tag, dirs in sorted(wos_result["coverage"].items()):
        status = "✅" if dirs else "❌"
        print(f"  {tag}: {status} ({len(dirs)} directions: {', '.join(f'D{d}' for d in dirs)})")
    print()

    # 校验结果
    all_errors = wos_errors + [f"[CNKI] {e}" for e in cnki_errors]
    if all_errors:
        # FAIL 时不写 _quota_result.json，避免覆盖上一次通过的配额
        print("=== VERIFY: FAIL ===")
        for e in all_errors:
            print(f"  ❌ {e}")
        print(f"未写入 {output_path}")
        sys.exit(1)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("=== VERIFY: PASS ===")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
