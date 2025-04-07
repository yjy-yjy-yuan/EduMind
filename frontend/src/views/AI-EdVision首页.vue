<!-- The exported code uses Tailwind CSS. Install Tailwind CSS in your dev environment to ensure all styles work. -->

<template>
  <div class="min-h-screen bg-gradient-to-b from-blue-50 to-white">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm sticky top-0 z-50">
      <div class="container mx-auto px-6 py-4 flex justify-between items-center">
        <div class="flex items-center space-x-2">
          <i class="fas fa-brain text-indigo-600 text-2xl"></i>
          <h1 class="text-xl font-bold text-gray-800">AI-EdVision</h1>
        </div>
        <div class="hidden md:flex items-center space-x-8">
          <a href="#features" class="text-gray-700 hover:text-indigo-600 transition-colors cursor-pointer whitespace-nowrap">功能介绍</a>
          <a href="#workflow" class="text-gray-700 hover:text-indigo-600 transition-colors cursor-pointer whitespace-nowrap">工作流程</a>
          <a href="#advantages" class="text-gray-700 hover:text-indigo-600 transition-colors cursor-pointer whitespace-nowrap">核心优势</a>
          <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg shadow-md hover:shadow-lg transition-all transform hover:-translate-y-1 !rounded-button cursor-pointer whitespace-nowrap">
            开始体验
          </button>
        </div>
        <div class="md:hidden">
          <button @click="toggleMobileMenu" class="text-gray-700 focus:outline-none cursor-pointer">
            <i class="fas fa-bars text-xl"></i>
          </button>
        </div>
      </div>
      <!-- 移动端菜单 -->
      <div v-if="mobileMenuOpen" class="md:hidden bg-white shadow-lg absolute w-full">
        <div class="container mx-auto px-6 py-4 flex flex-col space-y-4">
          <a href="#features" @click="toggleMobileMenu" class="text-gray-700 hover:text-indigo-600 transition-colors cursor-pointer">功能介绍</a>
          <a href="#workflow" @click="toggleMobileMenu" class="text-gray-700 hover:text-indigo-600 transition-colors cursor-pointer">工作流程</a>
          <a href="#advantages" @click="toggleMobileMenu" class="text-gray-700 hover:text-indigo-600 transition-colors cursor-pointer">核心优势</a>
          <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg shadow-md hover:shadow-lg transition-all !rounded-button cursor-pointer whitespace-nowrap">
            开始体验
          </button>
        </div>
      </div>
    </nav>

    <!-- Hero 区域 -->
    <div class="relative overflow-hidden">
      <div class="absolute inset-0 z-0">
        <img :src="heroBackground" alt="AI 教育背景" class="w-full h-full object-cover object-top" />
      </div>
      <div class="container mx-auto px-6 py-16 md:py-24 relative z-10">
        <div class="flex flex-col md:flex-row items-center">
          <div class="w-full md:w-1/2 text-center md:text-left mb-10 md:mb-0">
            <h1 class="text-4xl md:text-5xl font-bold text-gray-800 mb-6">
              AI-EdVision<br />
              <span class="text-indigo-600">智能教育视频分析系统</span>
            </h1>
            <p class="text-lg text-gray-700 mb-8">
              通过 AI 技术赋能教育视频，提供智能字幕、知识问答、笔记管理等功能，让学习更高效、更智能、更个性化。
            </p>
            <button class="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg shadow-md hover:shadow-lg transition-all transform hover:-translate-y-1 text-lg !rounded-button cursor-pointer whitespace-nowrap">
              立即开始学习
            </button>
          </div>
          <div class="w-full md:w-1/2">
            <img :src="heroImage" alt="AI 教育视频分析系统" class="w-full h-auto rounded-xl shadow-2xl transform hover:scale-105 transition-transform duration-500" />
          </div>
        </div>
      </div>
    </div>

    <!-- 功能介绍区域 -->
    <section id="features" class="py-16 bg-white">
      <div class="container mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-800 mb-4">强大功能，智能学习</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">
            AI-EdVision 集成多种智能功能，为您的学习体验带来革命性变化
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 transform hover:-translate-y-2 transition-transform duration-300 cursor-pointer">
            <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6 mx-auto">
              <i class="fas fa-cloud-upload-alt text-indigo-600 text-2xl"></i>
            </div>
            <h3 class="text-xl font-semibold text-gray-800 mb-3 text-center">智能视频上传</h3>
            <p class="text-gray-600 text-center">
              支持本地视频上传和哔哩哔哩/YouTube 链接导入，轻松获取学习资源
            </p>
          </div>

          <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 transform hover:-translate-y-2 transition-transform duration-300 cursor-pointer">
            <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6 mx-auto">
              <i class="fas fa-closed-captioning text-indigo-600 text-2xl"></i>
            </div>
            <h3 class="text-xl font-semibold text-gray-800 mb-3 text-center">智能字幕生成</h3>
            <p class="text-gray-600 text-center">
              使用 Whisper 语音识别模型，实时生成精准字幕，支持分段和语义合并显示
            </p>
          </div>

          <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 transform hover:-translate-y-2 transition-transform duration-300 cursor-pointer">
            <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6 mx-auto">
              <i class="fas fa-robot text-indigo-600 text-2xl"></i>
            </div>
            <h3 class="text-xl font-semibold text-gray-800 mb-3 text-center">智能问答系统</h3>
            <p class="text-gray-600 text-center">
              基于 RAG 系统的智能问答，支持深度思考模式，在线/离线模式任意切换
            </p>
          </div>

          <div class="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 transform hover:-translate-y-2 transition-transform duration-300 cursor-pointer">
            <div class="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6 mx-auto">
              <i class="fas fa-sticky-note text-indigo-600 text-2xl"></i>
            </div>
            <h3 class="text-xl font-semibold text-gray-800 mb-3 text-center">智能笔记管理</h3>
            <p class="text-gray-600 text-center">
              记录、导出、批量管理笔记，基于相似性推荐，帮助掌握核心知识点
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- 工作流程区域 -->
    <section id="workflow" class="py-16 bg-gray-50">
      <div class="container mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-800 mb-4">简单高效的学习流程</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">
            只需几个简单步骤，即可开启 AI 辅助学习之旅
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="bg-white rounded-xl shadow-md p-6 relative">
            <div class="absolute -top-5 -left-5 w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">1</div>
            <img :src="workflowImage1" alt="上传视频" class="w-full h-48 object-cover object-top rounded-lg mb-6" />
            <h3 class="text-xl font-semibold text-gray-800 mb-3">上传学习视频</h3>
            <p class="text-gray-600">
              上传本地视频文件或输入哔哩哔哩/YouTube 视频链接，系统自动处理并分析视频内容
            </p>
          </div>

          <div class="bg-white rounded-xl shadow-md p-6 relative">
            <div class="absolute -top-5 -left-5 w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">2</div>
            <img :src="workflowImage2" alt="观看学习" class="w-full h-48 object-cover object-top rounded-lg mb-6" />
            <h3 class="text-xl font-semibold text-gray-800 mb-3">观看并提问</h3>
            <p class="text-gray-600">
              观看视频的同时，查看智能生成的字幕，随时提问疑惑，获取 AI 即时解答
            </p>
          </div>

          <div class="bg-white rounded-xl shadow-md p-6 relative">
            <div class="absolute -top-5 -left-5 w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">3</div>
            <img :src="workflowImage3" alt="记录笔记" class="w-full h-48 object-cover object-top rounded-lg mb-6" />
            <h3 class="text-xl font-semibold text-gray-800 mb-3">记录与复习</h3>
            <p class="text-gray-600">
              记录学习笔记，系统智能推荐相关知识点，导出笔记便于后续复习
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心优势区域 -->
    <section id="advantages" class="py-16 bg-white">
      <div class="container mx-auto px-6">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-gray-800 mb-4">AI-EdVision 核心优势</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">
            我们的系统具备多项独特优势，为您的学习提供全方位支持
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0 w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <i class="fas fa-brain text-indigo-600 text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-semibold text-gray-800 mb-2">AI 驱动的智能分析</h3>
              <p class="text-gray-600">
                采用先进的 AI 技术，对视频内容进行深度分析，提取关键知识点，生成精准字幕
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0 w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <i class="fas fa-wifi text-indigo-600 text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-semibold text-gray-800 mb-2">在线/离线双模式</h3>
              <p class="text-gray-600">
                支持在线和离线两种模式，即使没有网络连接，也能继续学习和提问
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0 w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <i class="fas fa-project-diagram text-indigo-600 text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-semibold text-gray-800 mb-2">知识图谱可视化</h3>
              <p class="text-gray-600">
                基于知识图谱技术，直观展示知识点之间的关联，帮助构建完整知识体系
              </p>
            </div>
          </div>

          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0 w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <i class="fas fa-user-graduate text-indigo-600 text-xl"></i>
            </div>
            <div>
              <h3 class="text-xl font-semibold text-gray-800 mb-2">个性化学习体验</h3>
              <p class="text-gray-600">
                根据学习行为和笔记内容，智能推荐相关知识点，打造个性化学习路径
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 数据统计区域 -->
    <section class="py-16 bg-indigo-600 text-white">
      <div class="container mx-auto px-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div class="text-4xl font-bold mb-2">10,000+</div>
            <div class="text-lg">视频分析</div>
          </div>
          <div>
            <div class="text-4xl font-bold mb-2">5,000+</div>
            <div class="text-lg">活跃用户</div>
          </div>
          <div>
            <div class="text-4xl font-bold mb-2">98%</div>
            <div class="text-lg">用户满意度</div>
          </div>
          <div>
            <div class="text-4xl font-bold mb-2">50,000+</div>
            <div class="text-lg">智能问答</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 用户评价轮播 -->
    <section class="py-16 bg-white">
      <div class="container mx-auto px-6">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-gray-800 mb-4">用户的声音</h2>
          <p class="text-lg text-gray-600 max-w-2xl mx-auto">
            听听我们的用户如何评价 AI-EdVision
          </p>
        </div>

        <div class="relative">
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
              <div class="bg-gray-50 rounded-xl p-6 h-full flex flex-col">
                <div class="flex items-center mb-4">
                  <div class="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
                    <i :class="testimonial.icon" class="text-indigo-600"></i>
                  </div>
                  <div>
                    <h4 class="font-semibold text-gray-800">{{ testimonial.name }}</h4>
                    <p class="text-gray-500 text-sm">{{ testimonial.role }}</p>
                  </div>
                </div>
                <p class="text-gray-600 flex-grow">{{ testimonial.content }}</p>
                <div class="flex text-yellow-400 mt-4">
                  <i class="fas fa-star" v-for="star in 5" :key="star"></i>
                </div>
              </div>
            </swiper-slide>
          </swiper>
        </div>
      </div>
    </section>

    <!-- CTA 区域 -->
    <section class="py-16 bg-gray-50">
      <div class="container mx-auto px-6">
        <div class="bg-gradient-to-r from-indigo-600 to-blue-500 rounded-2xl p-10 text-white text-center">
          <h2 class="text-3xl font-bold mb-6">准备好开始智能学习之旅了吗？</h2>
          <p class="text-xl mb-8 max-w-2xl mx-auto">
            立即体验 AI-EdVision，让 AI 技术为您的学习提供全方位支持
          </p>
          <button class="bg-white text-indigo-600 hover:bg-gray-100 px-8 py-3 rounded-lg shadow-md hover:shadow-lg transition-all transform hover:-translate-y-1 text-lg font-semibold !rounded-button cursor-pointer whitespace-nowrap">
            免费开始使用
          </button>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="bg-gray-800 text-white py-12">
      <div class="container mx-auto px-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <div class="flex items-center space-x-2 mb-4">
              <i class="fas fa-brain text-indigo-400 text-2xl"></i>
              <h3 class="text-xl font-bold">AI-EdVision</h3>
            </div>
            <p class="text-gray-400">
              智能教育视频分析系统，让学习更高效、更智能、更个性化
            </p>
          </div>
          <div>
            <h4 class="text-lg font-semibold mb-4">功能</h4>
            <ul class="space-y-2 text-gray-400">
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">视频上传</a></li>
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">智能字幕</a></li>
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">智能问答</a></li>
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">笔记管理</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-lg font-semibold mb-4">资源</h4>
            <ul class="space-y-2 text-gray-400">
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">使用指南</a></li>
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">API 文档</a></li>
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">常见问题</a></li>
              <li><a href="#" class="hover:text-white transition-colors cursor-pointer">博客</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-lg font-semibold mb-4">联系我们</h4>
            <ul class="space-y-2 text-gray-400">
              <li class="flex items-center"><i class="fas fa-envelope mr-2"></i> contact@ai-edvision.com</li>
              <li class="flex items-center"><i class="fas fa-phone mr-2"></i> +86 123 4567 8910</li>
              <li class="flex items-center"><i class="fas fa-map-marker-alt mr-2"></i> 北京市海淀区中关村</li>
            </ul>
            <div class="flex space-x-4 mt-4">
              <a href="#" class="text-gray-400 hover:text-white transition-colors cursor-pointer"><i class="fab fa-weixin text-xl"></i></a>
              <a href="#" class="text-gray-400 hover:text-white transition-colors cursor-pointer"><i class="fab fa-weibo text-xl"></i></a>
              <a href="#" class="text-gray-400 hover:text-white transition-colors cursor-pointer"><i class="fab fa-github text-xl"></i></a>
              <a href="#" class="text-gray-400 hover:text-white transition-colors cursor-pointer"><i class="fab fa-linkedin text-xl"></i></a>
            </div>
          </div>
        </div>
        <div class="border-t border-gray-700 pt-8 text-center text-gray-400">
          <p>&copy; 2025 AI-EdVision. 保留所有权利。</p>
          <div class="flex justify-center space-x-4 mt-4">
            <a href="#" class="hover:text-white transition-colors cursor-pointer">隐私政策</a>
            <a href="#" class="hover:text-white transition-colors cursor-pointer">服务条款</a>
            <a href="#" class="hover:text-white transition-colors cursor-pointer">Cookie 政策</a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import { Swiper, SwiperSlide } from 'swiper/vue';
