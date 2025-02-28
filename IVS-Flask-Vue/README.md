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

### 后端
- Python 3.8+
- Flask 2.0+
- 其他依赖见 requirements.txt

### 前端
- Node.js 16+
- Vue 3
- 其他依赖见 package.json

## 安装和运行

### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

### 前端
```bash
cd frontend
npm install
npm run serve
```
