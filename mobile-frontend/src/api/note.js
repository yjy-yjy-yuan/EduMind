import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import {
  mockAddNoteTimestamp,
  mockCreateNote,
  mockDeleteNote,
  mockDeleteNoteTimestamp,
  mockGetNote,
  mockGetNoteTags,
  mockGetNotes,
  mockUpdateNote
} from '@/api/mockGateway'

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

export function addNoteTimestamp(noteId, data) {
  if (shouldUseMockApi()) return mockAddNoteTimestamp(noteId, data)
  return request({
    url: `/api/notes/notes/${noteId}/timestamps`,
    method: 'post',
    params: {
      time_seconds: data?.time_seconds,
      subtitle_text: data?.subtitle_text || ''
    }
  })
}

export function deleteNoteTimestamp(noteId, timestampId) {
  if (shouldUseMockApi()) return mockDeleteNoteTimestamp(noteId, timestampId)
  return request({ url: `/api/notes/notes/${noteId}/timestamps/${timestampId}`, method: 'delete' })
}

export function getNoteTags() {
  if (shouldUseMockApi()) return mockGetNoteTags()
  return request({ url: '/api/notes/tags', method: 'get' })
}

export function deleteNote(noteId) {
  if (shouldUseMockApi()) return mockDeleteNote(noteId)
  return request({ url: `/api/notes/notes/${noteId}`, method: 'delete' })
}
