"""Gunicorn配置文件"""

# 绑定的IP和端口
bind = "0.0.0.0:5001"

# 工作进程数
workers = 4

# 工作模式
worker_class = "sync"

# 超时时间
timeout = 120

# 日志级别
loglevel = "info"

# 是否后台运行
daemon = False

# 是否重载
reload = False

# 最大并发请求数
worker_connections = 1000

# 请求超时时间
keepalive = 5
