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

const subtitleLibrary = {
  1: [
    { id: 101, video_id: 1, start_time: 8, end_time: 18, text: '导数本质上描述函数变化率，可以理解为切线斜率的极限。', source: 'asr', language: 'zh' },
    { id: 102, video_id: 1, start_time: 22, end_time: 34, text: '当自变量增量趋近于零时，平均变化率就逼近瞬时变化率。', source: 'asr', language: 'zh' },
    { id: 103, video_id: 1, start_time: 40, end_time: 52, text: '几何意义上，导数对应曲线在某一点的切线斜率。', source: 'asr', language: 'zh' },
    { id: 104, video_id: 1, start_time: 60, end_time: 74, text: '常见求导法则包括常数法则、幂函数法则和和差法则。', source: 'asr', language: 'zh' },
    { id: 105, video_id: 1, start_time: 76, end_time: 92, text: '复合函数求导要用链式法则，先求外层再乘内层导数。', source: 'asr', language: 'zh' },
    { id: 106, video_id: 1, start_time: 96, end_time: 110, text: '遇到隐函数求导时，要对两边同时求导并整理 dy/dx。', source: 'asr', language: 'zh' }
  ],
  2: [
    { id: 201, video_id: 2, start_time: 10, end_time: 24, text: '一般现在时强调习惯、事实和经常发生的动作。', source: 'asr', language: 'zh' },
    { id: 202, video_id: 2, start_time: 28, end_time: 42, text: '一般过去时用于描述已经完成并结束的动作。', source: 'asr', language: 'zh' },
    { id: 203, video_id: 2, start_time: 45, end_time: 60, text: '现在完成时更强调结果以及对现在的影响。', source: 'asr', language: 'zh' },
    { id: 204, video_id: 2, start_time: 64, end_time: 80, text: '判断时态时要看时间状语和语境，而不是只背固定词。', source: 'asr', language: 'zh' }
  ],
  3: [
    { id: 301, video_id: 3, start_time: 12, end_time: 26, text: '列表适合按顺序存储和遍历，支持通过索引访问元素。', source: 'asr', language: 'zh' },
    { id: 302, video_id: 3, start_time: 30, end_time: 46, text: '字典适合键值映射场景，查找和更新通常更高效。', source: 'asr', language: 'zh' },
    { id: 303, video_id: 3, start_time: 50, end_time: 68, text: '选择列表还是字典，要根据访问方式和数据组织方式来定。', source: 'asr', language: 'zh' }
  ]
}

const semanticSubtitleLibrary = {
  1: [
    {
      start_time: 8,
      end_time: 34,
      title: '导数定义',
      text: '导数本质上描述函数变化率，可以理解为切线斜率的极限。当自变量增量趋近于零时，平均变化率就逼近瞬时变化率。'
    },
    {
      start_time: 40,
      end_time: 52,
      title: '几何意义',
      text: '几何意义上，导数对应曲线在某一点的切线斜率。'
    },
    {
      start_time: 60,
      end_time: 110,
      title: '求导法则',
      text: '常见求导法则包括常数法则、幂函数法则和和差法则。复合函数求导要用链式法则，先求外层再乘内层导数。遇到隐函数求导时，要对两边同时求导并整理 dy/dx。'
    }
  ],
  2: [
    {
      start_time: 10,
      end_time: 42,
      title: '基础时态',
      text: '一般现在时强调习惯、事实和经常发生的动作。一般过去时用于描述已经完成并结束的动作。'
    },
    {
      start_time: 45,
      end_time: 80,
      title: '完成时辨析',
      text: '现在完成时更强调结果以及对现在的影响。判断时态时要看时间状语和语境，而不是只背固定词。'
    }
  ],
  3: [
    {
      start_time: 12,
      end_time: 46,
      title: '列表与字典',
      text: '列表适合按顺序存储和遍历，支持通过索引访问元素。字典适合键值映射场景，查找和更新通常更高效。'
    },
    {
      start_time: 50,
      end_time: 68,
      title: '结构选择',
      text: '选择列表还是字典，要根据访问方式和数据组织方式来定。'
    }
  ]
}

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
const findVideoSubtitles = (videoId) => clone(subtitleLibrary[Number(videoId)] || [])
const findMergedVideoSubtitles = (videoId) => clone(semanticSubtitleLibrary[Number(videoId)] || [])

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
  [...list].sort(
    (a, b) => new Date(b?.updated_at || b?.created_at || 0) - new Date(a?.updated_at || a?.created_at || 0)
  )

