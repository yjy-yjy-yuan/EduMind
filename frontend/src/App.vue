<template>
  <div id="app">
    <!-- 导航菜单 -->
    <Navigation />

    <!-- 全局加载状态 -->
    <el-loading
      v-if="$store.state.loading"
      :fullscreen="true"
      text="加载中..."
    ></el-loading>

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
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.main-content {
  padding: 0 20px;
}

.global-error {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
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
