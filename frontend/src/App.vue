<template>
  <div id="app">
    <!-- 导航菜单 -->
    <Navigation />

    <!-- 全局加载状态 -->
    <div v-if="$store.state.loading" class="global-loading">
      <el-card class="loading-card">
        <div class="loading-spinner">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
      </el-card>
    </div>

    <!-- 全局错误提示 -->
    <el-alert
      v-if="$store.state.error"
      :title="$store.state.error"
      type="error"
      :closable="true"
      show-icon
      class="global-error"
    ></el-alert>

    <!-- 路由视图 -->
    <div class="main-content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import Navigation from './components/Navigation.vue'
import { Loading } from '@element-plus/icons-vue'
</script>

<style>
/* 全局样式 */
#app {
  font-family: 'PingFang SC', 'Helvetica Neue', Helvetica, 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 0 20px;
}

/* 全局错误提示 */
.global-error {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  min-width: 300px;
}

/* 全局加载状态 */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-card {
  padding: 20px 40px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.loading-spinner .el-icon {
  font-size: 24px;
}

/* 全局过渡效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
