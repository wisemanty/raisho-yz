#!/usr/bin/env python3
"""Build Markdown and Word operating summaries from a RAISHO weekly workbook."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from build_weekly_tables import categorize_product, effective_mask, find_col, money, read_table


def value_from_checks(checks: pd.DataFrame, key: str, default: Any = "") -> Any:
    if checks.empty or "检查项" not in checks.columns or "结果" not in checks.columns:
        return default
    rows = checks[checks["检查项"].astype(str) == key]
    if rows.empty:
        return default
    return rows.iloc[0]["结果"]


def format_money(value: float | int) -> str:
    return f"{float(value):,.2f}"


def safe_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def read_sheet(workbook: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(workbook, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def summarize_detail(detail_path: Path | None) -> tuple[dict[str, Any], pd.DataFrame]:
    if not detail_path or not detail_path.exists():
        return {}, pd.DataFrame()

    raw = read_table(detail_path)
    raw.columns = [str(c).strip() for c in raw.columns]
    uid_col = find_col(raw.columns, ["yz_open_id", "yzOpenId", "有赞客户ID"], required=True)
    order_col = find_col(raw.columns, ["订单号", "订单编号"], required=True)
    status_col = find_col(raw.columns, ["订单状态", "交易状态", "状态"])
    pay_time_col = find_col(raw.columns, ["支付时间", "付款时间"])
    order_time_col = find_col(raw.columns, ["下单时间", "订单创建时间", "创建时间"])
    product_col = find_col(raw.columns, ["商品名称", "商品", "商品标题"], required=True)
    amount_col = find_col(raw.columns, ["商品实收金额", "订单实收", "实收金额", "商品销售金额", "订单金额"], required=True)
    order_amount_col = find_col(raw.columns, ["订单实收", "实收金额", "订单金额"]) or amount_col
    qty_col = find_col(raw.columns, ["商品销售件数", "数量", "件数"])
    time_col = pay_time_col or order_time_col

    df = raw.copy()
    df["_uid"] = df[uid_col].map(safe_text)
    df = df[df["_uid"] != ""].copy()
    df["_order"] = df[order_col].map(safe_text)
    df["_product"] = df[product_col].map(safe_text)
    df["_category"] = df["_product"].map(categorize_product)
    df["_amount"] = money(df[amount_col])
    df["_order_amount"] = money(df[order_amount_col])
    df["_qty"] = money(df[qty_col]) if qty_col else 1
    df["_time"] = pd.to_datetime(df[time_col], errors="coerce") if time_col else pd.NaT
    df["_effective"] = effective_mask(df, status_col)
    eff = df[df["_effective"]].copy()

    orders = (
        eff.groupby("_order", dropna=False)
        .agg(订单实收=("_order_amount", "max"), yz_open_id=("_uid", "first"), 支付时间=("_time", "min"))
        .reset_index()
    )
    paid = float(orders["订单实收"].sum()) if not orders.empty else 0.0
    order_count = int(orders["_order"].nunique()) if not orders.empty else 0
    metrics = {
        "原始明细行数": len(raw),
        "有效明细行数": len(eff),
        "去重用户数": int(eff["_uid"].nunique()) if not eff.empty else 0,
        "有效订单数": order_count,
        "累计实付": paid,
        "客单价": paid / order_count if order_count else 0,
        "最早支付时间": eff["_time"].min() if not eff.empty else "",
        "最新支付时间": eff["_time"].max() if not eff.empty else "",
        "时间字段": time_col or "",
    }

    product = (
        eff.groupby("_category")
        .agg(
            客户数=("_uid", "nunique"),
            订单数=("_order", "nunique"),
            件数=("_qty", "sum"),
            商品实收=("_amount", "sum"),
        )
        .reset_index()
        .rename(columns={"_category": "品类"})
        .sort_values("商品实收", ascending=False)
    )
    if not product.empty:
        product["商品实收"] = product["商品实收"].round(2)
    return metrics, product


def table_to_md(df: pd.DataFrame, columns: list[str], max_rows: int = 12) -> str:
    if df.empty:
        return "暂无数据"
    view = df[[c for c in columns if c in df.columns]].head(max_rows).copy()
    if view.empty:
        return "暂无数据"
    headers = [str(c) for c in view.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in view.iterrows():
        cells = [safe_text(row[col]).replace("|", "/") for col in view.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_summary_text(
    workbook: Path,
    detail_path: Path | None,
    week_label: str,
    date_range: str,
) -> tuple[str, dict[str, Any]]:
    users = read_sheet(workbook, "01用户分层表")
    paths = read_sheet(workbook, "02商品路径表")
    distributors = read_sheet(workbook, "03分销员质量表")
    rules = read_sheet(workbook, "06规则校准说明")
    checks = read_sheet(workbook, "07数据质量检查")
    metrics, product = summarize_detail(detail_path)

    if not metrics:
        metrics = {
            "原始明细行数": value_from_checks(checks, "原始行数", 0),
            "有效明细行数": value_from_checks(checks, "有效明细行数", 0),
            "去重用户数": value_from_checks(checks, "去重用户数", 0),
            "有效订单数": value_from_checks(checks, "去重订单数", 0),
            "累计实付": float(users["累计实付"].sum()) if "累计实付" in users.columns else 0,
            "客单价": 0,
            "最早支付时间": "",
            "最新支付时间": "",
            "时间字段": value_from_checks(checks, "使用时间字段", ""),
        }

    p0 = users[users["优先级"].astype(str) == "P0"] if "优先级" in users.columns else pd.DataFrame()
    p1 = users[users["优先级"].astype(str) == "P1"] if "优先级" in users.columns else pd.DataFrame()
    top_dist = distributors.head(1).iloc[0].to_dict() if not distributors.empty else {}
    top_dist_name = safe_text(top_dist.get("分销员", "暂无"))

    high_signal = "黑标和高客单用户开始形成高信任成交"
    if not product.empty and "玉乃光黑标" in product["品类"].astype(str).tolist():
        black_amount = float(product.loc[product["品类"].astype(str) == "玉乃光黑标", "商品实收"].sum())
        if black_amount > 0:
            high_signal = f"黑标贡献 {format_money(black_amount)}，是本期最强的高信任成交信号"

    rules_text = "暂无"
    if not rules.empty:
        rules_text = "；".join(f"{r.get('项目', '')}：{r.get('说明', '')}" for _, r in rules.iterrows())

    md = f"""# 来处有赞经营分析总结 {week_label}

