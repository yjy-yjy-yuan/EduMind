#!/bin/bash
# 验证脚本：检查新模块的编译与导入
set -e

echo "============================================================"
echo "阶段 1-2 验证: 关键词搜索模块化改造"
echo "============================================================"

cd "$(dirname "$0")/backend_fastapi"

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
python3 -m compileall ../tests/unit/test_tag_similarity_prompts.py -q && echo "   ✅ test_tag_similarity_prompts.py"
python3 -m compileall ../tests/unit/test_similarity_score_parser.py -q && echo "   ✅ test_similarity_score_parser.py"
python3 -m compileall ../tests/unit/test_config_model_params.py -q && echo "   ✅ test_config_model_params.py"
python3 -m compileall ../tests/unit/test_similarity_analytics.py -q && echo "   ✅ test_similarity_analytics.py"

echo ""
echo "============================================================"
echo "✅ 所有编译与导入检查通过"
echo "============================================================"
echo ""
echo "下一步: 运行完整测试套件"
echo "  cd backend_fastapi"
echo "  pytest tests/unit/test_tag_similarity_prompts.py -v"
echo "  pytest tests/unit/test_similarity_score_parser.py -v"
echo "  pytest tests/unit/test_config_model_params.py -v"
echo "  pytest tests/unit/test_similarity_analytics.py -v"
echo "============================================================"
