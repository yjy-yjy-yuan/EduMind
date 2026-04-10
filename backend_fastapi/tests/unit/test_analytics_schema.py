"""AnalyticsEvent schema 校验。"""

import pytest
from app.analytics.schema import AnalyticsEvent
from app.analytics.schema import AnalyticsStatus
from app.analytics.schema import validate_analytics_event


class TestAnalyticsSchema:
    def test_valid_event(self):
        ev = AnalyticsEvent(
            event_type="search_completed",
            trace_id="abc123",
            module="search",
            status=AnalyticsStatus.OK.value,
            latency_ms=12.5,
            metadata={"user_id": 1},
        )
        validate_analytics_event(ev)
        env = ev.to_envelope()
        assert env["event_type"] == "search_completed"
        assert env["module"] == "search"
        assert env["schema_version"] == 1
        assert env["metadata"]["user_id"] == 1

    def test_invalid_event_type(self):
        ev = AnalyticsEvent(
            event_type="BAD TYPE",
            trace_id="x",
            module="search",
            status=AnalyticsStatus.OK.value,
        )
        with pytest.raises(ValueError):
            validate_analytics_event(ev)

    def test_invalid_module(self):
        ev = AnalyticsEvent(
            event_type="ok_event",
            trace_id="x",
            module="123bad",
            status=AnalyticsStatus.OK.value,
        )
        with pytest.raises(ValueError):
            validate_analytics_event(ev)

    def test_invalid_status(self):
        ev = AnalyticsEvent(
            event_type="ok_event",
            trace_id="x",
            module="search",
            status="nope",
        )
        with pytest.raises(ValueError):
            validate_analytics_event(ev)

    def test_invalid_latency(self):
        ev = AnalyticsEvent(
            event_type="ok_event",
            trace_id="x",
            module="search",
            status=AnalyticsStatus.OK.value,
            latency_ms=-1.0,
        )
        with pytest.raises(ValueError):
            validate_analytics_event(ev)
