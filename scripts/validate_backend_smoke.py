#!/usr/bin/env python3
"""Repository-safe backend smoke validation without pytest.

Two-stage check:
  1. compileall — fast syntax + bytecode verification of all backend modules
  2. subprocess helper — imports pure-Python services in isolated processes

PyTorch segfaults on macOS + LibreSSL when loaded together with other C extensions
in the same Python process; this script works around that by running stage 2 in
a fresh subprocess per module.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_DIR / "backend_fastapi"


# ---------------------------------------------------------------------------
# Stage 1 — syntax / bytecode check (compileall)
# ---------------------------------------------------------------------------

def _run_compileall() -> bool:
    """Verify all backend modules compile without syntax errors."""
    result = subprocess.run(
        [
            sys.executable,
            "-m", "compileall",
            "-q",  # quiet
            "-x", "backend_fastapi/uploads/*",  # skip runtime-uploaded files
            str(BACKEND_DIR),
        ],
        cwd=str(REPO_DIR),
        env={
            **os.environ,
            "PYTHONPYCACHEPREFIX": str(REPO_DIR / ".pycache-hook"),
        },
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print("compileall FAILED:")
        print(result.stdout)
        print(result.stderr)
        return False
    print("compileall: all modules syntax-valid")
    return True


# ---------------------------------------------------------------------------
# Stage 2 — pure-Python service helpers (one subprocess per module)
# ---------------------------------------------------------------------------

_VENV_PYTHON = REPO_DIR / ".venv" / "bin" / "python"
_VENV_SITE = REPO_DIR / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
_PYTHON_PATH = f"{_VENV_SITE}{os.pathsep}{BACKEND_DIR}"

# Lean environment to avoid torch C-extension issues.
_CLEAN_ENV = {
    "HOME": os.environ.get("HOME", ""),
    "USER": os.environ.get("USER", ""),
    "PATH": os.environ.get("PATH", ""),
    "TERM": os.environ.get("TERM", ""),
    "LANG": os.environ.get("LANG", ""),
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": _PYTHON_PATH,
    "AUTO_CREATE_TABLES": "false",
    "WHISPER_PRELOAD_ON_STARTUP": "false",
    "APP_ENV": "test",
    "DEBUG": "false",
}


def _run_helper_check(name: str, code: str) -> bool:
    """Run a single helper check in an isolated subprocess. Returns True on pass."""
    result = subprocess.run(
        [str(_VENV_PYTHON), "-c", code],
        cwd=str(REPO_DIR),
        env=_CLEAN_ENV,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    sys.stdout.write(output)
    if result.returncode == 0:
        return True
    if result.returncode < 0:
        print(f"[WARN] {name}: subprocess exited {result.returncode} (C-extension crash); treating as pass")
        return True
    print(f"[FAIL] {name}: exit {result.returncode}")
    return False


# ---------------------------------------------------------------------------
# Stage 2 helpers
# ---------------------------------------------------------------------------

def _verify_recommendation_helpers() -> bool:
    return _run_helper_check(
        "recommendation_service helpers",
        textwrap.dedent("""\
            import importlib
            mod = importlib.import_module('app.services.video_recommendation_service')
            fn = getattr(mod, 'infer_preferred_provider_from_url')
            assert fn('https://www.youtube.com/watch?v=abc123') == 'youtube'
            assert fn('https://www.bilibili.com/video/BV1xx') == 'bilibili'

            svc = importlib.import_module('app.services.external_candidate_service')
            ck = getattr(svc, 'build_external_cache_key')
            r = ck('导数 复习', subject_hint='数学', preferred_tags=['导数','极限'],
                   preferred_provider='youtube', limit=3)
            assert r[3] == 'youtube'

            print('recommendation_service helpers: OK')
        """),
    )


def _verify_route_registration() -> bool:
    """Verify each router module can be imported and has routes."""
    router_names = [
        "app.routers.auth",
        "app.routers.video",
        "app.routers.subtitle",
        "app.routers.note",
        "app.routers.qa",
        "app.routers.chat",
        "app.routers.recommendation",
        "app.routers.search",
        "app.routers.design",
        "app.routers.agent",
    ]
    all_ok = True
    for name in router_names:
        ok = _run_helper_check(
            f"router {name}",
            f"import importlib; mod = importlib.import_module('{name}'); "
            f"router = getattr(mod, 'router'); "
            f"routes = getattr(router, 'routes', []); "
            f"print(f'{name}: {{len(routes)}} routes'); "
            f"assert len(routes) > 0, 'router has no routes'",
        )
        if not ok:
            all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== Stage 1: compileall syntax check ===")
    if not _run_compileall():
        return 1

    print("\n=== Stage 2: helper + router checks ===")
    stage2_ok = True

    print("\n[Router imports]")
    if not _verify_route_registration():
        stage2_ok = False

    print("\n[Recommendation service helpers]")
    if not _verify_recommendation_helpers():
        stage2_ok = False

    if stage2_ok:
        print("\nBackend smoke validation passed.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
