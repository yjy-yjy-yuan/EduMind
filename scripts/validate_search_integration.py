#!/usr/bin/env python3
"""
EduMind 语义搜索系统验证脚本

验证范围：
- 后端模块导入一致性
- 自适应切片参数边界
- 日志集成
- 前端编译
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend_fastapi"
PROJECT_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def colored(text: str, color: str) -> str:
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m", "end": "\033[0m"}
    return f"{colors.get(color, '')}{text}{colors['end']}"


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")


def ensure_project_python() -> None:
    """如果当前不是项目 .venv，优先切到项目虚拟环境。"""
    current_python = Path(sys.executable).resolve()
    if PROJECT_VENV_PYTHON.exists() and current_python != PROJECT_VENV_PYTHON.resolve():
        os.execv(str(PROJECT_VENV_PYTHON), [str(PROJECT_VENV_PYTHON), __file__])


def backend_path_setup() -> None:
    backend_path = str(BACKEND_ROOT)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def verify_backend_imports() -> bool:
    print_section("后端模块导入验证")
    try:
        backend_path_setup()
        from app.models.vector_index import VectorIndex
        from app.schemas.search import SemanticSearchRequest
        from app.schemas.search import SemanticSearchResponse
        from app.services.search.chunker import chunk_video
        from app.services.search.embedder import get_embedder
        from app.services.search.search import get_adaptive_chunk_params
        from app.services.search.search import semantic_search_videos
        from app.services.search.search_logging import SearchEventLogger
        from app.services.search.store import EduMindStore

        checks = [
            "search.py",
            "chunker.py",
            "store.py",
            "embedder.py (get_embedder 工厂函数)",
            "search_logging.py",
            "VectorIndex 模型位置正确 (vector_index.py)",
            "Schema 类名正确 (SemanticSearchRequest/SemanticSearchResponse)",
        ]
        for item in checks:
            print(colored(f"✓ {item}", "green"))

        _ = (
            VectorIndex,
            SemanticSearchRequest,
            SemanticSearchResponse,
            chunk_video,
            get_embedder,
            get_adaptive_chunk_params,
            semantic_search_videos,
            SearchEventLogger,
            EduMindStore,
        )
        return True
    except Exception as exc:
        print(colored(f"✗ 导入失败: {exc}", "red"))
        return False


def verify_adaptive_chunking() -> bool:
    print_section("自适应切片参数边界验证")
    try:
        backend_path_setup()
        from app.services.search.search import get_adaptive_chunk_params

        test_cases = [
            (179.9, (12, 2), "短视频下限"),
            (180.0, (12, 2), "180 秒精确"),
            (180.5, (20, 4), "180.5 秒浮点"),
            (600.0, (20, 4), "600 秒精确"),
            (600.5, (45, 8), "600.5 秒浮点"),
            (1800.0, (45, 8), "1800 秒精确"),
            (1800.5, (60, 10), "1800.5 秒浮点"),
            (3600.0, (60, 10), "3600 秒精确"),
            (3600.5, (75, 12), "3600.5 秒浮点"),
        ]

        all_passed = True
        for duration, expected, label in test_cases:
            result = get_adaptive_chunk_params(duration)
            if result == expected:
                print(colored(f"✓ {duration:7.1f}s => {result} ({label})", "green"))
            else:
                all_passed = False
                print(colored(f"✗ {duration}s: 期望 {expected}, 得到 {result} ({label})", "red"))
        return all_passed
    except Exception as exc:
        print(colored(f"✗ 边界测试异常: {exc}", "red"))
        return False


def verify_logging_integration() -> bool:
    print_section("生产监控集成验证 (Phase 1)")
    try:
        backend_path_setup()
        from app.services.search import search as search_module
        from app.services.search.search_logging import SearchEventLogger

        methods = [
            "log_search_request",
            "log_adaptive_chunking_selected",
            "log_video_chunking_completed",
            "log_embedding_batch_completed",
            "log_indexing_completed",
            "log_indexing_failed",
            "log_search_completed",
            "log_search_failed",
            "log_chromadb_search_executed",
        ]
        for method in methods:
            if hasattr(SearchEventLogger, method):
                print(colored(f"✓ SearchEventLogger.{method}", "green"))
            else:
                print(colored(f"✗ SearchEventLogger.{method} 缺失", "red"))
                return False

        source = Path(search_module.__file__).read_text(encoding="utf-8")
        required_calls = [
            "SearchEventLogger.log_adaptive_chunking_selected",
            "SearchEventLogger.log_video_chunking_completed",
            "SearchEventLogger.log_embedding_batch_completed",
            "SearchEventLogger.log_indexing_completed",
            "SearchEventLogger.log_indexing_failed",
            "SearchEventLogger.log_search_request",
            "SearchEventLogger.log_search_completed",
            "SearchEventLogger.log_search_failed",
            "SearchEventLogger.log_chromadb_search_executed",
        ]
        for call in required_calls:
            if call in source:
                print(colored(f"✓ 已接入 {call}", "green"))
            else:
                print(colored(f"✗ 未找到 {call}", "red"))
                return False

        return True
    except Exception as exc:
        print(colored(f"✗ 日志验证异常: {exc}", "red"))
        return False


def verify_frontend_build() -> bool:
    print_section("前端编译验证")
    try:
        result = subprocess.run(
            ["npm", "run", "build:ios"],
            cwd=REPO_ROOT / "mobile-frontend",
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            print(colored("✗ 前端编译失败", "red"))
            return False
        built_line = next((line.strip() for line in output.splitlines() if "built in" in line), "")
        if built_line:
            print(colored(f"✓ 前端编译成功 ({built_line})", "green"))
        else:
            print(colored("✓ 前端编译成功", "green"))
        return True
    except subprocess.TimeoutExpired:
        print(colored("✗ 前端编译超时", "red"))
        return False
    except Exception as exc:
        print(colored(f"✗ 前端编译异常: {exc}", "red"))
        return False


def main() -> int:
    ensure_project_python()
    print(colored("=" * 60, "yellow"))
    print(colored("EduMind 语义搜索系统 - 完整验证", "yellow"))
    print(colored("=" * 60, "yellow"))

    checks = [
        ("后端模块导入", verify_backend_imports()),
        ("自适应切片边界", verify_adaptive_chunking()),
        ("生产监控集成", verify_logging_integration()),
        ("前端编译", verify_frontend_build()),
    ]

    print_section("验收总结")
    all_passed = True
    for name, passed in checks:
        print(f"{colored('✓', 'green') if passed else colored('✗', 'red')} {name}")
        all_passed = all_passed and passed

    print()
    if all_passed:
        print(colored("✅ 所有验证通过!", "green"))
        return 0

    print(colored("❌ 有验证未通过", "red"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
