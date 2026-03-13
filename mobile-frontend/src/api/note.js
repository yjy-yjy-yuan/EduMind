import request from '@/utils/request'
import { UI_ONLY_MODE } from '@/config'
import { mockCreateNote, mockDeleteNote, mockGetNote, mockGetNotes, mockUpdateNote } from '@/api/mockGateway'

export function getNotes(params) {
  if (UI_ONLY_MODE) return mockGetNotes(params)
  return request({ url: '/api/notes/notes', method: 'get', params })
}

export function getNote(noteId) {
  if (UI_ONLY_MODE) return mockGetNote(noteId)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'get' })
}

export function createNote(data) {
  if (UI_ONLY_MODE) return mockCreateNote(data)
  return request({ url: '/api/notes/notes', method: 'post', data })
}

export function updateNote(noteId, data) {
  if (UI_ONLY_MODE) return mockUpdateNote(noteId, data)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'put', data })
}

export function deleteNote(noteId) {
  if (UI_ONLY_MODE) return mockDeleteNote(noteId)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'delete' })
}
