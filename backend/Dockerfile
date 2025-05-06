FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV FLASK_CONFIG=production

# 暴露端口
EXPOSE 5001

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "run:app"]
