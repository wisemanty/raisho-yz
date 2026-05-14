# 有赞后台使用诊断 Workflow

Use this reference when the task asks for a full Youzan backend review, not only weekly table generation.

## Goal

Read Youzan like an operating system for trust, repurchase, private traffic, distribution, and product paths.

`有赞后台使用诊断` is a function review, not an order-result analysis. It should help 来处 use Youzan better.

The audit output should answer:

- Who is buying, returning, upgrading, or only watching?
- Which products are entry, profit, referral, or trust-upgrade carriers?
- Which distributors are actually creating customers and orders?
- Which traffic paths are producing paid trust?
- Which unused Youzan modules matter for 来处 next?

## Audit Discipline

For every page or module:

1. Set or confirm the time range.
2. Capture the top summary cards.
3. Scroll from top to bottom.
4. Use horizontal table scroll where present.
5. Open card arrows, detail links, ranking lists, and tabs.
6. Check filters, pagination, and export/download buttons.
7. If a module is unpurchased or locked, record the visible product description, demo images, feature names, and activation path. Do not treat demo numbers as real data.
8. Prefer exports over manual copying for any table used in final analysis.
9. Record what was inspected in a weekly audit note.
10. Save screenshots or visible evidence when a page contains important findings, locked-feature descriptions, or ambiguous UI states.

## Minimum Modules To Inspect

### Data Overview

Path:

`数据 -> 数据概况`

Inspect:

- 数据概况
- 实时分析
- 卡片 arrows for real-time payment amount, transaction formula, payment overview, AOV, visitor count, conversion, product pieces
- Date selector and comparison period
- Top-to-bottom page scroll

Use for:

- Business pulse
- Anomaly detection
- Directional explanation before exports

### Traffic Analysis

Path:

`数据 -> 流量分析`

Inspect:

- 流量概况
- 页面分析
- 热力图分析
- 推广分析
- Source, channel, page, and campaign breakdowns
- High-view low-conversion pages

Use for:

- Traffic source effectiveness
- Product page conversion diagnosis
- “反复看但不下单” hypothesis

### Product Analysis

Path:

`数据 -> 商品分析`

Inspect:

- 商品概况
- 商品洞察
- 交易分析
- Product rankings by visitor, add-cart, payment count, payment amount, conversion
- Product detail pages and trend arrows

Use for:

- Entry product
- Profit product
- Referral product
- Trust-upgrade product
- Browse-high conversion-low problems

### Customer Analysis

Path:

`数据 -> 客户分析`

Inspect:

- 客户概况
- 客户洞察
- 粉丝分析
- 会员分析
- 积分分析
- 储值分析
- New vs old users
- Repurchase, AOV, frequency, customer tags, membership behavior

Use for:

- User structure
- Repurchase system diagnosis
- Membership and CRM opportunities

### Marketing Analysis

Path:

`数据 -> 营销分析`

Inspect:

- 营销概况
- 插件分析
- 复盘报告
- Promotion, coupon, campaign, and plugin performance if available
- Locked/unpurchased module descriptions

Use for:

- Which Youzan tools are unused
- Which tools should become weekly operating levers

### Orders

Path:

`订单 -> 订单管理`

Inspect/export:

- Order list filters
- Order status
- Time range
- Source, product, promotion, after-sale, logistics, payment, amount filters
- `下载订单报表`
- `下载商品报表`

Use for:

- Amount/status reconciliation
- Refund and fulfillment risk
- Supplementary product-order checks

### Customers

Path:

`客户 -> 客户管理 -> 客户列表`

Inspect/export:

- Customer filters
- Customer detail pages where needed
- `yzUid` or stable IDs in URLs if visible
- Tags, membership, source, last consumption, frequency, cumulative spend
- Export list

Use for:

- CRM context only when stable IDs can be joined
- Do not replace `yz_open_id` as the primary key unless an export provides a reliable mapping

### Distribution

Path:

`分销员 -> 分销员管理`

Inspect/export:

- 数据概览
- 分销员列表
- Distributor ranking
- Product deal analysis
- Customers, orders, sales, commission, invitation relation
- Inactive registered distributors

Use for:

- Distributor quality table
- Distributor nurturing actions
- Identifying natural small-circle distribution

### CRM, Membership, Points, Automation, Community

Paths vary by store permissions and Youzan version.

Inspect visible modules such as:

- 会员
- 积分
- 储值
- 客户运营 / CRM
- 自动化营销
- 社群 / 企业微信 / 私域 tools
- 分销 / 推广 tools

For each module record:

- Is it enabled, configured, locked, or unpurchased?
- What exact function does the UI claim?
- Which 来处 problem it could solve: first conversion, repurchase, high-AOV upgrade, distributor enablement, private group retention, or service follow-up.
- What should be tested next week.

## Audit Note Template

Save a weekly audit note next to the workbook:

`/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/后台巡检记录.md`

Save screenshots and evidence files under:

`/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/巡检证据/`

Recommended filename format:

`YYYY-WW_模块_页面_序号_说明.png`

Examples:

- `2026-W20_数据概况_支付概况_01_卡片详情.png`
- `2026-W20_流量分析_页面分析_02_高浏览低转化.png`
- `2026-W20_营销分析_自动化营销_01_未购买功能描述.png`

Do not save private security codes, full unmasked phone numbers, or password/login pages as evidence unless explicitly needed and approved.

Use this structure:

```markdown
# 后台巡检记录 YYYY-WW

## 巡检范围

- 时间范围：
- 已巡检模块：
- 未能打开/权限不足模块：
- 人工介入事项：登录 / 验证码 / 安全确认
- 证据目录：`巡检证据/`

## 页面记录

| 模块 | 页面 | 是否完整上下滑 | 是否点详情/箭头 | 是否横向滚动 | 是否检查分页 | 可导出数据 | 关键发现 | 后续动作 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 证据索引

| 文件 | 对应模块 | 说明 | 是否含敏感信息 |
| --- | --- | --- | --- |

## 未购买或未启用功能

| 模块 | 功能描述 | 适合来处的用途 | 优先级 | 下周验证 |
| --- | --- | --- | --- | --- |

## 老板视角判断

- 已成立：
- 未成立：
- 需要补的数据：
- 下周动作：
```

## Relationship To The Four Tables

The four tables still come from exported data, mainly `来处订单商品明细_yz_open_id`.

The backend audit adds explanation and action context:

- If traffic pages show high browse and low conversion, add this to product-path interpretation.
- If customer pages show repeat or membership signals, use them to refine operating actions.
- If distribution overview shows active/inactive gaps, use it to qualify distributor actions.
- If locked modules describe useful automation, record them as future operating infrastructure, not current performance.

## 有赞后台使用诊断报告

After `后台巡检记录.md` is filled enough to support a conclusion, generate:

`有赞后台使用诊断报告_YYYY-WW.md`

Use:

```bash
python3 scripts/create_backend_audit_report.py \
  --audit-note "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/后台巡检记录.md" \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW" \
  --week-label "YYYY-WW"
```

Or use the controller:

```bash
python3 scripts/run_analysis.py --mode backend-audit --week-label "YYYY-WW"
```

The diagnosis report should explain:

- which Youzan functions are already in use
- which functions are enabled but underused
- which modules are locked, unpurchased, or not configured
- which data entrances are healthy or risky
- which functions should be tested next for repurchase, CRM, membership, automation, community, or distributor management
