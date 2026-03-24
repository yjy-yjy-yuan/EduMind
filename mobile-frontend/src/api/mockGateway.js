const nowISO = () => new Date().toISOString()

let videoAutoId = 6
let noteAutoId = 4
let noteTimestampAutoId = 5
let mockToken = 'ui-only-token'
let mockUser = {
  id: 1,
  username: 'demo_user',
  email: 'demo@edumind.app',
  phone: null,
  avatar: null,
  login_count: 0
}

const videos = [
  {
    id: 1,
    title: '高等数学导数专题',
    status: 'completed',
    process_progress: 100,
    current_step: '分析完成',
    requested_model: 'base',
    effective_model: 'base',
    summary: '本节梳理导数定义、几何意义与常见求导法则。',
    tags: ['导数定义', '几何意义', '求导法则'],
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 2,
    title: '英语语法时态精讲',
    status: 'processing',
    process_progress: 42,
    current_step: '语音识别中',
    requested_model: 'base',
    effective_model: 'base',
    summary: '',
    tags: [],
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 3,
    title: 'Python 数据结构入门',
    status: 'failed',
    process_progress: 18,
    current_step: '处理失败',
    requested_model: 'base',
    effective_model: 'base',
    summary: '',
    tags: [],
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 4,
    title: '中国近代史复习',
    status: 'pending',
    process_progress: 0,
    current_step: '排队中',
    requested_model: 'base',
    effective_model: 'base',
    summary: '',
    tags: [],
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 5,
    title: '物理力学专题讲解',
    status: 'uploaded',
    process_progress: 0,
    current_step: '已上传',
    requested_model: 'base',
    effective_model: 'base',
    summary: '',
    tags: [],
    created_at: nowISO(),
    updated_at: nowISO()
  }
]

const notes = [
  {
    id: 1,
    title: '导数速记卡',
    content: '基本求导公式、复合函数求导、隐函数求导。',
    note_type: 'text',
    video_id: 1,
    tags: ['导数', '求导'],
    keywords: ['导数', '复合函数'],
    timestamps: [
      {
        id: 1,
        note_id: 1,
        time_seconds: 125,
        subtitle_text: '导数定义和几何意义要对应理解。',
        created_at: nowISO()
      }
    ],
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 2,
    title: '英语时态易错点',
    content: '现在完成时与一般过去时的常见语境区分。',
    note_type: 'text',
    video_id: 2,
    tags: ['英语', '时态'],
    keywords: ['完成时', '过去时'],
    timestamps: [
      {
        id: 2,
        note_id: 2,
        time_seconds: 48,
        subtitle_text: '完成时更强调结果和对现在的影响。',
        created_at: nowISO()
      }
    ],
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 3,
    title: 'Python 列表与字典',
    content: '列表推导式、字典常见方法与时间复杂度。',
    note_type: 'text',
    video_id: 3,
    tags: ['Python', '数据结构'],
    keywords: ['列表', '字典'],
    timestamps: [
      {
        id: 3,
        note_id: 3,
        time_seconds: 92,
        subtitle_text: '列表适合顺序访问，字典适合键查找。',
        created_at: nowISO()
      }
    ],
    created_at: nowISO(),
    updated_at: nowISO()
  }
]

const clone = (value) => JSON.parse(JSON.stringify(value))
const normalizeModel = (value) => String(value || '').trim().toLowerCase() || 'base'
const extractFormModel = (formData) => normalizeModel(formData?.get?.('model'))
const normalizeText = (value) => String(value || '').trim()
const normalizeTagList = (value) => {
  const source = Array.isArray(value) ? value : String(value || '').split(',')
  const seen = new Set()
  return source
    .map((item) => normalizeText(item))
    .filter((item) => {
      if (!item || seen.has(item)) return false
      seen.add(item)
      return true
    })
}
const buildTimestamp = (noteId, payload) => ({
  id: noteTimestampAutoId++,
  note_id: Number(noteId),
  time_seconds: Math.max(0, Number(payload?.time_seconds || 0)),
  subtitle_text: normalizeText(payload?.subtitle_text),
  created_at: nowISO()
})
const decorateNote = (note) => {
  const cloned = clone(note)
  const video = findVideo(cloned.video_id)
  cloned.video_title = video?.title || null
  cloned.tags = Array.isArray(cloned.tags) ? cloned.tags : []
  cloned.keywords = Array.isArray(cloned.keywords) ? cloned.keywords : []
  cloned.timestamps = Array.isArray(cloned.timestamps) ? cloned.timestamps : []
  return cloned
}

