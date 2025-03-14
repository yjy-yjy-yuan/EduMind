// API基础URL配置
export const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
export const API_BASE_URL = baseUrl // 添加 API_BASE_URL 导出

// 其他全局配置
export const config = {
  // 视频播放器配置
  player: {
    defaultSubtitleLanguage: 'zh',
    subtitleFontSize: '20px',
    subtitleBackgroundColor: 'rgba(0, 0, 0, 0.7)',
  }
}
