<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="goBack">‹</button>
      <h2>新手使用指南</h2>
      <div />
    </header>

    <section class="hero">
      <div class="hero-title">快速掌握核心功能</div>
      <div class="hero-subtitle">上传 → 分析 → 观看 → 提问 → 记笔记 → 规划学习路径</div>
      <div class="hero-actions">
        <button class="btn btn--primary" @click="go('/upload')">开始上传视频</button>
        <button class="btn" @click="go('/videos')">浏览视频列表</button>
      </div>
      <div class="hero-tip">当前阶段仅实现 UI 页面与交互占位；真实功能将在后续通过预留接口接入。</div>
    </section>

    <section class="card">
      <div class="title">使用流程</div>
      <div class="workflow-flow" aria-label="使用流程图">
        <div v-for="step in flowSteps" :key="step" class="workflow-flow__step">{{ step }}</div>
      </div>
      <ol class="ol">
        <li>登录/注册后进入系统</li>
        <li>上传本地视频或粘贴链接</li>
        <li>当前版本用占位数据模拟处理流程与状态变化</li>
        <li>进入视频详情和播放器页查看完整 UI 流程</li>
        <li>使用问答与笔记巩固学习效果</li>
      </ol>
    </section>

    <section class="card">
      <div class="title">详细教程</div>
      <div class="accordions">
        <details class="acc" open>
          <summary class="acc-summary">
            <span class="acc-badge">01</span>
            <span class="acc-title">登录 / 注册</span>
          </summary>
          <div class="acc-body">
            <ol class="ol">
              <li>新用户点击“注册”，填写邮箱或手机号，并设置强密码</li>
              <li>老用户直接“登录”，输入邮箱/手机号与密码</li>
              <li>登录后可使用视频上传、分析、问答与笔记管理</li>
            </ol>
            <div class="acc-actions">
              <button class="btn" @click="go('/login')">去登录</button>
              <button class="btn" @click="go('/register')">去注册</button>
            </div>
          </div>
        </details>

        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-badge">02</span>
            <span class="acc-title">视频上传与分析</span>
          </summary>
          <div class="acc-body">
            <ol class="ol">
              <li>进入“上传”页，选择本地上传或链接导入</li>
              <li>当前阶段用本地 mock 数据驱动上传与分析状态</li>
              <li>在“视频”列表或详情页查看占位进度与状态</li>
              <li>后续接入真实接口后可无缝替换为正式处理流程</li>
            </ol>
            <div class="acc-actions">
              <button class="btn btn--primary" @click="go('/upload')">前往上传</button>
              <button class="btn" @click="go('/videos')">查看视频</button>
            </div>
          </div>
        </details>

        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-badge">03</span>
            <span class="acc-title">视频播放</span>
          </summary>
          <div class="acc-body">
            <ol class="ol">
              <li>在“视频”列表中选择一个“已完成”的视频进入详情</li>
              <li>点击“播放”进入播放器页面查看布局与交互占位</li>
              <li>真实视频流、字幕轨与播放状态将在后续接入接口</li>
            </ol>
            <div class="acc-actions">
              <button class="btn" @click="go('/videos')">浏览视频列表</button>
            </div>
          </div>
        </details>

        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-badge">04</span>
            <span class="acc-title">智能问答</span>
          </summary>
          <div class="acc-body">
            <ol class="ol">
              <li>进入“问答”页（可从视频详情页跳转带上 videoId）</li>
              <li>输入你的问题并发送，AI 将基于视频内容或通用知识回答</li>
              <li>问题越具体，回答质量越高；可连续追问深入探讨</li>
            </ol>
            <div class="acc-actions">
              <button class="btn btn--primary" @click="go('/qa')">打开问答</button>
            </div>
          </div>
        </details>

        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-badge">05</span>
            <span class="acc-title">笔记系统辅助学习</span>
          </summary>
          <div class="acc-body">
            <ol class="ol">
              <li>进入“笔记”页查看所有笔记</li>
              <li>点击“新建”创建笔记，记录关键结论与要点</li>
              <li>在笔记中可进行编辑与删除，便于反复迭代</li>
            </ol>
            <div class="acc-actions">
              <button class="btn btn--primary" @click="go('/notes')">前往笔记</button>
            </div>
            <div class="acc-note">当前优先完成页面结构，导出等能力后续通过接口扩展。</div>
          </div>
        </details>

        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-badge">06</span>
            <span class="acc-title">学习路径</span>
          </summary>
          <div class="acc-body">
            <ol class="ol">
              <li>进入“学习路径”查看当前建议的学习步骤与规划</li>
              <li>根据建议继续进入视频、问答或笔记页完成复习</li>
              <li>当前展示静态或 mock 内容，后续切换为真实接口数据</li>
            </ol>
            <div class="acc-actions">
              <button class="btn" @click="go('/learning-path')">学习路径</button>
            </div>
          </div>
        </details>
      </div>
    </section>

    <section class="card">
      <div class="title">常见问题</div>
      <div class="accordions">
        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-title">如何上传视频？</span>
          </summary>
          <div class="acc-body">
            在“上传”页面选择本地视频文件或输入视频链接即可开始上传。
          </div>
        </details>
        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-title">视频处理需要多长时间？</span>
          </summary>
          <div class="acc-body">
            当前为 UI-only 阶段，页面使用本地 mock 数据模拟处理时间与状态变化。
          </div>
        </details>
        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-title">如何使用 AI 问答功能？</span>
          </summary>
          <div class="acc-body">
            当前问答页使用占位回复演示交互；后续会切换到正式问答接口。
          </div>
        </details>
        <details class="acc">
          <summary class="acc-summary">
            <span class="acc-title">页面打不开/白屏怎么办？</span>
          </summary>
          <div class="acc-body">
            当前版本默认是 UI-only 模式，不依赖真实后端。若页面异常，请优先检查前端资源是否已重新构建并同步到 iOS 容器。
          </div>
        </details>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const flowSteps = ['登录', '上传', '分析', '播放', '问答', '笔记', '路径']