const mockResponse = (data) =>
  Promise.resolve({
    data,
    status: 200,
    headers: { 'x-edumind-ui-only': 'true' }
  })

const findVideo = (videoId) => videos.find((item) => Number(item.id) === Number(videoId))

const tickVideoProgress = (video) => {
  if (!video) return
  const status = String(video.status || '')
  if (!['pending', 'processing', 'downloading'].includes(status)) return

  const increment = Math.floor(Math.random() * 18) + 9
  const nextProgress = Math.min(100, Number(video.process_progress || 0) + increment)
  video.process_progress = nextProgress

  if (nextProgress >= 100) {
    video.status = 'completed'
    video.current_step = `分析完成（${video.effective_model || video.requested_model || 'base'}）`
    video.summary =
      video.summary || 'UI 模式示例摘要：本视频已完成转写、摘要与标签提取，可继续播放与问答。'
    video.tags = Array.isArray(video.tags) && video.tags.length > 0 ? video.tags : ['课程重点', '字幕转写', '学习复盘']
    video.updated_at = nowISO()
    return
  }

  video.status = 'processing'
  if (nextProgress < 35) video.current_step = '队列处理中'
  else if (nextProgress < 70) video.current_step = '语音识别中'
  else video.current_step = '生成摘要与标签'
  video.updated_at = nowISO()
}

const sortByUpdatedDesc = (list) =>
  [...list].sort((a, b) => new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0))

const normalizePhone = (value) => {
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.startsWith('86') && digits.length === 13) return digits.slice(2)
  return digits
}

const looksLikeEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim().toLowerCase())
const fileToDataUrl = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('头像读取失败（UI 模式）'))
    reader.readAsDataURL(file)
  })

export const mockLogin = (account) => {
  const raw = String(account || '').trim()
  const phone = normalizePhone(raw)
  const email = looksLikeEmail(raw) ? raw.toLowerCase() : null
  const username = email ? email.split('@')[0] : phone ? `user_${phone.slice(-4)}` : 'demo_user'
  mockUser = {
    ...mockUser,
    username,
    email: email || null,
    phone: email ? null : phone || mockUser.phone,
    login_count: Number(mockUser.login_count || 0) + 1
  }
  mockToken = `ui-token-${Date.now()}`
  return mockResponse({ success: true, user: clone(mockUser), token: mockToken, message: 'UI 模式登录成功' })
}

export const mockRegister = (userData) => {
  const email = userData?.email ? String(userData.email).trim().toLowerCase() : null
  const phone = userData?.phone ? normalizePhone(userData.phone) : null
  const username = email ? email.split('@')[0] : phone ? `user_${phone.slice(-4)}` : 'new_user'
  mockUser = { ...mockUser, username, email, phone }
  return mockResponse({ success: true, user: clone(mockUser), message: 'UI 模式注册成功' })
}

export const mockMe = () => mockResponse({ success: true, user: clone(mockUser), token: mockToken })

export const mockLogout = () => mockResponse({ success: true, message: 'UI 模式已退出' })

export const mockUpdateProfile = (payload = {}) => {
  const nextUsername = String(payload?.username || '').trim()
  if (nextUsername) {
    mockUser = { ...mockUser, username: nextUsername }
  }
  return mockResponse({ success: true, user: clone(mockUser), message: 'UI 模式：资料已更新' })
}

export const mockUploadAvatar = async (file) => {
  if (!file) throw new Error('请选择头像文件（UI 模式）')
  const avatar = await fileToDataUrl(file)
  mockUser = { ...mockUser, avatar }
  return mockResponse({ success: true, user: clone(mockUser), message: 'UI 模式：头像已更新' })
}

export const mockGetVideoList = (page = 1, perPage = 10) => {
  sortByUpdatedDesc(videos).forEach((item) => tickVideoProgress(item))
  const safePage = Math.max(1, Number(page) || 1)
  const safePerPage = Math.max(1, Number(perPage) || 10)
  const start = (safePage - 1) * safePerPage
  const list = sortByUpdatedDesc(videos).slice(start, start + safePerPage)
  return mockResponse({ videos: clone(list), total: videos.length, page: safePage, per_page: safePerPage })
}

export const mockGetVideo = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  tickVideoProgress(video)
  return mockResponse({ video: clone(video) })
}

