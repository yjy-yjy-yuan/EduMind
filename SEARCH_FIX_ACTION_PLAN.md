# 搜索系统修复 - 行动计划

**状态**：🟡 等待执行
**优先级**：🔴 P0 - 致命问题
**预估时间**：20-30 分钟

---

## 核心问题

```
❌ 全局搜索无法返回结果
  → VectorIndex 表：213 chunks ✓
  → ChromaDB 实际数据：0 chunks ✗
  → 原因：add_chunks_batch() 没有真正保存数据
```

---

## 执行步骤

### 📍 步骤 1：验证问题（5 分钟）

**命令**：
```bash
cd /Users/yuan/final-work/EduMind

# 检查 ChromaDB 实际数据
python3 << 'EOF'
import chromadb
client = chromadb.PersistentClient(path='./data/chroma')
total = 0
for col in client.list_collections():
    count = col.count()
    total += count
    print(f"{col.name}: {count} chunks")
print(f"\nTotal: {total} chunks")
EOF

# 检查数据库记录的索引数量
mysql -h 127.0.0.1 -u root -ppassword edumind -e \
  "SELECT SUM(chunk_count) FROM vector_indexes WHERE status='COMPLETED';"
```

**预期**：
- ChromaDB 显示 0 chunks
- 数据库显示 213 chunks
- 确认问题存在

### 📍 步骤 2：选择修复方式（1 分钟）

**方式 A：自动修复**（推荐）
```bash
python ../edumind-backend/scripts/fix_chromadb_persistence.py
```

**方式 B：手动修复**
参考 [SEARCH_FIX_GUIDE.md](SEARCH_FIX_GUIDE.md) § 修复步骤 (第 1-2 节)

**推荐**：使用自动修复方式

### 📍 步骤 3：编译验证（2 分钟）

**命令**：
```bash
python -m compileall ../edumind-backend/app/services/search/
```

**预期**：
- 无 SyntaxError
- 无 IndentationError

### 📍 步骤 4：清理旧数据（1 分钟）

**重要**：确保数据修复后再执行

```bash
# 备份 ChromaDB（可选）
cp -r data/chroma data/chroma.backup

# 清空 ChromaDB
rm -rf data/chroma
mkdir -p data/chroma

# 清空 VectorIndex 表
mysql -h 127.0.0.1 -u root -ppassword edumind -e "DELETE FROM vector_indexes;"

# 清除 has_semantic_index 标记
mysql -h 127.0.0.1 -u root -ppassword edumind -e \
  "UPDATE videos SET has_semantic_index=0, vector_index_id=NULL;"

# 确认清理
mysql -h 127.0.0.1 -u root -ppassword edumind -e \
  "SELECT COUNT(*) FROM vector_indexes;"  # 应显示 0
```

### 📍 步骤 5：启动后端（~15 分钟）

**命令**：
```bash
cd /Users/yuan/final-work/EduMind
python ../edumind-backend/run.py
```

**预期**：
- 后端启动成功
- 系统开始自动重新索引视频
- 日志显示 "Indexing video..." 和 "✓ Successfully added X chunks"

**等待时间**：约 15 分钟（取决于视频数量和硬件性能）

### 📍 步骤 6：验证修复（2 分钟）

**在另一个终端**：
```bash
cd /Users/yuan/final-work/EduMind
python ../edumind-backend/scripts/verify_chromadb_integrity.py
```

**预期输出**：
```
✓ 验证通过：所有索引数据完整无误
✓ 搜索功能应该正常工作
✓ ChromaDB(213) == Database(213)
```

**如果失败**：
- 检查 `logs/` 目录中的错误信息
- 运行 `DEBUG_FINAL_REPORT.log` 中的诊断命令

### 📍 步骤 7：功能测试（2 分钟）

**测试搜索功能**：
```bash
# 获取授权 token（如需要）
# 调用搜索 API
curl -X POST http://localhost:8000/api/search/semantic/search \
  -H "Content-Type: application/json" \
  -d '{"query":"学习"}'
```

**预期**：
- 返回非空的搜索结果
- 结果包含 video_id、score、text 等字段

---

## 完整时间表

| 步骤 | 任务 | 时间 | 累计 |
|------|------|------|------|
| 1 | 验证问题 | 5 min | 5 min |
| 2 | 选择修复方式 | 1 min | 6 min |
| 3 | 编译验证 | 2 min | 8 min |
| 4 | 清理旧数据 | 1 min | 9 min |
| 5 | 启动后端 | 15 min | 24 min |
| 6 | 验证修复 | 2 min | 26 min |
| 7 | 功能测试 | 2 min | 28 min |
| | **总计** | | **28 min** |

---

## 失败排查

### 症状：编译失败

**检查**：
```bash
# 查看错误
python -m compileall ../edumind-backend/app/services/search/ -v

# 检查代码
git diff ../edumind-backend/app/services/search/

# 回滚修改（如需要）
git checkout ../edumind-backend/app/services/search/store.py
git checkout ../edumind-backend/app/services/search/search.py
```

