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
}
</style>
