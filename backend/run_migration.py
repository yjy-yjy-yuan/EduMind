# 功能：运行数据库迁移脚本，确保数据库结构与应用模型一致

import logging
import sys

from migrations.add_summary_column import add_summary_column
from migrations.add_title_column import add_title_column

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def run_migrations():
    """运行所有迁移脚本"""
    logging.info("开始运行数据库迁移...")

    # 运行添加title列的迁移
    success = add_title_column()
    if not success:
        logging.error("添加title列失败")
        return False

    # 运行添加summary列的迁移
    success = add_summary_column()
    if not success:
        logging.error("添加summary列失败")
        return False

    logging.info("所有迁移已成功完成")
    return True


if __name__ == "__main__":
    success = run_migrations()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