### 症状：验证仍然失败（ChromaDB 仍为 0）

**可能原因**：
1. 修复代码未正确应用
2. 旧数据未清理
3. 后端未完全重新启动

**检查清单**：
- [ ] 代码修改是否保存？
- [ ] ChromaDB 目录是否真的被删除？
- [ ] VectorIndex 表是否真的被清空？
- [ ] 后端是否重新启动？
- [ ] 索引任务是否完成？

### 症状：搜索仍返回空结果

**可能原因**：
1. 搜索查询与任何视频内容不匹配
2. 相似度阈值设置过高
3. 某些视频索引失败

**检查**：
```bash
# 查看后端日志中的索引错误
tail -f logs/edumind.log | grep -i "error\|failed"

# 查看 vector_indexes 表中是否有失败记录（MySQL）
mysql -h 127.0.0.1 -u root -ppassword edumind \
  -e "SELECT id, video_id, status, error_message FROM vector_indexes WHERE status='FAILED';"

# 尝试其他搜索词
curl -X POST http://localhost:8000/api/search/semantic/search \
  -H "Content-Type: application/json" \
  -d '{"query":"数学"}'
```

---

## 回滚计划（如需要）

如果出现严重问题：

```bash
# 1. 停止后端
pkill -f "python ../edumind-backend/run.py"

# 2. 恢复备份
if [ -d data/chroma.backup ]; then
    rm -rf data/chroma
    mv data/chroma.backup data/chroma
fi

# 3. 恢复代码（如修改有问题）
git checkout ../edumind-backend/app/services/search/store.py
git checkout ../edumind-backend/app/services/search/search.py

# 4. 重新启动
python ../edumind-backend/run.py
```

---

## 关键文件

### 需要修改的源文件
- `../edumind-backend/app/services/search/store.py` - 添加验证逻辑
- `../edumind-backend/app/services/search/search.py` - 添加错误处理

### 需要查阅的文档
- [`SEARCH_DIAGNOSTIC_SUMMARY.md`](SEARCH_DIAGNOSTIC_SUMMARY.md) - 诊断摘要
- [`SEARCH_FIX_GUIDE.md`](SEARCH_FIX_GUIDE.md) - 详细修复指南
- [`logs/DEBUG_FINAL_REPORT.log`](logs/DEBUG_FINAL_REPORT.log) - 完整诊断日志

### 辅助工具
- `../edumind-backend/scripts/fix_chromadb_persistence.py` - 自动修复脚本
- `../edumind-backend/scripts/verify_chromadb_integrity.py` - 验证脚本

---

## 成功标志 ✅

执行完成后应该看到：

- ✅ 编译通过，无语法错误
- ✅ 验证脚本输出 "✓ 验证通过"
- ✅ ChromaDB 数据 = 数据库记录（213 chunks）
- ✅ 搜索 API 返回有效结果
- ✅ 后端日志显示 "✓ Successfully added" 而不是错误

---

## 下次调试入口

如果需要重新诊断：

```bash
# 快速检查状态
python ../edumind-backend/scripts/verify_chromadb_integrity.py

# 查看完整诊断日志
cat logs/DEBUG_FINAL_REPORT.log

# 查看导航文档
cat SEARCH_DIAGNOSIS_INDEX.md
```

---

## 文档导航

- 📍 **开始**：阅读本文件
- 📖 **详情**：[SEARCH_DIAGNOSTIC_SUMMARY.md](SEARCH_DIAGNOSTIC_SUMMARY.md)
- 🔧 **修复**：[SEARCH_FIX_GUIDE.md](SEARCH_FIX_GUIDE.md)
- 📚 **全索引**：[SEARCH_DIAGNOSIS_INDEX.md](SEARCH_DIAGNOSIS_INDEX.md)
- 📊 **快速参考**：[SEARCH_SYSTEM_QUICK_REFERENCE.md](SEARCH_SYSTEM_QUICK_REFERENCE.md)

---

## 确认清单

执行前确认：

- [ ] 了解问题是什么（ChromaDB 数据缺失）
- [ ] 备份过重要数据（如需要）
- [ ] 有 20-30 分钟的时间
- [ ] 已阅读 [SEARCH_FIX_GUIDE.md](SEARCH_FIX_GUIDE.md)
- [ ] 已选好修复方式（自动 vs 手动）

执行后确认：

- [ ] 编译成功
- [ ] 数据清理完成
- [ ] 后端正常启动
- [ ] 索引任务完成
- [ ] 验证脚本通过
- [ ] 搜索功能正常

---

**准备好？执行步骤 1：验证问题**

```bash
cd /Users/yuan/final-work/EduMind
python3 << 'EOF'
import chromadb
client = chromadb.PersistentClient(path='./data/chroma')
total = sum(col.count() for col in client.list_collections())
print(f"ChromaDB Total: {total} chunks")
EOF
```

如果显示 0，确认问题存在，可以继续执行步骤 2。

---

**最后更新**：2026-04-09 11:00:00
**版本**：1.0
**生成工具**：AI Assistant (Claude Haiku 4.5)