const recommendationScenes = [
  {
    value: 'home',
    label: '首页推荐',
    description: '适合首页首屏，优先给出当前最值得继续跟进的视频。',
    requires_seed: false
  },
  {
    value: 'continue',
    label: '继续学习',
    description: '优先返回处理中、失败待补跑和最近进入的视频。',
    requires_seed: false
  },
  {
    value: 'review',
    label: '复盘推荐',
    description: '优先返回已完成且适合整理笔记的视频。',
    requires_seed: false
  },
  {
    value: 'related',
    label: '相似内容',
    description: '根据 seed 视频推荐主题相关的视频。',
    requires_seed: true
  }
]

const recommendationTime = (video) => video.upload_time || video.updated_at || video.created_at || nowISO()
const externalRecommendationCatalog = [
  {
    key: 'bilibili-derivative-review',
    title: 'B站·导数与函数单调性综合串讲',
    source_label: 'B站',
    url: 'https://www.bilibili.com/video/BV1xk4y1x7m9',
    summary: '围绕导数、函数单调性和常见压轴题型做集中复盘。',
    tags: ['导数定义', '函数', '题型复盘'],
    published_at: nowISO()
  },
  {
    key: 'youtube-python-structures',
    title: 'YouTube · Python Data Structures Crash Review',
    source_label: 'YouTube',
    url: 'https://www.youtube.com/watch?v=python-structures-demo',
    summary: '用更短的节奏复盘列表、字典和集合在学习项目里的典型用法。',
    tags: ['Python', '数据结构', '列表'],
    published_at: nowISO()
  },
  {
    key: 'mooc-english-tense',
    title: '中国大学慕课 · 英语时态专项精讲',
    source_label: '中国大学慕课',
    url: 'https://www.icourse163.org/learn/FOREIGN-1001',
    summary: '聚焦一般过去时、现在完成时与写作语境辨析，适合配合已上传语法视频继续学习。',
    tags: ['英语', '时态', '写作'],
    published_at: nowISO()
  }
]

const resolveMockRecommendationSubject = (video) => {
  const title = String(video?.title || '').trim()
  if (/数学|导数|几何|函数/.test(title)) return '数学'
  if (/英语|语法|时态/.test(title)) return '英语'
  if (/python|数据结构|编程/i.test(title)) return '计算机'
  if (/物理|力学/.test(title)) return '物理'
  if (/历史/.test(title)) return '历史'
  return '综合学习'
}

const buildMockImportTarget = (candidate) => {
  const source = encodeURIComponent(String(candidate?.source_label || '站外推荐'))
  const url = encodeURIComponent(String(candidate?.url || ''))
  return `/upload?mode=url&url=${url}&source=${source}`
}

const buildMockRecommendationSources = (items) => {
  const bucket = new Map()
  items.forEach((item) => {
    const isExternal = Boolean(item?.is_external)
    const sourceType = isExternal ? 'external' : 'internal'
    const provider = isExternal
      ? String(item?.provider || item?.source_label || 'external')
      : String(item?.upload_source || 'video_library')
    const sourceLabel = isExternal ? String(item?.source_label || '站外候选') : String(item?.upload_source_label || '站内视频')
    const key = `${sourceType}:${provider}`
    const current = bucket.get(key) || { source_type: sourceType, provider, source_label: sourceLabel, count: 0 }
    current.count += 1
    bucket.set(key, current)
  })
  return Array.from(bucket.values())
}

const buildMockExternalProviderSummary = (includeExternal) => {
  if (!includeExternal) return []
  return externalRecommendationCatalog.map((candidate) => ({
    provider: String(candidate.source_label || '站外候选').toLowerCase().replace(/[^\w\u4e00-\u9fa5]+/g, '_'),
    source_label: String(candidate.source_label || '站外候选'),
    status: 'success',
    candidate_count: 1,
    error_message: '',
    latency_ms: 120
  }))
}

const buildMockExternalQuery = (scene, seedVideo) => {
  const tags = Array.isArray(seedVideo?.tags) ? seedVideo.tags.slice(0, 4) : []
  const subject = resolveMockRecommendationSubject(seedVideo)
  const primaryTopic = tags[0] || String(seedVideo?.title || '当前主题').trim() || '当前主题'
  return {
    query_text: `${subject} ${primaryTopic}`.trim(),
    subject,
    primary_topic: primaryTopic,
    preferred_tags: tags
  }
}