import { Pagination, Navigation, Autoplay } from 'swiper/modules'
import 'swiper/css'
import 'swiper/css/pagination'
import 'swiper/css/navigation'

const swiperModules = [Pagination, Autoplay];
const mobileMenuOpen = ref(false);

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value;
};

// 图片资源
const heroBackground = 'https://public.readdy.ai/ai/img_res/b2856a465ee244a4bb2ffa4b39614527.jpg';

const heroImage = 'https://public.readdy.ai/ai/img_res/3d0b4003873f780e91d428780abce6d6.jpg';

const workflowImage1 = 'https://public.readdy.ai/ai/img_res/06e83fad25171a893e307d4bd002735a.jpg';

const workflowImage2 = 'https://public.readdy.ai/ai/img_res/476cc88496e5400285d2b382daabf154.jpg';

const workflowImage3 = 'https://public.readdy.ai/ai/img_res/abfb0f0106752b9290d6f09432b497bb.jpg';

// 用户评价数据
const testimonials = [
  {
    name: "张明",
    role: "大学生",
    icon: "fas fa-user-graduate",
    content: "AI-EdVision 彻底改变了我的学习方式！智能问答功能让我能够即时解决疑惑，而不必翻阅大量资料。笔记管理功能也非常实用，帮助我更好地整理知识点。"
  },
  {
    name: "李华",
    role: "自学者",
    icon: "fas fa-book-reader",
    content: "作为一名自学者，我特别喜欢 AI-EdVision 的离线模式功能。即使在没有网络的环境下，我也能继续学习和提问，这真的太方便了！"
  },
  {
    name: "王芳",
    role: "教育工作者",
    icon: "fas fa-chalkboard-teacher",
    content: "我在课程准备中大量使用 AI-EdVision，它不仅帮助我分析教学视频，还能生成精准的字幕和知识点总结，大大提高了我的工作效率。"
  },
  {
    name: "刘强",
    role: "IT 专业人士",
    icon: "fas fa-laptop-code",
    content: "作为技术人员，我对 AI-EdVision 的技术实现印象深刻。RAG 系统的智能问答非常准确，知识图谱可视化也做得很棒，是学习技术知识的得力助手。"
  },
  {
    name: "赵雪",
    role: "研究生",
    icon: "fas fa-microscope",
    content: "在准备论文期间，AI-EdVision 帮助我快速理解和整理大量视频资料，智能笔记推荐功能特别有用，让我不会遗漏重要知识点。"
  }
];
</script>

<style scoped>
.testimonial-swiper {
  padding-bottom: 50px;
}

.testimonial-swiper .swiper-pagination {
  bottom: 0;
}

.testimonial-swiper .swiper-slide {
  height: auto;
}
</style>