const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.replace('/')
}

const go = (path) => router.push(path)
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px 16px 0;
}

.topbar {
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.back {
  border: 0;
  background: var(--card);
  border-radius: 12px;
  height: 36px;
  width: 40px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  font-size: 22px;
  line-height: 1;
}

.topbar h2 {
  margin: 0;
  font-size: 16px;
  text-align: center;
}

.hero {
  padding: 14px;
  border-radius: var(--radius);
  color: #fff;
  background: linear-gradient(135deg, #a792bc, #7f698f);
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.hero-title {
  font-weight: 900;
  font-size: 16px;
}

.hero-subtitle {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.92;
  line-height: 1.6;
}

.hero-actions {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.hero-tip {
  margin-top: 10px;
  font-size: 12px;
  opacity: 0.92;
}

.workflow-flow {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.workflow-flow__step {
  position: relative;
  padding: 10px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(139, 121, 157, 0.12), rgba(183, 157, 213, 0.22));
  color: #0f4c5c;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.btn {
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
  color: var(--text);
}

.btn--primary {
  border: 0;
  color: #fff;
  background: rgba(255, 255, 255, 0.18);
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.title {
  font-weight: 900;
  font-size: 13px;
}

.workflow {
  width: 100%;
  height: auto;
  display: block;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: #fff;
}

.ol {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.7;
}

.accordions {
  display: grid;
  gap: 10px;
}

.acc {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: #fff;
  overflow: hidden;
}

.acc-summary {
  list-style: none;
  cursor: pointer;
  padding: 12px;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  align-items: center;
  font-weight: 900;
}

.acc-summary::-webkit-details-marker {
  display: none;
}

.acc-badge {
  height: 22px;
  width: 34px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(79, 70, 229, 0.10);
  color: var(--primary);
  font-size: 12px;
}

.acc-title {
  font-size: 13px;
}

.acc-body {
  padding: 0 12px 12px;
  color: var(--text);
  font-size: 13px;
  line-height: 1.7;
}

.acc-actions {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.acc-note {
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}
</style>
<style scoped>
.hero {
  background:
    radial-gradient(circle at right top, rgba(255, 255, 255, 0.24), transparent 44%),
    linear-gradient(145deg, #8b799d, #665775);
}

.btn--primary {
  background: linear-gradient(145deg, #8b799d, #a48eb5);
}

.workflow {
  border-radius: 18px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: #fff;
}

.acc {
  border-color: rgba(32, 42, 55, 0.1);
  background: linear-gradient(180deg, #ffffff, #f0e8f7);
}

.acc-badge {
  background: rgba(139, 121, 157, 0.14);
  color: var(--primary-deep);
}

.acc-note {
  background: rgba(139, 121, 157, 0.08);
  color: var(--primary-deep);
}
</style>
