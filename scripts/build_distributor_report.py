#!/usr/bin/env python3
"""Build a single-distributor performance report from Youzan order-item detail."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from build_weekly_tables import (  # noqa: E402
    add_user_percentiles,
    categorize_product,
    classify_user,
    clean_text,
    compute_user_rule_profile,
    distributor_action,
    distributor_judgement,
    distributor_reason,
    effective_mask,
    find_col,
    format_workbook,
    join_unique,
    latest_nonempty,
    money,
    read_table,
)


def match_distributor(series: pd.Series, query: str, exact: bool) -> pd.Series:
    target = query.strip().lower()
    values = series.fillna("").astype(str).str.strip().str.lower()
    if exact:
        return values == target
    return values.str.contains(target, regex=False, na=False)


def build_distributor_report(
    detail_path: Path,
    output_dir: Path,
    week_label: str,
    distributor_query: str,
    exact: bool = False,
) -> tuple[Path, Path]:
    raw = read_table(detail_path)
    raw.columns = [str(c).strip() for c in raw.columns]

    uid_col = find_col(raw.columns, ["yz_open_id", "yzOpenId", "有赞客户ID"], required=True)
    nickname_col = find_col(raw.columns, ["客户昵称", "买家昵称", "昵称"])
    phone_col = find_col(raw.columns, ["手机号", "买家手机号", "客户手机号"])
    order_col = find_col(raw.columns, ["订单号", "订单编号"], required=True)
    status_col = find_col(raw.columns, ["订单状态", "交易状态", "状态"])
    pay_time_col = find_col(raw.columns, ["支付时间", "付款时间"])
    order_time_col = find_col(raw.columns, ["下单时间", "订单创建时间", "创建时间"])
    product_col = find_col(raw.columns, ["商品名称", "商品", "商品标题"], required=True)
    distributor_col = find_col(raw.columns, ["分销员", "分销员昵称", "推广员"], required=True)
    team_col = find_col(raw.columns, ["分销团队", "团队"])
    channel_col = find_col(raw.columns, ["来源渠道", "销售渠道", "订单来源"])
    source_col = find_col(raw.columns, ["来源方式", "来源"])
    tag_col = find_col(raw.columns, ["客户标签", "标签"])
    amount_col = find_col(raw.columns, ["商品实收金额", "订单实收", "实收金额", "商品销售金额", "订单金额"], required=True)
    order_amount_col = find_col(raw.columns, ["订单实收", "实收金额", "订单金额"]) or amount_col
    qty_col = find_col(raw.columns, ["商品销售件数", "数量", "件数"])

    df = raw.copy()
    df["_uid"] = df[uid_col].map(clean_text)
    df = df[df["_uid"] != ""].copy()
    df["_distributor"] = df[distributor_col].map(clean_text)
    matched = df[match_distributor(df[distributor_col], distributor_query, exact)].copy()

    if matched.empty:
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = safe_filename(distributor_query)
        out = output_dir / f"分销商业绩分析_{safe_name}_{week_label}.xlsx"
        summary_path = output_dir / f"分销商业绩总结_{safe_name}_{week_label}.md"
        checks = pd.DataFrame([
            {"检查项": "原始文件", "结果": str(detail_path)},
            {"检查项": "查询分销员", "结果": distributor_query},
            {"检查项": "匹配方式", "结果": "精确匹配" if exact else "包含匹配"},
            {"检查项": "匹配结果", "结果": "无匹配数据"},
            {"检查项": "分销员字段", "结果": distributor_col},
            {"检查项": "分销员聚合口径", "结果": "当前按分销员昵称字段筛选；买家客户按yz_open_id去重。若要避免分销员改名/重名，需要补充分销员ID或手机号导出。"},
        ])
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            checks.to_excel(writer, sheet_name="00口径说明", index=False)
            format_workbook(writer.book)
        summary_path.write_text(
            f"""# {distributor_query} 分销商业绩总结 {week_label}

## 结论

本次在核心明细 `{detail_path}` 中没有匹配到 `{distributor_query}` 的有效分销数据。

## 下一步

