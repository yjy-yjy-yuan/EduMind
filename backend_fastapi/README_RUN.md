# EduMind 后端运行指南

这份文档描述如何从零启动 `backend_fastapi/`。

## 1. 创建环境

你可以使用 `conda` 或系统 Python，环境名不强制。

```bash
conda create -n edumind python=3.10 -y
conda activate edumind
```

## 2. 安装依赖

```bash
cd backend_fastapi
pip install -r requirements.txt
```

## 3. 配置环境变量

```bash
cp .env.example .env
```

按实际环境修改 `.env` 中的数据库、Neo4j、模型服务和密钥配置。

## 4. 启动依赖服务

按需要启动：

```bash
brew services start mysql
brew services start neo4j
ollama serve
```

如果某些功能暂时不用，可以只启动当前接口链路需要的依赖。

## 5. 启动后端

```bash
cd backend_fastapi
conda activate edumind
python run.py
```

启动成功后默认监听：

- `http://127.0.0.1:2004`
- `http://127.0.0.1:2004/docs`

## 6. 验证服务

```bash
curl http://localhost:2004/health
```

## 7. 配合前端运行

桌面端：

```bash
cd frontend
npm install
npm run dev
```

移动端：

```bash
cd mobile-frontend
npm install
npm run dev
```

## 8. 运行测试

```bash
cd backend_fastapi
pytest tests/ -v
pytest -m smoke
```

## 9. 常见问题

### 端口占用

```bash
lsof -i :2004
```

### Neo4j 连接失败

```bash
brew services list | grep neo4j
brew services restart neo4j
```

### 依赖安装失败

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```
