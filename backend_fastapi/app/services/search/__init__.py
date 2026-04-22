"""搜索服务模块 - 修复 SQLite 版本"""
import sys

# 使用 pysqlite3-binary 替换系统 sqlite3
try:
    import pysqlite3
    sys.modules['sqlite3'] = sys.modules.get('sqlite3', pysqlite3)
    sys.modules['sqlite3.dbapi2'] = pysqlite3.dbapi2
except ImportError:
    pass
