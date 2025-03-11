<template>
  <div class="home">
    <el-container>
      <el-main>
        <div class="hero-section">
          <h1 class="main-title">欢迎使用 AI-EdVision</h1>
          <p class="subtitle">智能教育视频分析系统 - 让学习更高效，更智能</p>
          <el-button type="primary" size="large" @click="navigateToUpload">开始上传视频</el-button>
        </div>

        <el-divider content-position="center">核心功能</el-divider>

        <div class="features-section">
          <el-row :gutter="30">
            <el-col :span="8">
              <el-card class="feature-card">
                <template #header>
                  <div class="feature-header">
                    <el-icon class="feature-icon"><VideoCamera /></el-icon>
                    <h3>智能视频处理</h3>
                  </div>
                </template>
                <div class="feature-content">
                  <p>上传您的教育视频，系统将自动处理并提取关键信息，生成字幕和内容摘要。</p>
                  <ul>
                    <li>自动生成精准字幕</li>
                    <li>支持多种字幕格式下载</li>
                    <li>视频内容智能分析</li>
                  </ul>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="feature-card">
                <template #header>
                  <div class="feature-header">
                    <el-icon class="feature-icon"><ChatLineSquare /></el-icon>
                    <h3>AI 智能问答</h3>
                  </div>
                </template>
                <div class="feature-content">
                  <p>基于视频内容的智能问答系统，帮助您深入理解视频中的知识点。</p>
                  <ul>
                    <li>基于视频内容的精准回答</li>
                    <li>自由问答模式</li>
                    <li>智能上下文理解</li>
                  </ul>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="feature-card">
                <template #header>
                  <div class="feature-header">
                    <el-icon class="feature-icon"><Connection /></el-icon>
                    <h3>学习路径与笔记系统</h3>
                  </div>
                </template>
                <div class="feature-content">
                  <p>构建个性化学习路径，记录学习笔记，提升学习效率。</p>
                  <ul>
                    <li>个性化学习计划</li>
                    <li>智能笔记管理</li>
                    <li>学习进度追踪</li>
                  </ul>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-divider content-position="center">使用指南</el-divider>

        <div class="guide-section">
          <el-steps :active="1" finish-status="success" simple>
            <el-step title="上传视频" description="在&quot;视频管理&quot;中上传您的教育视频"></el-step>
            <el-step title="等待处理" description="系统将自动处理视频并生成字幕"></el-step>
            <el-step title="观看与互动" description="观看视频并使用AI问答功能深入学习"></el-step>
          </el-steps>

          <div class="guide-details">
            <h3>快速入门</h3>
            <ol>
              <li>点击顶部导航栏的<strong>&quot;视频管理&quot;</strong>进入视频上传页面</li>
              <li>选择或拖拽视频文件到上传区域</li>
              <li>等待视频处理完成（处理时间取决于视频长度）</li>
              <li>进入视频播放页面，享受智能字幕和AI问答功能</li>
              <li>使用<strong>&quot;学习路径&quot;</strong>和<strong>&quot;笔记系统&quot;</strong>功能记录和规划您的学习</li>
            </ol>
          </div>
        </div>

        <el-divider content-position="center">开始您的智能学习之旅</el-divider>

        <div class="cta-section">
          <el-card class="cta-card">
            <div class="cta-content">
              <h2>立即体验 AI-EdVision</h2>
              <p>上传您的第一个视频，探索智能教育的新可能</p>
              <el-button type="primary" size="large" @click="navigateToUpload">开始使用</el-button>
            </div>
          </el-card>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { VideoCamera, ChatLineSquare, Connection } from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    VideoCamera,
    ChatLineSquare,
    Connection
  },
  setup() {
    const router = useRouter()

    const navigateToUpload = () => {
      router.push('/video/upload')
    }

    return {
      navigateToUpload
    }
  }
}
</script>

<style scoped>
.home {
  height: 100%;
}

.el-container {
  height: 100%;
}

.el-main {
  padding: 20px;
  background-color: #f5f7fa;
}

.hero-section {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #1c92d2, #f2fcfe);
  border-radius: 8px;
  color: #fff;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.main-title {
  font-size: 2.5rem;
  margin-bottom: 15px;
  font-weight: 600;
}

.subtitle {
  font-size: 1.2rem;
  margin-bottom: 30px;
  opacity: 0.9;
}

.features-section {
  margin: 30px 0;
}

.feature-card {
  height: 100%;
  transition: transform 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.feature-header {
  display: flex;
  align-items: center;
}

.feature-icon {
  font-size: 24px;
  margin-right: 10px;
  color: #409EFF;
}

.feature-content {
  color: #606266;
}

.feature-content ul {
  padding-left: 20px;
  margin-top: 10px;
}

.feature-content li {
  margin-bottom: 5px;
}

.guide-section {
  margin: 30px 0;
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.guide-details {
  margin-top: 30px;
  padding: 0 20px;
}

.guide-details ol {
  padding-left: 20px;
}

.guide-details li {
  margin-bottom: 10px;
  line-height: 1.6;
}

.cta-section {
  margin: 30px 0;
}

.cta-card {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}

.cta-content {
  text-align: center;
  padding: 30px;
}

.cta-content h2 {
  margin-bottom: 15px;
}

.cta-content p {
  margin-bottom: 25px;
  opacity: 0.9;
}

.el-divider {
  margin: 40px 0;
}

.el-divider__text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #409EFF;
}
</style>
