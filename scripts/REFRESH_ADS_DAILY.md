# Ads 日报刷新说明

目标：产出与 AF 日报同结构的 **Ads 投后口径**日报。

## 输出文件
- `data/ads-daily-report.json`
- `ads-daily-report.html`（由 `scripts/build_ads_daily_html.py` 嵌入 JSON）

## 日期规则（UTC，与 AF 日报一致）
- `as_of` = 今天（UTC）
- 近三日 = `as_of-3` … `as_of-1`
- `yesterday` = `as_of-1`
- Day0 留存（设备维度）：仅当 `as_of >= date+2` 写入，否则 `null`

## Ads MCP 拉取
App 权限入口为 `app_name=yaahlan`，用 `package` 区分产品：
- Yaahlan：`package IN ["yaahlan"]`
- Yaha：`package IN ["yaha"]`

### 1. Yaahlan 整体近三日（daily）
指标：`cash_cost`, `signup`, `cost_per_signup_oversea`, `activation`, `cost_per_activation_oversea`,
`af_nonr_signup_roas_0`, `signup_pay_user_per_signup`, `af_signup_nonr_pay_user`,
`af_nonr_signup_amount_per_af_signup_nonr_pay_user`

### 2. Yaahlan Android 昨日分渠道（collect）
筛选：`os_name=Android`，`ad_channel IN [googleadwords_int, Facebook Ads, tiktokglobal_int]`，`package=yaahlan`  
同上指标，level=`ad_channel`

### 3. Yaha 整体近三日（daily）
筛选：`package=yaha`  
指标：`cash_cost`, `signup`, `cost_per_signup_oversea`, `activation`, `cost_per_activation_oversea`,
`af_signup_per_activation`, `af_returned_1day_per_af_signup`, `af_nonr_signup_roas_0`

### 4. Yaha Android 近三日分系列（daily × ad_plan_name）
筛选：`package=yaha`，`os_name=Android`  
按系列名分区：`hindi`→印度 / `arabic`→阿语区 / `portuguese`→巴西  
注册率、次留按安装加权；LTV(0)/CAC 按花费加权

## 写回
1. 覆盖写入 `data/ads-daily-report.json`
2. 运行：`python3 scripts/build_ads_daily_html.py`
