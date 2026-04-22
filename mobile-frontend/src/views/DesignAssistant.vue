<template>
  <div class="page design-page">
    <header class="topbar">
      <div>
        <div class="eyebrow">Sleek Integration</div>
        <h2>设计助手</h2>
      </div>
      <div class="topbar-actions">
        <button class="link" type="button" @click="refreshAll" :disabled="loading || submitting">
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
        <button class="link" type="button" @click="goBack">返回</button>
      </div>
    </header>

    <section class="card card--muted">
      <div class="card-title">接入状态</div>
      <p class="muted">
        该能力来自 `agent-skills` 对应的 Sleek API，但当前已经通过 EduMind 后端代理接入，不会在 H5 或 iOS 容器里暴露第三方密钥。
      </p>
      <div class="status-row">
        <span class="status-pill" :class="status.configured ? 'status-pill--ok' : 'status-pill--warn'">
          {{ status.configured ? '已配置 SLEEK_API_KEY' : '未配置 SLEEK_API_KEY' }}
        </span>
        <span class="status-detail">服务地址：{{ status.base_url || 'https://sleek.design' }}</span>
      </div>
      <p v-if="!status.configured" class="note">
        先在 `../edumind-backend/.env` 中配置 `SLEEK_API_KEY`，并为 key 打开 `projects`、`components`、`chats`、`screenshots` 相关 scope。
      </p>
    </section>

    <section class="card">
      <div class="card-head">
        <div>
          <div class="card-title">设计项目</div>
          <p class="muted">先选择一个 Sleek 项目，再把你希望生成的页面描述发给后端。</p>
        </div>
      </div>

      <label class="field">
        <span class="field-label">当前项目</span>
        <select v-model="selectedProjectId" class="input">
          <option value="">请选择项目</option>
          <option v-for="project in projects" :key="project.id" :value="project.id">
            {{ project.name || project.id }}
          </option>
        </select>
      </label>

      <label class="field">
        <span class="field-label">新建项目</span>
        <input
          v-model.trim="newProjectName"
          class="input"
          maxlength="120"
          placeholder="例如：EduMind Learning Redesign"
          :disabled="creatingProject"
        />
      </label>

      <div class="row-actions">
        <button class="btn btn--small" type="button" @click="createProjectAndSelect" :disabled="creatingProject || !newProjectName">
          {{ creatingProject ? '创建中…' : '创建并选中' }}
        </button>
      </div>
    </section>

    <section class="card">
      <div class="card-title">生成设计</div>
      <label class="field">
        <span class="field-label">设计描述</span>
        <textarea
          v-model.trim="prompt"
          class="input textarea"
          rows="6"
          placeholder="例如：为 EduMind 生成一个更克制的学习首页，包含最近学习、推荐入口、本地转录入口和上传动作。"
          :disabled="submitting"
        />
      </label>

      <label class="field">
        <span class="field-label">定向 screenId（可选）</span>
        <input
          v-model.trim="targetScreenId"
          class="input"
          placeholder="留空表示由 Sleek 自行决定新建或修改哪些页面"
          :disabled="submitting"
        />
      </label>

      <div class="row-actions">
        <button class="btn btn--small" type="button" @click="submitPrompt" :disabled="submitting || !canSubmit">
          {{ submitting ? '生成中…' : '生成设计稿' }}
        </button>
      </div>
      <p class="note">当前由后端等待任务完成，并在完成后自动拉回截图预览。</p>
    </section>

    <section v-if="runResult" class="card">
      <div class="card-title">最近结果</div>
      <div class="status-row">
        <span class="status-pill" :class="runStatusTone">{{ runResult.status || 'unknown' }}</span>
        <span class="status-detail">Run ID：{{ runResult.runId || '—' }}</span>
      </div>

      <p v-if="assistantText" class="assistant-copy">{{ assistantText }}</p>

      <div v-if="operations.length" class="operations">
        <button
          v-for="operation in operations"
          :key="operationKey(operation)"
          class="operation-chip"
          type="button"
          @click="viewComponent(operation.componentId)"
          :disabled="componentLoading || !operation.componentId"
        >
          {{ operation.screenName || operation.componentId || operation.type }}
        </button>
      </div>

      <p v-if="screenshotError" class="note note--warn">{{ screenshotError }}</p>

      <div v-if="combinedScreenshot" class="preview-block">
        <div class="preview-title">组合预览</div>
        <img :src="combinedScreenshot" alt="组合设计预览" class="preview-image" />
      </div>

      <div v-if="screenshots.length" class="preview-grid">
        <article v-for="item in screenshots" :key="item.key" class="preview-card">
          <div class="preview-title">{{ item.title }}</div>
          <img :src="item.src" :alt="item.title" class="preview-image" />
        </article>
      </div>
    </section>

    <section v-if="componentHtml" class="card card--muted">
      <div class="card-head">
        <div>
          <div class="card-title">组件 HTML 原型</div>
          <p class="muted">{{ componentMeta }}</p>
        </div>
        <button class="link" type="button" @click="componentHtml = ''">收起</button>
      </div>
      <textarea class="input code-box" :value="componentHtml" readonly rows="14" />
    </section>

    <div v-if="successMessage" class="alert alert--good">{{ successMessage }}</div>
    <div v-if="errorMessage" class="alert alert--bad">{{ errorMessage }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  createDesignProject,
  getDesignComponent,
  getDesignProjects,
  getDesignStatus,
  sendDesignMessage
} from '@/api/design'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const creatingProject = ref(false)
const status = ref({ configured: false, base_url: 'https://sleek.design' })
const projects = ref([])
const selectedProjectId = ref('')
const newProjectName = ref('')
const prompt = ref('')
const targetScreenId = ref('')
const runResult = ref(null)
const screenshots = ref([])
const combinedScreenshot = ref('')
const screenshotError = ref('')
const componentHtml = ref('')
const componentMeta = ref('')
const componentLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const parseErrorMessage = (error, fallback) => error?.response?.data?.detail || error?.message || fallback
const canSubmit = computed(() => Boolean(selectedProjectId.value && prompt.value))
const assistantText = computed(() => runResult.value?.result?.assistantText || '')
const operations = computed(() => {
  const list = runResult.value?.result?.operations
  return Array.isArray(list) ? list : []
})
const runStatusTone = computed(() => {
  const statusText = String(runResult.value?.status || '').toLowerCase()
  if (statusText === 'completed') return 'status-pill--ok'
  if (statusText === 'failed') return 'status-pill--warn'
  return 'status-pill--pending'
})