const buildMockRecommendationPayload = ({ scene, limit, includeExternal, seedVideo }) => {
  const ranked = sortByUpdatedDesc(videos)
    .filter((video) => !seedVideo || Number(video.id) !== Number(seedVideo.id))
    .map((video) => {
      if (scene === 'continue' || scene === 'home') {
        if (['processing', 'pending', 'downloading'].includes(String(video.status || ''))) {
          return buildMockRecommendationItem(video, 'continue', '继续跟进', 95)
        }
        if (String(video.status || '') === 'failed') {
          return buildMockRecommendationItem(video, 'retry', '建议补跑', 82)
        }
      }

      if (scene === 'review' && String(video.status || '') === 'completed') {
        return buildMockRecommendationItem(video, 'review', '适合复盘', 76)
      }

      if (scene === 'related' && seedVideo) {
        const seedTags = new Set(Array.isArray(seedVideo.tags) ? seedVideo.tags : [])
        const overlap = (Array.isArray(video.tags) ? video.tags : []).filter((tag) => seedTags.has(tag))
        return buildMockRecommendationItem(
          video,
          overlap.length > 0 ? 'related' : 'recent',
          overlap.length > 0 ? '主题相关' : '最近内容',
          overlap.length > 0 ? 88 + overlap.length : 40
        )
      }

      return buildMockRecommendationItem(video, 'recent', '最近内容', 56)
    })

  const externalItems = includeExternal ? buildMockExternalCandidates(scene, seedVideo) : []
  const items = [...ranked, ...externalItems]
    .sort((a, b) => b.recommendation_score - a.recommendation_score)
    .slice(0, limit)
  const internalItemCount = items.filter((item) => !item?.is_external).length
  const externalItemCount = items.filter((item) => item?.is_external).length

  return {
    message: '获取推荐视频成功',
    contract_version: '2',
    scene,
    strategy: 'ui_mock_recommendation_v2',
    personalized: true,
    fallback_used: false,
    seed_video_id: seedVideo?.id || null,
    internal_item_count: internalItemCount,
    external_item_count: externalItemCount,
    external_failed_provider_count: 0,
    external_fetch_failed: false,
    sources: buildMockRecommendationSources(items),
    external_query: includeExternal ? buildMockExternalQuery(scene, seedVideo) : null,
    external_providers: buildMockExternalProviderSummary(includeExternal),
    items
  }
}

const buildMockUploadRecommendations = (video) => {
  const hasSeedSignal = Boolean(String(video?.title || '').trim() || String(video?.summary || '').trim() || (Array.isArray(video?.tags) && video.tags.length > 0))
  return buildMockRecommendationPayload({
    scene: hasSeedSignal ? 'related' : 'home',
    limit: 4,
    includeExternal: false,
    seedVideo: hasSeedSignal ? video : null
  })
}

const buildMockRecommendationItem = (video, reasonCode, reasonLabel, score) => ({
  id: Number(video.id),
  title: String(video.title || '未命名视频'),
  status: String(video.status || 'uploaded'),
  upload_time: recommendationTime(video),
  summary: '',
  tags: [],
  process_progress: Number(video.process_progress || 0),
  current_step: String(video.current_step || ''),
  processing_origin: String(video.processing_origin || 'online_backend'),
  processing_origin_label: String(video.processing_origin_label || '在线处理'),
  upload_source: String(video.upload_source || 'local_file'),
  upload_source_label: String(video.upload_source_label || '本地上传'),
  recommendation_score: Number(score || 0),
  reason_code: reasonCode,
  reason_label: reasonLabel,
  reason_text: '',
  subject: resolveMockRecommendationSubject(video),
  cluster_key: (Array.isArray(video.tags) && video.tags[0]) ? String(video.tags[0]) : resolveMockRecommendationSubject(video),
  action_type: 'route',
  action_label: video.processing_origin === 'ios_offline' ? '打开本地结果' : '打开详情',
  action_target: video.processing_origin === 'ios_offline'
    ? `/local-transcripts/${video.task_id || video.id}`
    : `/videos/${video.id}`
})