## 数据口径

- 分析区间：{date_range or week_label}
- 数据来源：有赞自助取数 `来处订单商品明细_yz_open_id`
- 分析时间字段：{metrics.get('时间字段', '')}
- 实际最早支付时间：{metrics.get('最早支付时间', '')}
- 实际最新支付时间：{metrics.get('最新支付时间', '')}
- 原始明细行数：{metrics.get('原始明细行数', 0)}
- 有效明细行数：{metrics.get('有效明细行数', 0)}
- 去重用户数：{metrics.get('去重用户数', 0)}
- 有效订单数：{metrics.get('有效订单数', 0)}
- 累计实付：{format_money(metrics.get('累计实付', 0))}
- 客单价：{format_money(metrics.get('客单价', 0))}

## 一句话判断

本期来处的经营重点不是单纯销售额，而是信任结构是否成立。当前最清楚的信号是：{high_signal}；分销侧以 {top_dist_name} 最值得优先复盘。

## 商品结构

{table_to_md(product, ['品类', '客户数', '订单数', '件数', '商品实收'])}

## 用户结构

- P0 重点用户：{len(p0)} 人，累计实付 {format_money(p0['累计实付'].sum() if not p0.empty and '累计实付' in p0.columns else 0)}
- P1 跟进用户：{len(p1)} 人，累计实付 {format_money(p1['累计实付'].sum() if not p1.empty and '累计实付' in p1.columns else 0)}
- 本期规则校准：{rules_text}

## 重点用户

{table_to_md(users, ['优先级', '客户显示', '有效订单数', '累计实付', '客单价', '购买品类', '分销员归属', '下一步动作'], 15)}

## 商品路径

{table_to_md(paths, ['起点品类', '后续品类', '迁移人数', '迁移金额', '典型用户', '信任解释', '下一步商品策略'])}

## 分销员表现

{table_to_md(distributors, ['分销员', '带来客户数', '有效订单数', '累计实付', '客单价', '复购率', '高客单客户数', '黑标客户数', '质量判断', '培养动作'])}

## 哪里已经成立

- 高信任商品的成交信号已经出现，优先看黑标、本真和高客单用户。
- 买家侧已经按 `yz_open_id` 合并，可以持续追踪复购和商品迁移。
- 分销侧已经能看出不同分销员的带客能力差异。

## 哪里还没成立

- 分销员目前仍按昵称聚合，若分销员改名或重名，需要接入分销员 ID / 手机号。
- 行为数据仍不完整，浏览、收藏、加购、停留等信号还没有稳定进入四张表。
- 复购和转介绍是否成立，需要继续看后续周的数据。

## 本周经营动作

1. P0 用户做一对一维护，先问体验和预期，不要只催单。
2. P1 用户进入复购池，用会员、社群、新品优先权承接。
3. 对重点分销员做单独复盘，拆分哪些客户由老板跟，哪些由分销员跟。
4. 对低信号用户只做轻触达，观察咨询、复购、转介绍和再次浏览。

## 下周要验证

