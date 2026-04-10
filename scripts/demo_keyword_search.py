#!/usr/bin/env python3
"""
关键词搜索功能演示与验证脚本
- 10 组样例数据演示
- 两路径一致性验证
- 异常场景处理
"""

import sys

sys.path.insert(0, '/Users/yuan/final-work/EduMind/backend_fastapi')

# ============================================================================
# 演示数据
# ============================================================================

DEMO_CASES = [
    {
        "tag1": "Python",
        "tag2": "Python",
        "expected": 1.0,
        "scenario": "完全相同",
    },
    {
        "tag1": "Python",
        "tag2": "编程",
        "expected": 0.8,
        "scenario": "高度相关",
    },
    {
        "tag1": "深度学习",
        "tag2": "神经网络",
        "expected": 0.75,
        "scenario": "相关领域",
    },
    {
        "tag1": "机器学习",
        "tag2": "数据分析",
        "expected": 0.6,
        "scenario": "中等相关",
    },
    {
        "tag1": "前端",
        "tag2": "React",
        "expected": 0.85,
        "scenario": "直接关系",
    },
    {
        "tag1": "数据库",
        "tag2": "SQL",
        "expected": 0.8,
        "scenario": "常见关联",
    },
    {
        "tag1": "HTML",
        "tag2": "JavaScript",
        "expected": 0.65,
        "scenario": "同一领域",
    },
    {
        "tag1": "天气",
        "tag2": "天文",
        "expected": 0.3,
        "scenario": "弱相关",
    },
    {
        "tag1": "体育",
        "tag2": "烹饪",
        "expected": 0.1,
        "scenario": "几无关联",
    },
    {
        "tag1": "计算机科学",
        "tag2": "CS",
        "expected": 0.9,
        "scenario": "缩写识别",
    },
]

BOUNDARY_CASES = [
    {
        "tag1": "",
        "tag2": "Python",
        "description": "空标签",
        "should_fail": True,
    },
    {
        "tag1": "x" * 200,
        "tag2": "tag",
        "description": "超长标签",
        "should_fail": True,
    },
    {
        "tag1": "Python\n(ignore this)",
        "tag2": "code",
        "description": "注入尝试（换行）",
        "should_fail": False,  # 应该被清洗
    },
]

# ============================================================================
# 演示函数
# ============================================================================


def demo_basic_functionality():
    """演示基本功能"""
    print("=" * 70)
    print("【演示 1】基本功能 - 10 组样例数据")
    print("=" * 70)

    try:
        from app.services.llm_similarity_service import llm_similarity_service

        print("\n{:<15} {:<15} {:>8} {:>8} {:>8} {}".format("tag1", "tag2", "期望", "实际", "误差", "状态"))
        print("-" * 70)

        passed = 0
        for case in DEMO_CASES:
            tag1 = case["tag1"]
            tag2 = case["tag2"]
            expected = case["expected"]
            scenario = case["scenario"]

            try:
                actual = llm_similarity_service.calculate_tag_similarity_with_llm(tag1, tag2)
                diff = abs(actual - expected)

                # 判断是否通过（误差允许范围 ± 0.15）
                tolerance = 0.15
                passed_test = diff <= tolerance
                status = "✅" if passed_test else "⚠️"

                if passed_test:
                    passed += 1

                print(
                    "{:<15} {:<15} {:>8.2f} {:>8.2f} {:>8.2f} {} ({})".format(
                        tag1[:14],
                        tag2[:14],
                        expected,
                        actual,
                        diff,
                        status,
                        scenario,
                    )
                )
            except Exception as e:
                print(f"{tag1:<15} {tag2:<15} {'ERROR':<8} {str(e)[:20]:<8}")

        print("-" * 70)
        print(f"通过率: {passed}/{len(DEMO_CASES)} ({passed*100//len(DEMO_CASES)}%)")

    except Exception as e:
        print(f"❌ 演示 1 失败: {e}")


def demo_prompt_versions():
    """演示提示词版本管理"""
    print("\n" + "=" * 70)
    print("【演示 2】提示词版本管理")
    print("=" * 70)

    try:
        from app.services.tag_similarity_prompts import TagSimilarityPromptFactory
        from app.services.tag_similarity_prompts import get_prompt_changelog

        # 列出版本
        versions = TagSimilarityPromptFactory.list_versions()
        print(f"\n✅ 可用版本: {versions}")

        # 查看版本信息
        for version in versions:
            log = get_prompt_changelog(version)
            print(f"\n【版本 {version}】")
            print(f"  日期: {log['date']}")
            print(f"  说明: {log['description']}")
            print(f"  变更数: {len(log['changes'])}")
            if "rollback_to" in log:
                print(f"  回滚目标: {log['rollback_to']}")

        # 显示 v2 系统提示词片段
        print(f"\n【v2 系统提示词（片段）】")
        system = TagSimilarityPromptFactory.get_system_prompt("v2")
        lines = system.split('\n')[:3]
        for line in lines:
            print(f"  {line}")
        print(f"  ...")

    except Exception as e:
        print(f"❌ 演示 2 失败: {e}")


