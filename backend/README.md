# 后端部分(Backend)文件夹

## backend\app 实现的功能
- backend\app\__init__.py : 实现__all__变量，用于导入其他模型
- backend\app\celery_app.py : 实现Celery配置
- backend\app\config.py : 实现配置类
- backend\app\extensions.py : 实现扩展类

### app\models : 定义数据库表结构和数据模型
- backend\app\models\__init__.py : 实现__all__变量，用于导入其他模型
- backend\app\models\qa.py : 实现Question模型，用于表示问答信息
- backend\app\models\subtitle.py : 实现Subtitle模型，用于表示字幕信息
- backend\app\models\video.py : 实现Video模型，用于表示视频信息

### backend\app\routes : 定义路由
- backend\app\routes\__init__.py : 实现__all__变量，用于导入其他路由
- backend\app\routes\qa.py : 实现问答路由，用于处理问答相关的请求
- backend\app\routes\subtitle.py : 实现字幕路由，用于处理字幕相关的请求
- backend\app\routes\system.py : 实现系统路由，用于处理系统相关的请求
- backend\app\routes\test.py : 实现测试路由，用于处理测试相关的请求
- backend\app\routes\video.py : 实现视频路由，用于处理视频相关的请求

### backend\app\static : 静态文件夹，用于存放前端的静态资源

### backend\app\tasks : 定义任务
- backend\app\tasks\__init__.py : 实现__all__变量，用于导入其他任务
- backend\app\tasks\audio_processing.py : 实现音频处理任务
- backend\app\tasks\subtitle_tasks.py : 实现字幕处理任务
- backend\app\tasks\test.py : 实现测试任务
- backend\app\tasks\video_processing.py : 实现视频处理任务
- backend\app\tasks\video_tools.py : 实现视频工具类
- backend\app\tasks\video.py : 实现视频处理任务

### backend\app\utils : 定义工具函数
- backend\app\utils\__init__.py : 实现__all__变量，用于导入其他工具函数
- backend\app\utils\cors.py : 实现跨域请求工具类
- backend\app\utils\db_check.py : 实现数据库检查工具类
- backend\app\utils\qa_utils.py : 实现问答工具类
- backend\app\utils\subtitle_utils.py : 实现字幕工具类
- backend\app\utils\video_tools.py : 实现视频工具类
- backend\app\utils\video_utils.py : 实现视频工具类
- backend\app\utils\audio_utils.py : 实现音频工具类

### backend\instance\app.db : 数据库文件

### backend\migrations : 数据库迁移文件夹

## backend 根目录下的文件
- backend\app.db : 数据库文件
- backend\celery_app.py : Celery配置文件
- backend\config.py : 配置文件
- backend\init_db.py : 初始化数据库文件
- backend\requirements.txt : 依赖包列表
- backend\run_migration.py : 运行数据库迁移文件
- backend\run.py : 启动文件