- 先检查分销员昵称是否发生变化。
- 到 `分销员 -> 分销员管理 -> 分销员列表` 查询团队、邀请关系和状态。
- 确认本周 `来处订单商品明细_yz_open_id` 是否为最新导出。
- 不要直接判断该分销员无业绩，除非确认导出时间范围和后台显示名称都正确。
""",
            encoding="utf-8",
        )
        return out, summary_path

    matched["_order"] = matched[order_col].map(clean_text)
    matched["_product"] = matched[product_col].map(clean_text)
    matched["_category"] = matched["_product"].map(categorize_product)
    matched["_amount"] = money(matched[amount_col])
    matched["_order_amount"] = money(matched[order_amount_col])
    matched["_qty"] = money(matched[qty_col]) if qty_col else 1
    time_source = pay_time_col or order_time_col
    matched["_time"] = pd.to_datetime(matched[time_source], errors="coerce") if time_source else pd.NaT
    matched["_effective"] = effective_mask(matched, status_col)
    eff = matched[matched["_effective"]].copy()

    order_rows = (
        eff.sort_values("_time")
        .groupby(["_uid", "_order"], dropna=False)
        .agg(
            订单时间=("_time", "min"),
            订单实付=("_order_amount", "max"),
            客户显示=(nickname_col, lambda x: join_unique(x, 3) if nickname_col else ""),
            脱敏手机号=(phone_col, lambda x: latest_nonempty(pd.DataFrame({phone_col: x}), phone_col) if phone_col else ""),
            品类=("_category", lambda x: join_unique(x, 20)),
            商品=("_product", lambda x: join_unique(x, 20)),
            订单状态=(status_col, lambda x: join_unique(x, 5) if status_col else ""),
        )
        .reset_index()
    )

    customer_records = []
    for uid, group in eff.sort_values("_time").groupby("_uid"):
        user_orders = order_rows[order_rows["_uid"] == uid].sort_values("订单时间")
        paid = float(user_orders["订单实付"].sum())
        order_count = int(user_orders["_order"].nunique())
        categories = join_unique(group["_category"], 20)
        customer_records.append({
            "yz_open_id": uid,
            "客户显示": latest_nonempty(group, nickname_col) or uid,
            "历史昵称": join_unique(group[nickname_col]) if nickname_col else "",
            "脱敏手机号": latest_nonempty(group, phone_col),
            "有效订单数": order_count,
            "累计实付": round(paid, 2),
            "客单价": round(paid / order_count, 2) if order_count else 0,
            "首单时间": user_orders["订单时间"].min(),
            "最近下单时间": user_orders["订单时间"].max(),
            "购买品类": categories,
            "分销员归属": join_unique(group[distributor_col]) if distributor_col else "",
            "来源渠道": join_unique(group[channel_col]) if channel_col else "",
            "来源方式": join_unique(group[source_col]) if source_col else "",
            "客户标签": join_unique(group[tag_col]) if tag_col else "",
        })
    customers = pd.DataFrame(customer_records)
    customers = add_user_percentiles(customers)
    customer_rule_profile = compute_user_rule_profile(customers)
    classified = customers.apply(lambda r: classify_user(r, customer_rule_profile), axis=1, result_type="expand")
    classified.columns = [
        "用户标签", "优先级", "下一步动作", "本周推什么", "是否进群", "是否一对一",
        "话术编号", "命中规则", "判断原因", "建议置信度", "是否需人工复核"
    ]
    customers = pd.concat([customers, classified], axis=1)
    customers["客单价百分位"] = (customers["_客单价百分位"] * 100).round(1).astype(str) + "%"
    customers["累计实付百分位"] = (customers["_累计实付百分位"] * 100).round(1).astype(str) + "%"
    customers = customers.drop(columns=["_客单价百分位", "_累计实付百分位", "_订单数百分位"])
    customers = customers.sort_values(["优先级", "累计实付", "有效订单数"], ascending=[True, False, False])

    product = (
        eff.groupby(["_category", "_product"], dropna=False)
        .agg(
            购买客户数=("_uid", "nunique"),
            有效订单数=("_order", "nunique"),
            销售件数=("_qty", "sum"),
            商品实付=("_amount", "sum"),
        )
        .reset_index()
        .rename(columns={"_category": "品类", "_product": "商品"})
    )
    if not product.empty:
        product["商品实付"] = product["商品实付"].round(2)
        product["件单价"] = (product["商品实付"] / product["销售件数"].replace(0, pd.NA)).fillna(0).round(2)
        product = product.sort_values(["商品实付", "购买客户数"], ascending=[False, False])

    actions = customers[[
        "优先级", "yz_open_id", "客户显示", "购买品类", "有效订单数", "累计实付",
        "客单价", "下一步动作", "话术编号", "命中规则", "判断原因", "建议置信度", "是否需人工复核"
    ]].copy()
    actions["分销员执行建议"] = actions.apply(lambda r: distributor_customer_action(r), axis=1)

    distributor_names = join_unique(eff["_distributor"], 20)
    customer_count = int(eff["_uid"].nunique())
    order_count = int(order_rows["_order"].nunique()) if not order_rows.empty else 0
    paid = float(order_rows["订单实付"].sum()) if not order_rows.empty else 0
    repeat_count = int((customers["有效订单数"] >= 2).sum()) if not customers.empty else 0
    high_count = int(customers["用户标签"].astype(str).str.contains("高客单用户", na=False).sum()) if not customers.empty else 0
    black_count = int(customers["购买品类"].astype(str).str.contains("玉乃光黑标", na=False).sum()) if not customers.empty else 0
    quality_judgement = distributor_judgement(customer_count, paid, repeat_count, black_count, high_count)
    quality_reason = distributor_reason(pd.Series({
        "带来客户数": customer_count,
        "累计实付": round(paid, 2),
        "复购客户数": repeat_count,
        "高客单客户数": high_count,
        "黑标客户数": black_count,
        "_客户数百分位": 0.5,
        "_成交额百分位": 0.5,
    }))
    cultivation_action = distributor_action(customer_count, paid, repeat_count, black_count, high_count)
    summary = pd.DataFrame([
        {"指标": "查询分销员", "结果": distributor_query},
        {"指标": "匹配到的分销员名称", "结果": distributor_names},
        {"指标": "分销团队", "结果": join_unique(eff[team_col]) if team_col else ""},
        {"指标": "带来客户数", "结果": customer_count},
        {"指标": "有效订单数", "结果": order_count},
        {"指标": "累计实付", "结果": round(paid, 2)},
        {"指标": "客单价", "结果": round(paid / order_count, 2) if order_count else 0},
        {"指标": "复购客户数", "结果": repeat_count},
        {"指标": "复购率", "结果": f"{repeat_count / customer_count:.1%}" if customer_count else "0.0%"},
        {"指标": "高客单客户数", "结果": high_count},
        {"指标": "黑标客户数", "结果": black_count},
        {"指标": "主要成交品类", "结果": join_unique(eff["_category"], 10)},
        {"指标": "质量判断", "结果": quality_judgement},
        {"指标": "判断原因", "结果": quality_reason},
        {"指标": "培养动作", "结果": cultivation_action},
        {"指标": "规则校准", "结果": customer_rule_profile.get("生成逻辑", "")},
        {"指标": "分销员口径风险", "结果": "当前按分销员昵称筛选；如分销员改名或重名，需要接入分销员ID/手机号后再合并。"},
    ])
    summary_values = {str(row["指标"]): row["结果"] for row in summary.to_dict("records")}
    text_summary = build_text_summary(distributor_query, week_label, summary_values, customers, product, actions)

    checks = pd.DataFrame([
        {"检查项": "原始文件", "结果": str(detail_path)},
        {"检查项": "查询分销员", "结果": distributor_query},
        {"检查项": "匹配方式", "结果": "精确匹配" if exact else "包含匹配"},
        {"检查项": "原始行数", "结果": len(raw)},
        {"检查项": "匹配明细行数", "结果": len(matched)},
        {"检查项": "有效明细行数", "结果": len(eff)},
        {"检查项": "使用主键", "结果": uid_col},
        {"检查项": "使用时间字段", "结果": time_source or "缺失"},
        {"检查项": "使用金额字段", "结果": amount_col},
        {"检查项": "使用订单金额字段", "结果": order_amount_col},
        {"检查项": "分销员字段", "结果": distributor_col},
        {"检查项": "分销员聚合口径", "结果": "当前按分销员昵称字段筛选；买家客户按yz_open_id去重。若要避免分销员改名/重名，需要补充分销员ID或手机号导出。"},
        {"检查项": "状态字段", "结果": status_col or "缺失"},
    ])

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = safe_filename(distributor_query)
    out = output_dir / f"分销商业绩分析_{safe_name}_{week_label}.xlsx"
    summary_path = output_dir / f"分销商业绩总结_{safe_name}_{week_label}.md"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame([
            {"项目": "周度", "说明": week_label},
            {"项目": "分析对象", "说明": distributor_query},
            {"项目": "主键", "说明": "买家使用 yz_open_id 合并；分销员使用分销员字段筛选"},
            {"项目": "分销员口径", "说明": "当前核心明细只有分销员昵称/团队；本报告按昵称筛选，不等同于分销员ID级合并。"},
            {"项目": "核心框架", "说明": "分销员 -> 客户 -> 订单 -> 商品 -> 复购/高客单 -> 动作"},
            {"项目": "规则方式", "说明": "客户优先级按本分销员客户分布自动校准，并输出命中规则、判断原因、置信度和人工复核标记。"},
        ]).to_excel(writer, sheet_name="00口径说明", index=False)
        summary.to_excel(writer, sheet_name="01业绩总览", index=False)
        customers.to_excel(writer, sheet_name="02客户明细", index=False)
        product.to_excel(writer, sheet_name="03商品结构", index=False)
        order_rows.rename(columns={"_uid": "yz_open_id", "_order": "订单号"}).to_excel(writer, sheet_name="04订单明细", index=False)
        actions.to_excel(writer, sheet_name="05客户动作", index=False)
        checks.to_excel(writer, sheet_name="06数据质量检查", index=False)
        pd.DataFrame([{"文本总结": line} for line in text_summary.splitlines()]).to_excel(
            writer, sheet_name="07文本总结", index=False
        )
        format_workbook(writer.book)
    summary_path.write_text(text_summary, encoding="utf-8")
    return out, summary_path


def build_text_summary(
    distributor_query: str,
    week_label: str,
    summary_values: dict[str, object],
    customers: pd.DataFrame,
    product: pd.DataFrame,
    actions: pd.DataFrame,
) -> str:
    top_products = "暂无"
    if not product.empty:
        top_products = "；".join(
            f"{row['品类']} / {row['商品']}：{row['商品实付']}"
            for _, row in product.head(5).iterrows()
        )

    p0_customers = actions[actions["优先级"] == "P0"].head(8) if not actions.empty else pd.DataFrame()
    p1_customers = actions[actions["优先级"] == "P1"].head(8) if not actions.empty else pd.DataFrame()
    p0_names = join_unique(p0_customers["客户显示"], 8) if not p0_customers.empty else "暂无"
    p1_names = join_unique(p1_customers["客户显示"], 8) if not p1_customers.empty else "暂无"

    high_signal = []
    paid = float(summary_values.get("累计实付", 0) or 0)
    repeat_rate = str(summary_values.get("复购率", "0.0%"))
    black_count = int(summary_values.get("黑标客户数", 0) or 0)
    high_count = int(summary_values.get("高客单客户数", 0) or 0)
    if "重点培养" in str(summary_values.get("质量判断", "")):
        high_signal.append("已经进入重点培养区间")
    if repeat_rate != "0.0%":
        high_signal.append("已经出现复购")
    if high_count:
        high_signal.append("已有高客单客户")
    if black_count:
        high_signal.append("已有黑标客户")
    signal_text = "、".join(high_signal) if high_signal else "目前主要是基础成交信号，需要继续验证复购和高客单能力"

    return f"""# {distributor_query} 分销商业绩总结 {week_label}