export const mockGetVideoStatus = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  tickVideoProgress(video)
  return mockResponse({
    status: video.status,
    progress: Number(video.process_progress || 0),
    current_step: video.current_step || '',
    requested_model: video.requested_model || 'base',
    effective_model: video.effective_model || video.requested_model || 'base'
  })
}

export const mockProcessVideo = (videoId, options = {}) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  const model = normalizeModel(options?.model)
  video.status = 'pending'
  video.process_progress = 3
  video.current_step = `排队中（${model}）`
  video.requested_model = model
  video.effective_model = model
  video.summary = ''
  video.tags = []
  video.updated_at = nowISO()
  return mockResponse({ success: true, message: 'UI 模式：已提交处理任务', video_id: video.id })
}

export const mockDeleteVideo = (videoId) => {
  const index = videos.findIndex((item) => Number(item.id) === Number(videoId))
  if (index < 0) return Promise.reject(new Error('视频不存在（UI 模式）'))
  videos.splice(index, 1)
  return mockResponse({ success: true, message: 'UI 模式：已删除视频' })
}

export const mockUploadLocalVideo = (formData, { onUploadProgress } = {}) =>
  new Promise((resolve) => {
    const file = formData?.get?.('file')
    const model = extractFormModel(formData)
    const total = Number(file?.size || 5 * 1024 * 1024)
    const step = Math.max(Math.floor(total / 5), 256 * 1024)
    let loaded = 0

    const timer = setInterval(() => {
      loaded = Math.min(total, loaded + step)
      if (onUploadProgress) onUploadProgress({ loaded, total })
      if (loaded < total) return

      clearInterval(timer)
      videoAutoId += 1
      const id = videoAutoId
      const baseTitle = String(file?.name || `新上传视频-${id}`).replace(/\.[^/.]+$/, '')
      const created = {
        id,
        title: baseTitle,
        status: 'uploaded',
        process_progress: 0,
        current_step: `已上传（${model}）`,
        requested_model: model,
        effective_model: model,
        summary: '',
        tags: [],
        created_at: nowISO(),
        updated_at: nowISO()
      }
      videos.unshift(created)
      resolve({
        data: {
          success: true,
          message: 'UI 模式：本地视频上传成功',
          video_id: id,
          data: clone(created)
        },
        status: 200,
        headers: { 'x-edumind-ui-only': 'true' }
      })
    }, 80)
  })

export const mockUploadVideoUrl = (payload) => {
  videoAutoId += 1
  const id = videoAutoId
  const title = String(payload?.url || `链接视频-${id}`).slice(0, 80)
  const model = normalizeModel(payload?.model)
  const created = {
    id,
    title,
    status: 'pending',
    process_progress: 0,
    current_step: `排队中（${model}）`,
    requested_model: model,
    effective_model: model,
    summary: '',
    tags: [],
    created_at: nowISO(),
    updated_at: nowISO()
  }
  videos.unshift(created)
  return mockResponse({ success: true, message: 'UI 模式：链接提交成功', video_id: id, data: clone(created) })
}

export const mockGenerateVideoSummary = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  video.summary = video.summary || 'UI 模式摘要：本视频已完成重点提炼，可继续查看标签与问答。'
  video.updated_at = nowISO()
  return mockResponse({ success: true, summary: video.summary })
}

export const mockGenerateVideoTags = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  video.tags = Array.isArray(video.tags) && video.tags.length > 0 ? video.tags : ['重点知识', '视频复盘', '学习标签']
  video.updated_at = nowISO()
  return mockResponse({ success: true, tags: clone(video.tags) })
}

export const mockGetNotes = (params = {}) => {
  const videoId = Number(params?.video_id || 0)
  const tag = normalizeText(params?.tag)
  const search = normalizeText(params?.search).toLowerCase()
  const noteType = normalizeText(params?.note_type)

  const filtered = sortByUpdatedDesc(notes).filter((note) => {
    if (videoId > 0 && Number(note.video_id || 0) !== videoId) return false
    if (tag && !normalizeTagList(note.tags).includes(tag)) return false
    if (noteType && String(note.note_type || 'text') !== noteType) return false
    if (search) {
      const searchBody = [
        note.title,
        note.content,
        ...(Array.isArray(note.tags) ? note.tags : []),
        ...(Array.isArray(note.keywords) ? note.keywords : [])
      ]
        .join(' ')
        .toLowerCase()
      if (!searchBody.includes(search)) return false
    }
    return true
  })

  return mockResponse({ notes: filtered.map((note) => decorateNote(note)) })
}

