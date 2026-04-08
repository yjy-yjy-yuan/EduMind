# 语义搜索验证提示词

## 目标

验证 EduMind 当前语义搜索实现是否与真实代码一致，并补充必要的历史回归检查。

## 仓库约束

- 当前仓库要求：**修改程序时不要把 `pytest` 作为本次交付的主要验证手段**
- 本次应优先使用现有验证链路：

```bash
python -m compileall backend_fastapi/app backend_fastapi/scripts scripts/hooks scripts/validate_backend_smoke.py
python scripts/validate_backend_smoke.py
cd mobile-frontend && npm run build:ios
```

如涉及 iOS 容器，再补：

```bash
bash ios-app/sync_ios_web_assets.sh
bash ios-app/validate_ios_build.sh
```

## 当前真实实现

- 自适应切片逻辑在 `backend_fastapi/app/services/search/search.py`
- 固定参数切片与 FFmpeg 调用在 `backend_fastapi/app/services/search/chunker.py`
- 向量存储真实方法在 `backend_fastapi/app/services/search/store.py`
  - `search()`
  - `add_chunks_batch()`
  - `remove_file()`
  - `get_chunk_count()`
  - `get_stats()`
- 搜索 schema 在 `backend_fastapi/app/schemas/search.py`
  - `SemanticSearchRequest`
  - `SemanticSearchResponse`

## 必查行为

### 自适应切片边界

- `179.9 -> (12, 2)`
- `180.0 -> (12, 2)`
- `180.5 -> (20, 4)`
- `600.0 -> (20, 4)`
- `600.5 -> (45, 8)`
- `1800.0 -> (45, 8)`
- `1800.5 -> (60, 10)`
- `3600.0 -> (60, 10)`
- `3600.5 -> (75, 12)`

### 分片器

- `chunk_duration <= 0`
- `overlap < 0`
- `overlap >= chunk_duration`
- 文件不存在
- FFmpeg 非 0 退出
- `preprocess=True` / `False`

### 搜索流程

- 单视频搜索
- 多视频搜索
- 阈值过滤
- 结果按相似度降序
- `preview_text` 当前允许为空

## 禁止写偏的地方

- 不要把验证脚本写成依赖不存在的方法：
  - `search_chunks()`
  - `delete_collection()`
  - `clear_all_chunks()`
- 不要把 `chunk_video()` 的职责写成“自动清理临时文件”
- 不要把异常时“统一 return 0”写成 `build_video_index_internal()` 的行为
- 不要把 `pytest` 写成当前默认验收命令
