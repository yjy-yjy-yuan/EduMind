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

### 后端
- Python 3.10
- Flask 2.0+
- 其他依赖见 requirements.txt

### 前端
- Node.js 16+ ，参考：[text](https://blog.csdn.net/WHF__/article/details/129362462?ops_request_misc=%257B%2522request%255Fid%2522%253A%252292c74e602ab165368dc9716d84d7b355%2522%252C%2522scm%2522%253A%252220140713.130102334..%2522%257D&request_id=92c74e602ab165368dc9716d84d7b355&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~top_positive~default-1-129362462-null-null.142^v101^pc_search_result_base3&utm_term=nodejs%E5%AE%89%E8%A3%85%E5%8F%8A%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE&spm=1018.2226.3001.4187)

- Vue 3，参考：https://blog.csdn.net/qq_41729329/article/details/141890131?ops_request_misc=&request_id=&biz_id=102&utm_term=vue3%E5%AE%89%E8%A3%85&utm_medium=distribute.pc_search_result.none-task-blog-2~all~sobaiduweb~default-1-141890131.142^v101^pc_search_result_base3&spm=1018.2226.3001.4187

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
cd IVS-Flask-Vue/backend
conda create -n ivs python=3.10 -y
conda activate ivs
# 1. 安装 PyTorch（使用 CUDA 11.8）
pip install torch==2.0.0 torchvision==0.15.1 torchaudio==2.0.1 --index-url https://download.pytorch.org/whl/cu118

# 2. 安装 FAISS-GPU
conda install -c conda-forge faiss-gpu=1.8.0 -y

# 3. 安装其它依赖
pip install -r requirements.txt

```

## 环境配置注意事项

### 依赖版本兼容性
在安装依赖时，请注意以下版本兼容性问题：

1. **numpy版本**：必须使用1.23.5版本，更高版本可能导致与其他库的兼容性问题
   ```bash
   conda install numpy=1.23.5 -y
   ```

2. **scikit-learn版本**：推荐使用1.2.2版本以确保与numpy 1.23.5兼容
   ```bash
   conda install scikit-learn=1.2.2 -y
   ```

3. **FAISS模块**：如果安装FAISS失败，系统会自动降级使用备用搜索方法，但功能会受限

### 常见问题解决
如果遇到"numpy._core.multiarray failed to import"错误，请尝试以下步骤：
1. 卸载当前numpy：`conda remove numpy -y`
2. 安装指定版本：`conda install numpy=1.23.5 -y`
3. 安装scikit-learn：`conda install scikit-learn=1.2.2 -y`


### 前端
```bash
cd frontend
npm install @vitejs/plugin-vue --save-dev
npm install
npm run serve
```

### 启动项目
```bash

# 1. 启动Celery Worker  
conda activate ivs
cd IVS-Flask-Vue/backend
python -m celery -A app.celery_app worker --loglevel=info -P solo

# 2. 启动 Flask 后端 
conda activate ivs
cd IVS-Flask-Vue/backend
python run.py

# 3. 启动前端开发服务器(在Powershell中)  
cd E:/infomation/graduation/test/IVS-Flask-Vue/frontend
npm run dev
```
