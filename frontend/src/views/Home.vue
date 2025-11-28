<template>
  <!-- 英雄区域 -->
  <section class="hero-section">
    <div class="hero-overlay"></div>
    <div class="hero-container">
      <div class="hero-content-wrapper">
        <div class="hero-text">
          <h1 class="main-title"><span class="highlight">视频智能伴学系统</span></h1>
          <p class="subtitle">通过 AI 技术赋能教育视频，提供智能字幕、知识问答、笔记管理等功能，让学习更高效、更智能、更个性化</p>
          <el-button type="primary" size="large" class="hero-button" @click="navigateToUpload" :loading="isLoading">
            <span v-if="!isLoading">开始上传视频</span>
            <span v-else>正在准备...</span>
          </el-button>
        </div>
        <div class="hero-image-container">
          <img :src="heroImage" alt="AI 教育视频分析系统" class="hero-image" />
        </div>
      </div>
    </div>
  </section>

  <!-- 核心功能区域 -->
  <section class="features-section">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">强大功能，智能学习</h2>
        <p class="section-subtitle">视频智能伴学系统集成多种智能功能，为您的学习体验带来革命性变化</p>
      </div>

      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon-wrapper">
            <i class="fas fa-cloud-upload-alt feature-icon"></i>
          </div>
          <h3 class="feature-title">智能视频上传</h3>
          <p class="feature-description">
            支持本地视频上传和哔哩哔哩/YouTube 链接导入，轻松获取学习资源
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon-wrapper">
            <i class="fas fa-closed-captioning feature-icon"></i>
          </div>
          <h3 class="feature-title">智能字幕生成</h3>
          <p class="feature-description">
            使用 Whisper 语音识别模型，实时生成精准字幕，支持分段和语义合并显示
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon-wrapper">
            <i class="fas fa-robot feature-icon"></i>
          </div>
          <h3 class="feature-title">智能问答系统</h3>
          <p class="feature-description">
            基于 RAG 系统的智能问答，支持深度思考模式，在线/离线模式任意切换
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon-wrapper">
            <i class="fas fa-sticky-note feature-icon"></i>
          </div>
          <h3 class="feature-title">智能笔记管理</h3>
          <p class="feature-description">
            记录、导出、批量管理笔记，基于相似性推荐，帮助掌握核心知识点
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- 工作流程区域 -->
  <section class="workflow-section">
    <div class="section-header">
      <h2 class="section-title">简单高效的学习流程</h2>
      <p class="section-subtitle">只需几个简单步骤，即可开启 AI 辅助学习之旅</p>
    </div>

    <div class="workflow-container">
      <el-row :gutter="30">
        <el-col :xs="24" :sm="24" :md="8" v-for="(workflow, index) in workflows" :key="index">
          <div class="workflow-card">
            <div class="step-number">{{ workflow.step }}</div>
            <img :src="workflow.image" alt="workflow image" class="workflow-image">
            <h3 class="workflow-title">{{ workflow.title }}</h3>
            <p class="workflow-description">{{ workflow.description }}</p>
          </div>
        </el-col>
      </el-row>
    </div>
  </section>

  <!-- 核心优势区域 -->
  <section class="advantages-section">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">核心优势</h2>
        <p class="section-subtitle">我们的系统具备多项独特优势，为您的学习提供全方位支持</p>
      </div>

      <div class="advantages-grid">
        <div class="advantage-item">
          <div class="advantage-icon-wrapper">
            <i class="fas fa-brain advantage-icon"></i>
          </div>
          <div class="advantage-content">
            <h3 class="advantage-title">AI 驱动的智能分析</h3>
            <p class="advantage-description">
              采用先进的 AI 技术，对视频内容进行深度分析，提取关键知识点，生成精准字幕
            </p>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon-wrapper">
            <i class="fas fa-wifi advantage-icon"></i>
          </div>
          <div class="advantage-content">
            <h3 class="advantage-title">在线/离线双模式</h3>
            <p class="advantage-description">
              支持在线和离线两种模式，即使没有网络连接，也能继续学习和提问
            </p>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon-wrapper">
            <i class="fas fa-project-diagram advantage-icon"></i>
          </div>
          <div class="advantage-content">
            <h3 class="advantage-title">知识图谱可视化</h3>
            <p class="advantage-description">
              基于知识图谱技术，直观展示知识点之间的关联，帮助构建完整知识体系
            </p>
          </div>
        </div>

        <div class="advantage-item">
          <div class="advantage-icon-wrapper">
            <i class="fas fa-user-graduate advantage-icon"></i>
          </div>
          <div class="advantage-content">
            <h3 class="advantage-title">个性化学习体验</h3>
            <p class="advantage-description">
              根据学习行为和笔记内容，智能推荐相关知识点，打造个性化学习路径
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- 数据统计区域 -->
  <section class="stats-section">
    <div class="stats-container">
      <div class="stat-item" v-for="(stat, index) in stats" :key="index">
        <div class="stat-number">{{ stat.number }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </div>
  </section>

  <!-- 用户评价区域 -->
  <section class="testimonials-section">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">用户的声音</h2>
        <p class="section-subtitle">听听我们的用户如何评价视频智能伴学系统</p>
      </div>
    
      <div class="testimonials-container">
        <swiper
          :modules="swiperModules"
          :slides-per-view="1"
          :space-between="30"
          :pagination="{ clickable: true }"
          :breakpoints="{
            '640': { slidesPerView: 1 },
            '768': { slidesPerView: 2 },
            '1024': { slidesPerView: 3 }
          }"
          :autoplay="{ delay: 5000, disableOnInteraction: false }"
          class="testimonial-swiper"
        >
          <swiper-slide v-for="(testimonial, index) in testimonials" :key="index">
            <div class="testimonial-card">
              <div class="testimonial-header">
                <div class="testimonial-avatar">
                  <i :class="testimonial.icon"></i>
                </div>
                <div class="testimonial-user">
                  <h4 class="testimonial-name">{{ testimonial.name }}</h4>
                  <p class="testimonial-role">{{ testimonial.role }}</p>
                </div>
              </div>
              <p class="testimonial-content">{{ testimonial.content }}</p>
              <div class="testimonial-rating">
                <i class="fas fa-star" v-for="star in 5" :key="star"></i>
              </div>
            </div>
          </swiper-slide>
        </swiper>
      </div>
    </div>
  </section>

  <!-- CTA 区域 -->
  <section class="cta-section">
    <div class="cta-card">
      <h2 class="cta-title">准备好开始智能学习之旅了吗？</h2>
      <p class="cta-description">立即体验视频智能伴学系统，让深度学习技术为您的学习提供全方位支持</p>
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
            <h3>视频智能伴学系统</h3>
          </div>
          <p class="footer-description">
            基于深度学习的视频智能伴学系统，让学习更高效、更智能、更个性化
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
        <p>&copy; 2025 视频智能伴学系统. 保留所有权利。</p>
      </div>
    </div>
  </footer>
  
  <!-- Toast 通知组件 -->
  <div class="toast-notification" :class="{ show: showToast }">
    {{ toastMessage }}
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { VideoCamera, ChatLineSquare, Connection, UploadFilled, VideoPlay, Delete, Refresh, InfoFilled } from '@element-plus/icons-vue'
import { Swiper, SwiperSlide } from 'swiper/vue'
import { Pagination, Navigation, Autoplay } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/navigation'

