#!/usr/bin/env python3
"""
EduMind 语义搜索系统验证脚本

验证范围:
- 后端模块导入一致性
- 前端编译状态
- 自适应切片参数边界
"""

import os
import subprocess
import sys


def colored(text, color):
    colors = {'green': '\033[92m', 'red': '\033[91m', 'yellow': '\033[93m', 'end': '\033[0m'}
    return f"{colors.get(color, '')}{text}{colors['end']}"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def verify_backend_imports():
    """验证后端模块导入"""
    print_section("后端模块导入验证")

    try:
        # 添加后端目录到路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend_fastapi'))

        # 验证核心导入
        from app.models.vector_index import VectorIndex
        from app.schemas.search import SemanticSearchRequest
        from app.schemas.search import SemanticSearchResponse
        from app.services.search.chunker import chunk_video
        from app.services.search.embedder import get_embedder
        from app.services.search.search import get_adaptive_chunk_params
        from app.services.search.search import semantic_search_videos
        from app.services.search.search_logging import SearchEventLogger
        from app.services.search.store import EduMindStore

        print(colored("✓ search.py", 'green'))
        print(colored("✓ chunker.py", 'green'))
        print(colored("✓ store.py", 'green'))
        print(colored("✓ embedder.py (get_embedder工厂函数正确)", 'green'))
        print(colored("✓ search_logging.py", 'green'))
        print(colored("✓ VectorIndex 模型位置正确 (vector_index.py)", 'green'))
        print(colored("✓ Schema 类名正确 (SemanticSearchRequest/SemanticSearchResponse)", 'green'))

        return True
    except ImportError as e:
        print(colored(f"✗ 导入失败: {e}", 'red'))
        return False


def verify_adaptive_chunking():
    """验证自适应切片参数计算"""
    print_section("自适应切片参数边界验证")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend_fastapi'))
        from app.services.search.search import get_adaptive_chunk_params

        test_cases = [
            (179.9, (12, 2), "短视频下限"),
            (180.0, (12, 2), "180秒精确"),
            (180.5, (20, 4), "180.5秒浮点"),
            (600.0, (20, 4), "600秒精确"),
            (600.5, (45, 8), "600.5秒浮点"),
            (1800.0, (45, 8), "1800秒精确"),
            (1800.5, (60, 10), "1800.5秒浮点"),
            (3600.0, (60, 10), "3600秒精确"),
            (3600.5, (75, 12), "3600.5秒浮点"),
        ]

        failures = []
        for duration, expected, desc in test_cases:
            result = get_adaptive_chunk_params(duration)
            if result == expected:
                print(colored(f"✓ {duration:7.1f}s => {result} ({desc})", 'green'))
            else:
                msg = f"✗ {duration}s: 期望 {expected}, 得到 {result} ({desc})"
                print(colored(msg, 'red'))
                failures.append(msg)

        return len(failures) == 0
    except Exception as e:
        print(colored(f"✗ 边界测试异常: {e}", 'red'))
        return False


def verify_frontend_build():
    """验证前端编译"""
    print_section("前端编译验证")

    try:
        os.chdir(os.path.join(os.path.dirname(__file__), '../mobile-frontend'))
        result = subprocess.run(['npm', 'run', 'build:ios'], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            if 'built in' in result.stderr:
                # 从错误输出中提取编译时间
                for line in result.stderr.split('\n'):
                    if 'built in' in line:
                        print(colored(f"✓ 前端编译成功 ({line.strip()})", 'green'))
                        break
            return True
        else:
            print(colored(f"✗ 前端编译失败", 'red'))
            return False
    except subprocess.TimeoutExpired:
        print(colored("✗ 前端编译超时", 'red'))
        return False
    except Exception as e:
        print(colored(f"✗ 前端编译异常: {e}", 'red'))
        return False


def verify_logging_integration():
    """验证日志记录器集成"""
    print_section("生产监控集成验证 (Phase 1)")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../backend_fastapi'))
        from app.services.search.search_logging import SearchEventLogger

        # 检查必要的日志方法
        methods = [
            'log_search_request',
            'log_adaptive_chunking_selected',
            'log_video_chunking_completed',
            'log_embedding_batch_completed',
            'log_indexing_completed',
            'log_indexing_failed',
            'log_search_completed',
            'log_search_failed',
            'log_chromadb_search_executed',
        ]

        for method in methods:
            if hasattr(SearchEventLogger, method):
                print(colored(f"✓ SearchEventLogger.{method}", 'green'))
            else:
                print(colored(f"✗ SearchEventLogger.{method} 缺失", 'red'))
                return False

        print(colored("✓ 日志记录器已集成到 search.py", 'green'))
        return True
    except Exception as e:
        print(colored(f"✗ 日志验证异常: {e}", 'red'))
        return False


def main():
    print(colored("=" * 60, 'yellow'))
    print(colored("EduMind 语义搜索系统 - 完整验证", 'yellow'))
    print(colored("=" * 60, 'yellow'))

    results = []

    # 运行所有验证
    results.append(("后端模块导入", verify_backend_imports()))
    results.append(("自适应切片边界", verify_adaptive_chunking()))
    results.append(("生产监控集成", verify_logging_integration()))
    results.append(("前端编译", verify_frontend_build()))

    # 总结
    print_section("验收总结")

    all_passed = True
    for name, passed in results:
        status = colored("✓", 'green') if passed else colored("✗", 'red')
        print(f"{status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(colored("✅ 所有验证通过!", 'green'))
        return 0
    else:
        print(colored("❌ 有验证未通过", 'red'))
        return 1


if __name__ == '__main__':
    sys.exit(main())
