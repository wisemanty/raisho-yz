---
name: raisho-yz
description: Weekly Youzan backend analysis workflow for RAISHO/来处. Use when the user asks to run, update, rebuild, or explain the weekly Youzan analysis, generate the four operating tables, inspect Youzan backend modules, automate backend data collection, analyze users/products/distributors/repurchase, produce a named distributor performance report such as Jeff业绩分析, or build a fixed framework around data, users, behavior, trust, and actions.
---

# 来处有赞经营分析

## Version Notes

Before handing this skill to OpenClaw or debugging a deployed copy, read `CHANGELOG.md` for the current capability set, validated flows, and known Youzan/CDP caveats.

## Purpose

Run a weekly Youzan operating analysis for 来处. Treat Youzan as a trust-system backend, not only a sales dashboard.

Always output around this logic:

`数据 -> 用户 -> 行为 -> 信任 -> 动作`

The stable weekly deliverables are:

- `01用户分层表`
- `02商品路径表`
- `03分销员质量表`
- `04经营动作表`
- `经营分析总结_<week>.md`
- `经营分析总结_<week>.docx`

For a full weekly operation review, also produce or update:

- `后台巡检记录.md`
- boss-view summary of what is already成立 and what is not

For a named distributor request such as `Jeff 的业绩分析`, complete the whole chain:

`自动获取数据 -> 分销商业绩分析 -> 文本经营总结 -> 整理后的业绩数据`

For a `有赞后台使用诊断` request, produce:

- `后台巡检记录.md`
- `有赞后台使用诊断报告_<week>.md`

## Required Data Rule

Use `yz_open_id` as the user primary key. Nickname and phone are display fields only.

If the core order-item detail file does not contain `yz_open_id`, stop before final analysis and report that the data口径 is insufficient. Do not pretend nickname + phone is a final user identity.

Repurchase count and repurchase rate must use purchase sessions, not raw same-day order count:

- Same `yz_open_id` + same natural purchase date = 1 purchase session.
- `复购客户数` = customers with purchase sessions >= 2.
- `复购率` = `复购客户数 / 去重客户数`.
- Record this reason in outputs: current product specs can cause same-day split orders, and black-label/Imabari presale additions before arrival should not be counted as post-experience repurchase.

## Dynamic Judgment Rule

Do not ask the owner to manually tune weekly thresholds such as P0 amount, high-AOV amount, or key distributor amount.

The agent must first read the current data distribution, then calibrate judgment lines automatically:

- high-AOV users: compare against the current run's user AOV distribution.
- high-paid users: compare against the current run's cumulative paid distribution.
- key distributors: compare against the current run's distributor paid/customer distribution when available.
- black-label and Imabari signals must respect product lifecycle: both were added as presale links on 2026-05-10 and were expected to arrive around 2026-05-31.

Every priority or cultivation decision should expose the evidence, not only the conclusion. Weekly tables and distributor reports should include:

- `命中规则`
- `判断原因`
- `建议置信度`
- `是否需人工复核`

The owner decides business principles. The agent adjusts operating thresholds from the data and makes the adjustment visible in `规则校准说明`.

## Weekly Workflow

1. Decide the run type.
   - Table-only run: generate the four tables from an existing core export.
   - Full weekly run: use Computer Use to inspect Youzan modules, collect/export data, then generate the four tables and summary.
   - Named distributor run: collect or locate the core `yz_open_id` detail export, filter by distributor/promoter name, then generate a distributor performance workbook.
   - 有赞后台使用诊断 run: inspect/record Youzan backend function usage and generate a Youzan usage diagnosis report. The script mode remains `backend-audit`.
   - If the user says manual downloading is not acceptable, do not ask them to download data manually. Ask only for login, CAPTCHA, or security confirmation when Youzan requires it.
   - Prefer CDP direct export when Chrome is available with remote debugging and the user is already logged in. Use Computer Use only for login, CAPTCHA, backend inspection, or UI paths that do not yet have a stable endpoint.

