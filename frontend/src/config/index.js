// API基础URL配置
export const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 其他全局配置
export const config = {
  // 视频播放器配置
  player: {
    defaultSubtitleLanguage: 'zh',
    subtitleFontSize: '20px',
    subtitleBackgroundColor: 'rgba(0, 0, 0, 0.7)',
  }
}
