#!/usr/bin/env python3
"""Repository-safe backend smoke validation without pytest."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_DIR / "backend_fastapi"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Keep smoke validation side-effect light and deterministic.
os.environ.setdefault("AUTO_CREATE_TABLES", "false")
os.environ.setdefault("WHISPER_PRELOAD_ON_STARTUP", "false")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")

from app.main import app  # noqa: E402
from app.main import health  # noqa: E402
from app.main import root  # noqa: E402
from app.services.external_candidate_service import build_external_cache_key  # noqa: E402
from app.services.video_recommendation_service import infer_preferred_provider_from_url  # noqa: E402


def assert_route(method: str, path: str) -> None:
    for route in app.routes:
        route_path = getattr(route, "path", None)
        route_methods = set(getattr(route, "methods", set()) or set())
        if route_path == path and method.upper() in route_methods:
            return
    raise AssertionError(f"Missing route: {method.upper()} {path}")


def verify_routes() -> None:
    required_routes = [
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/api/health"),
        ("GET", "/api/recommendations/scenes"),
        ("GET", "/api/recommendations/videos"),
        ("POST", "/api/recommendations/import-external"),
        ("POST", "/api/qa/ask"),
        ("POST", "/api/auth/login"),
    ]
    for method, path in required_routes:
        assert_route(method, path)


def verify_recommendation_helpers() -> None:
    assert infer_preferred_provider_from_url("https://www.youtube.com/watch?v=abc123") == "youtube"
    assert infer_preferred_provider_from_url("https://www.bilibili.com/video/BV1xx") == "bilibili"
    cache_key = build_external_cache_key(
        "导数 复习",
        subject_hint="数学",
        preferred_tags=["导数", "极限"],
        preferred_provider="youtube",
        limit=3,
    )
    assert cache_key[3] == "youtube"


async def verify_basic_handlers() -> None:
    root_payload = await root()
    assert root_payload["status"] == "success"
    assert root_payload["docs"] == "/docs"

    health_payload = await health()
    assert health_payload["status"] == "healthy"
    assert "services" in health_payload
    assert "database" in health_payload["services"]


def main() -> int:
    verify_routes()
    verify_recommendation_helpers()
    asyncio.run(verify_basic_handlers())
    print("Backend smoke validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
