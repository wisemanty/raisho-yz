# 来处有赞经营分析 Skill 使用说明

命令名：`raisho-yz`

GitHub 仓库建议名：`raisho-yz`

## 这个 skill 是做什么的

这个 skill 用来每周自动分析来处有赞后台数据。

它不是只看销售额，而是围绕：

`数据 -> 用户 -> 行为 -> 信任 -> 动作`

输出适合周一经营会投屏的 Word 周总结，并保留 Excel 作为底层数据追溯。

## 能输出什么

### 1. 周度经营总结

输出文件：

- `经营分析总结_<week>.md`
- `经营分析总结_<week>.docx`
- `来处有赞周度四张表_<week>.xlsx`

Word 是开会主文件，固定大纲：

1. 本周一句话结论
2. 核心数据看板
3. 本周变化
4. 商品经营判断
5. 客户经营池
6. 分销员排行与经营判断
7. 本周经营动作复盘
8. 下周行动清单
9. 下周要验证的问题
10. 附录：数据口径

Excel 是支撑文件，用于追溯明细和检查口径。

核心工作表：

- `01用户分层表`
- `02商品路径表`
- `03分销员质量表`
- `04经营动作表`
- `05话术库`
- `06规则校准说明`
- `07数据质量检查`

### 2. 单经销商业绩分析

例如用户问：

```text
Jeff 的业绩分析来一个
```

输出：

- `分销商业绩分析_Jeff_<week>.xlsx`
- `分销商业绩总结_Jeff_<week>.md`

内容包括：

- 带来客户数
- 有效订单数
- 累计实付
- 客单价
- 复购率
- 高客单客户数
- 黑标客户数
- 客户动作清单
- 是否值得继续培养

复购率和复购客户数使用 `购买会话数` 计算：同一用户同一自然日内多笔有效订单，只算 1 次购买会话。这样可以避免 1 瓶/2 瓶规格导致的同日拆单，以及黑标、今治预售期同日追加订单，把复购率虚高。

### 3. 有赞后台使用诊断

输出：

- `后台巡检记录.md`
- `有赞后台使用诊断报告_<week>.md`

用于判断有赞后台哪些功能已经用起来，哪些还没有成为来处的经营基础设施。

## 数据从哪里来

核心数据来自有赞后台自助取数：

```text
数据 -> 数据报表 -> 自助取数 -> 我的取数
```

核心报表名：

```text
来处订单商品明细_yz_open_id
```

必须包含：

- `yz_open_id`
- 订单号
- 订单状态
- 支付时间或下单时间
- 商品名称
- 实收金额
- 分销员字段

`yz_open_id` 是唯一用户主键。昵称和手机号只用于展示，不能作为合并用户的依据。

复购统计口径：

- 客户合并：按 `yz_open_id`。
- 购买会话：同一 `yz_open_id` + 同一自然日 = 1 次购买会话。
- 复购客户数：购买会话数 >= 2。
- 复购率：复购客户数 / 去重客户数。
- 原因：当前酒类规格可能造成同日拆单；黑标和今治为 2026-05-10 新上预售，约 2026-05-31 到货，预售期同日追加不能等同于体验后的复购。

## 自动取数方式

优先使用 CDP 直连有赞接口，不要求人工下载。

启动 Chrome：

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir="/Users/wisemantong/Desktop/有赞后台分析/chrome-youzan-cdp-profile" \
  https://www.youzan.com/v4/statcenter/custompeek/index
```

自动导出报表：

```bash
node scripts/fetch_custompeek_report_cdp.js \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/原始数据" \
  --report-name "来处订单商品明细_yz_open_id"
```

如果没有登录，用登录辅助脚本：

```bash
node scripts/youzan_login_assist_cdp.js --mode status
node scripts/youzan_login_assist_cdp.js --mode screenshot --output "/path/to/youzan-login.png"
node scripts/youzan_login_assist_cdp.js --mode click-send-code
node scripts/youzan_login_assist_cdp.js --mode fill-code --code "123456"
node scripts/youzan_login_assist_cdp.js --mode wait-login --wait-seconds 300
```

OpenClaw 可以把截图发到飞书群或私聊，让同事扫码或回复验证码。

## 运行周度四张表

```bash
raisho-yz run weekly \
  --week-label "YYYY-WW" \
  --detail "/path/to/来处订单商品明细_yz_open_id.xlsx"
```

如果要分析指定日期区间：

```bash
raisho-yz run weekly \
  --week-label "2026-05-10_to_2026-05-18" \
  --detail "/path/to/来处订单商品明细_yz_open_id.xlsx" \
  --start 2026-05-10 \
  --end 2026-05-18
```

脚本会先从全量明细生成区间明细，再用区间明细生成四张表。

## 运行单经销商分析

```bash
raisho-yz run distributor \
  --week-label "YYYY-WW" \
  --detail "/path/to/来处订单商品明细_yz_open_id.xlsx" \
  --distributor "Jeff"
```

## 运行后台使用诊断

```bash
raisho-yz run backend-audit \
  --week-label "YYYY-WW" \
  --date-range "YYYY-MM-DD 至 YYYY-MM-DD"
```

## 安装和更新

推荐把 GitHub 仓库克隆到 Codex skills 目录：

```bash
git clone https://github.com/wisemanty/raisho-yz.git ~/.codex/skills/raisho-yz
```

把命令加入 PATH：

```bash
ln -sf ~/.codex/skills/raisho-yz/bin/raisho-yz ~/.local/bin/raisho-yz
```

以后更新：

```bash
raisho-yz update
```

常用命令：

```bash
raisho-yz version
raisho-yz validate
raisho-yz package
raisho-yz update
```

`raisho-yz` 默认优先使用 Codex bundled Python，避免系统 Python 缺少 pandas/openpyxl。需要指定 Python 时可以：

```bash
PYTHON_BIN=/path/to/python raisho-yz run weekly ...
```

## v0.5.0 之后的判断方式

这个 skill 不要求老板每周手动调整阈值。

老板只定义经营原则，例如：

- 黑标代表高信任
- 今治适合收货反馈和转介绍
- 白标适合复购和向黑标升级
- 分销员要看带客能力，不只看自己买多少

agent 每次会根据当周数据自动校准：

- 高客单线
- 高累计支付线
- 重点用户
- 重点分销员

并在表里写明：

- `命中规则`
- `判断原因`
- `建议置信度`
- `是否需人工复核`

所以不要只看 P0/P1，要重点看判断原因。

## 常见检查

如果结果不对，先检查：

- `06/07数据质量检查` 里是否缺少 `yz_open_id`
- 原始数据是否为最新导出
- 分销员名字是否发生变化
- 分销员统计目前是否只按昵称聚合；如果要解决改名/重名，要补充分销员 ID 或手机号导出
- 复购率是否按 `购买会话数` 计算，而不是直接按同日多笔订单计算
- 订单状态是否包含未支付、取消、退款
- 有赞导出的 `.csv` 是否其实是 XLSX 文件
- WorkBuddy/OpenClaw 是否使用了最新版本包

## 当前正式交付包

正式包必须带版本号：

```text
raisho-youzan-weekly-analysis-vX.Y.Z.zip
```

`raisho-yz-latest.zip` 是最新副本，方便测试。
