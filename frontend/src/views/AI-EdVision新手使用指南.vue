<template>
  <div class="user-guide">
    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-container">
        <div class="hero-content-wrapper">
          <div class="hero-text full-width">
            <h1 class="main-title">AI-EdVision<br><span class="highlight">新手使用指南</span></h1>
            <p class="subtitle">通过本指南快速掌握 AI-EdVision 的核心功能，让您的学习体验更高效、更智能、更个性化</p>
            <el-button type="primary" size="large" class="hero-button" @click="navigateToUpload">
              开始上传视频
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 使用流程 -->
    <section class="workflow-section">
      <div class="section-header">
        <h2 class="section-title">使用流程</h2>
        <p class="section-subtitle">按照以下步骤，轻松开始使用 AI-EdVision</p>
      </div>
      <div class="workflow-container">
        <div class="workflow-diagram">
          <img src="../assets/workflow.svg" alt="AI-EdVision使用流程图" class="workflow-image" />
          <div class="workflow-description">
            <div class="workflow-step-card">
              <div class="step-number">1</div>
              <div class="step-content">
                <h3 class="step-title">登录/注册</h3>
                <p class="step-desc">创建账号或登录系统，开始您的学习之旅</p>
              </div>
            </div>
            
            <div class="workflow-step-card">
              <div class="step-number">2</div>
              <div class="step-content">
                <h3 class="step-title">上传视频并分析</h3>
                <p class="step-desc">上传教学视频，系统自动分析内容</p>
              </div>
            </div>
            
            <div class="workflow-step-card">
              <div class="step-number">3</div>
              <div class="step-content">
                <h3 class="step-title">视频学习功能</h3>
                <p class="step-desc">系统提供多种学习辅助功能</p>
                
                <div class="substeps-container">
                  <div class="substep-item">
                    <div class="substep-dot"></div>
                    <div class="substep-content">
                      <h4 class="substep-title">视频播放</h4>
                      <p class="substep-desc">观看处理完成的视频</p>
                    </div>
                  </div>
                  
                  <div class="substep-item">
                    <div class="substep-dot"></div>
                    <div class="substep-content">
                      <h4 class="substep-title">智能问答与字幕查看</h4>
                      <p class="substep-desc">使用AI助手解答疑问</p>
                    </div>
                  </div>
                  
                  <div class="substep-item">
                    <div class="substep-dot"></div>
                    <div class="substep-content">
                      <h4 class="substep-title">笔记系统辅助学习</h4>
                      <p class="substep-desc">创建和管理学习笔记</p>
                    </div>
                  </div>
                  
                  <div class="substep-item">
                    <div class="substep-dot"></div>
                    <div class="substep-content">
                      <h4 class="substep-title">知识点总览与扩展</h4>
                      <p class="substep-desc">查看知识点并拓展学习</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 详细教程 -->
    <section class="tutorials-section">
      <div class="section-header">
        <h2 class="section-title">详细教程</h2>
        <p class="section-subtitle">跟随以下步骤，轻松掌握 AI-EdVision 的全部功能</p>
      </div>

      <div class="tutorials-container">
        <!-- 1. 登录/注册教程 -->
        <div class="tutorial-card">
          <div class="tutorial-header">
            <div class="tutorial-icon-wrapper">
              <i class="el-icon-user"></i>
            </div>
            <div class="tutorial-title-container">
              <div class="tutorial-order">01</div>
              <h3 class="tutorial-title">登录/注册</h3>
            </div>
          </div>
          <div class="tutorial-content full-width">
            <div class="tutorial-steps">
              <div class="step">
                <span class="step-number">1</span>
                <p>访问 AI-EdVision 首页，点击右上角的<strong>「登录/注册」</strong>按钮</p>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <p>新用户选择<strong>「注册」</strong>，填写用户名、邮箱和密码</p>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <p>老用户直接<strong>「登录」</strong>，输入用户名和密码</p>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <p>登录后即可使用所有功能，包括视频上传、分析和笔记管理</p>
              </div>
              <div class="tip">
                <i class="el-icon-info-filled tip-icon"></i>
                <p>首次注册用户将获得更多免费分析时长</p>
              </div>
            </div>
            <div class="tutorial-action">
              <el-button type="primary" @click="navigateToLogin">前往登录/注册</el-button>
            </div>
          </div>
        </div>

        <!-- 2. 视频上传教程 -->
        <div class="tutorial-card">
          <div class="tutorial-header">
            <div class="tutorial-icon-wrapper">
              <i class="el-icon-upload"></i>
            </div>
            <div class="tutorial-title-container">
              <div class="tutorial-order">02</div>
              <h3 class="tutorial-title">视频上传与分析</h3>
            </div>
          </div>
          <div class="tutorial-content full-width">
            <div class="tutorial-steps">
              <div class="step">
                <span class="step-number">1</span>
                <p>点击导航栏中的<strong>「视频上传」</strong>进入上传页面</p>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <p>选择<strong>本地上传</strong>或<strong>链接导入</strong>方式</p>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <p>上传完成后，系统自动开始分析视频内容</p>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <p>分析完成后，视频状态变为<strong>「已完成」</strong>，即可观看</p>
              </div>
              <div class="tip">
                <i class="el-icon-info-filled tip-icon"></i>
                <p>支持的格式：MP4、AVI、MOV等主流视频格式，最大支持1GB</p>
              </div>
            </div>
            <div class="tutorial-action">
              <el-button type="primary" @click="navigateToUpload">前往视频上传</el-button>
            </div>
          </div>
        </div>

        <!-- 3. 视频播放教程 -->
        <div class="tutorial-card">
          <div class="tutorial-header">
            <div class="tutorial-icon-wrapper">
              <i class="el-icon-video-play"></i>
            </div>
            <div class="tutorial-title-container">
              <div class="tutorial-order">03</div>
              <h3 class="tutorial-title">视频播放</h3>
            </div>
          </div>
          <div class="tutorial-content full-width">
            <div class="tutorial-steps">
              <div class="step">
                <span class="step-number">1</span>
                <p>在<strong>「已上传视频」</strong>列表中点击视频缩略图进入播放页面</p>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <p>使用播放器控制栏调整播放进度、音量和播放速度</p>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <p>点击<strong>全屏按钮</strong>可进入全屏模式观看</p>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <p>视频播放时自动显示智能生成的字幕</p>
              </div>
              <div class="tip">
                <i class="el-icon-info-filled tip-icon"></i>
                <p>支持快捷键控制：空格（播放/暂停）、方向键（快进/快退）</p>
              </div>
            </div>
            <div class="tutorial-action">
              <el-button type="primary" @click="navigateToVideos">浏览视频列表</el-button>
            </div>
          </div>
        </div>

        <!-- 4. 智能问答教程 -->
        <div class="tutorial-card">
          <div class="tutorial-header">
            <div class="tutorial-icon-wrapper">
              <i class="el-icon-chat-dot-round"></i>
            </div>
            <div class="tutorial-title-container">
              <div class="tutorial-order">04</div>
              <h3 class="tutorial-title">智能问答与字幕查看</h3>
            </div>
          </div>
          <div class="tutorial-content full-width">
            <div class="tutorial-steps">
              <div class="step">
                <span class="step-number">1</span>
                <p>在视频播放页面，点击右侧面板的<strong>「字幕」</strong>标签查看完整字幕</p>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <p>点击任意字幕行可跳转至视频对应时间点</p>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <p>点击右下角的<strong>「智能问答」</strong>按钮打开问答面板</p>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <p>输入问题并发送，AI将基于视频内容给出回答</p>
              </div>
              <div class="tip">
                <i class="el-icon-info-filled tip-icon"></i>
                <p>提问越具体，回答质量越高。可以连续提问深入探讨</p>
              </div>
            </div>
            <div class="tutorial-action">
              <el-button type="primary" @click="navigateToVideos">体验智能问答</el-button>
            </div>
          </div>
        </div>

        <!-- 5. 笔记管理教程 -->
        <div class="tutorial-card">
          <div class="tutorial-header">
            <div class="tutorial-icon-wrapper">
              <i class="el-icon-notebook-1"></i>
            </div>
            <div class="tutorial-title-container">
              <div class="tutorial-order">05</div>
              <h3 class="tutorial-title">笔记系统辅助学习</h3>
            </div>
          </div>
          <div class="tutorial-content full-width">
            <div class="tutorial-steps">
              <div class="step">
                <span class="step-number">1</span>
                <p>在视频播放页面，点击右侧面板中的<strong>「添加笔记」</strong>按钮</p>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <p>输入笔记内容，系统会自动关联当前视频时间点</p>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <p>点击导航栏中的<strong>「笔记管理」</strong>查看所有笔记</p>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <p>在笔记管理页面可进行编辑、删除、导出等操作</p>
              </div>
              <div class="tip">
                <i class="el-icon-info-filled tip-icon"></i>
                <p>系统会智能推荐相似笔记，帮助您建立知识连接</p>
              </div>
            </div>
            <div class="tutorial-action">
              <el-button type="primary" @click="navigateToNotes">前往笔记管理</el-button>
            </div>
          </div>
        </div>

        <!-- 6. 知识点总览教程 -->
        <div class="tutorial-card">
          <div class="tutorial-header">
            <div class="tutorial-icon-wrapper">
              <i class="el-icon-data-line"></i>
            </div>
            <div class="tutorial-title-container">
              <div class="tutorial-order">06</div>
              <h3 class="tutorial-title">知识点总览与扩展</h3>
            </div>
          </div>
          <div class="tutorial-content full-width">
            <div class="tutorial-steps">
              <div class="step">
                <span class="step-number">1</span>
                <p>在视频播放页面，点击右侧面板中的<strong>「知识点」</strong>标签</p>
              </div>
              <div class="step">
                <span class="step-number">2</span>
                <p>浏览系统自动提取的视频关键知识点</p>
              </div>
              <div class="step">
                <span class="step-number">3</span>
                <p>点击任意知识点可跳转至相关视频片段</p>
              </div>
              <div class="step">
                <span class="step-number">4</span>
                <p>使用<strong>「知识图谱」</strong>功能查看知识点之间的关联</p>
              </div>
              <div class="tip">
                <i class="el-icon-info-filled tip-icon"></i>
                <p>知识点支持导出，方便复习和分享</p>
              </div>
            </div>
            <div class="tutorial-action">
              <el-button type="primary" @click="navigateToVideos">探索知识点</el-button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 常见问题 -->
    <section class="faq-section">
      <div class="section-header">
        <h2 class="section-title">常见问题</h2>
        <p class="section-subtitle">解答您在使用过程中可能遇到的问题</p>
      </div>
      <div class="faq-container">
        <div class="faq-item">
          <div class="faq-question">
            <i class="fas fa-question-circle question-icon"></i>
            <h3>如何上传视频？</h3>
          </div>
          <div class="faq-answer">
            <p>点击导航栏中的"视频上传"，或在个人中心页面点击"上传视频"按钮，选择本地视频文件或输入视频链接即可开始上传。</p>
          </div>
        </div>
        
        <div class="faq-item">
          <div class="faq-question">
            <i class="fas fa-question-circle question-icon"></i>
            <h3>视频处理需要多长时间？</h3>
          </div>
          <div class="faq-answer">
            <p>视频处理时间取决于视频长度和服务器负载。一般情况下，10分钟的视频大约需要2-5分钟完成处理。您可以在"已上传视频"页面查看处理进度。</p>
          </div>
        </div>
        
        <div class="faq-item">
          <div class="faq-question">
            <i class="fas fa-question-circle question-icon"></i>
            <h3>如何使用AI问答功能？</h3>
          </div>
          <div class="faq-answer">
            <p>在视频播放页面右侧，您可以看到AI问答区域。直接输入您的问题，AI将基于视频内容为您提供答案。您还可以切换深度思考模式，获取更详细的解答。</p>
          </div>
        </div>
        
        <div class="faq-item">
          <div class="faq-question">
            <i class="fas fa-question-circle question-icon"></i>
            <h3>如何导出笔记？</h3>
          </div>
          <div class="faq-answer">
            <p>在笔记页面，选择您想要导出的笔记，点击"导出"按钮，选择导出格式（PDF、Word或Markdown），系统将自动生成文件并下载到您的设备上。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA 区域 -->
    <section class="cta-section">
      <div class="cta-card">
        <h2 class="cta-title">准备好开始智能学习之旅了吗？</h2>
        <p class="cta-description">立即体验 AI-EdVision，让 AI 技术为您的学习提供全方位支持</p>
        <el-button type="primary" size="large" class="cta-button" @click="navigateToUpload">
          免费开始使用
        </el-button>
      </div>
    </section>
    
    <!-- 页脚 -->
    <footer class="footer-section">
      <div class="container">
        <div class="footer-grid">
          <div class="footer-info">
            <div class="footer-logo">
              <i class="fas fa-brain"></i>
              <h3>AI-EdVision</h3>
            </div>
            <p class="footer-description">
              智能教育视频分析系统，让学习更高效、更智能、更个性化
            </p>
          </div>
          
          <div class="footer-links">
            <h4 class="footer-title">功能</h4>
            <ul>
              <li><a href="#">视频上传</a></li>
              <li><a href="#">智能字幕</a></li>
              <li><a href="#">智能问答</a></li>
              <li><a href="#">笔记管理</a></li>
              <li><a href="#">知识点总览与扩展</a></li>
            </ul>
          </div>
          
          <div class="footer-links">
            <h4 class="footer-title">资源</h4>
            <ul>
              <li><a href="#">使用指南</a></li>
              <li><a href="#">API 文档</a></li>
              <li><a href="#">常见问题</a></li>
              <li><a href="#">博客</a></li>
            </ul>
          </div>
          
          <div class="footer-contact">
            <h4 class="footer-title">联系我们</h4>
            <ul>
              <li><i class="fas fa-envelope"></i> contact@ai-edvision.com</li>
              <li><i class="fas fa-phone"></i> +86 123 4567 8910</li>
              <li><i class="fas fa-map-marker-alt"></i> 郑州市经济技术开发区</li>
            </ul>
            <div class="footer-social">
              <a href="#"><i class="fab fa-weixin"></i></a>
              <a href="#"><i class="fab fa-weibo"></i></a>
              <a href="#"><i class="fab fa-github"></i></a>
              <a href="#"><i class="fab fa-linkedin"></i></a>
            </div>
          </div>
        </div>
        
        <div class="footer-bottom">
          <p>&copy; 2025 AI-EdVision. 保留所有权利。</p>
        </div>
      </div>
    </footer>
    
    <!-- Toast 通知组件 -->
    <div class="toast-notification" :class="{ show: showToast }">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import authStore from '../store/auth'

