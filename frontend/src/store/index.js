import { createStore } from 'vuex'
import * as videoApi from '../api/video'

export default createStore({
  state: {
    currentVideo: null,
    subtitles: [],
    notes: [],
    user: null,
    loading: false,
    error: null
  },
  
  mutations: {
    setCurrentVideo(state, video) {
      state.currentVideo = video
    },
    setSubtitles(state, subtitles) {
      state.subtitles = subtitles
    },
    updateSubtitle(state, { index, subtitle }) {
      state.subtitles[index] = subtitle
    },
    setNotes(state, notes) {
      state.notes = notes
    },
    setUser(state, user) {
      state.user = user
    },
    setLoading(state, loading) {
      state.loading = loading
    },
    setError(state, error) {
      state.error = error
    }
  },
  
  actions: {
    // 视频上传
    async uploadVideo({ commit }, formData) {
      try {
        commit('setLoading', true)
        const { data } = await videoApi.uploadVideo(formData)
        commit('setCurrentVideo', data)
        return data
      } catch (error) {
        commit('setError', error.message)
        throw error
      } finally {
        commit('setLoading', false)
      }
    },

    // 获取视频详情
    async getVideoDetails({ commit }, videoId) {
      try {
        commit('setLoading', true)
        const { data } = await videoApi.getVideo(videoId)
        commit('setCurrentVideo', data)
        return data
      } catch (error) {
        commit('setError', error.message)
        throw error
      } finally {
        commit('setLoading', false)
      }
    },

    // 获取字幕
    async getSubtitles({ commit }, videoId) {
      try {
        commit('setLoading', true)
        const { data } = await videoApi.getSubtitles(videoId)
        commit('setSubtitles', data)
        return data
      } catch (error) {
        commit('setError', error.message)
        throw error
      } finally {
        commit('setLoading', false)
      }
    },

    // 更新字幕
    async updateSubtitle({ commit, state }, { videoId, subtitleId, data }) {
      try {
        commit('setLoading', true)
        const response = await videoApi.updateSubtitle(videoId, subtitleId, data)
        const index = state.subtitles.findIndex(s => s.id === subtitleId)
        if (index !== -1) {
          commit('updateSubtitle', { index, subtitle: response.data })
        }
        return response.data
      } catch (error) {
        commit('setError', error.message)
        throw error
      } finally {
        commit('setLoading', false)
      }
    },

    // 生成字幕
    async generateSubtitles({ commit }, { videoId, language, model }) {
      try {
        commit('setLoading', true)
        const { data } = await videoApi.generateSubtitles(videoId, language, model)
        commit('setSubtitles', data.subtitles)
        return data
      } catch (error) {
        commit('setError', error.message)
        throw error
      } finally {
        commit('setLoading', false)
      }
    },

    // 导出字幕
    async exportSubtitles({ commit }, { videoId, format }) {
      try {
        const response = await videoApi.exportSubtitles(videoId, format)
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `subtitles.${format}`
        a.click()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        commit('setError', error.message)
        throw error
      }
    }
  },
  
  getters: {
    isLoading: state => state.loading,
    currentError: state => state.error,
    hasVideo: state => !!state.currentVideo,
    hasSubtitles: state => state.subtitles.length > 0,
    getSubtitleById: state => id => state.subtitles.find(s => s.id === id)
  }
})
