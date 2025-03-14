<template>
  <el-menu
    :default-active="activeIndex"
    class="nav-menu"
    mode="horizontal"
    router
    @select="handleSelect"
  >
    <el-menu-item index="/">首页</el-menu-item>
    <el-menu-item index="/video/upload">视频管理</el-menu-item>
    <el-menu-item index="/notes">笔记系统</el-menu-item>
    <el-menu-item index="/learning-path">学习路径</el-menu-item>
  </el-menu>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = ref(route.path)

// 监听路由变化，更新激活的菜单项
watch(() => route.path, (newPath) => {
  activeIndex.value = newPath
})

const handleSelect = (key) => {
  activeIndex.value = key
}
</script>

<style scoped>
.nav-menu {
  padding: 0 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: flex-start; /* 改回左对齐 */
  background: linear-gradient(135deg, #1e3c72, #2a5298); /* 添加渐变背景，与整体风格一致 */
  border-radius: 0 0 8px 8px; /* 添加圆角 */
}

/* 为首页菜单项添加左边距，使其与侧边栏不重叠 */
.nav-menu .el-menu-item:first-child {
  margin-left: 80px; /* 增加左边距，避免与侧边栏按钮重叠 */
}

/* 为所有菜单项增加间距和样式 */
.nav-menu .el-menu-item {
  padding: 0 25px; /* 增加菜单项之间的间距 */
  height: 60px; /* 增加高度 */
  line-height: 60px; /* 行高与高度一致 */
  color: #fff !important; /* 文字颜色为白色 */
  font-weight: 500; /* 字体加粗 */
  transition: all 0.3s ease; /* 添加过渡效果 */
  border-bottom: none !important; /* 移除底部边框 */
}

/* 菜单项悬停和激活状态 */
.nav-menu .el-menu-item:hover, 
.nav-menu .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.1) !important; /* 半透明白色背景 */
  color: #fff !important; /* 保持文字为白色 */
  border-bottom: 3px solid #409EFF !important; /* 添加蓝色底部边框 */
}

/* 覆盖Element Plus默认样式 */
:deep(.el-menu--horizontal) {
  border-bottom: none;
  background: transparent;
}
</style>