2. Get the core Youzan detail export.
   - Read `references/data-sources.md` for exact backend click paths.
   - Required report: `来处订单商品明细_yz_open_id`.
   - Required backend path: `数据 -> 数据报表 -> 自助取数 -> 我的取数`.
   - If Chrome is running with `--remote-debugging-port=9222`, use:
     `scripts/fetch_custompeek_report_cdp.js --output-dir "<weekly>/原始数据"`.
     This connects to the logged-in Youzan page, finds the fixed report, submits `reExport`, waits for completion, and downloads the generated file without manual browser clicks.
   - Current observed endpoint family: `/v4/statcenter/custompeek/api`.
   - Current fixed report ID observed on 2026-05-12: `436628`. Do not hard-code this as the only source of truth; first search by report name, then fall back to report ID when supplied.
   - Youzan may return a file with `.csv` naming and `text/csv` content type while the bytes are XLSX. Trust file signature over extension.
   - Youzan XLSX may contain a bad sheet dimension such as `A1`; do not validate emptiness with `openpyxl` read-only `max_row` alone. Use `pandas.read_excel` or the weekly builder.
   - If not logged in, use the CDP login assistant script to create a Feishu-friendly login loop. It can screenshot the current login page or QR code, click a send-code control, fill a code supplied by the operator, and poll until the Youzan API is logged in.

3. If doing a full weekly run, inspect the backend.
   - Read `references/backend-audit.md`.
   - Create the weekly audit note before browsing:
     `scripts/create_audit_note.py --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW" --week-label "YYYY-WW" --date-range "YYYY-MM-DD 至 YYYY-MM-DD"`.
   - Browse each relevant module completely: scroll vertically, use horizontal table scroll, click arrows/details/tabs, inspect filters and pagination, and record locked or unpurchased feature descriptions.
   - Save the audit note as `/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/后台巡检记录.md`.
   - Do not use demo or locked-module numbers as real performance data.

4. Save raw files.
   - Use `/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/原始数据/`.
   - Keep original exports unchanged.

5. Check the data口径.
   - Confirm `yz_open_id`, order time, order status, product name, amount, and distributor fields exist.
   - Prefer `支付时间`; fall back to `下单时间`.
   - Exclude clearly invalid orders such as closed, unpaid, canceled, or fully refunded rows when status allows.

6. Generate the workbook.
   - Use `scripts/build_weekly_tables.py` when a core export file is available.
   - The script should auto-calibrate operating rules from the current export. Do not edit code just to change weekly amount thresholds.
   - For a date-range analysis, prefer `scripts/run_analysis.py --mode weekly --start YYYY-MM-DD --end YYYY-MM-DD`; it creates a filtered detail file before building the workbook.
   - Weekly mode must also generate a Markdown and Word operating summary through `scripts/build_operating_summary.py`.
   - Use the bundled Python runtime if normal `python3` lacks spreadsheet libraries:
     `/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`

Example:

```bash
/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/build_weekly_tables.py \
  --detail "/path/to/来处订单商品明细_yz_open_id.csv" \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/2026-W20" \
  --week-label "2026-W20" \
  --audit-note "/Users/wisemantong/Desktop/有赞后台分析/周报/2026-W20/后台巡检记录.md"
```

7. Review outputs before presenting them.
   - Check `06数据质量检查`.
   - Confirm the workbook states the repurchase metric rule: same user same natural day = 1 purchase session.
   - Open the workbook if possible and verify column widths, filters, frozen headers, and readable action text.
   - If exact values look suspicious, inspect the raw rows rather than smoothing over the issue.

8. Write the boss-view summary.
   - Say where the system is成立.
   - Say where it has not成立.
   - Say which trust path is forming.
   - Say which backend functions should become operating infrastructure.
   - Say what to do next week.

## Named Distributor Workflow

Use this when the user asks for one distributor/promoter, for example `Jeff 的业绩分析来一个`.

1. Ensure the core detail export is available.
   - Use `references/data-sources.md`.
   - If no current export is available and manual download is not acceptable, prefer CDP direct export:
     `scripts/fetch_custompeek_report_cdp.js --output-dir "<weekly>/原始数据" --report-name "来处订单商品明细_yz_open_id"`.
   - Use Computer Use only when login/CAPTCHA is required or the CDP route is unavailable.
   - The export must include `yz_open_id` and a distributor field such as `分销员`.
   - Current distributor statistics filter only the `分销员` field. `分销团队` is reported as context and should not pull in extra rows unless the user explicitly asks for team-level analysis.

2. Generate the distributor workbook:

```bash
/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/build_distributor_report.py \
  --detail "/path/to/来处订单商品明细_yz_open_id.csv" \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/2026-W20/分销商分析" \
  --week-label "2026-W20" \
  --distributor "Jeff"
```

3. Review `06数据质量检查`.
   - If no rows match, report that the distributor name did not match the export and suggest checking spelling, nickname changes, or using exact backend distributor export.
   - If multiple display names match by contains-search, note this in the summary.

4. Summarize in business language:
   - How many customers this distributor brought.
   - Effective orders, cumulative paid, AOV, repeat rate, high-AOV customers, black-label customers.
   - Which products this distributor can sell now.
   - Which customers require owner-level 1:1 versus distributor follow-up.
   - Whether this distributor is worth cultivating next week.
   - Output both files:
     - `分销商业绩总结_<name>_<week>.md`
     - `分销商业绩分析_<name>_<week>.xlsx`

