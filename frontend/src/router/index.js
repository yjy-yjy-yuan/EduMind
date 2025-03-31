import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import VideoUpload from '../views/VideoUpload.vue'
import VideoDetail from '../views/VideoDetail.vue'
import VideoPlayer from '../views/VideoPlayer.vue'
import Note from '../views/Note.vue'
import LearningPath from '../views/LearningPath.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '首页'
    }
  },
  {
    path: '/video/upload',
    name: 'VideoUpload',
    component: VideoUpload,
    meta: {
      title: '上传视频'
    }
  },
  {
    path: '/video/:id',
    name: 'VideoDetail',
    component: VideoDetail,
    meta: {
      title: '视频详情'
    }
  },
  {
    path: '/player/:id',
    name: 'VideoPlayer',
    component: VideoPlayer,
    meta: {
      title: '视频播放'
    }
  },
  {
    path: '/learning-path',
    name: 'LearningPath',
    component: LearningPath,
    meta: {
      title: '学习路径'
    }
  },
  {
    path: '/notes',
    name: 'Notes',
    component: Note,
    meta: {
      title: '笔记系统'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - AI-EdVision` : 'AI-EdVision'
  next()
})

export default router