## 一句话判断

{distributor_query} 本期{signal_text}。当前判断：{summary_values.get("质量判断", "")}

## 核心数据

- 匹配到的分销员名称：{summary_values.get("匹配到的分销员名称", "")}
- 分销团队：{summary_values.get("分销团队", "")}
- 带来客户数：{summary_values.get("带来客户数", 0)}
- 有效订单数：{summary_values.get("有效订单数", 0)}
- 累计实付：{summary_values.get("累计实付", 0)}
- 客单价：{summary_values.get("客单价", 0)}
- 复购客户数：{summary_values.get("复购客户数", 0)}
- 复购率：{summary_values.get("复购率", "0.0%")}
- 高客单客户数：{summary_values.get("高客单客户数", 0)}
- 黑标客户数：{summary_values.get("黑标客户数", 0)}
- 主要成交品类：{summary_values.get("主要成交品类", "")}

## 商品判断

主要成交商品/品类：

{top_products}

## 客户动作

- P0 必须重点跟进客户：{p0_names}
- P1 建议本周回访客户：{p1_names}

## 本周建议

{summary_values.get("培养动作", "")}

执行时不要只给分销员一个泛泛素材包，要把 `05客户动作` 里的客户逐个分层：P0 由老板或核心运营参与，P1 由分销员回访体验，P2/P3 做轻触达和内容观察。

