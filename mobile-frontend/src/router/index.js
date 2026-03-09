import { createRouter, createWebHistory } from 'vue-router'

import Guide from '@/views/Guide.vue'
import Home from '@/views/Home.vue'
import Knowledge from '@/views/Knowledge.vue'
import LearningPath from '@/views/LearningPath.vue'
import Login from '@/views/Login.vue'
import NoteEdit from '@/views/NoteEdit.vue'
import Notes from '@/views/Notes.vue'
import Player from '@/views/Player.vue'
import Profile from '@/views/Profile.vue'
import QA from '@/views/QA.vue'
import Register from '@/views/Register.vue'
import Upload from '@/views/Upload.vue'
import VideoDetail from '@/views/VideoDetail.vue'
import Videos from '@/views/Videos.vue'

const routes = [
  { path: '/', name: 'Home', component: Home, meta: { title: '首页' } },
  { path: '/guide', name: 'Guide', component: Guide, meta: { title: '新手指南' } },
  { path: '/videos', name: 'Videos', component: Videos, meta: { title: '视频列表' } },
  { path: '/videos/:id', name: 'VideoDetail', component: VideoDetail, meta: { title: '视频详情' } },
  { path: '/upload', name: 'Upload', component: Upload, meta: { title: '上传视频' } },
  { path: '/player/:id', name: 'Player', component: Player, meta: { title: '视频播放' } },
  { path: '/qa', name: 'QA', component: QA, meta: { title: 'AI 问答' } },
  { path: '/notes', name: 'Notes', component: Notes, meta: { title: '笔记' } },
  { path: '/notes/new', name: 'NoteNew', component: NoteEdit, meta: { title: '新建笔记' } },
  { path: '/notes/:id', name: 'NoteEdit', component: NoteEdit, meta: { title: '编辑笔记' } },
  { path: '/knowledge', name: 'Knowledge', component: Knowledge, meta: { title: '知识点总览' } },
  { path: '/learning-path', name: 'LearningPath', component: LearningPath, meta: { title: '学习路径' } },
  { path: '/profile', name: 'Profile', component: Profile, meta: { title: '我的' } },
  { path: '/login', name: 'Login', component: Login, meta: { title: '登录', hideTabBar: true } },
  { path: '/register', name: 'Register', component: Register, meta: { title: '注册', hideTabBar: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta?.title ? `${to.meta.title} - AI-EdVision Mobile` : 'AI-EdVision Mobile'
  next()
})

export default router
