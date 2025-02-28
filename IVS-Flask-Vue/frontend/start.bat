@echo off
echo 正在启动AI-EdVision前端服务...

REM 检查是否已安装依赖
if not exist "node_modules" (
    echo 正在安装依赖...
    call npm install
) else (
    echo 依赖已安装
)

REM 启动开发服务器
echo 正在启动开发服务器...
npm run dev
