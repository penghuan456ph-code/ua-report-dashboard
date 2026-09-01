#!/usr/bin/env python3
"""Embed data/af-daily-report.json into af-daily-report.html."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "data" / "af-daily-report.json"
HTML_PATH = ROOT / "af-daily-report.html"
MARKER_START = '<script type="application/json" id="report-data">'
MARKER_END = "</script>"


def d1_complete(date_str: str, as_of: str) -> bool:
    """D1 for date D is complete when as_of >= D+2."""
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    a = datetime.strptime(as_of, "%Y-%m-%d").date()
    return a >= d + timedelta(days=2)


def sanitize(data: dict) -> dict:
    as_of = data.get("meta", {}).get("as_of")
    if not as_of:
        return data
    for key in ("yaahlan_daily", "yaha_daily"):
        for row in data.get(key, []):
            if "d1" in row and row.get("date") and not d1_complete(row["date"], as_of):
                row["d1"] = None
    # Keep only Google / Facebook / TikTok for Android channel table.
    allowed = {"googleadwords_int", "Facebook Ads", "tiktokglobal_int"}
    channels = data.get("yaahlan_android_channel_yesterday")
    if isinstance(channels, list):
        data["yaahlan_android_channel_yesterday"] = [
            row for row in channels if row.get("media_source") in allowed
        ]
    return data


def embed(data: dict) -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    start = html.find(MARKER_START)
    if start < 0:
        raise SystemExit("report-data script block not found in HTML")
    start = start + len(MARKER_START)
    end = html.find(MARKER_END, start)
    if end < 0:
        raise SystemExit("closing script tag not found")
    payload = "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n  "
    HTML_PATH.write_text(html[:start] + payload + html[end:], encoding="utf-8")


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    meta = data.setdefault("meta", {})
    if "updated_at" not in meta or not meta.get("updated_at"):
        bj = timezone(timedelta(hours=8))
        meta["updated_at"] = datetime.now(bj).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    data = sanitize(data)
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    embed(data)
    print(f"OK → {HTML_PATH}")
    print(f"as_of={meta.get('as_of')} range={meta.get('date_range')} yesterday={meta.get('yesterday')}")


if __name__ == "__main__":
    main()
