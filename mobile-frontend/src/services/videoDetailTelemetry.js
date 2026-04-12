/**
 * 视频详情页结构化埋点：控制台 + CustomEvent，便于 WKWebView 原生侧订阅。
 * @param {string} event
 * @param {Record<string, unknown>} payload
 */
export function emitVideoDetailTelemetry(event, payload = {}) {
  const detail = {
    scope: 'video_detail',
    event,
    ts: Date.now(),
    ...payload
  }
  if (typeof window !== 'undefined') {
    try {
      window.dispatchEvent(new CustomEvent('edumind:telemetry', { detail }))
    } catch {
      /* ignore */
    }
    if (import.meta.env?.DEV) {
      // eslint-disable-next-line no-console
      console.info('[VideoDetailTelemetry]', event, detail)
    }
  }
}
