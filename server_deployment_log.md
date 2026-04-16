# EduMind 远程服务器部署文档

> 服务器：阿里云 ECS（公网 IP：47.84.228.226）
> 系统：Alibaba Cloud Linux 3（OpenAnolis Edition，等价 CentOS/RHEL 8）
> 操作时间：2026-04-15

---

## 一、环境总览

| 组件 | 版本/路径 |
|------|-----------|
| 操作系统 | Alibaba Cloud Linux 3（RHEL 系） |
| Python | 3.6.8（系统）/ 3.6+ 虚拟环境 |
| 虚拟环境 | `/var/www/edumind/.venv` |
| 应用目录 | `/var/www/edumind/backend_fastapi` |
| Nginx | 1.20.1 |
| MySQL | 8.0（本地 127.0.0.1:3306） |
| FFmpeg | 最新 nightly build（手动编译安装） |
| Whisper 模型 | `/var/www/edumind/models/whisper/base.pt` |
| API 端口 | 2004 |
| Nginx 端口 | 80 |
| systemd 服务 | `edumind-api.service` |

### 已安装的 Python 依赖（venv 中）

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
openai-whisper==20240930
torch==2.11.0          (含 CUDA 13 支持)
sentence-transformers==3.4.1
faiss-cpu==1.8.0
chromadb==0.5.0
pymysql==1.1.0
sqlalchemy==2.0.25
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
transformers>=4.36.0
Pillow>=10.0.0
opencv-python>=4.9.0.80
yt-dlp>=2024.3.10
jieba==0.42.1
numpy<2, numpy==1.26.4
pydub==0.25.1
scikit-learn>=1.4.0
httpx==0.26.0
requests>=2.31.0
python-dotenv==1.0.0
pysqlite3-binary
pytest>=8.2.0
```

---

## 二、新服务器初始部署步骤

### 1. SSH 登录

```bash
ssh root@47.84.228.226
```

### 2. 安装系统依赖

```bash
# 更新系统
dnf update -y

# 安装基础工具
dnf install -y python3 python3-pip python3-devel mysql-server git curl wget

# 安装编译工具（FFmpeg 从源码编译需要）
dnf install -y gcc gcc-c++ make pkgconfig SDL2-devel

# 安装 Nginx
dnf install -y nginx

# 安装 FFmpeg（Alibaba Cloud Linux 3）
dnf install -y epel-release
dnf install -y ffmpeg
# 若官方源版本过低，参考下方「从源码编译 FFmpeg」章节
```

### 3. 安装 FFmpeg（从源码编译，当前服务器用的这种方式）

```bash
# 安装依赖
dnf install -y nasm yasm libass-devel freetype-devel fribidi-devel \
  harfbuzz-devel libvorbis-devel libtheora-devel libvpx-devel \
  openssl-devel libx264-devel libx265-devel libmp3lame-devel \
  libopus-devel SDL2-devel

# 下载源码并编译
cd /tmp
wget https://ffmpeg.org/releases/ffmpeg-n6.1.1.tar.gz
tar xzf ffmpeg-n6.1.1.tar.gz
cd ffmpeg-n6.1.1
./configure --prefix=/usr/local --enable-gpl --enable-version3 \
  --enable-libx264 --enable-libx265 --enable-libmp3lame \
  --enable-libopus --enable-libvpx --enable-libass \
  --enable-libfreetype --enable-libharfbuzz
make -j$(nproc)
make install

# 让系统找到 ffmpeg
ln -sf /usr/local/bin/ffmpeg /usr/bin/ffmpeg
```

### 4. 配置并启动 MySQL

```bash
# 启动 MySQL
systemctl start mysqld
systemctl enable mysqld

# 安全初始化
mysql_secure_installation

# 创建数据库和用户
mysql -u root -p
```

```sql
CREATE DATABASE edumind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'edumind'@'localhost' IDENTIFIED BY '你的强密码';
GRANT ALL PRIVILEGES ON edumind.* TO 'edumind'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. 上传代码到服务器

```bash
# 在本地打包（本地项目根目录执行）
cd /Users/yuan/final-work/EduMind
tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    -czf edumind_deploy.tar.gz backend_fastapi/ mobile-frontend/ ios-app/ docs/

# 上传到服务器
scp edumind_deploy.tar.gz root@47.84.228.226:/tmp/

# 在服务器解压
ssh root@47.84.228.226
mkdir -p /var/www/edumind
tar xzf /tmp/edumind_deploy.tar.gz -C /var/www/edumind/
```

### 6. 创建虚拟环境并安装 Python 依赖

```bash
cd /var/www/edumind

# 创建虚拟环境（使用系统 Python 3）
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r backend_fastapi/requirements.txt
```

> 注意：服务器上 Whisper 等大包已手动安装。如果网络安装超时，可以先在本地下载 wheel 文件再上传：
> ```bash
> pip download openai-whisper torch sentence-transformers -d /tmp/wheels/
> scp -r /tmp/wheels root@47.84.228.226:/tmp/
> # 服务器上
> pip install --no-index --find-links=/tmp/wheels -r backend_fastapi/requirements.txt
> ```

### 7. 配置 .env 环境变量

```bash
cd /var/www/edumind
vi .env
```

写入以下关键配置（其余参数可沿用默认值）：

