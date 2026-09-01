# AF 日报刷新说明（供 Agent / Automation 每日执行）

目标：在**北京时间 11:00 前**更新 `af-daily-report.html`。

## 输出文件
- `data/af-daily-report.json`
- `af-daily-report.html`（由 `scripts/build_af_daily_html.py` 嵌入 JSON）

## 日期规则（UTC）
- `as_of` = 今天（UTC 日期）
- 近三日 = `as_of-3` … `as_of-1`（不含今天）
- `yesterday` = `as_of-1`
- 次留 D1：仅当 `as_of >= date+2` 时写入数值，否则 `null`（页面显示 —）
- 注意：D1 在跑权过程中会回升，刷新时务必重新拉取，勿沿用旧缓存

## AppsFlyer 拉取清单
App：
- Yaahlan：`id6448329713` + `com.immomo.biz.yaahlan`
- Yaha：`com.immomo.yaha` + `id6761163733`（分区表仅用 Android `com.immomo.yaha`）

1. Yaahlan 整体近三日（Date）  
   Cost, Installs, eCPI, ROAS D0 cumulative, Revenue D0 cumulative, Retention D1 on-period  
2. Yaahlan 整体近三日 Day0 付费（Date + in_app_event=`user_recharge`）  
   Unique users D0  
3. Yaahlan Android 昨日分渠道（Media source, app=`com.immomo.biz.yaahlan`）  
   **仅** `googleadwords_int` / `Facebook Ads` / `tiktokglobal_int`  
   Cost, Installs, eCPI, ROAS D0, Revenue D0  
4. 同上 + `user_recharge` Unique users D0  
5. Yaha 整体近三日（Date）  
   Cost, Installs, eCPI, ROAS D0, Retention D1  
6. Yaha 注册（Date + `user_register` Unique users D0）  
7. Yaha Android **近三日汇总** Campaign（不要按 Date 拆）  
   Cost / Installs / ROAS / Retention + `user_register` UU  
   分区：系列名含 `hindi`→印度，`arabic`→阿语区，`portuguese`→巴西  
   写入 `yaha_region_summary`（不分日）；按安装加权次留，按花费加权 ROAS

渠道展示名：
- googleadwords_int → Google  
- Facebook Ads → Facebook  
- tiktokglobal_int → TikTok  

## JSON 结构要点
- `yaahlan_android_channel_yesterday`：仅 Google / Facebook / TikTok 三行
- `yaha_region_summary`：分区汇总数组（字段含 region / cost / installs / registers / cpi / d1 / d0_roas / period），**不要**再用 `yaha_region_daily`

## 写回
1. 覆盖写入 `data/af-daily-report.json`（结构与现文件一致）  
2. 运行：`python3 scripts/build_af_daily_html.py`
