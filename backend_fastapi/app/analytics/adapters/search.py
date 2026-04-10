"""搜索模块：遗留 SearchEventLogger dict → 统一 AnalyticsEvent。"""

from __future__ import annotations

import uuid
from typing import Any
from typing import Dict

from app.analytics.pipeline import AnalyticsTelemetry
from app.analytics.schema import AnalyticsEvent
from app.analytics.schema import AnalyticsStatus

_MODULE = "search"


def _new_trace_id() -> str:
    return str(uuid.uuid4())[:12]


def _infer_status(event_name: str) -> str:
    name = (event_name or "").lower()
    if "failed" in name:
        return AnalyticsStatus.ERROR.value
    if name in ("search_request_received",):
        return AnalyticsStatus.STARTED.value
    return AnalyticsStatus.OK.value


def legacy_search_dict_to_event(legacy: Dict[str, Any]) -> AnalyticsEvent:
    """将 SearchEventLogger 产生的扁平 dict 转为 AnalyticsEvent。"""
    event_name = str(legacy.get("event") or "search_unknown")
    trace_id = str(legacy.get("trace_id") or _new_trace_id())
    latency = legacy.get("duration_ms")
    latency_ms = float(latency) if latency is not None else None

    skip = {"event", "timestamp", "trace_id", "duration_ms"}
    metadata = {k: v for k, v in legacy.items() if k not in skip and v is not None}

    return AnalyticsEvent(
        event_type=event_name,
        trace_id=trace_id,
        module=_MODULE,
        status=_infer_status(event_name),
        latency_ms=latency_ms,
        metadata=metadata,
    )


def emit_search_legacy_event(telemetry: AnalyticsTelemetry, legacy: Dict[str, Any]) -> None:
    telemetry.emit(legacy_search_dict_to_event(legacy))
