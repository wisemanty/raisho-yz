# 更新日志

本文件记录 `raisho-youzan-weekly-analysis` skill 的关键版本变化，方便 OpenClaw 测试、交接和后续每周固定运行。

## 2026-05-25 v0.10.1

### 商品分类修正

- `Add.03...` 这类商品名现在归入 `AddElm`，不再落入 `其他`。
- AddElm 识别规则兼容：
  - `AddElm`
  - `ADELM`
  - `ADDELM`
  - `Add.` 前缀

### 验证

- 已用 `2026-05-18 至 2026-05-25` 数据重跑周报。
- 本期不再出现 `其他` 类目。
- `Add.03福环硅胶项链FULOOPE NECKLACE（周长40cm）` 已归入 `AddElm`。

## 2026-05-25 v0.10.0

### 商品口径修正

- 玉乃光基础酒款统一改称 `玉乃光白标`。
- 原来输出里的 `玉乃光本真/品鉴`、`本真到黑标`、`本真复购` 等经营表达，后续统一改为 `白标` 口径。
- 原始商品名里仍会兼容识别 `玉乃光`、`本真`、`品鉴` 等关键词，但分析表、总结和话术输出统一展示为 `玉乃光白标`。

### 影响范围

- `01用户分层表`、`02商品路径表`、`03分销员质量表`、`04经营动作表`
- Markdown / Word 经营总结
- 单经销商报告中的商品结构、客户明细和动作建议

## 2026-05-18 v0.9.0

### 口径修正

- 复购客户数/复购率改为按 `购买会话数` 计算：
  - 同一 `yz_open_id` 在同一自然日内多笔有效订单，只算 1 次购买会话。
  - 复购客户 = 购买会话数 >= 2 的客户。
- 原因：
  - 当前部分商品只有 1 瓶装和 2 瓶装，客户想多买时可能在同一天拆成多笔订单。
  - 黑标、今治毛巾/浴巾为 2026-05-10 新上预售，约 2026-05-31 到货；预售期同日追加不应被误算成体验后的复购。

### 输出变化

- `01用户分层表` 和单经销商 `02客户明细` 新增 `购买会话数`。
- `03分销员质量表` 和单经销商 `01业绩总览` 的 `复购客户数`、`复购率` 使用购买会话口径。
- `00口径说明`、`07/06数据质量检查`、Markdown/Word 经营总结均写入复购统计口径，避免周报使用者误读。

### 边界说明

- 本次只修正复购数/复购率等统计指标。
- 用户标签里的 `复购用户` 暂仍保留为经营提示信号，不在本版本里扩大修改，以免影响现有动作框架。

## 2026-05-18 v0.8.0

### 新增

- 周度经营分析新增 Word 版总结：
  - `经营分析总结_<week>.md`
  - `经营分析总结_<week>.docx`
- 新增脚本：
  - `scripts/build_operating_summary.py`
- `raisho-yz run weekly` 现在会在生成四张表后，自动读取 workbook 和区间明细，生成 Markdown + Word 两份经营分析总结。

### 总结内容

- 数据口径
- 一句话判断
- 商品结构
- 用户结构
- 重点用户
- 商品路径
- 分销员表现
- 已成立/未成立的经营判断
- 本周经营动作
- 下周验证点

### 目的

- 以后经营分析不仅保留机器可读的 Excel 和 Markdown，也能直接交付一份适合汇报、转发和存档的 Word 文件。

## 2026-05-18 v0.7.0

### 效率优化

- `raisho-yz` 命令默认优先使用 Codex bundled Python：
  - `/Users/wisemantong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`
  - 避免系统 `python3` 缺少 `pandas/openpyxl` 时先失败一次。
- `raisho-yz run weekly` 支持日期过滤参数：
  - `--start YYYY-MM-DD`
  - `--end YYYY-MM-DD`
  - 脚本会先从全量明细生成区间明细，再用区间明细跑四张表。
- CDP 自动取数脚本支持登录后的自动选店：
  - 默认识别 `RAISHO来处`
  - 自动点击 `进入工作台`
  - 可用 `--shop-name` 覆盖，可用 `--no-auto-select-shop` 关闭。
- 登录辅助脚本新增：
  - `--mode select-shop`
  - `wait-login` 轮询时会尝试自动进入默认店铺。

### 口径强化

- 四张表和单经销商报告新增分销员口径提示：
  - 买家客户按 `yz_open_id` 去重。
  - 分销员当前按昵称字段聚合/筛选。
  - 若要避免分销员改名或重名，后续需要接入分销员 ID / 手机号导出。

### 推荐用法

```bash
raisho-yz run weekly \
  --week-label "2026-05-10_to_2026-05-18" \
  --detail "/path/to/来处订单商品明细_yz_open_id.xlsx" \
  --start 2026-05-10 \
  --end 2026-05-18
```

## 2026-05-14 v0.6.0

### 命名