export default {
  name: 'AIEdVisionUserGuide',
  setup() {
    const router = useRouter()
    const isLoading = ref(false)
    const showToast = ref(false)
    const toastMessage = ref('')
    
    // 获取用户认证状态
    const authState = computed(() => authStore.getState())
    
    // 导航到上传页面
    const navigateToUpload = () => {
      isLoading.value = true
      showToast.value = true
      toastMessage.value = '正在准备上传页面...'
      
      // 模拟加载过程
      setTimeout(() => {
        isLoading.value = false
        router.push('/video/upload')
      }, 800)
      
      // 2秒后隐藏提示
      setTimeout(() => {
        showToast.value = false
      }, 2000)
    }
    
    // 导航到登录页面或个人中心
    const navigateToLogin = () => {
      isLoading.value = true
      
      // 根据登录状态决定跳转目标
      if (authState.value.isAuthenticated) {
        showToast.value = true
        toastMessage.value = '正在前往个人中心...'
        
        // 模拟加载过程
        setTimeout(() => {
          isLoading.value = false
          router.push('/profile')
        }, 800)
      } else {
        showToast.value = true
        toastMessage.value = '正在前往登录页面...'
        
        // 模拟加载过程
        setTimeout(() => {
          isLoading.value = false
          router.push('/login')
        }, 800)
      }
      
      // 2秒后隐藏提示
      setTimeout(() => {
        showToast.value = false
      }, 2000)
    }
    
    return {
      navigateToUpload,
      navigateToLogin,
      isLoading,
      showToast,
      toastMessage
    }
  }
}
</script>