export default {
  name: 'Home',
  components: {
    Swiper,
    SwiperSlide,
    VideoCamera,
    ChatLineSquare,
    Connection,
    UploadFilled,
    VideoPlay,
    Delete,
    Refresh,
    InfoFilled
  },
  setup() {
    const router = useRouter()
    const isLoading = ref(false)
    const showToast = ref(false)
    const toastMessage = ref('')
    
    // 图片资源
    const heroBackground = 'https://public.readdy.ai/ai/img_res/b2856a465ee244a4bb2ffa4b39614527.jpg'
    const heroImage = 'https://public.readdy.ai/ai/img_res/3d0b4003873f780e91d428780abce6d6.jpg'
    const workflowImage1 = 'https://public.readdy.ai/ai/img_res/06e83fad25171a893e307d4bd002735a.jpg'
    const workflowImage2 = 'https://public.readdy.ai/ai/img_res/476cc88496e5400285d2b382daabf154.jpg'
    const workflowImage3 = 'https://public.readdy.ai/ai/img_res/abfb0f0106752b9290d6f09432b497bb.jpg'
    
    // 功能特性数据
    const features = ref([
      {
        icon: 'fa-cloud-upload-alt',
        title: '智能视频上传',
        description: '支持本地视频上传和哔哩哔哩/YouTube 链接导入，轻松获取学习资源'
      },
      {
        icon: 'fa-closed-captioning',
        title: '智能字幕生成',
        description: '使用 Whisper 语音识别模型，实时生成精准字幕，支持分段和语义合并显示'
      },
      {
        icon: 'fa-robot',
        title: 'AI 智能问答',
        description: '基于 RAG 系统的智能问答，支持深度思考模式，在线/离线模式任意切换'
      },
      {
        icon: 'fa-sticky-note',
        title: '智能笔记管理',
        description: '记录、导出、批量管理笔记，基于相似性推荐，帮助掌握核心知识点'
      }
    ])
    
    // 工作流程数据
    const workflows = ref([
      {
        step: 1,
        title: '上传学习视频',
        description: '上传本地视频文件或输入哔哩哔哩/YouTube 视频链接，系统自动处理并分析视频内容',
        image: workflowImage1
      },
      {
        step: 2,
        title: '观看并提问',
        description: '观看视频的同时，查看智能生成的字幕，随时提问疑惑，获取 AI 即时解答',
        image: workflowImage2
      },
      {
        step: 3,
        title: '记录与复习',
        description: '记录学习笔记，系统智能推荐相关知识点，导出笔记便于后续复习',
        image: workflowImage3
      }
    ])
    
    // Swiper 模块
    const swiperModules = [Pagination, Navigation, Autoplay]

    // 用户评价数据
    const testimonials = ref([
      {
        name: '张老师',
        role: '大学教授',
        icon: 'fas fa-chalkboard-teacher',
        content: '视频智能伴学系统彻底改变了我的教学方式，学生们可以随时回顾课程视频并获得 AI 辅助，学习效果显著提升。'
      },
      {
        name: '李同学',
        role: '研究生',
        icon: 'fas fa-user-graduate',
        content: '智能问答功能太棒了！即使是复杂的专业问题，系统也能给出清晰的解答，帮我节省了大量查阅资料的时间。'
      },
      {
        name: '王女士',
        role: '职场进修',
        icon: 'fas fa-briefcase',
        content: 'AI智能笔记同步功能太实用！视频看到哪里笔记就记到哪里，复习时图文并茂效率翻倍。'
      },
      {
        name: '李晓萌',
        role: '医学研究生',
        icon: 'fas fa-user-graduate',
        content: '手术视频的智能标注功能太惊艳！关键步骤自动标记时间戳，写论文时能快速定位参考资料。'
      },
      {
        name: '王经理',
        role: '企业培训师',
        icon: 'fas fa-briefcase',
        content: '我们公司将所有培训视频都上传到了视频智能伴学系统，员工培训效率提高了 50%，满意度也大幅提升。'
      },
      {
        name: '山田健太',
        role: '留学生',
        icon: 'fas fa-globe-asia',
        content: 'AI实时学术翻译精准度惊人！专业文献中的复杂术语都能即时解析，语言障碍不再是问题。'
      },
    ])
    
    // 统计数据
    const stats = ref([
      { number: '10,000+', label: '视频分析' },
      { number: '5,000+', label: '活跃用户' },
      { number: '98%', label: '用户满意度' },
      { number: '50,000+', label: '智能问答' }
    ])
    
    // 使用步骤数据
    const steps = ref([
      { title: '上传视频', description: '在"视频管理"中上传您的教育视频' },
      { title: '等待处理', description: '系统将自动处理视频并生成字幕' },
      { title: '观看与互动', description: '观看视频并使用AI问答功能深入学习' }
    ])
    
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

    return {
      navigateToUpload,
      UploadFilled,
      VideoCamera,
      Delete,
      VideoPlay,
      Refresh,
      InfoFilled,
      isLoading,
      showToast,
      toastMessage,
      features,
      steps,
      stats,
      swiperModules,
      heroBackground,
      heroImage,
      workflowImage1,
      workflowImage2,
      workflowImage3,
      workflows,
      testimonials
    }
  }
}
</script>

