/**
 * 语义搜索默认参数与文案（首页 /search 入口与 Search 页共用）
 *
 * 路由 query 中 `scope` 的取值与「跨视频语义搜索」范围一致时，均使用 DEFAULT_SEARCH_SCOPE（单一来源，避免与 SEARCH_ROUTE_SCOPE_* 重复）。
 */
export const DEFAULT_SEARCH_SCOPE = 'all'
export const DEFAULT_SEARCH_LIMIT = 20
export const DEFAULT_SEARCH_THRESHOLD = 0.5

/** 路由 query：首页进入全局搜索时携带 scope=DEFAULT_SEARCH_SCOPE */
export const SEARCH_ROUTE_SCOPE_QUERY = 'scope'
/** 首页输入框预填到搜索页的关键词参数 */
export const SEARCH_ROUTE_PREFILL_QUERY = 'q'

/** 跨视频范围一句说明（首页说明、搜索页范围选项与锁定条共用；仅覆盖已建立语义索引的内容） */
export const SEARCH_COPY_ALL_SCOPE_HINT = '在我的全部已索引视频中搜索'

/** 首页：跨视频语义搜索卡片 */
export const SEARCH_COPY_HOME_SEMANTIC_TITLE = '跨视频语义搜索'
export const SEARCH_COPY_HOME_SEMANTIC_DESCRIPTION = SEARCH_COPY_ALL_SCOPE_HINT
export const SEARCH_COPY_HOME_INPUT_PLACEHOLDER = '输入关键词，在全部已索引视频中搜索…'

/** 搜索页：顶栏输入框占位 */
export const SEARCH_COPY_PAGE_INPUT_PLACEHOLDER_ALL = SEARCH_COPY_HOME_INPUT_PLACEHOLDER
export const SEARCH_COPY_PAGE_INPUT_PLACEHOLDER_CURRENT = '输入关键词，在当前视频中搜索…'
/** 搜索页：未锁定「全部已索引」且尚未搜索时的空态 */
export const SEARCH_COPY_EMPTY_STATE_GENERIC = '输入关键词开始搜索'
/** 搜索页：锁定跨视频范围时角标（与已索引语义一致） */
export const SEARCH_COPY_SCOPE_LOCKED_BADGE = '全部已索引视频'

/** 搜索页：操作与状态文案 */
export const SEARCH_COPY_SEARCH_BUTTON = '搜索'
export const SEARCH_COPY_SEARCHING = '搜索中...'
export const SEARCH_COPY_RETRY = '重试'
export const SEARCH_COPY_RESULTS_HEADER_CURRENT = '搜索结果'
export const SEARCH_COPY_RESULTS_HEADER_ALL = '跨视频搜索结果'
export const SEARCH_COPY_NO_RESULTS_TEMPLATE = '未找到与“{query}”相关的内容'
export const SEARCH_COPY_PREVIEW_FALLBACK = '（暂无文本预览）'
export const SEARCH_COPY_PLAY_HINT = '点击播放此片段'
export const SEARCH_COPY_CURRENT_VIDEO_LABEL_NO_CONTEXT = '当前视频（需从详情页进入）'
export const SEARCH_COPY_CURRENT_VIDEO_LABEL_FALLBACK = '当前视频'
export const SEARCH_COPY_CURRENT_VIDEO_LABEL_PREFIX = '当前视频：'

/** 从首页进入且锁定全站范围时，未搜索前的提示 */
export const SEARCH_COPY_EMPTY_STATE_SCOPE_ALL = '输入关键词，在全部已索引视频中搜索'

/** 后端返回无可索引视频时的典型说明（用于展示引导，不用于伪造状态） */
export const SEARCH_COPY_NO_INDEX_GUIDE =
  '上传视频并等待处理与索引完成后，即可跨视频搜索。也可在视频库中打开某个视频，从详情页针对单条内容搜索。'
