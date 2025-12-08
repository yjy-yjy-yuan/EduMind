# 测试说明

## 运行测试
```bash
PYTHONPATH=backend python -m pytest tests/ -v
```

## 当前测试统计
| 类别 | 数量 | 说明 |
|------|------|------|
| passed | 159 | API、模型、工作流测试 |
| skipped | 18 | Chat API（蓝图未注册） |

## 测试结构
```
tests/
├── conftest.py     # fixtures 配置
├── smoke/          # 应用启动检查
├── unit/           # 模型单元测试
├── api/            # API 端点测试
└── integration/    # 工作流集成测试
```

## 迁移验证
修改 `tests/conftest.py` 中注释的 FastAPI fixtures 即可验证迁移是否成功。