export const mockGetNote = (noteId) => {
  const note = notes.find((item) => Number(item.id) === Number(noteId))
  if (!note) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  return mockResponse({ note: decorateNote(note) })
}

export const mockCreateNote = (data) => {
  const nextNoteId = noteAutoId
  noteAutoId += 1
  const tags = normalizeTagList(data?.tags)
  const timestamps = Array.isArray(data?.timestamps)
    ? data.timestamps.map((item) => buildTimestamp(nextNoteId, item))
    : []
  const created = {
    id: nextNoteId,
    title: String(data?.title || '未命名笔记'),
    content: String(data?.content || ''),
    note_type: String(data?.note_type || 'text'),
    video_id: data?.video_id ? Number(data.video_id) : null,
    tags,
    keywords: [],
    timestamps,
    created_at: nowISO(),
    updated_at: nowISO()
  }
  notes.unshift(created)
  return mockResponse({ success: true, note: decorateNote(created), message: 'UI 模式：已创建笔记' })
}

export const mockUpdateNote = (noteId, data) => {
  const note = notes.find((item) => Number(item.id) === Number(noteId))
  if (!note) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  if (Object.prototype.hasOwnProperty.call(data || {}, 'title')) note.title = String(data?.title || note.title)
  if (Object.prototype.hasOwnProperty.call(data || {}, 'content')) note.content = String(data?.content ?? note.content)
  if (Object.prototype.hasOwnProperty.call(data || {}, 'note_type')) note.note_type = String(data?.note_type || 'text')
  if (Object.prototype.hasOwnProperty.call(data || {}, 'video_id')) {
    note.video_id = data?.video_id ? Number(data.video_id) : null
  }
  if (Object.prototype.hasOwnProperty.call(data || {}, 'tags')) {
    note.tags = normalizeTagList(data?.tags)
  }
  note.updated_at = nowISO()
  return mockResponse({ success: true, note: decorateNote(note), message: 'UI 模式：已更新笔记' })
}

export const mockAddNoteTimestamp = (noteId, data = {}) => {
  const note = notes.find((item) => Number(item.id) === Number(noteId))
  if (!note) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  const timestamp = buildTimestamp(noteId, data)
  note.timestamps = Array.isArray(note.timestamps) ? note.timestamps : []
  note.timestamps.push(timestamp)
  note.updated_at = nowISO()
  return mockResponse({ success: true, data: clone(timestamp), message: 'UI 模式：已新增时间点' })
}

export const mockDeleteNoteTimestamp = (noteId, timestampId) => {
  const note = notes.find((item) => Number(item.id) === Number(noteId))
  if (!note) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  const index = (Array.isArray(note.timestamps) ? note.timestamps : []).findIndex(
    (item) => Number(item.id) === Number(timestampId)
  )
  if (index < 0) return Promise.reject(new Error('时间点不存在（UI 模式）'))
  note.timestamps.splice(index, 1)
  note.updated_at = nowISO()
  return mockResponse({ success: true, message: 'UI 模式：已删除时间点' })
}

export const mockGetNoteTags = () => {
  const counter = new Map()
  notes.forEach((note) => {
    normalizeTagList(note.tags).forEach((tag) => {
      counter.set(tag, Number(counter.get(tag) || 0) + 1)
    })
  })
  const data = [...counter.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'zh-Hans-CN'))
    .map(([name, count]) => ({ name, count }))
  return mockResponse({ data })
}

export const mockDeleteNote = (noteId) => {
  const index = notes.findIndex((item) => Number(item.id) === Number(noteId))
  if (index < 0) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  notes.splice(index, 1)
  return mockResponse({ success: true, message: 'UI 模式：已删除笔记' })
}

export const mockAskQuestion = ({ question, video_id, provider = 'qwen', deep_thinking = false }) => {
  const q = String(question || '').trim()
  const prefix = video_id ? `视频 ${video_id}` : '通用问答'
  const providerText = provider === 'deepseek' ? 'DeepSeek' : '通义千问'
  const modeText = provider === 'deepseek' ? (deep_thinking ? '先思考再回答' : '直接回答') : '标准回答'
  const answer = q
    ? `【UI 模式】这是 ${prefix} 的占位回复，当前模型通道为 ${providerText}（${modeText}）：你问的是“${q}”。后续接入真实 AI 接口后会返回正式答案。`
    : '【UI 模式】请输入问题内容。'
  return mockResponse({ answer })
}
