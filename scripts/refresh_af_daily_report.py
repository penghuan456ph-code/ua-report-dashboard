#!/usr/bin/env python3
"""Refresh AF daily report JSON/HTML via AppsFlyer MCP Bearer token."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "af-daily-report.json"
BUILD_SCRIPT = ROOT / "scripts" / "build_af_daily_html.py"

sys.path.insert(0, str(ROOT / "scripts"))
from appsflyer_mcp_client import (  # noqa: E402
    AppsFlyerMCPClient,
    AppsFlyerMCPError,
    parse_csv_section,
    to_float,
    to_int,
)

YAAHLAN_APPS = ["id6448329713", "com.immomo.biz.yaahlan"]
YAHA_APPS = ["com.immomo.yaha", "id6761163733"]
YAHA_ANDROID = ["com.immomo.yaha"]
CHANNELS = {
    "googleadwords_int": "Google",
    "Facebook Ads": "Facebook",
    "tiktokglobal_int": "TikTok",
}
ALLOWED_MEDIA = set(CHANNELS.keys())
BJ = timezone(timedelta(hours=8))


def d1_complete(d: str, as_of: date) -> bool:
    row_date = datetime.strptime(d, "%Y-%m-%d").date()
    return as_of >= row_date + timedelta(days=2)


def region(campaign: str) -> str | None:
    c = (campaign or "").lower()
    if "hindi" in c:
        return "印度"
    if "arabic" in c:
        return "阿语区"
    if "portuguese" in c:
        return "巴西"
    return None


def r2(x: float | None) -> float | None:
    return None if x is None else round(x, 2)


def r4(x: float | None) -> float | None:
    return None if x is None else round(x, 4)


def fetch(client: AppsFlyerMCPClient, query: dict) -> list[dict[str, str]]:
    text = client.fetch_aggregated_data(query)
    return parse_csv_section(text)


def metric_col(row: dict[str, str], prefix: str) -> str | None:
    for key in row:
        if key.startswith(prefix):
            return row[key]
    return None


def build_report(client: AppsFlyerMCPClient, as_of: date) -> dict:
    start = as_of - timedelta(days=3)
    end = as_of - timedelta(days=1)
    start_s, end_s = start.isoformat(), end.isoformat()
    yesterday_s = end.isoformat()
    date_range = [(start + timedelta(days=i)).isoformat() for i in range(3)]

    # 1. Yaahlan daily
    rows = fetch(
        client,
        {
            "start_date": start_s,
            "end_date": end_s,
            "app_ids": YAAHLAN_APPS,
            "groupings": ["Date"],
            "metrics": [
                {"metric_name": "Cost"},
                {"metric_name": "Installs"},
                {"metric_name": "eCPI"},
                {"metric_name": "ROAS", "period": "0", "aggregation_type": "cumulative"},
                {"metric_name": "Revenue", "period": "0", "aggregation_type": "cumulative"},
                {"metric_name": "Retention rate", "period": "1", "aggregation_type": "on-period"},
            ],
            "row_count": 10,
            "sort_by_metrics": [{"metric_name": "Cost", "order": "desc"}],
        },
    )
    payers_rows = fetch(
        client,
        {
            "start_date": start_s,
            "end_date": end_s,
            "app_ids": YAAHLAN_APPS,
            "groupings": ["Date"],
            "in_app_event": ["user_recharge"],
            "metrics": [{"metric_name": "Unique users", "period": "0", "aggregation_type": "cumulative"}],
            "row_count": 10,
        },
    )
    payers_by_date = {r["Date"]: to_int(metric_col(r, "Unique users")) for r in payers_rows if r.get("Date")}

    yaahlan_daily = []
    for r in sorted(rows, key=lambda x: x.get("Date", "")):
        d = r.get("Date")
        if not d:
            continue
        d1 = to_float(metric_col(r, "Retention rate"))
        yaahlan_daily.append(
            {
                "date": d,
                "cost": r2(to_float(metric_col(r, "Cost"))),
                "installs": to_int(metric_col(r, "Installs")),
                "cpi": r2(to_float(metric_col(r, "eCPI"))),
                "d0_roas": r4(to_float(metric_col(r, "ROAS"))),
                "d1": r4(d1) if d1 is not None and d1_complete(d, as_of) else None,
                "d0_revenue": r2(to_float(metric_col(r, "Revenue"))),
                "d0_payers": payers_by_date.get(d),
            }
        )

    # 2. Yaahlan Android channels (yesterday only)
    ch_rows = fetch(
        client,
        {
            "start_date": yesterday_s,
            "end_date": yesterday_s,
            "app_ids": ["com.immomo.biz.yaahlan"],
            "groupings": ["Media source"],
            "filters": {"Media source": list(ALLOWED_MEDIA)},
            "metrics": [
                {"metric_name": "Cost"},
                {"metric_name": "Installs"},
                {"metric_name": "eCPI"},
                {"metric_name": "ROAS", "period": "0", "aggregation_type": "cumulative"},
                {"metric_name": "Revenue", "period": "0", "aggregation_type": "cumulative"},
            ],
            "row_count": 10,
            "sort_by_metrics": [{"metric_name": "Cost", "order": "desc"}],
        },
    )
    ch_payers = fetch(
        client,
        {
            "start_date": yesterday_s,
            "end_date": yesterday_s,
            "app_ids": ["com.immomo.biz.yaahlan"],
            "groupings": ["Media source"],
            "filters": {"Media source": list(ALLOWED_MEDIA)},
            "in_app_event": ["user_recharge"],
            "metrics": [{"metric_name": "Unique users", "period": "0", "aggregation_type": "cumulative"}],
            "row_count": 10,
        },
    )
    payers_by_ms = {r["Media source"]: to_int(metric_col(r, "Unique users")) for r in ch_payers if r.get("Media source")}

    channels = []
    for r in ch_rows:
        ms = r.get("Media source")
        if ms not in ALLOWED_MEDIA:
            continue
        channels.append(
            {
                "channel": CHANNELS[ms],
                "media_source": ms,
                "cost": r2(to_float(metric_col(r, "Cost"))),
                "installs": to_int(metric_col(r, "Installs")),
                "cpi": r2(to_float(metric_col(r, "eCPI"))),
                "d0_roas": r4(to_float(metric_col(r, "ROAS"))),
                "d0_revenue": r2(to_float(metric_col(r, "Revenue"))),
                "d0_payers": payers_by_ms.get(ms),
            }
        )
    order = ["Google", "Facebook", "TikTok"]
    channels.sort(key=lambda x: order.index(x["channel"]) if x["channel"] in order else 99)

    # 3. Yaha daily
    y_rows = fetch(
        client,
        {
            "start_date": start_s,
            "end_date": end_s,
            "app_ids": YAHA_APPS,
            "groupings": ["Date"],
            "metrics": [
                {"metric_name": "Cost"},
                {"metric_name": "Installs"},
                {"metric_name": "eCPI"},
                {"metric_name": "ROAS", "period": "0", "aggregation_type": "cumulative"},
                {"metric_name": "Retention rate", "period": "1", "aggregation_type": "on-period"},
            ],
            "row_count": 10,
        },
    )
    y_reg = fetch(
        client,
        {
            "start_date": start_s,
            "end_date": end_s,
            "app_ids": YAHA_APPS,
            "groupings": ["Date"],
            "in_app_event": ["user_register"],
            "metrics": [{"metric_name": "Unique users", "period": "0", "aggregation_type": "cumulative"}],
            "row_count": 10,
        },
    )
    reg_by_date = {r["Date"]: to_int(metric_col(r, "Unique users")) for r in y_reg if r.get("Date")}

    yaha_daily = []
    for r in sorted(y_rows, key=lambda x: x.get("Date", "")):
        d = r.get("Date")
        if not d:
            continue
        d1 = to_float(metric_col(r, "Retention rate"))
        yaha_daily.append(
            {
                "date": d,
                "cost": r2(to_float(metric_col(r, "Cost"))),
                "installs": to_int(metric_col(r, "Installs")),
                "registers": reg_by_date.get(d),
                "cpi": r2(to_float(metric_col(r, "eCPI"))),
                "d1": r4(d1) if d1 is not None and d1_complete(d, as_of) else None,
                "d0_roas": r4(to_float(metric_col(r, "ROAS"))),
            }
        )

    # 4. Yaha region daily (Date × Campaign → region)
    camp_rows = fetch(
        client,
        {
            "start_date": start_s,
            "end_date": end_s,
            "app_ids": YAHA_ANDROID,
            "groupings": ["Date", "Campaign"],
            "metrics": [
                {"metric_name": "Cost"},
                {"metric_name": "Installs"},
                {"metric_name": "eCPI"},
                {"metric_name": "ROAS", "period": "0", "aggregation_type": "cumulative"},
                {"metric_name": "Retention rate", "period": "1", "aggregation_type": "on-period"},
            ],
            "row_count": 300,
            "sort_by_metrics": [{"metric_name": "Cost", "order": "desc"}],
        },
    )
    camp_reg = fetch(
        client,
        {
            "start_date": start_s,
            "end_date": end_s,
            "app_ids": YAHA_ANDROID,
            "groupings": ["Date", "Campaign"],
            "in_app_event": ["user_register"],
            "metrics": [{"metric_name": "Unique users", "period": "0", "aggregation_type": "cumulative"}],
            "row_count": 300,
        },
    )
    reg_by_key = {
        (r.get("Date"), r.get("Campaign")): to_int(metric_col(r, "Unique users")) or 0
        for r in camp_reg
        if r.get("Date") and r.get("Campaign")
    }

    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"cost": 0.0, "installs": 0, "roas_w": 0.0, "roas_cost": 0.0, "d1_w": 0.0, "d1_inst": 0, "registers": 0}
    )
    for r in camp_rows:
        camp = r.get("Campaign", "")
        d = r.get("Date")
        reg_name = region(camp)
        if not reg_name or not d:
            continue
        cost = to_float(metric_col(r, "Cost")) or 0.0
        inst = to_int(metric_col(r, "Installs")) or 0
        roas = to_float(metric_col(r, "ROAS"))
        d1 = to_float(metric_col(r, "Retention rate"))
        a = agg[(d, reg_name)]
        a["cost"] += cost
        a["installs"] += inst
        a["registers"] += reg_by_key.get((d, camp), 0)
        if roas is not None and cost:
            a["roas_w"] += roas * cost
            a["roas_cost"] += cost
        if d1 is not None and inst:
            a["d1_w"] += d1 * inst
            a["d1_inst"] += inst

    region_daily = []
    for d in date_range:
        for reg_name in ["印度", "阿语区", "巴西"]:
            a = agg[(d, reg_name)]
            cost, inst = a["cost"], a["installs"]
            if inst == 0 and cost == 0:
                continue
            d1 = r4(a["d1_w"] / a["d1_inst"]) if a["d1_inst"] else None
            region_daily.append(
                {
                    "date": d,
                    "region": reg_name,
                    "cost": r2(cost),
                    "installs": inst,
                    "registers": a["registers"],
                    "cpi": r2(cost / inst) if inst else None,
                    "d1": d1 if d1 is not None and d1_complete(d, as_of) else None,
                    "d0_roas": r4(a["roas_w"] / a["roas_cost"]) if a["roas_cost"] else None,
                }
            )

    return {
        "meta": {
            "timezone": "UTC",
            "currency": "USD",
            "as_of": as_of.isoformat(),
            "date_range": date_range,
            "yesterday": yesterday_s,
            "updated_at": datetime.now(BJ).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
            "source": "AppsFlyer MCP · Cohort UA · GitHub Actions",
            "notes": [
                "时区为 UTC（与 AF 面板 Asia/Shanghai 可能差日历日边界）",
                "次留 D1：仅展示已跑完的日期（as_of 的前 2 天及更早）；未完整日显示 —；跑权过程中数值会回升，以最新刷新为准",
                "Day0 付费人数 = user_recharge Unique users (D0)",
                "Yaha 注册数 = user_register Unique users (D0)",
                "Yaahlan Android 分渠道仅展示 Google / Facebook / TikTok",
                "Yaha 分区为近三日分日（Date×分区）；系列名含 hindi→印度 / arabic→阿语区 / portuguese→巴西；次留按安装加权，ROAS 按花费加权",
                "分日表最新一日：花费 / Install / 注册数 / CPI 相对前一日（分区表按同分区）变动超过 20% 时该单元格标红",
            ],
        },
        "yaahlan_daily": yaahlan_daily,
        "yaahlan_android_channel_yesterday": channels,
        "yaha_daily": yaha_daily,
        "yaha_region_daily": region_daily,
    }


def main() -> None:
    token = os.environ.get("APPSFLYER_MCP_TOKEN", "")
    as_of_str = os.environ.get("AF_AS_OF")
    as_of = date.fromisoformat(as_of_str) if as_of_str else datetime.now(BJ).date()

    client = AppsFlyerMCPClient(token)
    client.initialize()
    data = build_report(client, as_of)

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=True)
    print(f"OK as_of={data['meta']['as_of']} yesterday={data['meta']['yesterday']}")


if __name__ == "__main__":
    try:
        main()
    except AppsFlyerMCPError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