## Controller Script

Prefer `scripts/run_analysis.py` as the stable entry point for OpenClaw or repeated use.

Weekly mode:

```bash
/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/run_analysis.py \
  --mode weekly \
  --week-label "2026-W20" \
  --detail "/path/to/来处订单商品明细_yz_open_id.csv"
```

Distributor mode:

```bash
/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/run_analysis.py \
  --mode distributor \
  --week-label "2026-W20" \
  --detail "/path/to/来处订单商品明细_yz_open_id.csv" \
  --distributor "Jeff"
```

有赞后台使用诊断 mode:

```bash
/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/run_analysis.py \
  --mode backend-audit \
  --week-label "2026-W20" \
  --date-range "2026-05-04 至 2026-05-10"
```

The controller creates the weekly folder, `原始数据/`, `巡检证据/`, and `运行日志.md`.

CDP direct data fetch:

```bash
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/fetch_custompeek_report_cdp.js \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/2026-W20/原始数据" \
  --report-name "来处订单商品明细_yz_open_id"
```

If Youzan stops at the shop-selection page after login, the CDP fetch script should auto-select `RAISHO来处` by default. Override with `--shop-name` when needed.

Prerequisite:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir="/Users/wisemantong/Desktop/有赞后台分析/chrome-youzan-cdp-profile" \
  https://www.youzan.com/v4/statcenter/custompeek/index
```

The user may need to log in or complete verification once. Do not print cookies, csrf tokens, signed download URLs, or other secrets.

CDP login assistant:

```bash
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js \
  --mode status

node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js \
  --mode screenshot \
  --output "/Users/wisemantong/Desktop/有赞后台分析/周报/2026-W20/巡检证据/youzan-login.png"

node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js \
  --mode click-send-code

node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js \
  --mode fill-code \
  --code "123456"

node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js \
  --mode wait-login \
  --wait-seconds 300
```

Feishu/OpenClaw login loop:

1. Run `--mode status`.
2. If logged in, continue data fetch.
3. If not logged in, run `--mode screenshot` and send the image to Feishu.
4. If the page supports QR login, ask the operator to scan and confirm, then run `--mode wait-login`.
5. If SMS is required, run `--mode click-send-code`, ask the operator for the code in the configured channel, then run `--mode fill-code --code "<code>"` and `--mode wait-login`.
6. The channel can be group or private depending on OpenClaw config. Do not store the code in files unless the user explicitly configures that behavior.

## 有赞后台使用诊断

Use `有赞后台使用诊断` when the user asks whether Youzan functions are being used well, what backend functions are missing, or what Youzan modules should be configured next.

This is not a replacement for the four operating tables. It is a functional diagnosis of the Youzan backend:

- used functions
- underused functions
- unpurchased or locked functions
- data入口 health
- recommended Youzan setup actions

## Output Rules

The workbook should include:

- `00口径说明`
- `01用户分层表`
- `02商品路径表`
- `03分销员质量表`
- `04经营动作表`
- `05话术库`
- `06数据质量检查`
- `07后台巡检摘要` when an audit note exists

A named distributor workbook should include:

- `00口径说明`
- `01业绩总览`
- `02客户明细`
- `03商品结构`
- `04订单明细`
- `05客户动作`
- `06数据质量检查`
- `07文本总结`

Keep action tables executable:

- Use short action text in user rows.
- Put long 1:1 scripts in `05话术库`.
- Use script IDs like `S01`, `S02`, `S03` in action rows.
- Include `yz_open_id` and current nickname together so changed nicknames can still merge correctly.
- In distributor reports, group customers by `yz_open_id`; distributor names are filters, not customer identity.

## Product Categories

Use these categories unless the user gives newer business facts:

- `玉乃光白标`
- `玉乃光黑标`
- `今治毛巾`
- `今治浴巾`
- `AddElm`
- `其他`

Business fact currently known:

- 黑标 and 今治毛巾 were launched as presale links on `2026-05-10`.
- Expected arrival is around `2026-05-31`.
- Interpret black-label orders as presale trust and high-AOV commitment, not ordinary in-stock conversion.

## References

- Read `references/data-sources.md` when operating Youzan backend or explaining where data comes from.
- Read `references/table-rules.md` when adjusting fields, user layers, product paths, distributor scoring, or action rules.
- Read `references/backend-audit.md` when the user asks for a full backend review, OpenClaw/Codex automation, module browsing, locked-feature interpretation, or “老板看后台” analysis.
