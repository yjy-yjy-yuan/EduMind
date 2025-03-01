<template>
  <div class="home">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="200px">
        <el-menu
          :router="true"
          class="el-menu-vertical"
        >
          <el-menu-item index="/video/upload">
            <el-icon><Upload /></el-icon>
            <span>视频上传</span>
          </el-menu-item>
          
          <el-menu-item index="/video/list">
            <el-icon><VideoCamera /></el-icon>
            <span>我的视频</span>
          </el-menu-item>
          
          <el-menu-item index="/learning-path">
            <el-icon><Connection /></el-icon>
            <span>学习路径</span>
            <el-tag size="small" type="warning">开发中</el-tag>
          </el-menu-item>
          
          <el-menu-item index="/notes">
            <el-icon><Notebook /></el-icon>
            <span>笔记系统</span>
            <el-tag size="small" type="warning">开发中</el-tag>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { Upload, VideoCamera, Connection, Notebook } from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    Upload,
    VideoCamera,
    Connection,
    Notebook
  }
}
</script>

<style scoped>
.home {
  height: 100vh;
}

.el-container {
  height: 100%;
}

.el-aside {
  background-color: #fff;
  border-right: 1px solid #e6e6e6;
}

.el-menu-vertical {
  height: 100%;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}
</style>