## 数据文件

- 整理后的业绩数据：`分销商业绩分析_{safe_filename(distributor_query)}_{week_label}.xlsx`
- 文本总结：`分销商业绩总结_{safe_filename(distributor_query)}_{week_label}.md`
"""


def distributor_customer_action(row: pd.Series) -> str:
    if row["优先级"] == "P0":
        return "老板或核心运营先一对一，分销员补充关系背书。"
    if row["优先级"] == "P1":
        return "分销员本周回访体验，运营提供产品/权益素材。"
    return "分销员轻触达，不强推，观察咨询、复购或转介绍。"


def safe_filename(value: str) -> str:
    text = clean_text(value) or "unknown"
    for char in r'\/:*?"<>|':
        text = text.replace(char, "_")
    return text[:60]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", required=True, help="Core order-item detail export containing yz_open_id")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--week-label", required=True)
    parser.add_argument("--distributor", required=True, help="Distributor/promoter display name to analyze")
    parser.add_argument("--exact", action="store_true", help="Use exact distributor name match instead of contains match")
    args = parser.parse_args()

    workbook, summary_path = build_distributor_report(
        Path(args.detail).expanduser(),
        Path(args.output_dir).expanduser(),
        args.week_label,
        args.distributor,
        args.exact,
    )
    print(workbook)
    print(summary_path)


if __name__ == "__main__":
    main()