```env
# 数据库
DATABASE_URL=mysql+pymysql://edumind:你的强密码@127.0.0.1:3306/edumind

# 阿里云 DashScope（通义千问）
QWEN_API_KEY=sk-你的API密钥

# 应用环境
APP_ENV=production
DEBUG=false
HOST=127.0.0.1
PORT=2004

# Whisper（服务器上已下载模型可指定路径）
WHISPER_MODEL=base
WHISPER_MODEL_PATH=/var/www/edumind/models/whisper
WHISPER_PRELOAD_ON_STARTUP=true

# 文件存储
BASE_DIR=/var/www/edumind/backend_fastapi

# CORS（允许 iOS WKWebView 和本地开发）
CORS_ORIGINS=http://47.84.228.226,http://localhost:328,http://127.0.0.1:328
```

### 8. 下载 Whisper 模型

```bash
# 激活虚拟环境后执行
source /var/www/edumind/.venv/bin/activate

mkdir -p /var/www/edumind/models/whisper
python3 -c "
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch

model_id = 'openai/whisper-base'
model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id, cache_dir='/var/www/edumind/models/whisper')
processor = AutoProcessor.from_pretrained(model_id, cache_dir='/var/www/edumind/models/whisper')
print('Whisper base 模型下载完成')
"
```

或使用项目脚本：

```bash
cd /var/www/edumind
python3 download_whisper.py
```

### 9. 初始化数据库表

```bash
cd /var/www/edumind/backend_fastapi
source /var/www/edumind/.venv/bin/activate
python3 -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('数据库表创建完成')
"
```

### 10. 配置 Nginx 反向代理

```bash
# 写入 Nginx 子配置
cat > /etc/nginx/conf.d/edumind-api-http.conf << 'EOF'
server {
    listen 80 default_server;
    server_name 47.84.228.226 _;
    access_log /var/log/nginx/edumind_api_access.log;
    error_log  /var/log/nginx/edumind_api_error.log warn;

    location / {
        proxy_pass http://127.0.0.1:2004;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 5G;
    }
}
EOF

# 验证配置语法
nginx -t

# 启动并设置开机自启
systemctl start nginx
systemctl enable nginx
```

> **关键点**：确保 `/etc/nginx/nginx.conf` 中 `include /etc/nginx/conf.d/*.conf;` **没有被注释掉**。
> 注释掉后 nginx 不加载子配置，80 端口不会监听，外网无法访问。

### 11. 创建 systemd 服务

```bash
cat > /etc/systemd/system/edumind-api.service << 'EOF'
[Unit]
Description=EduMind FastAPI
After=network.target

[Service]
WorkingDirectory=/var/www/edumind/backend_fastapi
ExecStart=/var/www/edumind/.venv/bin/python /var/www/edumind/backend_fastapi/run_prod.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start edumind-api
systemctl enable edumind-api
```

### 12. 验证部署

```bash
# 检查服务状态
systemctl status edumind-api
systemctl status nginx
systemctl status mysqld

# 验证端口监听
ss -tlnp | grep -E ':80|:2004|:3306'

# 本地测试 API
curl http://127.0.0.1:2004/
curl http://127.0.0.1:2004/health

# 公网测试（确保安全组已放行 TCP 80）
curl http://47.84.228.226/
curl http://47.84.228.226/health
curl http://47.84.228.226/docs
```

---

## 三、阿里云安全组配置

登录阿里云控制台 → ECS → 实例 → 安全组 → **入方向规则**，添加：

| 方向 | 协议 | 端口范围 | 来源 | 说明 |
|------|------|----------|------|------|
| 入方向 | TCP | 80/80 | 0.0.0.0/0 | HTTP Web 访问 |
| 入方向 | TCP | 443/443 | 0.0.0.0/0 | HTTPS（后续扩展） |
| 入方向 | TCP | 22/22 | 0.0.0.0/0 | SSH（仅限管理） |

---

## 四、常见问题排查

### 外网无法访问，但本地 curl 正常

1. 确认安全组已放行 TCP 80
2. 确认 Nginx 配置 `include /etc/nginx/conf.d/*.conf;` 未被注释
3. 确认 Nginx 和 FastAPI 服务均已启动

```bash
# 逐项检查
ss -tlnp | grep :80          # Nginx 是否监听 80
systemctl status nginx        # Nginx 进程状态
systemctl status edumind-api  # FastAPI 进程状态
tail -f /var/log/nginx/edumind_api_access.log  # 查看访问日志
```

### FastAPI 启动报错（chromadb sqlite 相关）

```bash
# 确保 pysqlite3-binary 已安装
source /var/www/edumind/.venv/bin/activate
pip install pysqlite3-binary
```

### Whisper 模型未找到

```bash
ls /var/www/edumind/models/whisper/
# 应包含 base.pt 或对应模型文件
```

### MySQL 连接失败

```bash
# 检查 MySQL 是否运行
systemctl status mysqld

# 测试连接
mysql -u edumind -p edumind
```

---

## 五、服务管理命令

```bash
# 启动/停止/重启 API
systemctl start edumind-api
systemctl stop edumind-api
systemctl restart edumind-api

# 重载 Nginx 配置
nginx -s reload

# 查看 API 日志（systemd journal）
journalctl -u edumind-api -f

# 查看 Nginx 访问日志
tail -f /var/log/nginx/edumind_api_access.log

# 查看 Nginx 错误日志
tail -f /var/log/nginx/edumind_api_error.log
```

---

## 六、本次部署关键修复记录

| 时间 | 问题 | 解决方案 |
|------|------|----------|
| 2026-04-15 | `/etc/nginx/nginx.conf` 中 `include /etc/nginx/conf.d/*.conf;` 被注释，导致 Nginx 不加载子配置，80 端口未监听 | 取消注释该行，`nginx -s reload` |
| 2026-04-15 | 确认安全组 TCP 80 已开放 | 无需修改 |
| 2026-04-15 | 确认 MySQL、Nginx、FastAPI 服务均开机自启 | 无需修改 |
