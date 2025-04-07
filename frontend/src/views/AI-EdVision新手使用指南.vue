<!-- The exported code uses Tailwind CSS. Install Tailwind CSS in your dev environment to ensure all styles work. -->

<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container mx-auto px-4 py-8 max-w-7xl">
      <header class="mb-10">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="text-3xl font-bold text-blue-600">AI-EdVision</div>
            <div class="ml-4 text-gray-500">智能教育视频分析系统</div>
          </div>
          <div class="flex items-center space-x-4">
            <button class="text-gray-600 hover:text-blue-600 cursor-pointer">
              <i class="fas fa-question-circle text-xl"></i>
            </button>
            <button class="text-gray-600 hover:text-blue-600 cursor-pointer">
              <i class="fas fa-user-circle text-xl"></i>
            </button>
          </div>
        </div>
      </header>

      <main class="relative">
        <!-- 主内容区 -->
        <div class="flex">
          <!-- 左侧内容区 (70%) -->
          <div class="w-[70%] pr-6">
            <div class="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-10 text-white mb-10">
              <h1 class="text-4xl font-bold mb-4">智能教育视频分析系统</h1>
              <p class="text-xl mb-8">利用AI技术，让每一个教育视频都成为个性化学习资源</p>
              <button class="bg-white text-blue-600 px-8 py-3 rounded-button font-semibold hover:bg-blue-50 transition duration-300 cursor-pointer whitespace-nowrap">
                开始上传
              </button>
            </div>

            <div class="grid grid-cols-3 gap-6 mb-10">
              <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition duration-300">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <i class="fas fa-cloud-upload-alt text-blue-600 text-2xl"></i>
                </div>
                <h3 class="text-xl font-semibold mb-2">视频上传与处理</h3>
                <p class="text-gray-600">支持本地视频上传和视频链接导入，AI自动生成字幕和知识点</p>
              </div>
              <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition duration-300">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <i class="fas fa-robot text-blue-600 text-2xl"></i>
                </div>
                <h3 class="text-xl font-semibold mb-2">智能问答系统</h3>
                <p class="text-gray-600">基于RAG技术的智能问答，支持在线/离线模式随时切换</p>
              </div>
              <div class="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition duration-300">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <i class="fas fa-sticky-note text-blue-600 text-2xl"></i>
                </div>
                <h3 class="text-xl font-semibold mb-2">智能笔记管理</h3>
                <p class="text-gray-600">记录笔记、导出笔记，系统自动推荐相似知识点</p>
              </div>
            </div>

            <div class="bg-white p-8 rounded-xl shadow-sm mb-10">
              <h2 class="text-2xl font-semibold mb-6">系统功能概览</h2>
              <div class="space-y-6">
                <div class="flex items-start">
                  <img class="w-32 h-24 rounded-lg object-cover object-top mr-6" :src="featureImage1" alt="视频上传功能" />
                  <div>
                    <h3 class="text-xl font-semibold mb-2">视频上传和处理</h3>
                    <p class="text-gray-600">支持本地视频上传和哔哩哔哩/YouTube视频链接上传学习视频，使用Whisper语音转录模型进行视频的转录，实时生成字幕。</p>
                  </div>
                </div>
                <div class="flex items-start">
                  <img class="w-32 h-24 rounded-lg object-cover object-top mr-6" :src="featureImage2" alt="视频播放功能" />
                  <div>
                    <h3 class="text-xl font-semibold mb-2">智能视频播放</h3>
                    <p class="text-gray-600">视频基础播放功能、智能问答系统、两种字幕显示格式（标准分段字幕和语义合并显示字幕），侧边栏可快速切换到其他功能页面。</p>
                  </div>
                </div>
                <div class="flex items-start">
                  <img class="w-32 h-24 rounded-lg object-cover object-top mr-6" :src="featureImage3" alt="笔记功能" />
                  <div>
                    <h3 class="text-xl font-semibold mb-2">笔记管理系统</h3>
                    <p class="text-gray-600">记录笔记和管理笔记，防止知识遗忘，可以播放视频、显示语义合并字幕、导出笔记、批量管理笔记，系统会基于已记录的笔记进行相似性推荐。</p>
                  </div>
                </div>
                <div class="flex items-start">
                  <img class="w-32 h-24 rounded-lg object-cover object-top mr-6" :src="featureImage4" alt="知识图谱功能" />
                  <div>
                    <h3 class="text-xl font-semibold mb-2">知识点总览与扩展</h3>
                    <p class="text-gray-600">基于知识图谱的知识点总览与扩展，可以查看当前视频的全部知识点以及推荐的相似知识点，帮助用户构建完整知识体系。</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧引导面板 (30%) -->
          <div class="w-[30%] bg-white rounded-xl shadow-md p-6 h-fit sticky top-4">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-2xl font-bold text-blue-600">欢迎使用 AI-EdVision</h2>
              <button class="text-gray-400 hover:text-gray-600 cursor-pointer">
                <i class="fas fa-times"></i>
              </button>
            </div>
            
            <p class="text-gray-600 mb-6">让我们快速了解系统的核心功能</p>
            
            <div class="flex mb-6">
              <div v-for="(step, index) in 4" :key="index" 
                   :class="`h-2 rounded-full flex-1 mx-1 ${currentStep >= step ? 'bg-blue-600' : 'bg-gray-200'}`">
              </div>
            </div>
            
            <div class="overflow-y-auto max-h-[500px] mb-6 pr-2 custom-scrollbar">
              <div v-if="currentStep === 1" class="guide-step">
                <div class="bg-blue-50 rounded-lg p-4 mb-4">
                  <div class="text-blue-600 font-semibold mb-2">步骤 1</div>
                  <h3 class="text-xl font-bold mb-3">开始上传您的学习视频</h3>
                </div>
                <img :src="guideImage1" alt="视频上传指南" class="w-full h-48 object-cover object-top rounded-lg mb-4" />
                <p class="text-gray-700 mb-4">AI-EdVision 支持两种视频上传方式：</p>
                <ul class="list-disc pl-5 mb-4 text-gray-600 space-y-2">
                  <li>本地视频文件上传（支持 MP4、AVI、MOV 等格式）</li>
                  <li>哔哩哔哩/YouTube 视频链接导入</li>
                </ul>
                <p class="text-gray-700 mb-2">操作提示：</p>
                <p class="text-gray-600 mb-4">点击首页的"开始上传"按钮，或直接将视频文件拖拽到上传区域。</p>
              </div>
              
              <div v-if="currentStep === 2" class="guide-step">
                <div class="bg-blue-50 rounded-lg p-4 mb-4">
                  <div class="text-blue-600 font-semibold mb-2">步骤 2</div>
                  <h3 class="text-xl font-bold mb-3">AI 智能处理</h3>
                </div>
                <img :src="guideImage2" alt="视频处理指南" class="w-full h-48 object-cover object-top rounded-lg mb-4" />
                <p class="text-gray-700 mb-4">上传视频后，AI-EdVision 将自动进行：</p>
                <ul class="list-disc pl-5 mb-4 text-gray-600 space-y-2">
                  <li>使用 Whisper 语音转录模型生成精准字幕</li>
                  <li>分析视频内容，提取关键知识点</li>
                  <li>构建知识图谱，为智能问答做准备</li>
                </ul>
                <p class="text-gray-700 mb-2">操作提示：</p>
                <p class="text-gray-600 mb-4">等待处理完成后，系统会自动跳转到视频播放页面。处理时间取决于视频长度。</p>
              </div>
              
              <div v-if="currentStep === 3" class="guide-step">
                <div class="bg-blue-50 rounded-lg p-4 mb-4">
                  <div class="text-blue-600 font-semibold mb-2">步骤 3</div>
                  <h3 class="text-xl font-bold mb-3">观看与互动</h3>
                </div>
                <img :src="guideImage3" alt="视频播放指南" class="w-full h-48 object-cover object-top rounded-lg mb-4" />
                <p class="text-gray-700 mb-4">视频播放页面提供多种智能功能：</p>
                <ul class="list-disc pl-5 mb-4 text-gray-600 space-y-2">
                  <li>基于 RAG 系统的智能问答，支持深度思考模式</li>
                  <li>在线/离线模式任意切换，离线也可进行问答学习</li>
                  <li>两种字幕显示格式：标准分段字幕和语义合并显示字幕</li>
                </ul>
                <p class="text-gray-700 mb-2">操作提示：</p>
                <p class="text-gray-600 mb-4">点击问答按钮开始对话，使用侧边栏切换至其他功能页面。</p>
              </div>
              
              <div v-if="currentStep === 4" class="guide-step">
                <div class="bg-blue-50 rounded-lg p-4 mb-4">
                  <div class="text-blue-600 font-semibold mb-2">步骤 4</div>
                  <h3 class="text-xl font-bold mb-3">知识管理</h3>
                </div>
                <img :src="guideImage4" alt="笔记管理指南" class="w-full h-48 object-cover object-top rounded-lg mb-4" />
                <p class="text-gray-700 mb-4">AI-EdVision 提供强大的知识管理功能：</p>
                <ul class="list-disc pl-5 mb-4 text-gray-600 space-y-2">
                  <li>记录笔记，系统自动关联视频内容</li>
                  <li>基于已记录笔记进行相似性推荐，更好地串联知识点</li>
                  <li>知识点总览与扩展，构建完整知识体系</li>
                  <li>笔记导出功能，支持多种格式</li>
                </ul>
                <p class="text-gray-700 mb-2">操作提示：</p>
                <p class="text-gray-600 mb-4">通过视频播放页面的侧边栏进入笔记页面和知识点总览页面。</p>
              </div>
            </div>
            
            <div class="flex justify-between items-center">
              <button 
                @click="prevStep" 
                :class="`px-4 py-2 rounded-button ${currentStep > 1 ? 'bg-gray-200 text-gray-700' : 'bg-gray-100 text-gray-400 cursor-not-allowed'} whitespace-nowrap cursor-pointer`"
                :disabled="currentStep <= 1">
                <i class="fas fa-arrow-left mr-2"></i>上一步
              </button>
              
              <div class="text-gray-500">{{ currentStep }}/4</div>
              
              <button 
                @click="nextStep" 
                :class="`px-4 py-2 rounded-button ${currentStep < 4 ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-400 cursor-not-allowed'} whitespace-nowrap cursor-pointer`"
                :disabled="currentStep >= 4">
                下一步<i class="fas fa-arrow-right ml-2"></i>
              </button>
            </div>
            
            <div class="text-center mt-4">
              <button class="text-gray-500 hover:text-blue-600 text-sm cursor-pointer whitespace-nowrap">跳过教程</button>
            </div>
          </div>
        </div>
      </main>

      <footer class="mt-16 border-t border-gray-200 pt-8 pb-12">
        <div class="grid grid-cols-4 gap-8">
          <div>
            <h3 class="text-lg font-semibold mb-4">AI-EdVision</h3>
            <p class="text-gray-500">智能教育视频分析系统，让每一个教育视频都成为个性化学习资源。</p>
          </div>
          <div>
            <h3 class="text-lg font-semibold mb-4">功能</h3>
            <ul class="space-y-2 text-gray-500">
              <li class="cursor-pointer hover:text-blue-600">视频上传与处理</li>
              <li class="cursor-pointer hover:text-blue-600">智能视频播放</li>
              <li class="cursor-pointer hover:text-blue-600">笔记管理系统</li>
              <li class="cursor-pointer hover:text-blue-600">知识点总览与扩展</li>
            </ul>
          </div>
          <div>
            <h3 class="text-lg font-semibold mb-4">资源</h3>
            <ul class="space-y-2 text-gray-500">
              <li class="cursor-pointer hover:text-blue-600">使用指南</li>
              <li class="cursor-pointer hover:text-blue-600">常见问题</li>
              <li class="cursor-pointer hover:text-blue-600">API 文档</li>
              <li class="cursor-pointer hover:text-blue-600">开发者社区</li>
            </ul>
          </div>
          <div>
            <h3 class="text-lg font-semibold mb-4">联系我们</h3>
            <ul class="space-y-2 text-gray-500">
              <li><i class="fas fa-envelope mr-2"></i>support@ai-edvision.com</li>
              <li><i class="fas fa-phone mr-2"></i>400-123-4567</li>
              <li class="flex mt-4 space-x-4">
                <i class="fab fa-weixin text-xl cursor-pointer hover:text-blue-600"></i>
                <i class="fab fa-weibo text-xl cursor-pointer hover:text-blue-600"></i>
                <i class="fab fa-github text-xl cursor-pointer hover:text-blue-600"></i>
              </li>
            </ul>
          </div>
        </div>
        <div class="mt-8 pt-8 border-t border-gray-200 text-center text-gray-500">
          <p>© 2025 AI-EdVision. 保留所有权利。</p>
          <div class="flex justify-center mt-4 space-x-6">
            <i class="fab fa-cc-visa text-xl"></i>
            <i class="fab fa-cc-mastercard text-xl"></i>
            <i class="fab fa-alipay text-xl"></i>
            <i class="fab fa-cc-paypal text-xl"></i>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from "vue";