const buildMockExternalRecommendationItem = (candidate, reasonCode, reasonLabel, score) => ({
  title: String(candidate.title || '站外候选'),
  status: '',
  upload_time: candidate.published_at || nowISO(),
  summary: '',
  tags: [],
  process_progress: 0,
  current_step: '',
  processing_origin: 'external_candidate',
  processing_origin_label: '站外候选',
  upload_source: 'external_candidate',
  upload_source_label: String(candidate.source_label || '站外候选'),
  recommendation_score: Number(score || 0),
  reason_code: reasonCode,
  reason_label: reasonLabel,
  reason_text: '',
  is_external: true,
  item_type: 'external_candidate',
  source_label: String(candidate.source_label || '站外候选'),
  external_url: String(candidate.url || ''),
  external_source_label: String(candidate.source_label || '站外候选'),
  subject: resolveMockRecommendationSubject({ title: candidate.title }),
  cluster_key: Array.isArray(candidate.tags) && candidate.tags[0] ? String(candidate.tags[0]) : resolveMockRecommendationSubject({ title: candidate.title }),
  provider: String(candidate.source_label || '站外候选').toLowerCase().replace(/[^\w\u4e00-\u9fa5]+/g, '_'),
  can_import: true,
  import_hint: '点导入后会带着链接进入上传链路，不会直接当作已入库视频播放。',
  action_type: 'route',
  action_label: '导入学习',
  action_target: buildMockImportTarget(candidate),
  action_api: '/api/recommendations/import-external',
  action_method: 'POST'
})

const buildMockExternalCandidates = (scene, seedVideo) => {
  const seedTags = new Set(Array.isArray(seedVideo?.tags) ? seedVideo.tags : [])
  return externalRecommendationCatalog.map((candidate) => {
    const overlap = candidate.tags.filter((tag) => seedTags.has(tag))
    if (scene === 'related' && seedVideo) {
      return buildMockExternalRecommendationItem(
        candidate,
        overlap.length > 0 ? 'external_related' : 'external_recent',
        overlap.length > 0 ? '站外同主题' : '站外扩展',
        overlap.length > 0 ? 79 + overlap.length : 48
      )
    }

    if (scene === 'review') {
      return buildMockExternalRecommendationItem(
        candidate,
        'external_review',
        '站外复盘',
        68
      )
    }

    if (scene === 'continue') {
      return buildMockExternalRecommendationItem(
        candidate,
        'external_continue',
        '站外延伸',
        64
      )
    }

    return buildMockExternalRecommendationItem(
      candidate,
      'external_discovery',
      '站外发现',
      62
    )
  })
}

export const mockGetRecommendationScenes = () =>
  mockResponse({ message: '获取推荐场景成功', scenes: clone(recommendationScenes) })

export const mockGetVideoRecommendations = (params = {}) => {
  const scene = String(params?.scene || 'home').trim().toLowerCase() || 'home'
  const limit = Math.max(1, Math.min(12, Number(params?.limit || 4) || 4))
  const includeExternal = ['1', 'true', 'yes'].includes(String(params?.include_external || '').trim().toLowerCase())
  const seedVideoId = Number(params?.seed_video_id || 0) || null
  const seedVideo = seedVideoId ? findVideo(seedVideoId) : null

  if (scene === 'related' && !seedVideo) {
    return Promise.reject({
      response: {
        status: 422,
        data: { detail: 'scene=related 时必须传入 seed_video_id' }
      }
    })
  }

  return mockResponse(buildMockRecommendationPayload({ scene, limit, includeExternal, seedVideo }))
}

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
          data: clone(created),
          recommendations: buildMockUploadRecommendations(created)
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
  return mockResponse({
    success: true,
    message: 'UI 模式：链接提交成功',
    video_id: id,
    data: clone(created),
    recommendations: buildMockUploadRecommendations(created)
  })
}

export const mockImportExternalRecommendation = (payload) => mockUploadVideoUrl(payload)

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

export const mockGetVideoSubtitles = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  return mockResponse({
    status: 'success',
    video_id: Number(videoId),
    video_status: String(video.status || ''),
    subtitles: findVideoSubtitles(videoId)
  })
}

export const mockGetMergedVideoSubtitles = (videoId) => {
  const video = findVideo(videoId)
  if (!video) return Promise.reject(new Error('视频不存在（UI 模式）'))
  return mockResponse(findMergedVideoSubtitles(videoId))
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
