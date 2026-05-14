#!/usr/bin/env python3
"""Create a Youzan backend usage diagnosis report from an audit note."""

from __future__ import annotations

import argparse
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_markdown_tables(text: str) -> dict[str, list[dict[str, str]]]:
    tables: dict[str, list[dict[str, str]]] = {}
    current_section = "未分组"
    pending_header: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line.lstrip("#").strip()
            pending_header = None
            continue
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-"} for cell in cells if cell):
            continue
        if pending_header is None:
            pending_header = cells
            tables.setdefault(current_section, [])
            continue
        row = {pending_header[i]: cells[i] if i < len(cells) else "" for i in range(len(pending_header))}
        tables.setdefault(current_section, []).append(row)
    return tables


def useful_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        combined = " ".join(str(v) for v in row.values())
        if not combined.strip():
            continue
        output.append(row)
    return output


def classify_modules(page_rows: list[dict[str, str]]) -> tuple[list[str], list[str], list[str]]:
    used = []
    weak = []
    blocked = []
    for row in page_rows:
        module = row.get("模块", "")
        page = row.get("页面", "")
        key = f"{module}：{page}".strip("：")
        combined = " ".join(row.values())
        if "权限" in combined or "未购买" in combined or "未启用" in combined or "打不开" in combined:
            blocked.append(key)
        elif "待检查" in combined or "待确认" in combined:
            weak.append(key)
        else:
            used.append(key)
    return used, weak, blocked


def bullet(items: list[str], empty: str = "暂无明确记录") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def build_report(audit_note: Path, output_dir: Path, week_label: str) -> Path:
    text = read_text(audit_note)
    tables = parse_markdown_tables(text)
    page_rows = useful_rows(tables.get("页面记录", []))
    locked_rows = useful_rows(tables.get("未购买或未启用功能", []))
    data_rows = useful_rows(tables.get("数据获取记录", []))
    evidence_rows = useful_rows(tables.get("证据索引", []))
    used, weak, blocked = classify_modules(page_rows)

    locked_lines = [
        f"{row.get('模块', '')}：{row.get('功能描述', '')}；用途：{row.get('适合来处的用途', '')}；优先级：{row.get('优先级', '')}"
        for row in locked_rows
        if any(row.values())
    ]
    data_lines = [
        f"{row.get('数据', '')}：{row.get('后台路径', '')}；获取方式：{row.get('获取方式', '')}；文件：{row.get('文件名', '')}；yz_open_id：{row.get('是否包含 yz_open_id', '')}"
        for row in data_rows
        if any(row.values())
    ]
    evidence_lines = [
        f"{row.get('文件', '')}：{row.get('对应模块', '')}；{row.get('说明', '')}"
        for row in evidence_rows
        if any(row.values())
    ]

    recommendations = []
    if any("自助取数" in item or "订单" in item for item in weak + blocked):
        recommendations.append("优先保证自助取数、订单、商品明细导出稳定，这是四张经营表的地基。")
    if any("客户" in item or "会员" in item or "CRM" in item for item in weak + blocked):
        recommendations.append("补齐客户、会员、CRM 的配置和数据出口，用来承接复购用户和高客单用户。")
    if any("分销" in item for item in weak + blocked):
        recommendations.append("把分销员数据概览、分销员列表和成交明细固定纳入月度检查，用来筛选真实有圈层的人。")
    if any("营销" in item or "自动化" in item or "社群" in item for item in weak + blocked):
        recommendations.append("把自动化、社群、营销插件按来处的复购和私域目标分级，不急着全开，先挑一个能闭环的功能测试。")
    if not recommendations:
        recommendations.append("本次巡检没有暴露明确后台能力缺口，下一步重点看功能是否持续产出可用数据。")

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"有赞后台使用诊断报告_{week_label}.md"
    out.write_text(
        f"""# 有赞后台使用诊断报告 {week_label}

## 报告定位

这份报告不是经营结果表，而是有赞后台功能检视、后台能力盘点和数据入口健康检查。

四张表回答“来处经营结果怎么样”；本报告回答“有赞这个工具有没有被用好，哪些后台能力应该被启用、配置或修复”。

## 一句话判断

本次巡检记录显示：后台能力需要按“数据入口稳定性、客户复购承接、分销员管理、自动化和社群能力”四条线继续盘点。若页面记录仍大量为“待检查/待确认”，说明本次只能作为巡检底稿，不能作为最终功能诊断。

## 已使用或可用功能

{bullet(used)}

## 未充分确认的功能

{bullet(weak)}

## 未启用、未购买或受权限影响的功能

{bullet(blocked)}

## 未购买或未启用功能明细

{bullet(locked_lines)}

## 数据入口健康检查

{bullet(data_lines)}

## 证据索引

{bullet(evidence_lines)}

## 对来处的优先级建议

{bullet(recommendations)}

## 本月建议动作

- 保证 `来处订单商品明细_yz_open_id` 可以稳定自动导出。
- 每周轻量检查自助取数、商品、客户、分销员和订单入口。
- 每月全量检查流量、页面、热力图、营销、会员、积分、CRM、自动化和社群。
- 对未购买功能，只记录功能描述和来处用途，不把演示数据当真实经营数据。

## 下次验证

- 哪些后台功能能直接帮助复购？
- 哪些功能能让分销员动作被记录和复盘？
- 是否能拿到收藏、加购、停留、页面转化等行为数据？
- 自助取数字段是否稳定包含 `yz_open_id`？

## 来源

- 巡检底稿：`{audit_note}`
""",
        encoding="utf-8",
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-note", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--week-label", required=True)
    args = parser.parse_args()

    out = build_report(Path(args.audit_note).expanduser(), Path(args.output_dir).expanduser(), args.week_label)
    print(out)


if __name__ == "__main__":
    main()