<style scoped>
/* 基本变量定义 */
:root {
  --primary-color: #4F46E5;
  --secondary-color: #8B5CF6;
  --accent-color: #EC4899;
  --text-primary: #1F2937;
  --text-secondary: #4B5563;
  --bg-light: #F9FAFB;
  --card-bg: #FFFFFF;
  --border-radius: 8px;
  --transition-speed: 0.3s;
}

/* 英雄区域样式 */
.hero-section {
  position: relative;
  padding: 80px 20px;
  background-image: none;
  background-size: cover;
  background-position: center;
  color: #fff;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.hero-container {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-text {
  text-align: center;
  margin-bottom: 2rem;
}

.hero-text.full-width {
  padding-right: 0;
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
}

/* 通用部分样式 */
section {
  padding: 2.5rem 0;
}

.section-header {
  text-align: center;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 1rem;
  position: relative;
  display: inline-block;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 3px;
  background-color: var(--primary-color);
  transition: width 0.3s ease;
}

.section-header:hover .section-title::after {
  width: 120px;
}

.section-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  max-width: 700px;
  margin: 0 auto;
  line-height: 1.6;
}

/* 工作流程区域样式 */
.workflow-section {
  background-color: var(--bg-light);
  padding: 2.5rem 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.workflow-container {
  margin-top: 2rem;
  overflow-x: auto;
  padding-bottom: 1rem;
}

.workflow-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.workflow-image {
  max-width: 100%;
  height: auto;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  transition: transform 0.3s ease;
}

.workflow-image:hover {
  transform: scale(1.02);
}

.workflow-description {
  background-color: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 800px;
}

.workflow-step-card {
  display: flex;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.workflow-step-card:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-color, #667eea), var(--secondary-color, #764ba2));
  color: white;
  font-weight: bold;
  border-radius: 50%;
  margin-right: 1rem;
  flex-shrink: 0;
  font-size: 1.2rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary, #1F2937);
  margin: 0 0 0.5rem 0;
}

.step-desc {
  font-size: 1rem;
  color: var(--text-secondary, #4B5563);
  margin: 0;
  line-height: 1.5;
}

.substeps-container {
  margin-top: 1rem;
  padding-left: 1rem;
  border-left: 2px solid #f0f0f0;
}

.substep-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.substep-item:last-child {
  margin-bottom: 0;
}

.substep-dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, var(--primary-color, #667eea), var(--secondary-color, #764ba2));
  border-radius: 50%;
  margin-right: 1rem;
  margin-top: 0.4rem;
  flex-shrink: 0;
}

.substep-content {
  flex: 1;
}

.substep-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-primary, #1F2937);
  margin: 0 0 0.25rem 0;
}

.substep-desc {
  font-size: 0.95rem;
  color: var(--text-secondary, #4B5563);
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .workflow-description {
    padding: 1.5rem;
  }
  
  .step-number {
    width: 32px;
    height: 32px;
    font-size: 1rem;
  }
  
  .step-title {
    font-size: 1.1rem;
  }
  
  .step-desc {
    font-size: 0.95rem;
  }
  
  .substep-title {
    font-size: 1rem;
  }
  
  .substep-desc {
    font-size: 0.9rem;
  }
}

/* 详细教程区域样式 */
.tutorials-section {
  padding: 5rem 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.tutorials-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  margin-top: 3rem;
}

.tutorial-card {
  background-color: var(--card-bg, #FFFFFF);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
  border-top: 5px solid transparent;
  border-image: linear-gradient(to right, #667eea, #764ba2);
  border-image-slice: 1;
}

.tutorial-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
}

.tutorial-header {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  background: linear-gradient(to right, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.tutorial-icon-wrapper {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 1rem;
  flex-shrink: 0;
}

.tutorial-icon-wrapper i {
  color: white;
  font-size: 1.5rem;
}

.tutorial-title-container {
  display: flex;
  align-items: center;
}

.tutorial-order {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  margin-right: 0.75rem;
  opacity: 0.8;
}

.tutorial-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary, #1F2937);
  margin: 0;
}

.tutorial-content {
  padding: 1.5rem;
}

.tutorial-content.full-width {
  padding: 1.5rem;
  width: 100%;
}

.tutorial-steps {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.step {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.step-number {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.step p {
  margin: 0;
  flex: 1;
  line-height: 1.5;
  color: var(--text-secondary, #4B5563);
}

.tip {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-top: 1rem;
  padding: 1rem;
  background-color: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
}

.tip-icon {
  color: #667eea;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.tip p {
  margin: 0;
  font-size: 0.9rem;
  font-style: italic;
  color: var(--text-secondary, #4B5563);
}

.tutorial-action {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
}

.tutorial-action .el-button {
  padding: 0.6rem 1.5rem;
  font-weight: 500;
}

@media (min-width: 768px) {
  .tutorials-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1200px) {
  .tutorials-section {
    padding: 5rem 2rem;
  }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-title {
    font-size: 2.5rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
}

@media (max-width: 992px) {
  .hero-section {
    padding: 80px 20px;
  }
  
  .main-title {
    font-size: 2.25rem;
  }
  
  .subtitle {
    font-size: 1.1rem;
  }
  
  .section-title {
    font-size: 1.75rem;
  }
  
  .feature-title {
    font-size: 1.25rem;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 60px 15px;
  }
  
  .main-title {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  section {
    padding: 3rem 0;
  }
  
  .section-title {
    font-size: 1.5rem;
  }
}

@media (max-width: 576px) {
  .hero-section {
    padding: 50px 15px;
  }
  
  .main-title {
    font-size: 1.75rem;
  }
  
  .subtitle {
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
  }
  
  .hero-button {
    padding: 0.5rem 1.5rem !important;
    font-size: 1rem !important;
  }
  
  .section-title {
    font-size: 1.35rem;
  }
  
  .section-subtitle {
    font-size: 0.9rem;
  }
  
  .feature-card {
    padding: 1.5rem;
  }
  
  .feature-icon-wrapper {
    width: 60px;
    height: 60px;
  }
  
  .feature-title {
    font-size: 1.15rem;
  }
}

/* 常见问题区域样式 */
.faq-section {
  background-color: var(--bg-light);
  padding: 3rem 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.faq-container {
  margin-top: 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 1.5rem;
}

.faq-item {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.faq-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.faq-question {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.question-icon {
  color: var(--primary-color, #667eea);
  font-size: 1.5rem;
  margin-right: 1rem;
}

.faq-question h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary, #1F2937);
  margin: 0;
}

.faq-answer p {
  color: var(--text-secondary, #4B5563);
  line-height: 1.6;
  margin: 0;
}

/* CTA 区域样式 */
.cta-section {
  padding: 3rem 1.5rem;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
  max-width: 1200px;
  margin: 0 auto;
}

.cta-card {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  color: white;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.cta-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.cta-description {
  font-size: 1.1rem;
  max-width: 600px;
  margin: 0 auto 2rem;
  opacity: 0.9;
}

.cta-button {
  font-size: 1.1rem;
  padding: 0.75rem 2rem;
  font-weight: 600;
  border-radius: 8px;
  background-color: white;
  color: var(--primary-color, #667eea);
  border: none;
  transition: all 0.3s ease;
}

.cta-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

/* 页脚样式 */
.footer-section {
  background-color: #1F2937;
  color: white;
  padding: 4rem 1.5rem 2rem;
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  gap: 2rem;
  margin-bottom: 3rem;
}

.footer-logo {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.footer-logo i {
  font-size: 1.75rem;
  margin-right: 0.75rem;
  color: var(--primary-color, #667eea);
}

.footer-logo h3 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.footer-description {
  color: #D1D5DB;
  line-height: 1.6;
  margin-top: 1rem;
}

.footer-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  position: relative;
}

.footer-title::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -0.5rem;
  width: 40px;
  height: 3px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 3px;
}

.footer-links ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-links li {
  margin-bottom: 0.75rem;
}

.footer-links a {
  color: #D1D5DB;
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: white;
}

.footer-contact ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-contact li {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  color: #D1D5DB;
}

.footer-contact li i {
  margin-right: 0.75rem;
  color: var(--primary-color, #667eea);
}

.footer-social {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.footer-social a {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: white;
  transition: all 0.3s ease;
}

.footer-social a:hover {
  background-color: var(--primary-color, #667eea);
  transform: translateY(-3px);
}

.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 1.5rem;
  text-align: center;
  color: #9CA3AF;
}

/* Toast 通知组件样式 */
.toast-notification {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background-color: #4F46E5;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transform: translateY(100px);
  opacity: 0;
  transition: all 0.3s ease;
  z-index: 1000;
}

.toast-notification.show {
  transform: translateY(0);
  opacity: 1;
}

@media (max-width: 1024px) {
  .faq-container {
    grid-template-columns: 1fr;
  }
  
  .footer-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .cta-title {
    font-size: 1.75rem;
  }
}

@media (max-width: 768px) {
  .footer-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .cta-card {
    padding: 2rem 1.5rem;
  }
  
  .cta-title {
    font-size: 1.5rem;
  }
  
  .cta-description {
    font-size: 1rem;
  }
}
</style>
