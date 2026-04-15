"""
Kiểm tra freshness từ manifest pipeline (SLA đơn giản theo giờ).

Sinh viên mở rộng: đọc watermark DB, so sánh với clock batch, v.v.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

#hoangviet
LATEST_TS_KEYS = ("latest_exported_at", "latest_source_at", "max_exported_at")
WATERMARK_KEYS = ("source_watermark_at", "watermark_at", "upstream_watermark")
BATCH_CLOCK_KEYS = ("batch_clock_at", "batch_started_at", "run_timestamp")


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Cho phép "2026-04-10T08:00:00" không có timezone
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _pick_ts(data: Dict[str, Any], keys: tuple[str, ...]) -> tuple[str | None, datetime | None]:
    for k in keys:
        raw = data.get(k)
        if raw in (None, ""):
            continue
        dt = parse_iso(str(raw))
        if dt is not None:
            return k, dt
    return None, None

#hoangviet
def check_manifest_freshness(
    manifest_path: Path,
    *,
    sla_hours: float = 24.0,
    watermark_lag_hours: float = 2.0,
    clock_skew_hours: float = 0.5,
    future_tolerance_minutes: float = 5.0,
    now: datetime | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Trả về ("PASS" | "WARN" | "FAIL", detail dict).

    Đọc manifest và kiểm freshness theo nhiều góc nhìn:
    - Freshness SLA: now - latest_exported_at
    - Watermark lag: batch_clock_at - source_watermark_at
    - Clock skew: now - batch_clock_at

    Trả về PASS/WARN/FAIL kèm detail để debug nhanh.
    """
    now = now or datetime.now(timezone.utc)
    if not manifest_path.is_file():
        return "FAIL", {"reason": "manifest_missing", "path": str(manifest_path)}

    data: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    latest_key, latest_dt = _pick_ts(data, LATEST_TS_KEYS)
    if latest_dt is None:
        # Backward-compatible fallback với bản manifest cũ.
        latest_key, latest_dt = _pick_ts(data, ("run_timestamp",))
    if latest_dt is None:
        return "WARN", {"reason": "no_timestamp_in_manifest", "manifest": data}

    watermark_key, watermark_dt = _pick_ts(data, WATERMARK_KEYS)
    batch_key, batch_dt = _pick_ts(data, BATCH_CLOCK_KEYS)

    age_hours = (now - latest_dt).total_seconds() / 3600.0
    detail = {
        "latest_timestamp_key": latest_key,
        "latest_exported_at": latest_dt.isoformat(),
        "age_hours": round(age_hours, 3),
        "sla_hours": sla_hours,
        "watermark_lag_hours_threshold": watermark_lag_hours,
        "clock_skew_hours_threshold": clock_skew_hours,
        "future_tolerance_minutes": future_tolerance_minutes,
    }

    reasons_fail: list[str] = []
    reasons_warn: list[str] = []

    if age_hours > sla_hours:
        reasons_fail.append("freshness_sla_exceeded")

    # Timestamp tương lai thường do lệch timezone/clock trên source.
    if age_hours < -(future_tolerance_minutes / 60.0):
        reasons_warn.append("latest_timestamp_in_future")

    if watermark_dt is None:
        reasons_warn.append("watermark_missing")
    else:
        detail["watermark_key"] = watermark_key
        detail["watermark_at"] = watermark_dt.isoformat()
        if batch_dt is not None:
            watermark_lag = (batch_dt - watermark_dt).total_seconds() / 3600.0
            detail["watermark_lag_hours"] = round(watermark_lag, 3)
            if watermark_lag < -(future_tolerance_minutes / 60.0):
                reasons_warn.append("watermark_after_batch_clock")
            elif watermark_lag > watermark_lag_hours:
                reasons_warn.append("watermark_lag_exceeded")

    if batch_dt is None:
        reasons_warn.append("batch_clock_missing")
    else:
        detail["batch_clock_key"] = batch_key
        detail["batch_clock_at"] = batch_dt.isoformat()
        skew_hours = abs((now - batch_dt).total_seconds() / 3600.0)
        detail["clock_skew_hours"] = round(skew_hours, 3)
        if skew_hours > clock_skew_hours:
            reasons_warn.append("batch_clock_skew_high")

    if reasons_fail:
        return "FAIL", {**detail, "reasons": reasons_fail, "warnings": reasons_warn}
    if reasons_warn:
        return "WARN", {**detail, "reasons": reasons_warn}
    return "PASS", detail
