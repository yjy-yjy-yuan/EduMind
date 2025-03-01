# 前端部分功能介绍(Frontend)文件夹

## 根目录下的代码文件实现的功能
- index.html: 该文件是前端应用的入口 HTML 文件，定义了页面的基本结构和加载脚本。
- package.json: 该文件定义了前端应用的依赖和脚本命令，如启动开发服务器、构建应用等。
- start.bat: 该批处理文件用于启动前端开发服务器，并自动安装依赖。
- vite.config.js: 该文件是 Vite 的配置文件，定义了别名和插件等。

## frontend\node_modules 文件夹的介绍
- node_modules 文件夹是 Node.js 的默认模块存放目录，存放项目依赖的包
- 包含以下功能：
依赖管理: 存放项目所需的所有第三方库和工具。
自动生成: 通过 npm install 或 yarn install 命令自动生成，无需手动修改。
模块加载: Node.js 运行时从这里加载所需的模块。


## frontend\src 文件夹的介绍
- frontend\src\components : 存放 Vue 或 React 组件，用于构建用户界面
- frontend\src\router : 定义前端路由，管理页面导航
- frontend\src\store : 定义前端状态管理，用于存储应用的数据
- frontend\src\views : 存放前端页面，用于展示用户界面
- frontend\src\api : 存放前端与后端通信的 API，用于数据交互
- frontend\src\utils : 存放前端工具函数，用于实现前端逻辑
- frontend\src\main : 存放前端应用的主入口