<style scoped>
/* 基本变量定义 */
:root {
  --primary-color: #3CAEA3;
  --primary-light: rgba(60, 174, 163, 0.2);
  --text-primary: #2C3E50;
  --text-secondary: #8492A6;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F5F8FA;
  --border-color: #E5E9F2;
  --transition-default: all 0.3s ease;
  --indigo-600: #4F46E5;
  --indigo-400: #818CF8;
  --indigo-100: #E0E7FF;
  --primary-gradient: linear-gradient(135deg, #667eea, #764ba2);
}

.home {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: var(--text-primary);
  overflow-x: hidden;
}

/* 英雄区域样式 */
.hero-section {
  position: relative;
  padding: 80px 20px;
  background-image: url('https://public.readdy.ai/ai/img_res/b2856a465ee244a4bb2ffa4b39614527.jpg');
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

.hero-image-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.hero-image {
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
  transform: translateY(0);
  transition: transform 0.5s ease;
}

.hero-image:hover {
  transform: translateY(-10px);
}

.main-title {
  font-size: 2.75rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  letter-spacing: -0.5px;
  line-height: 1.2;
  animation: fadeInDown 1s ease-out;
  color: #fff; 
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); 
}

.main-title .highlight {
  /* 移除渐变背景和透明文字 */
  color: #fff; /* 使用与按钮相同的紫色 */
  font-weight: 800;
  display: inline-block; /* 确保整个文本块作为一个整体 */
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* 添加文字阴影 */
}

.subtitle {
  font-size: 1.25rem;
  margin-bottom: 2.5rem;
  line-height: 1.6;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  animation: fadeInUp 1s ease-out 0.3s both;
}

.hero-button {
  padding: 0.75rem 2.5rem !important; /* 增大内边距，使按钮更大 */
  font-size: 1.1rem !important;  /* 增大字体大小 */
  font-weight: 600 !important;  /* 适当加粗 */
  border-radius: 8px !important;  /* 调整圆角与CTA按钮一致 */
  background-color: #fff !important;
  color: #764ba2 !important; /* 与CTA按钮颜色一致 */
  border: none !important;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1) !important; /* 与CTA按钮阴影一致 */
  transition: all 0.3s ease !important;
  animation: fadeInUp 1s ease-out 0.6s both;
}

