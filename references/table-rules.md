# Weekly Table Rules

Use this reference when generating or modifying the four weekly operating tables.

## Identity Rule

- Primary key: `yz_open_id`.
- Display fields: latest customer nickname, historical nicknames, masked phone.
- Never split a user because nickname or phone changed.
- Keep raw IDs in the workbook so future weeks can be merged.

## Valid Order Rule

Prefer order status filtering from the export.

Exclude rows whose status clearly contains:

- 关闭
- 取消
- 未支付
- 待付款
- 退款成功
- 全额退款

Keep rows such as:

- 等待商家发货
- 已发货
- 已完成
- 交易成功
- 已支付

If status semantics are unclear, keep rows and flag the ambiguity in `06数据质量检查`.

## Repurchase Metric Rule

Use purchase sessions for repurchase counts and rates.

- Purchase session key: same `yz_open_id` + same natural purchase date.
- Same user, same day, multiple effective orders = 1 purchase session.
- `复购客户数`: customers with purchase sessions >= 2.
- `复购率`: `复购客户数 / 去重客户数`.

Reason:

- Current sake options may be limited to 1-bottle and 2-bottle choices, so same-day split orders can simply mean quantity replenishment.
- Black-label and Imabari towel/bath towel were new presale links on 2026-05-10, with expected arrival around 2026-05-31. Same-day presale additions should not be treated as post-experience repurchase.

Only repurchase count/rate metrics must use this stricter session rule. Other operating signals can still show effective order count as context, as long as the workbook explains the difference.

## User Layering

Assign tag-style layers, not only one exclusive segment.

Suggested layers:

- `尝鲜用户`: 1 effective order and not high-AOV.
- `复购用户`: 2+ effective orders as an operating signal. For official repurchase count/rate, use the purchase-session rule above.
- `高客单用户`: agent-calibrated high value signal based on the current run's AOV/cumulative paid distribution. Do not use a permanent fixed amount as the only criterion.
- `黑标潜力用户`: bought black label, or bought sake with relatively strong AOV/cumulative paid signal but no black label yet.
- `分销潜力用户`: has distributor relationship, repeated purchases, or visible sharing/distribution behavior.

Priority for action:

- `P0`: high trust or high money signal; usually needs 1:1, but the table must show the exact reason.
- `P1`: repeatable conversion or clear upgrade path.
- `P2`: fresh or low-risk nurturing.
- `P3`: weak signal, observe or automate.

Required explanation columns:

- `命中规则`: machine-readable rule names such as `dynamic_high_value`, `black_label_potential`, `repeat_order`.
- `判断原因`: human-readable evidence, including percentile position and product lifecycle where relevant.
- `建议置信度`: high/medium/low confidence based on number and quality of signals.
- `是否需人工复核`: mark edge cases, especially high-value but no repeat/no black-label signal.

The agent, not the owner, should recalibrate weekly thresholds from the data. The owner only sets business principles such as "black label means high trust" or "Imabari can be a referral product".

## Product Path

Build product paths only from the same `yz_open_id` sorted by order time.

Useful fields:

- first category
- recent category
- purchased categories
- ordered category sequence
- transition from first category to next category
- transition users
- transition amount
- typical users

Do not infer trust migration without a user-level sequence.

## Distributor Quality

Group by distributor display name from the core order-item detail.

Metrics:

- unique customers by `yz_open_id`
- effective orders
- cumulative paid
- average order value
- repeat customers
- repeat rate
- high-AOV customers
- black-label customers
- main categories
- quality judgment
- judgment reason
- cultivation action

Interpretation:

- Repeat customers and repeat rate must use purchase sessions, not raw same-day order count.
- A distributor with few customers but high AOV can be valuable.
- A distributor with sharing/browsing but no paid orders is a content or trust-nurture candidate.
- A distributor with registered status but no customer/order signal is inactive until proven otherwise.
- Avoid permanent fixed thresholds such as "paid >= 3000 is always key". Compare distributor paid/customer scale against the current distributor distribution when available, then explain the evidence.

## Named Distributor Report

Use this when the user asks for one distributor/promoter, such as `Jeff 的业绩分析`.

Data source:

- Primary: core order-item detail with `yz_open_id`.
- Filter field: `分销员`, `分销员昵称`, or `推广员`.
- Customer identity: always `yz_open_id`, not nickname or phone.

Required metrics:

- matched distributor display names
- unique customers by `yz_open_id`
- effective orders
- cumulative paid
- average order value
- repeat customers
- repeat rate
- high-AOV customers
- black-label customers
- product/category structure
- top customers and next actions

Required output:

- text business summary in Markdown
- organized performance workbook
- performance overview
- customer detail
- product structure
- order detail
- customer action table
- data quality check

The report must not stop at numbers. It should explicitly say:

- whether the distributor is worth cultivating
- which customers need owner/core-operator 1:1
- which customers can be followed by the distributor
- which product materials the distributor should receive next
- what to verify next week

Interpretation:

- High AOV with few customers means the distributor may have a small but valuable trust circle.
- Many customers with low repeat means the distributor can spread but needs repurchase materials.
- Black-label customers mean high-trust presale ability; owner or core operation should join the 1:1 follow-up.
- No matched rows means do not conclude the distributor is inactive; first check nickname spelling, date range, export freshness, and whether the distributor export has a different display name.

## Operating Actions

Actions should be concrete and short in the table. Put long scripts in a speech library.

Default script families:

- `S01A`: Imabari/new buyer delivery and usage feedback.
- `S02A`: black-label presale buyer 1:1 trust maintenance.
- `S02B`: sake/high-value buyer upgrade from white-label/basic tasting to black label.
- `S02C`: high-value but unclear-signal manual review before strong 1:1.
- `S03A`: repeat buyer membership/group invitation.
- `S04A`: distributor nurturing and material support.
- `S05A`: low-signal automated content touch.

Suggested action mapping:

- 黑标 or high-AOV: 1:1 follow-up, ask feedback, explain presale rhythm, offer next allocation.
- 白标 -> 黑标 potential: compare rice, aroma, and occasion; invite black-label tasting or reservation.
- 今治毛巾/bath towel: ask use/texture feedback, encourage gift or referral scenario.
- one-time low-AOV buyer: light group/content nurture, do not over-sell.
- repeat buyer: invite membership, points, private group, or early access.
- distributor with customers/orders: provide specific product copy and conversion feedback.
- inactive distributor: send one onboarding package; stop manual chasing if no response.

## Weekly Summary

Always answer these:

1. Which part of the trust system has started to work?
2. Which part is not yet working?
3. Which product is acting as entry, profit, trust upgrade, or referral carrier?
4. Which distributor deserves cultivation?
5. What should be done this week?
6. What should be verified next week?
