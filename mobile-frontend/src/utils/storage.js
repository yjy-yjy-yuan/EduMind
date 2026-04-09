const memoryStore = new Map()

let localStore = null

const resolveLocalStorage = () => {
  if (localStore) return localStore
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    const probe = '__edumind_storage_probe__'
    window.localStorage.setItem(probe, '1')
    window.localStorage.removeItem(probe)
    localStore = window.localStorage
    return localStore
  } catch {
    return null
  }
}

export const storageGet = (key) => {
  if (!key) return null
  const store = resolveLocalStorage()
  if (store) {
    try {
      return store.getItem(key)
    } catch {
      // fall through to memory store
    }
  }
  return memoryStore.has(key) ? memoryStore.get(key) : null
}

export const storageSet = (key, value) => {
  if (!key) return
  const normalized = String(value ?? '')
  const store = resolveLocalStorage()
  if (store) {
    try {
      store.setItem(key, normalized)
      return
    } catch {
      // fall through to memory store
    }
  }
  memoryStore.set(key, normalized)
}

export const storageRemove = (key) => {
  if (!key) return
  const store = resolveLocalStorage()
  if (store) {
    try {
      store.removeItem(key)
    } catch {
      // ignore
    }
  }
  memoryStore.delete(key)
}
