import request from '@/utils/request'

export function getNotes(params) {
  return request({ url: '/api/notes/notes', method: 'get', params })
}

export function getNote(noteId) {
  return request({ url: `/api/notes/notes/${noteId}`, method: 'get' })
}

export function createNote(data) {
  return request({ url: '/api/notes/notes', method: 'post', data })
}

export function updateNote(noteId, data) {
  return request({ url: `/api/notes/notes/${noteId}`, method: 'put', data })
}

export function deleteNote(noteId) {
  return request({ url: `/api/notes/notes/${noteId}`, method: 'delete' })
}

