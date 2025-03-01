<template>
  <div class="notes">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <h2>笔记系统</h2>
        </div>
      </template>
      <div class="content">
        <el-empty description="笔记系统功能开发中...">
          <template #image>
            <el-icon :size="60"><Edit /></el-icon>
          </template>
          <template #description>
            <p>智能笔记系统正在开发中</p>
            <p>即将推出的功能：</p>
            <ul>
              <li>与视频时间轴关联的笔记</li>
              <li>AI 辅助笔记整理</li>
              <li>知识点提取与总结</li>
              <li>笔记分享与协作</li>
            </ul>
          </template>
        </el-empty>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { Edit } from '@element-plus/icons-vue'
</script>

<style scoped>
.notes {
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
