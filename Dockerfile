# EduMind Backend - Railway 部署镜像（轻量版）
# 构建上下文为仓库根目录，.dockerignore 排除无关文件
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 从后端子目录复制代码
COPY backend_fastapi/requirements.txt /app/requirements.txt

# 安装 Python 依赖（轻量版，不含 torch/whisper）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        fastapi==0.109.0 \
        uvicorn[standard]==0.27.0 \
        python-multipart==0.0.6 \
        sqlalchemy==2.0.25 \
        alembic==1.13.1 \
        pymysql==1.1.0 \
        cryptography>=42.0.0 \
        pydantic==2.5.3 \
        pydantic-settings==2.1.0 \
        email-validator>=2.1.0 \
        Werkzeug>=3.0.0 \
        sentence-transformers==3.4.1 \
        faiss-cpu==1.8.0 \
        chromadb>=0.4.0 \
        "numpy<2" \
        google-generativeai>=0.3.0 \
        transformers>=4.36.0 \
        Pillow>=10.0.0 \
        python-dotenv==1.0.0 \
        yt-dlp>=2024.3.10 \
        opencv-python-headless>=4.9.0.80 \
        pydub==0.25.1 \
        jieba==0.42.1 \
        scikit-learn>=1.4.0 \
        httpx==0.26.0 \
        requests>=2.31.0

# 复制后端应用代码（从子目录）
COPY backend_fastapi/ /app/

RUN mkdir -p /app/uploads /app/subtitles /app/previews /app/temp /app/data/chroma && \
    chmod 755 /app/uploads /app/subtitles /app/previews /app/temp /app/data

ENV PORT=8000
ENV HOST=0.0.0.0

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
