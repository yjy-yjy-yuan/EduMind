/**
 * 语义搜索默认参数与文案（首页 /search 入口与 Search 页共用）
 */
export const DEFAULT_SEARCH_SCOPE = 'all'
export const DEFAULT_SEARCH_LIMIT = 20
export const DEFAULT_SEARCH_THRESHOLD = 0.5

/** 路由 query：首页进入全局搜索时携带 */
export const SEARCH_ROUTE_SCOPE_QUERY = 'scope'
export const SEARCH_ROUTE_SCOPE_ALL = 'all'
/** 首页输入框预填到搜索页的关键词参数 */
export const SEARCH_ROUTE_PREFILL_QUERY = 'q'

/** 搜索页：跨视频范围说明（与产品一致） */
export const SEARCH_COPY_ALL_SCOPE_HINT = '在我的全部视频中搜索'

/** 从首页进入且锁定全站范围时，未搜索前的提示 */
export const SEARCH_COPY_EMPTY_STATE_SCOPE_ALL = '输入关键词，在全部已索引视频中搜索'

/** 后端返回无可索引视频时的典型说明（用于展示引导，不用于伪造状态） */
export const SEARCH_COPY_NO_INDEX_GUIDE =
  '上传视频并等待处理与索引完成后，即可跨视频搜索。也可在视频库中打开某个视频，从详情页针对单条内容搜索。'