def demo_parameter_whitelist():
    """演示参数白名单"""
    print("\n" + "=" * 70)
    print("【演示 3】参数白名单与配置化")
    print("=" * 70)

    try:
        from app.services.config_model_params import ModelParamWhitelist
        from app.services.config_model_params import SimilarityConfig

        # 允许的模型
        print(f"\n✅ OpenAI 允许的模型:")
        for model in ModelParamWhitelist.list_openai_models():
            profile = ModelParamWhitelist.get_openai_profile(model)
            print(f"  {model}")
            print(f"    温度: {profile.temperature} (低随机性)")
            print(f"    超时: {profile.timeout_sec}s")
            print(f"    最大 token: {profile.max_tokens}")

        print(f"\n✅ Ollama 允许的模型:")
        for model in ModelParamWhitelist.list_ollama_models():
            profile = ModelParamWhitelist.get_ollama_profile(model)
            print(f"  {model}")
            print(f"    温度: {profile.temperature}")
            print(f"    超时: {profile.timeout_sec}s")

        # 白名单防护
        print(f"\n✅ 白名单防护演示")
        print(f"  尝试获取非法模型 'gpt-999'...")
        try:
            ModelParamWhitelist.get_openai_profile("gpt-999")
            print(f"  ❌ 不应该成功！")
        except ValueError as e:
            print(f"  ✅ 被拒绝: {str(e)[:60]}...")

    except Exception as e:
        print(f"❌ 演示 3 失败: {e}")


def demo_parser_unified():
    """演示统一解析器"""
    print("\n" + "=" * 70)
    print("【演示 4】统一解析器 - 多格式支持")
    print("=" * 70)

    try:
        from app.services.similarity_score_parser import ParseErrorType
        from app.services.similarity_score_parser import SimilarityScoreParser

        test_responses = [
            ("0.75", True, 0.75, "单浮点数"),
            ("score: 0.85", True, 0.85, "score: 格式"),
            ("``` 0.65 ```", True, 0.65, "代码块格式"),
            ("1.5", False, None, "超出范围（应失败）"),
            ("没有数字", False, None, "无数字（应失败）"),
            ("0.75 or 0.80", False, None, "多个数字（应失败）"),
            ("", False, None, "空响应（应失败）"),
        ]

        print(f"\n{'输入':<20} {'成功':<6} {'分值':<8} {'错误类型':<25} {'说明':<15}")
        print("-" * 80)

        for response, should_succeed, expected_score, description in test_responses:
            result = SimilarityScoreParser.parse(response)

            status = "✅" if result.success == should_succeed else "❌"
            score_display = f"{result.score:.2f}" if result.score is not None else "N/A"
            error_display = result.error_type if result.error_type else "N/A"

            print(
                f"{response[:19]:<20} {str(result.success):<6} {score_display:<8} {error_display:<25} {description:<15}"
            )

            if result.success and result.score != expected_score:
                print(f"  ⚠️ 分值不匹配！期望 {expected_score}, 得到 {result.score}")

    except Exception as e:
        print(f"❌ 演示 4 失败: {e}")


def demo_audit_logging():
    """演示审计日志"""
    print("\n" + "=" * 70)
    print("【演示 5】审计日志与可观测性")
    print("=" * 70)

    try:
        from app.services.similarity_analytics import SimilarityAuditLog
        from app.services.similarity_analytics import SimilarityMetrics

        # 创建审计日志
        log = SimilarityAuditLog(
            tag1="Python",
            tag2="编程",
            model="qwen-max",
            provider="openai",
            prompt_version="v2",
            success=True,
            score=0.82,
            parse_ok=True,
            latency_ms=245.5,
        )

        print(f"\n✅ 审计日志示例:")
        print(f"  trace_id: {log.trace_id}")
        print(f"  tag1: {log.tag1}, tag2: {log.tag2}")
        print(f"  分值: {log.score}")
        print(f"  提示词版本: {log.prompt_version}")
        print(f"  延迟: {log.latency_ms}ms")
        print(f"  JSON 长度: {len(log.to_json())} 字节")

        # 统计演示
        print(f"\n✅ 性能指标统计:")
        metrics = SimilarityMetrics()

        # 模拟记录
        for i in range(10):
            test_log = SimilarityAuditLog(
                success=i < 9,  # 最后一条是失败
                score=0.5 + i * 0.03,
                latency_ms=200 + i * 10,
            )
            metrics.record_log(test_log)

        import datetime

        today = datetime.datetime.utcnow().date().isoformat()
        stats = metrics.get_stats_for_day(today)

        print(f"  总调用数: {stats.get('total_calls', 0)}")
        print(f"  成功率: {stats.get('success_rate', 0):.1%}")
        print(f"  平均分值: {stats.get('avg_score', 0):.2f}")
        print(f"  平均延迟: {stats.get('avg_latency_ms', 0):.1f}ms")
        print(f"  P95 延迟: {stats.get('p95_latency_ms', 0):.1f}ms")

    except Exception as e:
        print(f"❌ 演示 5 失败: {e}")


