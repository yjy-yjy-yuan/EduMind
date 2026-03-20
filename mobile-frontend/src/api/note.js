import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import { mockCreateNote, mockDeleteNote, mockGetNote, mockGetNotes, mockUpdateNote } from '@/api/mockGateway'

export function getNotes(params) {
  if (shouldUseMockApi()) return mockGetNotes(params)
  return request({ url: '/api/notes/notes', method: 'get', params })
}

export function getNote(noteId) {
  if (shouldUseMockApi()) return mockGetNote(noteId)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'get' })
}

export function createNote(data) {
  if (shouldUseMockApi()) return mockCreateNote(data)
  return request({ url: '/api/notes/notes', method: 'post', data })
}

export function updateNote(noteId, data) {
  if (shouldUseMockApi()) return mockUpdateNote(noteId, data)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'put', data })
}

export function deleteNote(noteId) {
  if (shouldUseMockApi()) return mockDeleteNote(noteId)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'delete' })
}
