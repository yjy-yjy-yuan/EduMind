# AI-EdVision 云端部署指南

## 1. 服务器要求

### 1.1 硬件配置建议
- CPU: 4核或以上
- 内存: 至少8GB RAM
- 磁盘空间: 至少50GB
- GPU: NVIDIA GPU（推荐，用于Whisper模型加速）

### 1.2 软件要求
- Ubuntu 20.04/22.04 LTS 或 CentOS 7/8
- Python 3.8或以上
- CUDA 11.8（如果使用GPU）
- FFmpeg

## 2. 环境准备

### 2.1 更新系统
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get upgrade -y

# CentOS
sudo yum update -y
```

### 2.2 安装Python
```bash
# Ubuntu/Debian
sudo apt-get install -y python3 python3-pip python3-venv

# CentOS
sudo yum install -y python3 python3-pip
```

### 2.3 安装CUDA（如果使用GPU）
请参考NVIDIA官方指南：https://developer.nvidia.com/cuda-11-8-0-download-archive

## 3. 项目部署

### 3.1 获取代码
```bash
# 创建项目目录
mkdir -p /opt/ai-edvision
cd /opt/ai-edvision

# 克隆代码（替换为实际仓库地址）
git clone <repository_url> .
```

### 3.2 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 3.3 运行部署脚本
```bash
# 添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 3.4 配置项目
1. 创建必要的目录：
```bash
mkdir -p captions downloads logs
```

2. 配置环境变量（如果需要）：
```bash
# 创建环境变量文件
touch .env

# 添加必要的环境变量
echo "OPENAI_API_KEY=your_api_key" >> .env
```

## 4. 启动服务

### 4.1 使用Screen运行（开发环境）
```bash
# 安装screen
sudo apt-get install screen  # Ubuntu
sudo yum install screen     # CentOS

# 创建新的screen会话
screen -S ai-edvision

# 启动服务
python main.py

# 分离screen会话（Ctrl+A+D）
```

### 4.2 使用Systemd运行（生产环境）
1. 创建服务文件：
```bash
sudo nano /etc/systemd/system/ai-edvision.service
```

2. 添加以下内容：
```ini
[Unit]
Description=AI-EdVision Service
After=network.target

[Service]
Type=simple
User=<your_user>
WorkingDirectory=/opt/ai-edvision
Environment=PATH=/opt/ai-edvision/venv/bin:$PATH
ExecStart=/opt/ai-edvision/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. 启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-edvision
sudo systemctl start ai-edvision
```

## 5. 监控和维护

### 5.1 查看日志
```bash
# 查看应用日志
tail -f logs/app.log

# 查看系统服务日志
sudo journalctl -u ai-edvision -f
```

### 5.2 更新部署
```bash
# 停止服务
sudo systemctl stop ai-edvision

# 更新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl start ai-edvision
```

## 6. 故障排除

### 6.1 常见问题
1. FFmpeg相关错误
```bash
# 检查FFmpeg安装
ffmpeg -version

# 重新安装FFmpeg
sudo apt-get install --reinstall ffmpeg  # Ubuntu
sudo yum reinstall ffmpeg               # CentOS
```

2. CUDA相关错误
```bash
# 检查CUDA安装
nvidia-smi

# 检查PyTorch是否使用GPU
python -c "import torch; print(torch.cuda.is_available())"
```

### 6.2 性能优化
1. 使用GPU加速
2. 配置适当的并发数
3. 根据服务器配置调整内存使用

## 7. 备份策略

### 7.1 数据备份
```bash
# 备份重要数据
tar -czf backup.tar.gz captions downloads logs
```

### 7.2 定期备份
创建定时备份脚本并添加到crontab。

## 8. 安全建议

1. 配置防火墙
2. 使用HTTPS
3. 定期更新系统和依赖
4. 使用非root用户运行服务
5. 设置适当的文件权限

## 9. 联系与支持

如遇到问题，请联系：
- 技术支持：[联系方式]
- 项目文档：[文档链接]
