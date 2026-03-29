export const OFFLINE_MEMORY_ENDPOINTS = Object.freeze({
  notes: {
    create: {
      method: 'POST',
      url: '/api/notes',
      fields: ['title', 'content', 'note_type', 'video_id', 'tags', 'timestamps']
    },
    update: {
      method: 'PUT',
      url: '/api/notes/{note_id}',
      fields: ['title', 'content', 'note_type', 'video_id', 'tags']
    }
  },
  qa: {
    ask: {
      method: 'POST',
      url: '/api/qa/ask',
      fields: ['user_id', 'video_id', 'question', 'mode', 'stream', 'provider', 'model', 'deep_thinking', 'history']
    }
  },
  subtitles: {
    list: {
      method: 'GET',
      url: '/api/subtitles/videos/{video_id}/subtitles',
      fields: []
    },
    merged: {
      method: 'GET',
      url: '/api/subtitles/videos/{video_id}/subtitles/semantic-merged',
      fields: ['force_refresh']
    }
  }
})

export const OFFLINE_SYNC_ACTION = Object.freeze({
  CREATE_NOTE: 'create_note',
  UPDATE_NOTE: 'update_note',
  ASK_QUESTION: 'ask_question'
})
