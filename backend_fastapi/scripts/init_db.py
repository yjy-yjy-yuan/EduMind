#!/usr/bin/env python
"""数据库初始化脚本 - 创建所有表结构"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.models import Note
from app.models import Question
from app.models import Subtitle
from app.models import User
from app.models import Video


def init_database():
    """初始化数据库，创建所有表"""
    print(
        f"数据库连接: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}"
    )
    print("正在创建数据库表...")

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    print("数据库表创建成功!")
    print("\n已创建的表:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


def show_table_info():
    """显示表结构信息"""
    print("\n" + "=" * 60)
    print("数据库表结构详情")
    print("=" * 60)

    tables = {
        "videos": {
            "description": "视频信息表",
            "fields": [
                ("id", "INT", "主键"),
                ("title", "VARCHAR(255)", "视频标题"),
                ("filename", "VARCHAR(255)", "文件名"),
                ("filepath", "VARCHAR(255)", "文件路径"),
                ("url", "VARCHAR(255)", "视频URL"),
                ("md5", "VARCHAR(32)", "文件MD5"),
                ("status", "ENUM", "状态: uploaded/pending/processing/completed/failed"),
                ("error_message", "TEXT", "错误信息"),
                ("upload_time", "DATETIME", "上传时间"),
                ("updated_at", "DATETIME", "更新时间"),
                ("process_progress", "FLOAT", "处理进度 0-100"),
                ("current_step", "VARCHAR(255)", "当前处理步骤"),
                ("task_id", "VARCHAR(255)", "任务ID"),
                ("duration", "FLOAT", "视频时长(秒)"),
                ("fps", "FLOAT", "帧率"),
                ("width", "INT", "宽度"),
                ("height", "INT", "高度"),
                ("frame_count", "INT", "总帧数"),
                ("summary", "TEXT", "视频摘要"),
                ("tags", "TEXT", "标签(JSON)"),
            ],
        },
        "users": {
            "description": "用户信息表",
            "fields": [
                ("id", "INT", "主键"),
                ("username", "VARCHAR(64)", "用户名 (唯一)"),
                ("email", "VARCHAR(120)", "邮箱 (唯一)"),
                ("password_hash", "VARCHAR(128)", "密码哈希"),
                ("created_at", "DATETIME", "创建时间"),
                ("last_login", "DATETIME", "最后登录"),
                ("gender", "VARCHAR(10)", "性别"),
                ("education", "VARCHAR(50)", "学历"),
                ("occupation", "VARCHAR(50)", "职业"),
                ("learning_direction", "VARCHAR(100)", "学习方向"),
                ("avatar", "VARCHAR(255)", "头像URL"),
                ("bio", "TEXT", "个人简介"),
            ],
        },
        "subtitles": {
            "description": "字幕数据表",
            "fields": [
                ("id", "INT", "主键"),
                ("video_id", "INT", "视频ID (外键)"),
                ("start_time", "FLOAT", "开始时间(秒)"),
                ("end_time", "FLOAT", "结束时间(秒)"),
                ("text", "TEXT", "字幕文本"),
                ("source", "VARCHAR(50)", "来源: asr/extract/manual"),
                ("language", "VARCHAR(10)", "语言: zh/en"),
                ("created_at", "DATETIME", "创建时间"),
                ("updated_at", "DATETIME", "更新时间"),
            ],
        },
        "notes": {
            "description": "学习笔记表",
            "fields": [
                ("id", "INT", "主键"),
                ("title", "VARCHAR(255)", "笔记标题"),
                ("content", "TEXT", "笔记内容"),
                ("content_vector", "TEXT", "内容向量(JSON)"),
                ("note_type", "VARCHAR(50)", "类型: text/code/list"),
                ("video_id", "INT", "关联视频ID"),
                ("created_at", "DATETIME", "创建时间"),
                ("updated_at", "DATETIME", "更新时间"),
                ("tags", "VARCHAR(255)", "标签(逗号分隔)"),
                ("keywords", "VARCHAR(500)", "关键词"),
            ],
        },
        "note_timestamps": {
            "description": "笔记时间戳关联表",
            "fields": [
                ("id", "INT", "主键"),
                ("note_id", "INT", "笔记ID (外键)"),
                ("time_seconds", "FLOAT", "时间点(秒)"),
                ("subtitle_text", "TEXT", "对应字幕文本"),
                ("created_at", "DATETIME", "创建时间"),
            ],
        },
        "questions": {
            "description": "问答记录表",
            "fields": [
                ("id", "INT", "主键"),
                ("video_id", "INT", "关联视频ID"),
                ("content", "TEXT", "问题内容"),
                ("answer", "TEXT", "回答内容"),
                ("created_at", "DATETIME", "创建时间"),
                ("updated_at", "DATETIME", "更新时间"),
            ],
        },
    }

    for table_name, info in tables.items():
        print(f"\n[{table_name}] - {info['description']}")
        print("-" * 50)
        for field, field_type, desc in info["fields"]:
            print(f"  {field:20} {field_type:15} {desc}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument("--info", action="store_true", help="显示表结构信息")
    parser.add_argument("--create", action="store_true", help="创建数据库表")
    args = parser.parse_args()

    if args.info:
        show_table_info()
    elif args.create:
        init_database()
    else:
        # 默认执行创建和显示信息
        init_database()
        show_table_info()
