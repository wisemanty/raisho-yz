# Data Sources And Youzan Export Paths

Use this reference when collecting or explaining data sources for the weekly RAISHO Youzan analysis.

## Core Data: Order-Item Detail With `yz_open_id`

This is the mandatory file.

Use this same file for:

- weekly four-table analysis
- product path analysis
- distributor quality table
- named distributor reports such as `Jeff 的业绩分析`

Backend path:

1. Open Youzan backend and log in.
2. Go to `数据 -> 数据报表 -> 自助取数`.
3. Open `我的取数`.
4. Find `来处订单商品明细_yz_open_id`.
5. If it exists, click `下载`, `下载记录`, or `详情` as needed.
6. If it does not exist:
   - Click `新建报表`.
   - Choose `新建明细报表`.
   - Go to `字段设置`.
   - Click `添加字段`.
   - Choose field group `订单&商品`.
   - Select the required fields below.
   - Name it `来处订单商品明细_yz_open_id`.
   - Save, execute, wait for success, then download.

Required fields:

- 客户昵称
- 手机号
- yz_open_id
- 来源渠道
- 来源方式
- 客户标签
- 订单号
- 订单实收
- 订单状态
- 支付时间
- 下单时间
- 商品ID
- 商品名称
- 商品规格
- 订单金额
- 商品销售金额
- 商品实收金额
- 商品销售件数
- 销售渠道
- 分销员
- 分销团队
- 是否是免费等级会员
- 是否是付费等级会员
- 是否有权益卡

## Preferred Automated Route: CDP Direct Export

When manual download is not acceptable, prefer this route before falling back to Computer Use.

Prerequisite:

1. Start a separate Chrome profile with remote debugging:

   ```bash
   open -na "Google Chrome" --args \
     --remote-debugging-port=9222 \
     --user-data-dir="/Users/wisemantong/Desktop/有赞后台分析/chrome-youzan-cdp-profile" \
     https://www.youzan.com/v4/statcenter/custompeek/index
   ```

2. Ask the user only to log in, enter CAPTCHA, or approve security verification.
3. Never print cookies, csrf tokens, access tokens, signed file URLs, or password fields.

Automated command:

```bash
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/fetch_custompeek_report_cdp.js \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/原始数据" \
  --report-name "来处订单商品明细_yz_open_id"
```

Login assist command set:

```bash
# Check whether the Youzan API is logged in.
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js --mode status

# Save the current login page or QR code screenshot for Feishu.
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js \
  --mode screenshot \
  --output "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/巡检证据/youzan-login.png"

# Try to click a visible send-code button.
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js --mode click-send-code

# Fill a code received from Feishu and submit.
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js --mode fill-code --code "123456"

# Wait until login succeeds.
node /Users/wisemantong/.codex/skills/raisho-youzan-weekly-analysis/scripts/youzan_login_assist_cdp.js --mode wait-login --wait-seconds 300
```

Feishu login interaction can be configured in two ways:

- `group`: send screenshots and request verification codes in the group where the task was triggered.
- `private`: send screenshots and request verification codes in a direct message to the triggering operator.

The skill supports either mode. The OpenClaw deployment owner decides which channel is appropriate.

Observed endpoint map from 2026-05-12 testing:

- List/detail reports: `/v4/statcenter/custompeek/api/queryReport.json`
- Get report by ID: `/v4/statcenter/custompeek/api/queryReportById.json`
- Field/model metadata: `/v4/statcenter/custompeek/api/getModels.json`
- Submit fresh export: `/v4/statcenter/custompeek/api/reExport.json`
- Download generated file: `/v4/statcenter/custompeek/api/getDownload.json`
- New detail report page: `/v4/statcenter/customreport/detail-data`
- New detail report field enums: `/v4/statcenter/customreport/detail-data/getFieldEnums.json`

Observed required model and field metadata:

- Model: `交易-订单&商品`
- Model ID: `22`
- Table: `dm_dc.tc_order_item_export`
- `yz_open_id` field: `id=455`, `fieldTableName=yz_openid`
- Distributor fields:
  - `分销员`: `id=487`, `fieldTableName=salesman_nickname`
  - `分销团队`: `id=488`, `fieldTableName=salesman_group_name`

Observed existing report from 2026-05-12:

- Report name: `来处订单商品明细_yz_open_id`
- Report ID: `436628`
- Model: `交易-订单&商品`
- Existing fields match the current required field list.

Important status behavior:

- `status=1` appeared as `执行中` in the UI.
- `status=2` is completed/downloadable.
- Do not download a newly submitted export while it is still `执行中`; poll until completion or time out.
- Youzan may return a file URL with a `.csv` name and `text/csv` content type while the actual file bytes are OOXML/XLSX. Detect file type from magic bytes and rename to `.xlsx` when the file starts with `PK`.
- Some Youzan-generated XLSX files set an incorrect sheet dimension such as `A1`; `openpyxl` read-only `max_row` can look empty even when the XML has data. Validate with `pandas.read_excel` or parse actual rows before declaring the export empty.

