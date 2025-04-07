import request from '@/utils/request'

// 获取所有笔记
export function getNotes(params) {
  return request({
    url: '/api/notes/notes',
    method: 'get',
    params
  })
}

// 获取单个笔记
export function getNote(noteId) {
  return request({
    url: `/api/notes/notes/${noteId}`,
    method: 'get'
  })
}

// 创建笔记
export function createNote(data) {
  return request({
    url: '/api/notes/notes',
    method: 'post',
    data
  })
}

// 更新笔记
export function updateNote(noteId, data) {
  return request({
    url: `/api/notes/notes/${noteId}`,
    method: 'put',
    data
  })
}

// 删除笔记
export function deleteNote(noteId) {
  return request({
    url: `/api/notes/notes/${noteId}`,
    method: 'delete'
  })
}

// 批量删除笔记
export function batchDeleteNotes(noteIds) {
  return request({
    url: '/api/notes/notes/batch-delete',
    method: 'post',
    data: { note_ids: noteIds }
  })
}

// 批量导出笔记
export function batchExportNotes(noteIds) {
  return request({
    url: '/api/notes/notes/batch-export',
    method: 'post',
    responseType: 'blob',
    data: { note_ids: noteIds }
  })
}

// 导出单个笔记
export function exportNote(noteId) {
  return request({
    url: `/api/notes/notes/${noteId}/export`,
    method: 'get',
    responseType: 'blob'
  })
}

// 添加时间戳
export function addTimestamp(noteId, data) {
  return request({
    url: `/api/notes/notes/${noteId}/timestamps`,
    method: 'post',
    data
  })
}

// 删除时间戳
export function deleteTimestamp(noteId, timestampId) {
  return request({
    url: `/api/notes/notes/${noteId}/timestamps/${timestampId}`,
    method: 'delete'
  })
}

// 获取所有标签
export function getTags() {
  return request({
    url: '/api/notes/tags',
    method: 'get'
  })
}

// 获取相似笔记
export function getSimilarNotes(data) {
  return request({
    url: '/api/notes/notes/similar',
    method: 'post',
    data
  })
}

// 同步标签
export function syncTags() {
  return request({
    url: '/api/notes/tags/sync',
    method: 'post'
  })
}