# Frontend CLAUDE.md

Vue 3 + Element Plus + D3.js 前端应用

## Bash Commands
```bash
npm run dev      # 启动开发服务器 (端口 328)
npm run build    # 构建生产版本
npm run preview  # 预览生产构建
```

## Core Files
```
src/
├── main.js              # 应用入口
├── App.vue              # 根组件
├── config/index.js      # 配置设置
├── router/index.js      # Vue Router 路由
├── store/               # Vuex 状态管理
│   ├── index.js
│   └── auth.js          # 认证状态
├── api/                 # API 层 (与组件分离)
│   ├── video.js         # 视频 API
│   ├── note.js          # 笔记 API
│   ├── qa.js            # 问答 API
│   └── chat.js          # 聊天 API
├── views/               # 页面组件
│   ├── Home.vue
│   ├── VideoPlayer.vue
│   ├── VideoUpload.vue
│   ├── KnowledgeGraph.vue
│   └── Note.vue
├── components/          # 可复用组件
│   ├── Navigation.vue
│   ├── VideoPlayer.vue
│   └── VideoQA.vue
└── utils/
    └── request.js       # Axios 实例
```

## Code Style
- Vue 3 Composition API (`<script setup>`)
- Scoped 样式: `<style scoped>`
- API 层与组件分离 (所有 HTTP 请求放 `api/` 目录)
- 组件命名: PascalCase

## API Layer
所有后端请求通过 `src/api/` 模块，基于 `src/utils/request.js` 的 axios 实例：
```js
// 正确: 使用 api 模块
import { videoApi } from '@/api/video'
await videoApi.getList()

// 错误: 组件内直接调用 axios
```

## Backend API
- Base URL: `http://localhost:2004/api`
- 视频: `/api/videos`
- 字幕: `/api/subtitles`
- 笔记: `/api/notes`
- 问答: `/api/qa`
- 知识图谱: `/api/knowledge-graph`