.hero-button:hover {
  transform: scale(1.1) !important;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}

.hero-button:active {
  transform: translateY(-2px) !important;
}

@media (min-width: 768px) {
  .hero-content-wrapper {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
  
  .hero-text {
    width: 50%;
    text-align: left;
    margin-bottom: 0;
    padding-right: 2rem;
  }
  
  .hero-image-container {
    width: 50%;
  }
  
  .subtitle {
    margin-left: 0;
  }
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

/* 功能特性区域样式 */
.features-section {
  background-color: #fff;
  padding: 5rem 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 2rem;
  margin-top: 4rem;
}

.feature-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  transform: translateY(0);
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.feature-icon-wrapper {
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  background-color: var(--indigo-100);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
}

.feature-icon {
  color: #4F46E5;  /*强大功能，智能学习图标颜色*/
  font-size: 1.75rem;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
  text-align: center;
}

.feature-description {
  color: var(--text-secondary);
  line-height: 1.6;
  text-align: center;
}

@media (min-width: 768px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .features-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 工作流程区域样式 */
.workflow-section {
  background-color: var(--bg-secondary);
  padding: 2.5rem 1.5rem;  /* 从5rem减小到2.5rem */
  max-width: 1200px;
  margin: 0 auto;
}

.workflow-container {
  margin-top: 2rem;
}

.workflow-card {
  background-color: #fff;
  border-radius: 12px;
  padding: 2rem;
  height: 100%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  margin-bottom: 2rem;
  position: relative;
}

.workflow-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.step-number {
  position: absolute;
  top: -15px;
  left: -15px;
  width: 40px;
  height: 40px;
  background-color: #4F46E5;  /* 简单高效的学习流程图标颜色*/
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.25rem;
  z-index: 2;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.step-icon {
  color: #4F46E5;
  font-size: 1.5rem;
}

.workflow-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.workflow-description {
  color: var(--text-secondary);
  margin-bottom: 0;
  line-height: 1.6;
}

.workflow-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

/* 核心优势区域样式 */
.advantages-section {
  background-color: #fff;
  padding: 2.5rem 0;  /* 从5rem减小到2.5rem */
}

.advantages-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  margin-top: 3rem;
}

.advantage-item {
  background-color: #fff;
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  animation: fadeInUp 0.8s ease-out both;
}

/* 为每个卡片添加不同的延迟，创造错落有致的动画效果 */
.advantage-item:nth-child(1) {
  animation-delay: 0.1s;
}

.advantage-item:nth-child(2) {
  animation-delay: 0.3s;
}

.advantage-item:nth-child(3) {
  animation-delay: 0.5s;
}

.advantage-item:nth-child(4) {
  animation-delay: 0.7s;
}

.advantage-item:hover {
  transform: translateY(-10px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.advantage-icon-wrapper {
  width: 3rem;
  height: 3rem;
  background-color: #EEF2FF; /* 浅紫色背景 */
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.advantage-item:hover .advantage-icon-wrapper {
  transform: rotate(10deg) scale(1.1);
  background-color: #E0E7FF;
}

.advantage-icon {
  color: #4F46E5;  /* 核心优势图标颜色*/
  font-size: 1.75rem;
  transition: all 0.3s ease;
}

.advantage-item:hover .advantage-icon {
  transform: scale(1.1);
}

.advantage-content {
  flex-grow: 1;
}

.advantage-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.advantage-description {
  color: var(--text-secondary);
  line-height: 1.6;
}

@media (min-width: 768px) {
  .advantages-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 用户评价区域样式 */
.testimonials-section {
  padding: 5rem 1.5rem;
  background-color: #fff;
}

.testimonial-swiper {
  padding-bottom: 3rem;
  width: 100%;
}

.testimonials-container {
  max-width: 1200px;
  margin: 0 auto;
}

.testimonial-card {
  background-color: #f9fafb;
  border-radius: 1rem;
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.testimonial-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.testimonial-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.testimonial-avatar {
  width: 3rem;
  height: 3rem;
  background-color: var(--indigo-100);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.testimonial-avatar i {
  color: #4F46E5; /*用户的声音图标颜色*/
  font-size: 1.25rem;
}

.testimonial-user {
  flex-grow: 1;
}

.testimonial-name {
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.testimonial-role {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
}

.testimonial-content {
  color: #4b5563;
  line-height: 1.6;
  flex-grow: 1;
  margin-bottom: 1rem;
}

.testimonial-rating {
  color: #fbbf24;
  display: flex;
  gap: 0.25rem;
}

.testimonial-rating i {
  color: #fbbf24; /* 黄色星星 */
}

/* Swiper 分页器样式 */
:deep(.swiper-pagination-bullet) {
  background-color: var(--indigo-200);
  opacity: 1;
}

:deep(.swiper-pagination-bullet-active) {
  background-color: var(--indigo-600);
}

/* 数据统计区域样式 */
.stats-section {
  background-color: #5b5cff; /* 紫色背景 */
  padding: 3rem 0;
  color: #fff;
}

.stats-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  padding: 0 1.5rem;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  flex: 1;
  min-width: 200px;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1.125rem;
}

@media (max-width: 768px) {
  .stat-item {
    min-width: 150px;
    padding: 1rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .stat-label {
    font-size: 1rem;
  }
}

/* CTA 区域样式 */
.cta-section {
  padding: 5rem 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.cta-card {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
  color: #fff;
  box-shadow: 0 10px 30px rgba(118, 75, 162, 0.3);
  transition: all 0.3s ease;
}

.cta-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(118, 75, 162, 0.4);
}

.cta-title {
  font-size: 2.25rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
}

.cta-description {
  font-size: 1.2rem;
  margin-bottom: 2.5rem;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
  opacity: 0.95;
}

.cta-button {
  padding: 0.75rem 2.5rem !important;
  font-size: 1.1rem !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  background-color: #fff !important;
  color: #764ba2 !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1) !important;
  transition: all 0.3s ease !important;
}

.cta-button:hover {
  transform: translateY(-5px) !important;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15) !important;
}

/* 页脚样式 */
.footer-section {
  background-color: #1f2937;
  color: #fff;
  padding: 4rem 0 2rem;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
}

.footer-info {
  max-width: 300px;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.footer-logo i {
  color: #818CF8; /* 页脚logo图标颜色*/
  font-size: 1.5rem;
}

.footer-logo h3 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.footer-description {
  color: #9ca3af;
  line-height: 1.6;
}

.footer-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.footer-links ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-links li {
  margin-bottom: 0.5rem;
}

.footer-links a {
  color: #9ca3af;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-links a:hover {
  color: #fff;
}

.footer-contact ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-contact li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: #9ca3af;
}

.footer-contact li i {
  color: #818CF8; /*联系我们图标颜色*/
  margin-right: 0.5rem;
}

.footer-social {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.footer-social a {
  color: #9ca3af;
  font-size: 1.25rem;
  transition: color 0.2s ease;
}

.footer-social a:hover {
  color: #fff;
}

.footer-bottom {
  border-top: 1px solid #374151;
  padding-top: 1.5rem;
  text-align: center;
  color: #9ca3af;
}

@media (min-width: 768px) {
  .footer-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .footer-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* Toast 提示 */
.toast-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: var(--primary-color);
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  opacity: 0;
  transform: translateY(-20px);
  transition: all 0.3s ease;
}

.toast-notification.show {
  opacity: 1;
  transform: translateY(0);
}

/* 动画效果 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-30px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-title {
    font-size: 2.5rem;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .cta-title {
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
  
  .stat-number {
    font-size: 2rem;
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
  
  .cta-title {
    font-size: 1.5rem;
  }
  
  .cta-description {
    font-size: 1rem;
  }
  
  .stat-item {
    min-width: 150px;
    padding: 1rem;
  }
  
  .stat-number {
    font-size: 1.75rem;
  }
  
  .stat-label {
    font-size: 0.9rem;
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
  
  .cta-card {
    padding: 2.5rem 1.5rem;
  }
  
  .cta-title {
    font-size: 1.35rem;
  }
  
  .cta-button {
    padding: 0.5rem 1.5rem !important;
    font-size: 1rem !important;
  }
}
</style>