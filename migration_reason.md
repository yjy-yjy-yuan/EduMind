# 迁移框架和技术原因

## 当前使用的框架/技术以及局限性

- Flask 同步阻塞：上传/下载/ffmpeg/Whisper 都在请求线程里跑，单个用户就能卡住 worker，`app/routes/video.py` 超 1000 行，定位问题慢。
- 运维过重：必须起 redis-server + celery worker 才能处理后台任务，本地调试要开 3-4 个进程。

## 新框架/技术以及迁移原因

- FastAPI 异步路由：耗时 IO（yt-dlp 下载、文件读写、流式回答）不会卡住主线程，并自动生成 Swagger `/docs`；Pydantic 先验校验把无效参数挡在业务外。
- 后台任务：默认用 `ProcessPoolExecutor`（无需 Redis/Celery，启动只要 FastAPI + 前端两条命令）；要分布式或重试再启 Celery。依赖注入让 DB/配置不绑 `current_app`，测试可替换 `get_db` 直接跑。

一句话选型：FastAPI (async+Pydantic+Swagger) + 轻量进程池，保留可选 Celery，在少改业务的前提下提升并发、文档和可测试性。
