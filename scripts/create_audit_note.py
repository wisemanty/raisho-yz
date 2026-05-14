#!/usr/bin/env python3
"""Create a weekly Youzan backend audit note for RAISHO."""

from __future__ import annotations

import argparse
from pathlib import Path


MODULE_ROWS = [
    ("数据", "数据概况 / 实时分析", "数据 -> 数据概况"),
    ("流量", "流量概况 / 页面分析 / 热力图分析 / 推广分析", "数据 -> 流量分析"),
    ("商品", "商品概况 / 商品洞察 / 交易分析", "数据 -> 商品分析"),
    ("客户", "客户概况 / 客户洞察 / 粉丝 / 会员 / 积分 / 储值", "数据 -> 客户分析"),
    ("营销", "营销概况 / 插件分析 / 复盘报告", "数据 -> 营销分析"),
    ("订单", "订单管理 / 导出订单报表 / 导出商品报表", "订单 -> 订单管理"),
    ("客户列表", "客户管理 / 客户列表 / 客户详情 / 导出", "客户 -> 客户管理"),
    ("分销员", "数据概览 / 分销员列表 / 排行 / 商品成交分析", "分销员 -> 分销员管理"),
    ("会员积分CRM", "会员 / 积分 / CRM / 自动化 / 社群", "按后台可见入口"),
]


def build_note(week_label: str, date_range: str) -> str:
    rows = "\n".join(
        f"| {module} | {page} | {path} | 待检查 | 待检查 | 待检查 | 待检查 | 待确认 |  |  |"
        for module, page, path in MODULE_ROWS
    )
    return f"""# 后台巡检记录 {week_label}

## 巡检范围

- 时间范围：{date_range or "待填写"}
- 已巡检模块：待填写
- 未能打开/权限不足模块：待填写
- 人工介入事项：登录 / 验证码 / 安全确认
- 原始数据目录：`原始数据/`
- 证据目录：`巡检证据/`
- 核心报表：`来处订单商品明细_yz_open_id`

## 页面记录

| 模块 | 页面 | 后台路径 | 是否完整上下滑 | 是否点详情/箭头 | 是否横向滚动 | 是否检查分页 | 可导出数据 | 关键发现 | 后续动作 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{rows}

## 证据索引

| 文件 | 对应模块 | 说明 | 是否含敏感信息 |
| --- | --- | --- | --- |

## 未购买或未启用功能

| 模块 | 功能描述 | 界面证据/入口 | 适合来处的用途 | 优先级 | 下周验证 |
| --- | --- | --- | --- | --- | --- |

## 数据获取记录

| 数据 | 后台路径 | 获取方式 | 文件名 | 是否包含 yz_open_id | 备注 |
| --- | --- | --- | --- | --- | --- |
| 订单商品明细 | 数据 -> 数据报表 -> 自助取数 -> 我的取数 | 自动下载 | 待填写 | 待确认 | 必须使用 `来处订单商品明细_yz_open_id` |

## 老板视角判断

- 已成立：
- 未成立：
- 为什么会这样：
- 需要补的数据：
- 本周动作：
- 下周验证：
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, help="Weekly output directory, e.g. .../周报/2026-W20")
    parser.add_argument("--week-label", required=True, help="Week label, e.g. 2026-W20")
    parser.add_argument("--date-range", default="", help="Date range text for the audit")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "巡检证据").mkdir(exist_ok=True)
    note_path = output_dir / "后台巡检记录.md"

    if note_path.exists() and not args.overwrite:
        print(f"exists: {note_path}")
        return

    note_path.write_text(build_note(args.week_label, args.date_range), encoding="utf-8")
    print(f"created: {note_path}")


if __name__ == "__main__":
    main()