def demo_boundary_and_injection():
    """演示边界值与防注入"""
    print("\n" + "=" * 70)
    print("【演示 6】边界值测试与防注入")
    print("=" * 70)

    try:
        from app.services.config_model_params import InputValidationConfig

        print(f"\n✅ 输入验证演示:")

        for case in BOUNDARY_CASES:
            tag1 = case["tag1"]
            tag2 = case["tag2"]
            description = case["description"]
            should_fail = case["should_fail"]

            try:
                sanitized1 = InputValidationConfig.sanitize_tag(tag1)
                sanitized2 = InputValidationConfig.sanitize_tag(tag2)

                # 验证
                InputValidationConfig.validate_tag(sanitized1)
                InputValidationConfig.validate_tag(sanitized2)

                result = "✅ 通过" if not should_fail else "⚠️ 未拒绝"
                print(f"  {description:<20} {result}")
                print(f"    输入: {tag1[:30]}...")
                print(f"    清洗后: {sanitized1[:30]}...")

            except ValueError as e:
                result = "✅ 被拒绝" if should_fail else "❌ 不应该失败"
                print(f"  {description:<20} {result}")
                print(f"    原因: {str(e)[:50]}")
            except Exception as e:
                print(f"  {description:<20} ❌ 异常: {e}")

    except Exception as e:
        print(f"❌ 演示 6 失败: {e}")


def demo_service_interface():
    """演示服务接口"""
    print("\n" + "=" * 70)
    print("【演示 7】服务接口与向后兼容性")
    print("=" * 70)

    try:
        from app.services.llm_similarity_service import llm_similarity_service

        print(f"\n✅ 当前服务状态:")
        print(f"  提示词版本: {llm_similarity_service.get_prompt_version()}")
        print(f"  OpenAI 可用: {llm_similarity_service.use_openai}")
        print(f"  Ollama 可用: {llm_similarity_service.use_ollama}")

        print(f"\n✅ 支持的方法:")
        methods = [
            "calculate_tag_similarity_with_llm(tag1, tag2)",
            "calculate_tag_sets_similarity(tags1, tags2)",
            "find_similar_videos(target_tags, all_videos, threshold, limit)",
            "get_metrics_for_day(date)",
            "check_score_drift(date, baseline, threshold)",
            "get_prompt_version()",
            "set_prompt_version(version)",
        ]
        for method in methods:
            print(f"  • {method}")

        print(f"\n✅ 版本切换演示:")
        original = llm_similarity_service.get_prompt_version()
        print(f"  原始版本: {original}")

        # 尝试切换（如果有多个版本）
        from app.services.tag_similarity_prompts import TagSimilarityPromptFactory

        available = TagSimilarityPromptFactory.list_versions()

        if len(available) > 1:
            new_version = [v for v in available if v != original][0]
            llm_similarity_service.set_prompt_version(new_version)
            print(f"  切换到版本: {new_version}")
            print(f"  当前版本: {llm_similarity_service.get_prompt_version()}")

            # 切换回原版本
            llm_similarity_service.set_prompt_version(original)
            print(f"  回滚到版本: {llm_similarity_service.get_prompt_version()}")
        else:
            print(f"  ⚠️ 只有一个版本可用: {available}")

    except Exception as e:
        print(f"❌ 演示 7 失败: {e}")


# ============================================================================
# 主函数
# ============================================================================


def main():
    print("\n" + "=" * 70)
    print("🚀 关键词搜索功能优化 - 完整演示")
    print("=" * 70)
    print("\n本演示展示关键词搜索功能的 7 项改进:")
    print("  1. 基本功能 - 10 组样例数据")
    print("  2. 提示词版本管理")
    print("  3. 参数白名单与配置化")
    print("  4. 统一解析器（多格式支持）")
    print("  5. 审计日志与可观测性")
    print("  6. 边界值测试与防注入")
    print("  7. 服务接口与向后兼容性")

    # 运行所有演示
    demo_basic_functionality()
    demo_prompt_versions()
    demo_parameter_whitelist()
    demo_parser_unified()
    demo_audit_logging()
    demo_boundary_and_injection()
    demo_service_interface()

    print("\n" + "=" * 70)
    print("✅ 演示完成")
    print("=" * 70)
    print("\n📖 更多信息请见: docs/KEYWORD_SEARCH_OPTIMIZATION.md")
    print()


if __name__ == "__main__":
    main()