- skill 名称改为：`raisho-yz`
- 中文名：`来处有赞经营分析`
- 推荐 GitHub 仓库名：`raisho-yz`
- 推荐命令名：`raisho-yz`

### 新增

- 新增命令行管理脚本：
  - `bin/raisho-yz`
- 支持命令：
  - `raisho-yz version`
  - `raisho-yz validate`
  - `raisho-yz package`
  - `raisho-yz update`
  - `raisho-yz run weekly ...`
  - `raisho-yz run distributor ...`
  - `raisho-yz run backend-audit ...`
- 新增 `.gitignore`，避免提交本地周报、原始数据、Excel、zip、日志、token/cookie 等文件。

### 目的

- 支持把 skill 托管到 GitHub。
- 后续 WorkBuddy/OpenClaw/本机可以通过 `raisho-yz update` 拉取最新版本、校验并重新打包。

## 2026-05-14 v0.5.1

### 打包文件

- 版本包：`raisho-youzan-weekly-analysis-v0.5.1.zip`
- 最新包副本：`raisho-youzan-weekly-analysis-latest.zip`

### 新增

- 新增内置中文使用说明：
  - `README.md`
- 说明覆盖：
  - skill 是做什么的
  - 周度四张表、单经销商分析、后台使用诊断分别输出什么
  - 有赞数据从哪里来
  - CDP 自动取数和登录辅助怎么跑
  - OpenClaw/飞书登录协作方式
  - v0.5.0 之后的动态判断逻辑
  - 常见检查项

### 目的

- 让 WorkBuddy、OpenClaw 或同事拿到压缩包后，不只依赖 `SKILL.md` 给 agent 读取，也能直接阅读一份人类可理解的使用说明。

## 2026-05-14 v0.5.0

### 打包文件

- 版本包：`raisho-youzan-weekly-analysis-v0.5.0.zip`
- 最新包副本：`raisho-youzan-weekly-analysis-latest.zip`

### 变更

- 用户优先级从固定金额门槛升级为动态判断：
  - agent 先读取当周用户数据分布。
  - 高客单按当周客单价/累计实付百分位判断。
  - P0/P1/P2/P3 叠加黑标、预售、复购、分销关系等信号。
  - 不再要求老板每周手动调整金额阈值。
- 四张表新增解释型字段：
  - `命中规则`
  - `判断原因`
  - `建议置信度`
  - `是否需人工复核`
- 新增 `06规则校准说明` 工作表：
  - 记录本次自动校准出的高客单线、高累计支付线、重点累计支付线和生成逻辑。
- 话术从固定 S01-S05 升级为场景话术族：
  - `S01A` 今治/新买家收货反馈
  - `S02A` 黑标预售高信任维护
  - `S02B` 白标/高客单到黑标升级
  - `S02C` 高价值但信号不清晰的人工复核
  - `S03A` 复购用户会员/社群承接
  - `S04A` 分销转化支持
  - `S05A` 低信号轻触达
- 分销员质量判断从固定 `3000` 成交门槛升级为动态解释：
  - 优先看黑标客户、复购客户、高客单客户。
  - 有分销员分布时比较成交额和客户数百分位。
  - 输出 `判断原因`，避免只给“重点培养/可培养”的结论。
- 单经销商业绩分析同步使用动态客户分层，并在客户动作中输出命中规则、判断原因、置信度和人工复核标记。

### 口径

- 老板只定义经营原则；agent 根据每周数据自动校准执行阈值。
- 黑标和今治仍按 2026-05-10 预售、约 2026-05-31 到货的生命周期处理。
- 高金额但无复购/无黑标/无明确关系来源的客户会被标记为需要人工复核，避免机械强推。

## 2026-05-12 v0.4.0

### 打包文件

- 版本包：`raisho-youzan-weekly-analysis-v0.4.0.zip`
- 最新包副本：`raisho-youzan-weekly-analysis-latest.zip`
- 后续所有交付压缩包必须带版本号，格式为：
  - `raisho-youzan-weekly-analysis-vX.Y.Z.zip`

### 新增

- 新增 CDP 直连取数脚本：
  - `scripts/fetch_custompeek_report_cdp.js`
  - 用途：连接已登录的 Chrome DevTools Protocol 会话，查找 `来处订单商品明细_yz_open_id`，提交重新导出，轮询完成，自动下载原始数据。
- 新增 CDP 登录辅助脚本：
  - `scripts/youzan_login_assist_cdp.js`
  - 用途：检测有赞登录态、截图登录页/二维码、点击发送验证码、填写验证码、等待登录成功。
- 新增飞书登录协作方案：
  - 支持把登录页或二维码截图发到飞书群或私聊。
  - 支持同事在飞书回复验证码后由脚本代填。
  - `channel` 可配置为 `group` 或 `private`。
- 单经销商业绩分析明确支持无 Computer Use 链路：
  - CDP 自动取数。
  - 本地按 `分销员` 字段筛选。
  - 用 `yz_open_id` 合并客户。
  - 输出 Excel 和 Markdown 总结。

