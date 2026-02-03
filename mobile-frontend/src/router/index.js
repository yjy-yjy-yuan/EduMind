import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import * as authStore from '@/store/auth'

import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Videos from '@/views/Videos.vue'
import VideoDetail from '@/views/VideoDetail.vue'
import Player from '@/views/Player.vue'
import Upload from '@/views/Upload.vue'
import Notes from '@/views/Notes.vue'
import NoteEdit from '@/views/NoteEdit.vue'
import QA from '@/views/QA.vue'
import Profile from '@/views/Profile.vue'
import LearningPath from '@/views/LearningPath.vue'
import Knowledge from '@/views/Knowledge.vue'
import Guide from '@/views/Guide.vue'

const router = createRouter({
  history: window.location.protocol === 'file:' ? createWebHashHistory() : createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: Home, meta: { title: '首页' } },
    { path: '/videos', name: 'Videos', component: Videos, meta: { title: '视频' } },
    { path: '/videos/:id', name: 'VideoDetail', component: VideoDetail, meta: { title: '视频详情' } },
    { path: '/player/:id', name: 'Player', component: Player, meta: { title: '播放', hideTabBar: true } },
    { path: '/upload', name: 'Upload', component: Upload, meta: { title: '上传' } },
    { path: '/notes', name: 'Notes', component: Notes, meta: { title: '笔记', requiresAuth: true } },
    { path: '/notes/new', name: 'NoteNew', component: NoteEdit, meta: { title: '新建笔记', hideTabBar: true, requiresAuth: true } },
    { path: '/notes/:id', name: 'NoteEdit', component: NoteEdit, meta: { title: '编辑笔记', hideTabBar: true, requiresAuth: true } },
    { path: '/qa', name: 'QA', component: QA, meta: { title: 'AI 问答', hideTabBar: true } },
    { path: '/learning-path', name: 'LearningPath', component: LearningPath, meta: { title: '学习路径' } },
    { path: '/knowledge', name: 'Knowledge', component: Knowledge, meta: { title: '知识点总览' } },
    { path: '/guide', name: 'Guide', component: Guide, meta: { title: '使用指南', hideTabBar: true } },
    { path: '/profile', name: 'Profile', component: Profile, meta: { title: '我的', requiresAuth: true } },
    { path: '/login', name: 'Login', component: Login, meta: { title: '登录', hideTabBar: true } },
    { path: '/register', name: 'Register', component: Register, meta: { title: '注册', hideTabBar: true } }
  ]
})

router.beforeEach(async (to, from, next) => {
  document.title = to.meta?.title ? `${to.meta.title} - EduMind Mobile` : 'EduMind Mobile'

  const state = authStore.getState()
  const isAuthed = Boolean(state.isAuthenticated)
  const isAuthPage = to.path === '/login' || to.path === '/register'

  if (to.meta?.requiresAuth && !isAuthed && !isAuthPage) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

export default router
