# A101 投放数据报表

## 报表入口（名称 · 链接）

本地先在仓库根目录启动静态服务：

```bash
cd /Users/momo/Documents/a101周报数据looker/ua-report-dashboard
python3 -m http.server 8765
```

线上总入口：https://penghuan456ph-code.github.io/ua-report-dashboard/

本地总入口：http://127.0.0.1:8765/

| 报表名称 | 线上链接 |
|---|---|
| AF 日报 | https://penghuan456ph-code.github.io/ua-report-dashboard/af-daily-report.html |
| Ads 日报 | https://penghuan456ph-code.github.io/ua-report-dashboard/ads-daily-report.html |
| Looker 上传分析面板 | https://penghuan456ph-code.github.io/ua-report-dashboard/looker-upload-dashboard.html |
| Yaahlan 分月增长系数 | https://penghuan456ph-code.github.io/ua-report-dashboard/yaahlan-growth-coef-monthly.html |

对应文件都在仓库根目录：`af-daily-report.html` / `ads-daily-report.html` / `looker-upload-dashboard.html` / `yaahlan-growth-coef-monthly.html`。

---

## AF 日报（AppsFlyer）

打开 `af-daily-report.html` 查看 Yaahlan / Yaha 近三日核心表。

- 数据：`data/af-daily-report.json`
- 嵌入构建：`python3 scripts/build_af_daily_html.py`
- 刷新步骤：见 `scripts/REFRESH_AF_DAILY.md`（建议每日北京时间 11:00 前跑一遍）

口径：UTC · Cohort UA；次留仅展示已跑完日；付费人数=`user_recharge` UU；Yaha 注册=`user_register` UU。

## Ads 日报

打开 `ads-daily-report.html`。刷新说明见 `scripts/REFRESH_ADS_DAILY.md`。

## Looker Excel 面板

本地单页 HTML：上传与周报 Looker 导出一致的 Excel，自动生成拆系统 / 拆国家 / 拆渠道分析。

1. 打开 `looker-upload-dashboard.html`（若 CDN 被拦，需联网加载 SheetJS / Chart.js）
2. 拖入或选择 `数据看板-YYYY-MM-DD-wy.67nw.xlsx`
3. 用日期、大区筛选后，切换「拆系统 / 拆渠道 / 拆国家」
4. 可导出当前维度明细为 CSV

### 必需表头

`日期` `大区` `国家` `渠道` `系统` `账面花费` `注册数-排大R`

以及可选但会用于报表的：

- `付费用户数-排大R(0/3/7)`
- `付费金额-排大R(0/3/7/15/30/60/90…)`

### 派生指标

| 指标 | 计算 |
|---|---|
| CPI | 花费 / 注册 |
| 付费率 Dn | 付费用户 Dn / 注册 |
| ROAS Dn | 付费金额 Dn / 花费 |
| ARPPU D0 | 付费金额 D0 / 付费用户 D0 |

数据仅在浏览器本地解析，不会上传服务器。

## Yaahlan 分月增长系数

打开 `yaahlan-growth-coef-monthly.html`。刷新说明见 `scripts/REFRESH_YAAHLAN_GROWTH_COEF.md`。
