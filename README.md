# A101 投放数据分析面板

## AF 日报（AppsFlyer）

打开 `af-daily-report.html` 查看 Yaahlan / Yaha 近三日核心表。

- 数据：`data/af-daily-report.json`
- 嵌入构建：`python3 scripts/build_af_daily_html.py`
- 刷新步骤：见 `scripts/REFRESH_AF_DAILY.md`（建议每日北京时间 11:00 前跑一遍）

口径：UTC · Cohort UA；次留仅展示已跑完日；付费人数=`user_recharge` UU；Yaha 注册=`user_register` UU。

## Looker Excel 面板

本地单页 HTML 报表：上传与周报 Looker 导出一致的 Excel，自动生成拆系统 / 拆国家 / 拆渠道分析。

## 使用方法

1. 用浏览器打开 `index.html`（双击即可；若 CDN 被拦，需联网加载 SheetJS / Chart.js）
2. 拖入或选择 `数据看板-YYYY-MM-DD-wy.67nw.xlsx`
3. 用日期、大区筛选后，切换「拆系统 / 拆渠道 / 拆国家」
4. 可导出当前维度明细为 CSV

## 必需表头

`日期` `大区` `国家` `渠道` `系统` `账面花费` `注册数-排大R`

以及可选但会用于报表的：

- `付费用户数-排大R(0/3/7)`
- `付费金额-排大R(0/3/7/15/30/60/90…)`

## 派生指标

| 指标 | 计算 |
|---|---|
| CPI | 花费 / 注册 |
| 付费率 Dn | 付费用户 Dn / 注册 |
| ROAS Dn | 付费金额 Dn / 花费 |
| ARPPU D0 | 付费金额 D0 / 付费用户 D0 |

数据仅在浏览器本地解析，不会上传服务器。
