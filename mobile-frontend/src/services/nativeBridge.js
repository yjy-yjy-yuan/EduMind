const NATIVE_EVENT_PREFIX = 'edumind-native:'
const BRIDGE_READY_EVENT = `${NATIVE_EVENT_PREFIX}bridge-ready`
export const NATIVE_OFFLINE_TRANSCRIPTION_PROGRESS_EVENT = 'offline-transcription-progress'
export const NATIVE_OFFLINE_TRANSCRIPTION_COMPLETED_EVENT = 'offline-transcription-completed'
export const NATIVE_OFFLINE_TRANSCRIPTION_FAILED_EVENT = 'offline-transcription-failed'

const logNativeBridge = (level, label, details = '') => {
  const text = details ? `${label} | ${details}` : label
  console[level](`[NATIVE][Bridge] ${text}`)
  return text
}

const getNativeBridge = () => window.__edumindNativeBridge || null

export const hasNativeBridge = () => Boolean(getNativeBridge()?.isAvailable?.())

export const requestNative = async (action, payload = {}) => {
  const bridge = getNativeBridge()
  if (!bridge?.send) {
    throw new Error('Native bridge unavailable')
  }
  return bridge.send(action, payload)
}

export const pingNativeBridge = () => requestNative('ping')

export const getNativeCapabilities = () => requestNative('getCapabilities')

export const startNativeOfflineTranscription = (payload = {}) => requestNative('startOfflineTranscription', payload)

export const onNativeEvent = (name, handler) => {
  const eventName = `${NATIVE_EVENT_PREFIX}${String(name || '')}`
  const listener = (event) => handler?.(event?.detail || {})
  window.addEventListener(eventName, listener)
  return () => window.removeEventListener(eventName, listener)
}

export const waitForNativeBridge = (timeoutMs = 1500) =>
  new Promise((resolve) => {
    if (hasNativeBridge()) {
      resolve(true)
      return
    }

    let done = false
    let timer = null

    const finish = (value) => {
      if (done) return
      done = true
      if (timer) window.clearTimeout(timer)
      window.removeEventListener(BRIDGE_READY_EVENT, onReady)
      resolve(value)
    }

    const onReady = () => finish(true)

    window.addEventListener(BRIDGE_READY_EVENT, onReady, { once: true })
    timer = window.setTimeout(() => finish(hasNativeBridge()), timeoutMs)
  })

export const bootstrapNativeBridge = async () => {
  const available = await waitForNativeBridge()
  if (!available) {
    logNativeBridge('info', 'unavailable')
    window.__edumindNativeState = {
      available: false,
      capabilities: null,
      ping: null
    }
    return window.__edumindNativeState
  }

  const [pingResult, capabilityResult] = await Promise.allSettled([
    pingNativeBridge(),
    getNativeCapabilities()
  ])

  const ping = pingResult.status === 'fulfilled' ? pingResult.value : null
  const capabilities = capabilityResult.status === 'fulfilled' ? capabilityResult.value : null

  if (ping) {
    logNativeBridge('info', 'ping', JSON.stringify(ping))
  }
  if (capabilities) {
    logNativeBridge('info', 'capabilities', JSON.stringify(capabilities))
  }
  if (pingResult.status === 'rejected') {
    logNativeBridge('error', 'ping-failed', pingResult.reason?.message || String(pingResult.reason || 'unknown'))
  }
  if (capabilityResult.status === 'rejected') {
    logNativeBridge(
      'error',
      'capabilities-failed',
      capabilityResult.reason?.message || String(capabilityResult.reason || 'unknown')
    )
  }

  window.__edumindNativeState = {
    available: true,
    ping,
    capabilities
  }

  return window.__edumindNativeState
}