- 黑标/高客单用户是否产生反馈、复购或转介绍。
- 今治类生活品是否真的带来礼赠和转介绍。
- 重点分销员的客户是否能继续复购或升级。
- 新增用户是否能从尝鲜进入复购池。
"""
    context = {
        "users": users,
        "paths": paths,
        "distributors": distributors,
        "product": product,
        "metrics": metrics,
    }
    return md, context


def add_dataframe_table(doc, df: pd.DataFrame, columns: list[str], max_rows: int = 12) -> None:
    view = df[[c for c in columns if c in df.columns]].head(max_rows).copy()
    if view.empty:
        doc.add_paragraph("暂无数据")
        return
    table = doc.add_table(rows=1, cols=len(view.columns))
    table.style = "Table Grid"
    for i, col in enumerate(view.columns):
        table.rows[0].cells[i].text = str(col)
    for _, row in view.iterrows():
        cells = table.add_row().cells
        for i, col in enumerate(view.columns):
            cells[i].text = safe_text(row[col])


def build_docx(
    out_docx: Path,
    week_label: str,
    date_range: str,
    context: dict[str, Any],
) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor

    doc = Document()
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10.5)
    styles["Title"].font.name = "Arial"
    styles["Title"].font.size = Pt(20)
    styles["Heading 1"].font.name = "Arial"
    styles["Heading 1"].font.size = Pt(15)
    styles["Heading 1"].font.color.rgb = RGBColor(11, 92, 126)
    styles["Heading 2"].font.name = "Arial"
    styles["Heading 2"].font.size = Pt(12.5)

    metrics = context["metrics"]
    product = context["product"]
    users = context["users"]
    paths = context["paths"]
    distributors = context["distributors"]
    p0 = users[users["优先级"].astype(str) == "P0"] if "优先级" in users.columns else pd.DataFrame()
    p1 = users[users["优先级"].astype(str) == "P1"] if "优先级" in users.columns else pd.DataFrame()
    top_dist = safe_text(distributors.iloc[0]["分销员"]) if not distributors.empty and "分销员" in distributors.columns else "暂无"

    title = doc.add_paragraph()
    title.style = "Title"
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("来处有赞经营分析总结")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run(date_range or week_label).italic = True

    doc.add_heading("核心判断", level=1)
    doc.add_paragraph(
        f"本期有效订单 {metrics.get('有效订单数', 0)} 单，去重用户 {metrics.get('去重用户数', 0)} 人，"
        f"累计实付 {format_money(metrics.get('累计实付', 0))}，客单价 {format_money(metrics.get('客单价', 0))}。"
        f"经营重点应放在高信任用户维护、复购承接和重点分销员复盘，其中 {top_dist} 是本期最值得优先观察的分销对象。"
    )

    doc.add_heading("数据口径", level=1)
    for label in ["时间字段", "最早支付时间", "最新支付时间", "原始明细行数", "有效明细行数", "去重用户数", "有效订单数"]:
        doc.add_paragraph(f"{label}：{metrics.get(label, '')}", style=None)

    doc.add_heading("商品结构", level=1)
    add_dataframe_table(doc, product, ["品类", "客户数", "订单数", "件数", "商品实收"])

    doc.add_heading("用户结构", level=1)
    doc.add_paragraph(f"P0 重点用户：{len(p0)} 人，累计实付 {format_money(p0['累计实付'].sum() if not p0.empty and '累计实付' in p0.columns else 0)}")
    doc.add_paragraph(f"P1 跟进用户：{len(p1)} 人，累计实付 {format_money(p1['累计实付'].sum() if not p1.empty and '累计实付' in p1.columns else 0)}")
    add_dataframe_table(doc, users, ["优先级", "客户显示", "有效订单数", "累计实付", "客单价", "购买品类", "下一步动作"], 12)

    doc.add_heading("商品路径", level=1)
    add_dataframe_table(doc, paths, ["起点品类", "后续品类", "迁移人数", "迁移金额", "典型用户", "信任解释"], 10)

    doc.add_heading("分销员表现", level=1)
    add_dataframe_table(doc, distributors, ["分销员", "带来客户数", "有效订单数", "累计实付", "复购率", "黑标客户数", "质量判断"], 12)
    doc.add_paragraph("注：买家客户按 yz_open_id 去重；分销员当前按昵称字段聚合，若分销员改名或重名，需要接入分销员 ID / 手机号。")

    doc.add_heading("本周经营动作", level=1)
    actions = [
        "P0 用户做一对一维护，先问体验和预期，不只催单。",
        "P1 用户进入复购池，用会员、社群、新品优先权承接。",
        "重点分销员做单独复盘，拆分老板跟进和分销员跟进对象。",
        "低信号用户只做轻触达，观察咨询、复购、转介绍和再次浏览。",
    ]
    for item in actions:
        doc.add_paragraph(item, style="List Number")

    out_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_docx)


def build_summary(workbook: Path, output_dir: Path, week_label: str, detail: Path | None = None, date_range: str = "") -> tuple[Path, Path]:
    md, context = build_summary_text(workbook, detail, week_label, date_range)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"经营分析总结_{week_label}.md"
    docx_path = output_dir / f"经营分析总结_{week_label}.docx"
    md_path.write_text(md, encoding="utf-8")
    build_docx(docx_path, week_label, date_range, context)
    return md_path, docx_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--week-label", required=True)
    parser.add_argument("--detail")
    parser.add_argument("--date-range", default="")
    args = parser.parse_args()

    detail = Path(args.detail).expanduser() if args.detail else None
    md_path, docx_path = build_summary(
        Path(args.workbook).expanduser(),
        Path(args.output_dir).expanduser(),
        args.week_label,
        detail,
        args.date_range,
    )
    print(md_path)
    print(docx_path)


if __name__ == "__main__":
    main()