### 验证

- CDP 登录态检测已在本机跑通：
  - `youzan_login_assist_cdp.js --mode status`
  - 返回 `loggedIn: true`。
- CDP 页面截图已在本机跑通：
  - 输出 `/Users/wisemantong/Desktop/有赞后台分析/周报/CDP脚本验证/youzan-current-page.png`。
- CDP 核心数据下载已跑通：
  - 报表名：`来处订单商品明细_yz_open_id`
  - 报表 ID：`436628`
  - 模型：`交易-订单&商品`
  - 下载结果：`325 行 x 24 列`
- 四张经营表端到端验证通过：
  - 输出 `/Users/wisemantong/Desktop/有赞后台分析/周报/CDP端到端验证/来处有赞周度四张表_2026-W20-CDP.xlsx`
- Jeff 单经销商业绩分析端到端验证通过：
  - 输出 `/Users/wisemantong/Desktop/有赞后台分析/周报/CDP单经销商验证/Jeff/分销商业绩分析_Jeff_2026-W20-CDP.xlsx`
  - 输出 `/Users/wisemantong/Desktop/有赞后台分析/周报/CDP单经销商验证/Jeff/分销商业绩总结_Jeff_2026-W20-CDP.md`

### 口径确认

- 用户主键必须使用 `yz_open_id`。
- 单经销商筛选默认只使用 `分销员` 字段。
- `分销团队` 只作为展示和辅助判断，不额外纳入团队订单。
- 当前 Jeff 默认包含匹配与 `--exact Jeff` 精确匹配结果一致。

### 已知坑位

- 有赞下载文件可能显示为 `.csv` 和 `text/csv`，但真实字节是 XLSX。脚本按文件头自动识别并改后缀。
- 有赞生成的 XLSX 可能写入错误的 `dimension ref="A1"`。不要只用 `openpyxl` 只读模式的 `max_row/max_column` 判断是否为空；优先用 `pandas.read_excel` 或四表脚本验证。
- CDP 取数要求 Chrome 已用 `--remote-debugging-port=9222` 启动，并且保留有效有赞登录态。
- 后台功能巡检仍需要 Computer Use 或浏览器页面自动化；经营数据取数和分析已基本不需要 Computer Use。

### OpenClaw 使用提示

- 数据取数首选：

```bash
node scripts/fetch_custompeek_report_cdp.js \
  --output-dir "/Users/wisemantong/Desktop/有赞后台分析/周报/YYYY-WW/原始数据" \
  --report-name "来处订单商品明细_yz_open_id"
```

- 登录辅助首选：

```bash
node scripts/youzan_login_assist_cdp.js --mode status
node scripts/youzan_login_assist_cdp.js --mode screenshot --output "/path/to/youzan-login.png"
node scripts/youzan_login_assist_cdp.js --mode click-send-code
node scripts/youzan_login_assist_cdp.js --mode fill-code --code "123456"
node scripts/youzan_login_assist_cdp.js --mode wait-login --wait-seconds 300
```

## 2026-05-12 v0.3.0

### 新增

- 新增有赞后台使用诊断模式：
  - 中文名：`有赞后台使用诊断`
  - 脚本模式：`--mode backend-audit`
- 新增后台巡检记录模板和诊断报告生成脚本：
  - `scripts/create_audit_note.py`
  - `scripts/create_backend_audit_report.py`
- 新增 OpenClaw 调用 Codex CLI / Codex app-server 说明书。

### 变更

- `scripts/run_analysis.py` 成为 OpenClaw 和重复运行的总控入口。
- 明确区分四张经营表与后台功能诊断：
  - 四张表回答经营结果和用户动作。
  - 后台诊断回答有赞功能是否被用起来、哪些入口需要配置。

## 2026-05-12 v0.2.0

### 新增

- 新增单经销商业绩分析：
  - `scripts/build_distributor_report.py`
  - 支持 `--distributor "Jeff"` 这类点名分析。
  - 输出 Excel 和 Markdown 总结。
- 分销商报告包含：
  - `00口径说明`
  - `01业绩总览`
  - `02客户明细`
  - `03商品结构`
  - `04订单明细`
  - `05客户动作`
  - `06数据质量检查`
  - `07文本总结`

### 口径

- 买家合并使用 `yz_open_id`。
- 分销商统计以核心订单商品明细为主，分销员列表导出只做辅助解释。

## 2026-05-11 v0.1.0

### 新增

- 创建来处有赞周度四表分析 skill。
- 建立固定框架：
  - `数据 -> 用户 -> 行为 -> 信任 -> 动作`
- 生成四张核心经营表：
  - `01用户分层表`
  - `02商品路径表`
  - `03分销员质量表`
  - `04经营动作表`
- 强制要求核心明细必须包含 `yz_open_id`。

### 初始数据源

- 有赞路径：
  - `数据 -> 数据报表 -> 自助取数 -> 我的取数`
- 核心报表：
  - `来处订单商品明细_yz_open_id`
