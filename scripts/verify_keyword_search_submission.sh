#!/bin/bash
# 完整的验证检查清单（供提交前使用）

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend_fastapi"

echo "=========================================="
echo "🔍 关键词搜索优化 - 完整验证清单"
echo "=========================================="
echo ""

# 1. 检查模块文件是否存在
echo "【步骤 1】检查核心模块文件..."
modules=(
    "app/services/tag_similarity_prompts.py"
    "app/services/config_model_params.py"
    "app/services/similarity_score_parser.py"
    "app/services/similarity_analytics.py"
)

for module in "${modules[@]}"; do
    if [ -f "$BACKEND_DIR/$module" ]; then
        echo "  ✅ $module"
    else
        echo "  ❌ $module (缺失)"
        exit 1
    fi
done

# 2. 检查测试文件
echo ""
echo "【步骤 2】检查测试文件..."
tests=(
    "tests/unit/test_tag_similarity_prompts.py"
    "tests/unit/test_similarity_score_parser.py"
    "tests/unit/test_config_model_params.py"
    "tests/unit/test_similarity_analytics.py"
)

for test in "${tests[@]}"; do
    if [ -f "$BACKEND_DIR/$test" ]; then
        echo "  ✅ $test"
    else
        echo "  ❌ $test (缺失)"
        exit 1
    fi
done

# 3. 编译检查
echo ""
echo "【步骤 3】编译检查..."
cd "$BACKEND_DIR"

for module in "${modules[@]}"; do
    if python3 -m py_compile "$module" 2>/dev/null; then
        echo "  ✅ $module"
    else
        echo "  ❌ $module (编译失败)"
        exit 1
    fi
done

# 4. 检查导入路径（不运行，仅检查 AST）
echo ""
echo "【步骤 4】导入路径检查..."
cd "$BACKEND_DIR"

python3 << 'EOF'
import ast
import sys

modules_to_check = [
    "app/services/tag_similarity_prompts.py",
    "app/services/config_model_params.py",
    "app/services/similarity_score_parser.py",
    "app/services/similarity_analytics.py",
]

for module_path in modules_to_check:
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            code = f.read()
            tree = ast.parse(code)

        # 检查类定义
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        if classes or functions:
            print(f"  ✅ {module_path} ({len(classes)} 类, {len(functions)} 函数)")
        else:
            print(f"  ⚠️ {module_path} (无定义)")
    except Exception as e:
        print(f"  ❌ {module_path} ({e})")
        sys.exit(1)
EOF

# 5. 检查 llm_similarity_service.py 重构
echo ""
echo "【步骤 5】检查服务层重构..."
cd "$BACKEND_DIR"

if python3 -m py_compile app/services/llm_similarity_service.py 2>/dev/null; then
    echo "  ✅ llm_similarity_service.py 编译成功"
else
    echo "  ❌ llm_similarity_service.py 编译失败"
    exit 1
fi

# 检查关键导入
python3 << 'EOF'
import ast
with open("app/services/llm_similarity_service.py", 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

imports = []
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        if node.module and node.module.startswith('app.services'):
            imports.append(node.module)

required_imports = [
    'tag_similarity_prompts',
    'config_model_params',
    'similarity_score_parser',
    'similarity_analytics',
]

print("  新模块导入检查:")
for required in required_imports:
    found = any(required in imp for imp in imports)
    status = "✅" if found else "❌"
    print(f"    {status} {required}")
    if not found:
        import sys
        sys.exit(1)

print(f"  ✅ 共导入 {len(imports)} 个服务模块")
EOF

# 6. 检查 CHANGELOG 更新
echo ""
echo "【步骤 6】检查变更日志..."
cd "$PROJECT_ROOT"

if grep -q "关键词搜索\|keyword.*search" CHANGELOG.md 2>/dev/null; then
    echo "  ✅ CHANGELOG.md 已更新"
else
    echo "  ⚠️ CHANGELOG.md 未更新（需要手动添加）"
fi

# 7. 检查文档
echo ""
echo "【步骤 7】检查交付文档..."
if [ -f "docs/KEYWORD_SEARCH_OPTIMIZATION.md" ]; then
    lines=$(wc -l < docs/KEYWORD_SEARCH_OPTIMIZATION.md)
    echo "  ✅ KEYWORD_SEARCH_OPTIMIZATION.md ($lines 行)"
else
    echo "  ❌ KEYWORD_SEARCH_OPTIMIZATION.md (缺失)"
    exit 1
fi

# 8. 检查演示脚本
echo ""
echo "【步骤 8】检查演示脚本..."
if [ -f "scripts/demo_keyword_search.py" ]; then
    lines=$(wc -l < scripts/demo_keyword_search.py)
    echo "  ✅ demo_keyword_search.py ($lines 行)"
else
    echo "  ❌ demo_keyword_search.py (缺失)"
    exit 1
fi

# 9. Commit 格式检查
echo ""
echo "【步骤 9】Commit 检查清单..."
echo "  提交前请确保:"
echo "  □ 已经开启新分支（例如 git checkout -b feature/keyword-search-optimization）"
echo "  □ 已经运行验证脚本"
echo "  □ 没有包含调试代码或 print 语句"
echo "  □ 没有提交 .bak 或临时文件"
echo "  □ Commit 信息遵循准则："
echo "    feat(search): 标签相似度企业级重构"
echo "    "
echo "    - 提示词版本管理（单一事实源）"
echo "    - 参数白名单约束（防注入）"
echo "    - 统一解析器（两路径一致性）"
echo "    - 结构化审计日志（可观测性）"
echo "    - 完整 TDD 测试套件"
echo "    "
echo "    涉及模块:"
echo "    - app/services/tag_similarity_prompts.py (新)"
echo "    - app/services/config_model_params.py (新)"
echo "    - app/services/similarity_score_parser.py (新)"
echo "    - app/services/similarity_analytics.py (新)"
echo "    - app/services/llm_similarity_service.py (重构)"
echo "    - tests/unit/test_*.py x4 (新)"
echo "    "
echo "    Verification: All syntactic checks pass ✅"

# 10. Git 状态检查
echo ""
echo "【步骤 10】Git 状态..."
cd "$PROJECT_ROOT"

if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "  ✅ Git 仓库"

    # 检查当前分支
    branch=$(git rev-parse --abbrev-ref HEAD)
    echo "  当前分支: $branch"

    # 检查未追踪的文件
    untracked=$(git status --porcelain | grep "^??" | wc -l)
    if [ "$untracked" -gt 0 ]; then
        echo "  ⚠️ 未追踪的文件: $untracked 个"
    fi
else
    echo "  ⚠️ 不是 Git 仓库"
fi

echo ""
echo "=========================================="
echo "✅ 验证完成"
echo "=========================================="
echo ""
echo "💡 下一步:"
echo "  1. 查看差异: git diff --stat"
echo "  2. 暂存变更: git add app/services/ tests/unit/ docs/ scripts/"
echo "  3. 提交: git commit -m '...'"
echo "  4. 推送: git push origin [branch]"
echo ""
