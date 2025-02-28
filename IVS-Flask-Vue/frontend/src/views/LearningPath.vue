<template>
  <div class="learning-path">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <h2>学习路径规划</h2>
        </div>
      </template>
      <div class="content">
        <el-empty description="知识图谱功能开发中...">
          <template #image>
            <el-icon :size="60"><Connection /></el-icon>
          </template>
          <template #description>
            <p>基于 Neo4j 的知识图谱功能正在开发中</p>
            <p>该功能将帮助您：</p>
            <ul>
              <li>根据视频内容构建知识点关联</li>
              <li>生成个性化学习路径</li>
              <li>推荐相关学习资源</li>
            </ul>
          </template>
        </el-empty>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { Connection } from '@element-plus/icons-vue'
</script>

<style scoped>
.learning-path {
  padding: 20px;
}

.box-card {
  width: 100%;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content {
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}

ul {
  text-align: left;
  margin-top: 10px;
}

li {
  margin: 5px 0;
  color: #666;
}
</style>
