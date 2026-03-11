# 测试说明

## 运行测试

推荐在仓库根目录执行：

```bash
pytest tests/ -v
```

如果只验证 FastAPI 后端，也可以在 `backend_fastapi/` 目录执行：

```bash
cd backend_fastapi
pytest tests/ -v
```

## 常用测试命令

```bash
pytest -m smoke
pytest -m unit
pytest -m api
pytest -m integration
```

## 当前测试结构

```text
tests/
├── conftest.py
├── smoke/
├── unit/
├── api/
└── integration/
```

## 说明

- 根目录 `tests/` 主要覆盖共享后端测试。
- `backend_fastapi/tests/` 是 FastAPI 工程内测试集。
- 新增功能时，至少补对应的单元测试或 API 测试。