Acceptance checks:

- `yz_open_id` exists and is populated for paid rows.
- A usable order time exists: prefer `支付时间`, otherwise `下单时间`.
- A status field exists for filtering invalid orders.
- Product name or product ID exists.
- A real amount field exists.
- Distributor fields exist if distributor quality will be reported.
- For named distributor reports, the distributor field must be populated enough to match the requested name.

Known current report status from 2026-05-11:

- Report name: `来处订单商品明细_yz_open_id`
- Location: `数据 -> 数据报表 -> 自助取数 -> 我的取数`
- Status: `执行成功`
- Created at: `2026-05-11 15:24:09`
- Recent export time: `2026-05-11 15:28:43`

## Auxiliary Data: Customer Export

Purpose:

- Add customer tags, membership, source, recent browse, and recent consumption context.
- Do not use as final user identity unless it contains `yz_open_id`, `yzUid`, or `buyer_id`.

Backend path:

1. Go to `客户`.
2. Open `客户管理 -> 客户列表`.
3. Page shape: `/v4/scrm/customer/manage`.
4. Set filters such as:
   - 上次消费时间
   - 成为客户时间
   - 成为会员时间
   - 关键词
   - 来源渠道
   - 来源方式
   - 分销员
   - 标签
   - 购买次数
   - 笔单价
   - 累计消费金额
5. Click `筛选`.
6. Click `导出`.
7. Use `查看已导出列表` for historical exports.

Important:

- Customer detail URLs can contain `yzUid`, but the checked batch customer export did not include a stable ID.
- Treat this as auxiliary unless stable ID fields are present in the exported file.

## Auxiliary Data: Order And Product Reports

Purpose:

- Reconcile order amounts, statuses, refunds, product payment count, and product payment amount.
- These reports are not the primary user-level source when they lack `yz_open_id`.

Backend path:

1. Go to `订单`.
2. Open `订单管理 -> 订单管理`.
3. Page shape: `/v4/trade/order/index`.
4. Set filters:
   - `时间搜索`: use `下单时间` for weekly exports unless the user specifies otherwise.
   - Fill week start/end.
   - Keep `订单状态` as all if local filtering will be done later.
   - Optionally filter product, promotion, after-sale, logistics, source, payment, or amount.
5. Click `筛选`.
6. Click `导出`.
7. Click `查看已导出列表`.
8. On `/v4/trade/order/export-list`, download:
   - `下载订单报表`
   - `下载商品报表`

Security note:

- Youzan may require SMS verification before downloading. Ask the user to enter the code.

## Auxiliary Data: Distributor Export

Purpose:

- Identify distributor base information, status, cumulative sales, commission, customers, and invitations.
- Final distributor quality still comes from the core detail file grouped by buyer `yz_open_id`.
- For a named distributor report, use this export only as supplementary context or to resolve display-name ambiguity. Do not replace buyer-level statistics from `来处订单商品明细_yz_open_id`.

Backend path:

1. Go to `分销员`.
2. Open `分销员管理 -> 分销员列表`.
3. Page shape: `/v4/salesman/promoter/list`.
4. Set filters:
   - 加入时间
   - 分销员手机号或昵称
   - 分组
   - 等级
   - 邀请方
   - 团队
5. Click `筛选`.
6. Click `导出`.
7. Use `查看已导出列表` for historical exports.

Supplementary page:

- `分销员 -> 分销员管理 -> 数据概览` shows core summary, trends, distributor ranking, product deal analysis, and detail links.
- Use this page for explanation and directional judgment; use exported rows for final tables.

Named distributor backend flow:

1. If the user asks for `某分销商的业绩分析`, first locate or export `来处订单商品明细_yz_open_id`.
2. If the report is stale, execute a fresh export for the requested week/date range.
3. Prefer CDP direct export and download through `scripts/fetch_custompeek_report_cdp.js`; do not ask the user to download it manually.
4. Use Computer Use only for login/CAPTCHA/security confirmation or if the CDP route is unavailable.
5. Run `scripts/build_distributor_report.py` with `--distributor "<name>"`.
6. Default single-distributor口径 filters only the `分销员` field. `分销团队` is output as context and does not include extra rows unless doing explicit team-level analysis.
7. If the distributor name does not match any rows, check `分销员 -> 分销员列表` for display-name variants, team, invitation relation, or inactive status.

## Page Browsing Rule

When browsing Youzan pages:

1. Confirm the time range.
2. Scroll from top to bottom.
3. Check horizontal table scroll where present.
4. Switch tabs and filters.
5. Inspect pagination.
6. Click details, trends, and card arrows.
7. Prefer export/download over manual copying.
8. For unpurchased modules, record function descriptions but do not treat demo data as real data.
