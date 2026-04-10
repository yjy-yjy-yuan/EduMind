"""适配器：search / similarity 遗留结构映射。"""

import pytest
from app.analytics.adapters.search import legacy_search_dict_to_event
from app.analytics.pipeline import AnalyticsTelemetry
from app.analytics.pipeline import reset_telemetry_for_tests
from app.services.similarity_analytics import SimilarityAuditLog
from app.services.similarity_analytics import SimilarityEventType


@pytest.fixture(autouse=True)
def _reset():
    reset_telemetry_for_tests()
    yield
    reset_telemetry_for_tests()


class TestSearchAdapter:
    def test_legacy_maps_module_and_status(self):
        legacy = {
            "event": "search_completed",
            "timestamp": "x",
            "user_id": 1,
            "duration_ms": 42.0,
            "result_count": 3,
        }
        ev = legacy_search_dict_to_event(legacy)
        assert ev.module == "search"
        assert ev.status == "ok"
        assert ev.latency_ms == 42.0
        assert ev.metadata.get("result_count") == 3

    def test_failed_event_status(self):
        legacy = {"event": "search_failed", "user_id": 1}
        ev = legacy_search_dict_to_event(legacy)
        assert ev.status == "error"


class TestSimilarityAdapter:
    def test_success_audit(self):
        from app.analytics.adapters.similarity import similarity_audit_to_event

        log = SimilarityAuditLog(
            trace_id="abc",
            event_type=SimilarityEventType.CALL_SUCCESS.value,
            tag1="a",
            tag2="b",
        )
        log.success = True
        log.latency_ms = 10.0
        ev = similarity_audit_to_event(log)
        assert ev.module == "similarity"
        assert ev.status == "ok"

    def test_emit_roundtrip(self, caplog):
        import logging

        from app.analytics.adapters.similarity import emit_similarity_audit_event

        caplog.set_level(logging.INFO, logger="app.analytics.telemetry")
        log = SimilarityAuditLog(
            event_type=SimilarityEventType.CALL_SUCCESS.value,
            tag1="a",
            tag2="b",
        )
        log.success = True
        log.latency_ms = 5.0
        emit_similarity_audit_event(AnalyticsTelemetry(), log)
        assert any("similarity_call_success" in r.message for r in caplog.records)
