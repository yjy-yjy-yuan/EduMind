const nowISO = () => new Date().toISOString()

let videoAutoId = 6
let noteAutoId = 4
let mockToken = 'ui-only-token'
let mockUser = {
  id: 1,
  username: 'demo_user',
  email: 'demo@edumind.app'
}

const videos = [
  {
    id: 1,
    title: '高等数学导数专题',
    status: 'completed',
    process_progress: 100,
    current_step: '分析完成',
    summary: '本节梳理导数定义、几何意义与常见求导法则。',
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 2,
    title: '英语语法时态精讲',
    status: 'processing',
    process_progress: 42,
    current_step: '语音识别中',
    summary: '',
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 3,
    title: 'Python 数据结构入门',
    status: 'failed',
    process_progress: 18,
    current_step: '处理失败',
    summary: '',
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 4,
    title: '中国近代史复习',
    status: 'pending',
    process_progress: 0,
    current_step: '排队中',
    summary: '',
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 5,
    title: '物理力学专题讲解',
    status: 'uploaded',
    process_progress: 0,
    current_step: '已上传',
    summary: '',
    created_at: nowISO(),
    updated_at: nowISO()
  }
]

const notes = [
  {
    id: 1,
    title: '导数速记卡',
    content: '基本求导公式、复合函数求导、隐函数求导。',
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 2,
    title: '英语时态易错点',
    content: '现在完成时与一般过去时的常见语境区分。',
    created_at: nowISO(),
    updated_at: nowISO()
  },
  {
    id: 3,
    title: 'Python 列表与字典',
    content: '列表推导式、字典常见方法与时间复杂度。',
    created_at: nowISO(),
    updated_at: nowISO()
  }
]

const clone = (value) => JSON.parse(JSON.stringify(value))

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
    video.current_step = '分析完成'
    video.summary =
      video.summary || 'UI 模式示例摘要：本视频已完成转写、摘要与标签提取，可继续播放与问答。'
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

export const mockLogin = (username) => {
  const name = String(username || '').trim() || 'demo_user'
  mockUser = { ...mockUser, username: name, email: `${name}@edumind.app` }
  mockToken = `ui-token-${Date.now()}`
  return mockResponse({ success: true, user: clone(mockUser), token: mockToken, message: 'UI 模式登录成功' })
}

export const mockRegister = (userData) => {
  const name = String(userData?.username || '').trim() || 'new_user'
  mockUser = { ...mockUser, username: name, email: String(userData?.email || `${name}@edumind.app`) }
  return mockResponse({ success: true, user: clone(mockUser), message: 'UI 模式注册成功' })
}

export const mockMe = () => mockResponse({ success: true, user: clone(mockUser), token: mockToken })

export const mockLogout = () => mockResponse({ success: true, message: 'UI 模式已退出' })

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
    current_step: video.current_step || ''
  })
}

export const mockProcessVideo = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  video.status = 'pending'
  video.process_progress = 3
  video.current_step = '排队中'
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
        current_step: '已上传',
        summary: '',
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
  const created = {
    id,
    title,
    status: 'pending',
    process_progress: 0,
    current_step: '排队中',
    summary: '',
    created_at: nowISO(),
    updated_at: nowISO()
  }
  videos.unshift(created)
  return mockResponse({ success: true, message: 'UI 模式：链接提交成功', video_id: id, data: clone(created) })
}

export const mockGetNotes = () => mockResponse({ notes: clone(sortByUpdatedDesc(notes)) })

export const mockGetNote = (noteId) => {
  const note = notes.find((item) => Number(item.id) === Number(noteId))
  if (!note) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  return mockResponse({ note: clone(note) })
}

export const mockCreateNote = (data) => {
  noteAutoId += 1
  const created = {
    id: noteAutoId,
    title: String(data?.title || '未命名笔记'),
    content: String(data?.content || ''),
    created_at: nowISO(),
    updated_at: nowISO()
  }
  notes.unshift(created)
  return mockResponse({ success: true, note: clone(created), message: 'UI 模式：已创建笔记' })
}

export const mockUpdateNote = (noteId, data) => {
  const note = notes.find((item) => Number(item.id) === Number(noteId))
  if (!note) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  note.title = String(data?.title || note.title)
  note.content = String(data?.content ?? note.content)
  note.updated_at = nowISO()
  return mockResponse({ success: true, note: clone(note), message: 'UI 模式：已更新笔记' })
}

export const mockDeleteNote = (noteId) => {
  const index = notes.findIndex((item) => Number(item.id) === Number(noteId))
  if (index < 0) return Promise.reject(new Error('笔记不存在（UI 模式）'))
  notes.splice(index, 1)
  return mockResponse({ success: true, message: 'UI 模式：已删除笔记' })
}

export const mockAskQuestion = ({ question, video_id }) => {
  const q = String(question || '').trim()
  const prefix = video_id ? `视频 ${video_id}` : '通用问答'
  const answer = q
    ? `【UI 模式】这是 ${prefix} 的占位回复：你问的是“${q}”。后续接入真实 AI 接口后会返回正式答案。`
    : '【UI 模式】请输入问题内容。'
  return mockResponse({ answer })
}