const currentStep = ref(1);

const nextStep = () => {
  if (currentStep.value < 4) {
    currentStep.value++;
  }
};

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
};

// 功能展示图片
const featureImage1 = "https://public.readdy.ai/ai/img_res/0bd77a093894060dfff25e902a4078ee.jpg";
const featureImage2 = "https://public.readdy.ai/ai/img_res/8a5474b6e9dd8476e47e8cb3d7cb422a.jpg";
const featureImage3 = "https://public.readdy.ai/ai/img_res/cf4f452ff5b23449786c51390e127729.jpg";
const featureImage4 = "https://public.readdy.ai/ai/img_res/4dba3fc84f5c2f149898bcd41eb96d2f.jpg";

// 引导图片
const guideImage1 = "https://public.readdy.ai/ai/img_res/0ce075d310fee3cc88f9fbed4015e051.jpg";
const guideImage2 = "https://public.readdy.ai/ai/img_res/f40840c3739010bb33d0c0cdbee246da.jpg";
const guideImage3 = "https://public.readdy.ai/ai/img_res/6c326103b8b155db8c301a78eabe23e4.jpg";
const guideImage4 = "https://public.readdy.ai/ai/img_res/f9272e0d2258eff8fa184faedb98e067.jpg";
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #c5c5c5;
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a0a0a0;
}

.guide-step {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

