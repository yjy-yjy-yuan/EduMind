#!/bin/bash

# 错误处理
set -e
trap 'echo "Error on line $LINENO"' ERR

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 检测操作系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
fi

# 创建必要的目录
log "Creating necessary directories..."
mkdir -p captions downloads logs

# 安装系统依赖
log "Installing system dependencies..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg python3-dev python3-pip python3-venv
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    sudo yum install -y epel-release
    sudo yum install -y ffmpeg ffmpeg-devel python3-devel python3-pip
else
    log "Unsupported OS. Please install dependencies manually."
    exit 1
fi

# 验证FFmpeg安装
log "Verifying FFmpeg installation..."
if command -v ffmpeg >/dev/null 2>&1; then
    log "FFmpeg installed successfully"
    ffmpeg -version
else
    log "FFmpeg installation failed"
    exit 1
fi

# 创建并激活虚拟环境
log "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
log "Upgrading pip..."
pip install --upgrade pip

# 安装Python依赖
log "Installing Python dependencies..."
pip install -r requirements.txt

# 检查CUDA可用性
log "Checking CUDA availability..."
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# 设置文件权限
log "Setting file permissions..."
chmod -R 755 .
chmod -R 777 captions downloads logs

# 创建示例环境变量文件
if [ ! -f .env ]; then
    log "Creating example .env file..."
    cat > .env << EOF
# OpenAI API Key
OPENAI_API_KEY=your_api_key_here

# 其他配置项
DEBUG=False
LOG_LEVEL=INFO
EOF
fi

# 创建systemd服务文件
log "Creating systemd service file..."
sudo bash -c 'cat > /etc/systemd/system/ai-edvision.service << EOF
[Unit]
Description=AI-EdVision Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin:$PATH
ExecStart=$PWD/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

# 重新加载systemd配置
log "Reloading systemd configuration..."
sudo systemctl daemon-reload

# 启用服务
log "Enabling service..."
sudo systemctl enable ai-edvision

log "Deployment completed successfully!"
log "To start the service, run: sudo systemctl start ai-edvision"
log "To check status, run: sudo systemctl status ai-edvision"
log "To view logs, run: sudo journalctl -u ai-edvision -f"
