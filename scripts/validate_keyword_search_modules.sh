#!/bin/bash
# 验证脚本：检查新模块的编译与导入
set -e

echo "============================================================"
echo "阶段 1-2 验证: 关键词搜索模块化改造"
echo "============================================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

resolve_backend_dir() {
  local candidates=()
  if [ -n "${EDUMIND_BACKEND_DIR:-}" ]; then
    candidates+=("${EDUMIND_BACKEND_DIR}")
  fi
  candidates+=(
    "$PROJECT_ROOT/../edumind-backend"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate/run.py" ] && [ -d "$candidate/app" ]; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

BACKEND_DIR="$(resolve_backend_dir || true)"
[ -n "$BACKEND_DIR" ] || { echo "❌ 未找到后端目录（../edumind-backend）"; exit 1; }
cd "$BACKEND_DIR"

echo ""
echo "1. 编译检查..."
python3 -m compileall app/services/tag_similarity_prompts.py -q && echo "   ✅ tag_similarity_prompts.py"
python3 -m compileall app/services/config_model_params.py -q && echo "   ✅ config_model_params.py"
python3 -m compileall app/services/similarity_score_parser.py -q && echo "   ✅ similarity_score_parser.py"
python3 -m compileall app/services/similarity_analytics.py -q && echo "   ✅ similarity_analytics.py"

echo ""
echo "2. 导入检查..."
python3 -c "from app.services.tag_similarity_prompts import TagSimilarityPromptFactory; print('   ✅ tag_similarity_prompts'); assert 'v1' in TagSimilarityPromptFactory.list_versions(); assert 'v2' in TagSimilarityPromptFactory.list_versions()"
python3 -c "from app.services.config_model_params import ModelParamWhitelist; print('   ✅ config_model_params'); assert len(ModelParamWhitelist.list_openai_models()) > 0"
python3 -c "from app.services.similarity_score_parser import SimilarityScoreParser; result = SimilarityScoreParser.parse('score: 0.75'); print('   ✅ similarity_score_parser'); assert result.score == 0.75"
python3 -c "from app.services.similarity_analytics import SimilarityAuditLog; log = SimilarityAuditLog(); print('   ✅ similarity_analytics'); assert log.trace_id"

echo ""
echo "3. 测试文件编译..."
python3 -m compileall tests/unit/test_tag_similarity_prompts.py -q && echo "   ✅ test_tag_similarity_prompts.py"
python3 -m compileall tests/unit/test_similarity_score_parser.py -q && echo "   ✅ test_similarity_score_parser.py"
python3 -m compileall tests/unit/test_config_model_params.py -q && echo "   ✅ test_config_model_params.py"
python3 -m compileall tests/unit/test_similarity_analytics.py -q && echo "   ✅ test_similarity_analytics.py"

echo ""
echo "============================================================"
echo "✅ 所有编译与导入检查通过"
echo "============================================================"
echo ""
echo "下一步: 执行仓库规定的非 pytest 本地验证（如 compileall / smoke 脚本）"
echo "============================================================"
