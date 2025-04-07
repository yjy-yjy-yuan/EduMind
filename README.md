# IVS-Flask-Vue

基于Flask和Vue的智能教育视频分析系统

## 项目结构

```
IVS-Flask-Vue/
├── backend/                # Flask后端
│   ├── app/
│   │   ├── __init__.py    # Flask应用初始化
│   │   ├── models/        # 数据模型
│   │   ├── routes/        # API路由
│   │   ├── services/      # 业务逻辑
│   │   └── utils/         # 工具函数
│   ├── config.py          # 配置文件
│   ├── requirements.txt   # Python依赖
│   └── run.py            # 启动脚本
│
├── frontend/              # Vue前端
│   ├── public/           # 静态资源
│   ├── src/
│   │   ├── assets/       # 资源文件
│   │   ├── components/   # Vue组件
│   │   ├── views/        # 页面视图
│   │   ├── router/       # 路由配置
│   │   ├── store/        # Vuex状态管理
│   │   ├── api/          # API接口
│   │   └── utils/        # 工具函数
│   ├── package.json      # npm配置
│   └── vue.config.js     # Vue配置
```

## 开发环境要求

### 配置内存数据库 Redis
- 访问 https://github.com/microsoftarchive/redis/releases 
- 下载最新的 Redis-x64-xxx.msi 安装包，双击安装包进行安装
- 安装时选择"Add the Redis installation folder to the PATH environment variable"

### 配置ffmpeg
[ffmpeg配置](https://blog.csdn.net/qq_45956730/article/details/125272407?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522fe6e09d28e4e26828992bf3d6d5ba651%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=fe6e09d28e4e26828992bf3d6d5ba651&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~top_positive~default-1-125272407-null-null.142^v102^pc_search_result_base3&utm_term=ffmpeg%E5%AE%89%E8%A3%85&spm=1018.2226.3001.4187)

### 本地部署ollama并Pull指定模型
- 官网下载ollama：https://ollama.com/
- 配置ollama：[配置ollama，避免存储空间紧张](https://blog.csdn.net/2501_90561511/article/details/145615092?ops_request_misc=%257B%2522request%255Fid%2522%253A%2522ed67978029517f895d00870bb578cd9e%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=ed67978029517f895d00870bb578cd9e&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~baidu_landing_v2~default-1-145615092-null-null.142^v102^pc_search_result_base3&utm_term=ollama%E9%85%8D%E7%BD%AE%E5%AE%89%E8%A3%85&spm=1018.2226.3001.4187)
- Pull指定模型：
    ```bash
    ollama run deepseek-r1:8b
    ollama run qwen2.5:7b
    ```
### 后端
- Python 3.10
- Flask 2.0+
- 其他依赖见 requirements.txt

### 前端
- Node.js 16+ ，参考：[Node.js安装及环境配置](https://blog.csdn.net/WHF__/article/details/129362462?ops_request_misc=%257B%2522request%255Fid%2522%253A%252292c74e602ab165368dc9716d84d7b355%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=92c74e602ab165368dc9716d84d7b355&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~top_positive~default-1-129362462-null-null.142^v101^pc_search_result_base3&utm_term=nodejs%E5%AE%89%E8%A3%85%E5%8F%8A%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE&spm=1018.2226.3001.4187)

- Vue 3，参考：[Vue 3安装配置](https://blog.csdn.net/qq_41729329/article/details/141890131?ops_request_misc=&request_id=&biz_id=102&utm_term=vue3%E5%AE%89%E8%A3%85&utm_medium=distribute.pc_search_result.none-task-blog-2~all~sobaiduweb~default-1-141890131.142^v101^pc_search_result_base3&spm=1018.2226.3001.4187)

- 其他依赖见 package.json(看下就好，不用太在意)


## 安装和运行

### 启动 Redis
```bash
# 终端中进行
redis-server

# 另一个终端中，检查一下Redis服务是否正在运行
redis-cli ping  #结果返回 PONG 即运行成功
```

### 后端
```bash
cd ....../IVS-Flask-Vue/backend # 切换为自己的backend文件路径
conda create -n ivs python=3.10 -y
conda activate ivs

# 1. 安装主要依赖
pip install -r requirements.txt

# 2. 安装 PyTorch（使用 CUDA 11.8）
# 2.1 GPU环境
conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.8 -c pytorch -c nvidia

# 2.2 CPU环境
pip install torch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu


# 3. 安装 FAISS-GPU
# 3.1 如果你有 CUDA 11.8 的 GPU 资源
conda install -c conda-forge faiss-gpu=1.8.0 -y

# 3.2 如果你只有 CPU 资源
conda install -c conda-forge faiss-cpu=1.8.0 -y

```


### 前端(可能需要管理员身份)
```bash
cd ....../IVS-Flask-Vue/frontend # 切换为自己的frontend文件路径
npm install @vitejs/plugin-vue --save-dev
npm install
```

### 启动项目
```bash
# 1. 启动Celery Worker  
conda activate ivs
cd ....../IVS-Flask-Vue/backend # 切换为自己的backend文件路径
python -m celery -A app.celery_app worker --loglevel=info -P solo

# 2. 启动 Flask 后端 
conda activate ivs
cd ....../AI-EdVision/backend  #切换为自己的backend文件路径
python run.py

# 3. 启动前端开发服务器(在Powershell中)  
cd ....../AI-EdVision/frontend  #切换为自己的frontend文件路径
npm run dev
npm run dev -- --host # 可以让同一局域网下都可以访问，生成的192.168.xx.xx可以作为服务外网访问
```