const toDataUrl = (item) => {
  const mimeType = item?.mime_type || 'image/png'
  const dataBase64 = item?.data_base64 || ''
  return dataBase64 ? `data:${mimeType};base64,${dataBase64}` : ''
}

const normalizeProjectList = (payload) => {
  const list = payload?.items || payload?.data || []
  return Array.isArray(list) ? list : []
}

const operationKey = (operation) =>
  `${operation?.type || 'op'}:${operation?.screenId || 'screen'}:${operation?.componentId || 'component'}`

const refreshAll = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const [statusRes, projectsRes] = await Promise.all([getDesignStatus(), getDesignProjects()])
    status.value = statusRes.data || status.value
    projects.value = normalizeProjectList(projectsRes.data)
    if (!selectedProjectId.value && projects.value.length > 0) {
      selectedProjectId.value = projects.value[0].id
    }
  } catch (error) {
    errorMessage.value = parseErrorMessage(error, '设计助手状态加载失败')
  } finally {
    loading.value = false
  }
}

const createProjectAndSelect = async () => {
  if (!newProjectName.value) return
  creatingProject.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await createDesignProject(newProjectName.value)
    const project = response.data?.project
    if (project?.id) {
      selectedProjectId.value = project.id
      newProjectName.value = ''
      await refreshAll()
      successMessage.value = `已创建项目：${project.name || project.id}`
      return
    }
    await refreshAll()
  } catch (error) {
    errorMessage.value = parseErrorMessage(error, '创建项目失败')
  } finally {
    creatingProject.value = false
  }
}

const submitPrompt = async () => {
  if (!canSubmit.value) return
  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''
  screenshotError.value = ''
  componentHtml.value = ''
  componentMeta.value = ''
  screenshots.value = []
  combinedScreenshot.value = ''
  runResult.value = null

  try {
    const response = await sendDesignMessage(selectedProjectId.value, {
      message: prompt.value,
      target_screen_id: targetScreenId.value || null,
      wait: true,
      include_screenshots: true
    })
    const payload = response.data || {}
    runResult.value = payload.run || null
    screenshotError.value = payload.screenshot_error || ''
    combinedScreenshot.value = payload.combined_screenshot ? toDataUrl(payload.combined_screenshot) : ''
    screenshots.value = Array.isArray(payload.screenshots)
      ? payload.screenshots.map((item, index) => ({
          key: `${(item.component_ids || []).join(',') || 'preview'}:${index}`,
          title: (item.component_ids || []).join(', ') || `预览 ${index + 1}`,
          src: toDataUrl(item)
        }))
      : []
    successMessage.value = runResult.value?.status === 'completed' ? '设计结果已返回' : '设计任务已提交'
  } catch (error) {
    errorMessage.value = parseErrorMessage(error, '生成设计失败')
  } finally {
    submitting.value = false
  }
}

const viewComponent = async (componentId) => {
  if (!componentId || !selectedProjectId.value) return
  componentLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getDesignComponent(selectedProjectId.value, componentId)
    const component = response.data?.component || {}
    const versions = Array.isArray(component.versions) ? component.versions : []
    const activeVersion = versions.find((item) => item.version === component.activeVersion) || versions[versions.length - 1] || {}
    componentHtml.value = activeVersion.code || ''
    componentMeta.value = `${component.name || componentId} · version ${activeVersion.version || component.activeVersion || 1}`
  } catch (error) {
    errorMessage.value = parseErrorMessage(error, '读取组件 HTML 失败')
  } finally {
    componentLoading.value = false
  }
}

const goBack = () => {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.replace('/profile')
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.design-page {
  display: grid;
  gap: 14px;
}

.topbar-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.eyebrow {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.status-pill--ok {
  background: rgba(234, 225, 246, 0.9);
  color: var(--lilac-text);
}

.status-pill--warn {
  background: rgba(234, 225, 246, 0.92);
  color: var(--lilac-text);
}

.status-pill--pending {
  background: rgba(240, 232, 245, 0.92);
  color: var(--primary-deep);
}

.status-detail,
.note,
.assistant-copy {
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
}

.note {
  margin: 8px 0 0;
}

.note--warn {
  color: var(--lilac-text);
}

.textarea {
  min-height: 132px;
  resize: vertical;
}

.operations {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.operation-chip {
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 999px;
  background: rgba(242, 235, 248, 0.94);
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary-deep);
}

.preview-block,
.preview-card {
  display: grid;
  gap: 8px;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.preview-title {
  font-size: 12px;
  font-weight: 700;
  color: #111827;
}

.preview-image {
  width: 100%;
  display: block;
  border-radius: 18px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(255, 255, 255, 0.82);
}

.code-box {
  min-height: 280px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
  line-height: 1.5;
}
</style>
