import { createMemoryHistory, createRouter, createWebHistory } from 'vue-router'
import * as authStore from '@/store/auth'

const Home = () => import('@/views/Home.vue')
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const Recommendations = () => import('@/views/Recommendations.vue')
const Videos = () => import('@/views/Videos.vue')
const VideoDetail = () => import('@/views/VideoDetail.vue')
const Player = () => import('@/views/Player.vue')
const Upload = () => import('@/views/Upload.vue')
const Notes = () => import('@/views/Notes.vue')
const NoteEdit = () => import('@/views/NoteEdit.vue')
const QA = () => import('@/views/QA.vue')
const Profile = () => import('@/views/Profile.vue')
const LearningPath = () => import('@/views/LearningPath.vue')
const Guide = () => import('@/views/Guide.vue')
const DesignAssistant = () => import('@/views/DesignAssistant.vue')
const Search = () => import('@/views/Search.vue')

const isFileProtocol = window.location.protocol === 'file:'
const history = isFileProtocol ? createMemoryHistory() : createWebHistory()

const router = createRouter({
  history,
  routes: [
    { path: '/', name: 'Home', component: Home, meta: { title: '首页' } },
    { path: '/recommendations', name: 'Recommendations', component: Recommendations, meta: { title: '推荐学习' } },
    { path: '/videos', name: 'Videos', component: Videos, meta: { title: '视频' } },
    { path: '/videos/:id', name: 'VideoDetail', component: VideoDetail, meta: { title: '视频详情' } },
    { path: '/player/:id', name: 'Player', component: Player, meta: { title: '播放', hideTabBar: true } },
    { path: '/upload', name: 'Upload', component: Upload, meta: { title: '上传' } },
    { path: '/notes', name: 'Notes', component: Notes, meta: { title: '笔记', requiresAuth: true } },
    { path: '/notes/new', name: 'NoteNew', component: NoteEdit, meta: { title: '新建笔记', hideTabBar: true, requiresAuth: true } },
    { path: '/notes/:id', name: 'NoteEdit', component: NoteEdit, meta: { title: '编辑笔记', hideTabBar: true, requiresAuth: true } },
    { path: '/qa', name: 'QA', component: QA, meta: { title: 'AI 问答', hideTabBar: true } },
    { path: '/search', name: 'Search', component: Search, meta: { title: '搜索' } },
    { path: '/learning-path', name: 'LearningPath', component: LearningPath, meta: { title: '学习路径' } },
    { path: '/guide', name: 'Guide', component: Guide, meta: { title: '使用指南', hideTabBar: true } },
    { path: '/design-assistant', name: 'DesignAssistant', component: DesignAssistant, meta: { title: '设计助手', hideTabBar: true, requiresAuth: true } },
    { path: '/profile', name: 'Profile', component: Profile, meta: { title: '我的', requiresAuth: true } },
    { path: '/login', name: 'Login', component: Login, meta: { title: '登录', hideTabBar: true } },
    { path: '/register', name: 'Register', component: Register, meta: { title: '注册', hideTabBar: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

if (isFileProtocol) {
  router.replace('/').catch(() => {})
}

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
