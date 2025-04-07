<template>
  <div class="navigation-container" :class="{ 'eye-care-mode': isEyeCareMode }">
    <!-- 自定义导航栏，不使用 el-menu 避免自动添加的 ... 菜单 -->
    <div class="custom-nav">
      <!-- 左侧Logo和名称 -->
      <div class="logo-container">
        <i class="fas fa-graduation-cap logo-icon"></i>
        <span class="logo-text">AI-EdVision</span>
      </div>
      
      <div class="flex-spacer"></div>
      
      <!-- 右侧导航菜单 -->
      <div class="nav-items">
        <router-link to="/" class="nav-item" :class="{ active: activeRoute === '/' }">首页</router-link>
        <router-link to="/video/upload" class="nav-item" :class="{ active: activeRoute === '/video/upload' }">视频管理</router-link>
        <router-link to="/guide" class="nav-item" :class="{ active: activeRoute === '/guide' }">使用指南</router-link>
        
        <!-- 护眼模式切换按钮 -->
        <div class="nav-item theme-item" @click="toggleEyeCareMode">
          <i :class="isEyeCareMode ? 'fas fa-sun' : 'fas fa-eye'"></i>
          <span>{{ isEyeCareMode ? '标准模式' : '护眼模式' }}</span>
        </div>
        
        <!-- 用户登录状态 -->
        <template v-if="authState.isAuthenticated">
          <el-dropdown trigger="click" @command="handleCommand" class="user-dropdown">
            <div class="nav-item user-item">
              <i class="fas fa-user-circle"></i>
              <span>{{ authState.user.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-item login-item">
            <i class="fas fa-sign-in-alt"></i>
            <span>登录/注册</span>
          </router-link>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import authStore from '../store/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const isEyeCareMode = ref(localStorage.getItem('eyeCareMode') === 'true')
const authState = computed(() => authStore.getState())

// 检查用户登录状态
onMounted(() => {
  authStore.checkAuthStatus()
})

// 计算当前活动路由
const activeRoute = computed(() => {
  return route.path
})

// 处理下拉菜单命令
const handleCommand = (command) => {
  if (command === 'logout') {
    logout()
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

// 退出登录
const logout = async () => {
  try {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    })
    
    const data = await response.json()
    
    if (data.success) {
      // 清除认证状态
      authStore.clearAuth()
      // 显示成功消息
      ElMessage.success('退出成功')
      // 跳转到首页
      router.push('/')
    } else {
      ElMessage.error(data.message || '退出失败')
    }
  } catch (error) {
    console.error('退出错误:', error)
    ElMessage.error('退出失败，请重试')
  }
}

// 护眼模式切换功能
const toggleEyeCareMode = () => {
  isEyeCareMode.value = !isEyeCareMode.value
  
  if (isEyeCareMode.value) {
    document.body.classList.add('eye-care-mode')
    localStorage.setItem('eyeCareMode', 'true')
  } else {
    document.body.classList.remove('eye-care-mode')
    localStorage.setItem('eyeCareMode', 'false')
  }
}

// 监听路由变化，更新激活的菜单项
watch(() => route.path, (newPath) => {
  activeRoute.value = newPath
})

// 从本地存储中获取护眼模式设置
onMounted(() => {
  const savedMode = localStorage.getItem('eyeCareMode')
  if (savedMode === 'true') {
    isEyeCareMode.value = true
    document.body.classList.add('eye-care-mode')
  }
})
</script>

<style scoped>
.navigation-container {
  margin-bottom: 20px;
}

.custom-nav {
  padding: 0 20px;
  height: 64px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 0 0 12px 12px;
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s ease;
  align-items: center;
}

/* Logo容器样式 */
.logo-container {
  display: flex;
  align-items: center;
  padding: 0 15px;
  height: 64px;
  margin-right: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  line-height: 64px;
}

.logo-icon {
  font-size: 24px;
  color: #fff;
  margin-right: 10px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
  display: inline-block;
  vertical-align: middle;
}

.flex-spacer {
  flex-grow: 1;
}

/* 导航菜单项样式 */
.nav-items {
  display: flex;
  align-items: center;
  height: 100%;
}

.nav-item {
  padding: 0 25px;
  height: 64px;
  line-height: 64px;
  color: #fff;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
  text-decoration: none;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.nav-item:hover, 
.nav-item.active {
  background-color: rgba(255, 255, 255, 0.15);
  color: #fff;
  transform: translateY(-2px);
}

/* 添加悬停时的下划线动画 */
.nav-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 3px;
  background-color: #fff;
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.nav-item:hover::after,
.nav-item.active::after {
  width: 70%;
}

/* 主题切换菜单项样式 */
.theme-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.theme-item i {
  font-size: 18px;
}

/* 登录/注册按钮样式 */
.login-item {
  background-color: var(--primary-color);
  color: white !important;
  border-radius: 6px;
  padding: 6px 16px;
  transition: all 0.3s ease;
}

.login-item:hover {
  background-color: var(--primary-color-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* 用户下拉菜单 */
.user-dropdown {
  cursor: pointer;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--primary-color);
  color: white !important;
  border-radius: 6px;
  padding: 6px 16px;
  transition: all 0.3s ease;
}

.user-item:hover {
  background-color: var(--primary-color-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.user-item i {
  font-size: 16px;
}

/* 修复护眼模式下的样式 */
.eye-care-mode .user-item,
.eye-care-mode .login-item {
  background-color: var(--primary-color-eye-care);
  color: var(--text-color-eye-care) !important;
}

.eye-care-mode .user-item:hover,
.eye-care-mode .login-item:hover {
  background-color: var(--primary-color-eye-care-dark);
}

/* 适配移动端 */
@media (max-width: 768px) {
  .logo-text {
    display: none;
  }
  
  .nav-item {
    padding: 0 15px;
    font-size: 14px;
  }
  
  .theme-item span {
    display: none;
  }
}
</style>

<style>
/* 全局样式，不使用scoped */
body {
  --primary-bg: #ffffff;
  --secondary-bg: #f8f9fa;
  --primary-text: #333333;
  --secondary-text: #6c757d;
  --border-color: #e9ecef;
  --card-bg: #ffffff;
  --shadow-color: rgba(0, 0, 0, 0.1);
  --accent-color: #667eea;
  --button-bg: #667eea;
  --button-hover: #5a6acf;
  --hero-bg: linear-gradient(135deg, #667eea, #764ba2);
  --nav-bg: linear-gradient(135deg, #667eea, #764ba2);
  --link-color: #5a6acf;
  --code-bg: #f5f7ff;
  --selection-bg: #e6e9f5;
  --selection-text: #333333;
  
  background-color: var(--primary-bg);
  color: var(--primary-text);
  transition: all 0.3s ease;
}

body.eye-care-mode {
  --primary-bg: #f0f5e5;
  --secondary-bg: #e6f0d8;
  --primary-text: #3e4a3d;
  --secondary-text: #5c6b5c;
  --border-color: #c9d6c2;
  --card-bg: #e8f0dd;
  --shadow-color: rgba(0, 0, 0, 0.08);
  --accent-color: #68a357;
  --button-bg: #68a357;
  --button-hover: #5a8f4b;
  --hero-bg: linear-gradient(135deg, #a8c896, #68a357);
  --nav-bg: linear-gradient(135deg, #a8c896, #68a357);
  --link-color: #4d7b3e;
  --code-bg: #e6f0d8;
  --selection-bg: #c9d6c2;
  --selection-text: #3e4a3d;
}

/* 应用护眼模式到导航栏 */
body.eye-care-mode .custom-nav {
  background: var(--nav-bg);
}

/* 应用护眼模式到所有卡片 */
.el-card {
  background-color: var(--card-bg);
  color: var(--primary-text);
  border-color: var(--border-color);
  transition: all 0.3s ease;
}

/* 应用护眼模式到所有按钮 */
.el-button {
  transition: all 0.3s ease;
}

body.eye-care-mode .el-button--primary {
  background-color: var(--button-bg);
  border-color: var(--button-bg);
}

body.eye-care-mode .el-button--primary:hover,
body.eye-care-mode .el-button--primary:focus {
  background-color: var(--button-hover);
  border-color: var(--button-hover);
}

body.eye-care-mode .el-button--text {
  color: var(--accent-color);
}

/* 应用护眼模式到所有输入框 */
.el-input__inner {
  background-color: var(--card-bg);
  color: var(--primary-text);
  border-color: var(--border-color);
  transition: all 0.3s ease;
}

/* 应用护眼模式到表格 */
body.eye-care-mode .el-table {
  background-color: var(--card-bg);
  color: var(--primary-text);
}

body.eye-care-mode .el-table th,
body.eye-care-mode .el-table tr {
  background-color: var(--secondary-bg);
}

body.eye-care-mode .el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: var(--primary-bg);
}

/* 应用护眼模式到链接 */
body.eye-care-mode a:not(.nav-item) {
  color: var(--link-color);
}

/* 应用护眼模式到分割线 */
body.eye-care-mode .el-divider {
  background-color: var(--border-color);
}

/* 应用护眼模式到弹窗 */
body.eye-care-mode .el-dialog,
body.eye-care-mode .el-message-box {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

body.eye-care-mode .el-dialog__title,
body.eye-care-mode .el-message-box__title {
  color: var(--primary-text);
}

/* 应用护眼模式到下拉菜单 */
body.eye-care-mode .el-dropdown-menu {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

body.eye-care-mode .el-dropdown-menu__item {
  color: var(--primary-text);
}

body.eye-care-mode .el-dropdown-menu__item:hover {
  background-color: var(--secondary-bg);
}

/* 应用护眼模式到标签页 */
body.eye-care-mode .el-tabs__item {
  color: var(--secondary-text);
}

body.eye-care-mode .el-tabs__item.is-active {
  color: var(--accent-color);
}

body.eye-care-mode .el-tabs__active-bar {
  background-color: var(--accent-color);
}

/* 应用护眼模式到分页器 */
body.eye-care-mode .el-pagination {
  color: var(--secondary-text);
}

body.eye-care-mode .el-pagination button:disabled {
  color: var(--secondary-text);
}

body.eye-care-mode .el-pager li {
  background-color: var(--card-bg);
  color: var(--secondary-text);
}

body.eye-care-mode .el-pager li.active {
  color: var(--accent-color);
}

/* 应用护眼模式到代码块 */
body.eye-care-mode pre,
body.eye-care-mode code {
  background-color: var(--code-bg);
  color: var(--primary-text);
  border-color: var(--border-color);
}

/* 应用护眼模式到滚动条 */
body.eye-care-mode::-webkit-scrollbar {
  width: 10px;
}

body.eye-care-mode::-webkit-scrollbar-track {
  background: var(--primary-bg);
}

body.eye-care-mode::-webkit-scrollbar-thumb {
  background-color: var(--border-color);
  border-radius: 6px;
  border: 3px solid var(--primary-bg);
}

/* 应用护眼模式到文本选择 */
body.eye-care-mode ::selection {
  background-color: var(--selection-bg);
  color: var(--selection-text);
}

/* 应用护眼模式到英雄区域 */
body.eye-care-mode .hero-section {
  background: var(--hero-bg);
}

/* 应用护眼模式到视频播放器 */
body.eye-care-mode video {
  box-shadow: 0 4px 12px var(--shadow-color);
}

/* 应用护眼模式到表单 */
body.eye-care-mode .el-form-item__label {
  color: var(--primary-text);
}

body.eye-care-mode .el-checkbox__label {
  color: var(--primary-text);
}

body.eye-care-mode .el-radio__label {
  color: var(--primary-text);
}

/* 应用护眼模式到加载指示器 */
body.eye-care-mode .el-loading-spinner .path {
  stroke: var(--accent-color);
}

/* 应用护眼模式到通知 */
body.eye-care-mode .el-notification {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

body.eye-care-mode .el-notification__title {
  color: var(--primary-text);
}

body.eye-care-mode .el-notification__content {
  color: var(--secondary-text);
}

/* 应用护眼模式到提示 */
body.eye-care-mode .el-tooltip__popper {
  background-color: var(--card-bg);
  color: var(--primary-text);
  border-color: var(--border-color);
}
</style>
