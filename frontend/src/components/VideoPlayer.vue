<template>
  <div class="video-player">
    <video
      ref="videoRef"
      class="video-element"
      controls
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleMetadataLoaded"
    >
      <source :src="src" :type="videoType">
      <track
        v-if="subtitleUrl"
        kind="subtitles"
        :src="subtitleUrl"
        :srclang="subtitleLang"
        :label="subtitleLabel"
        default
      >
      您的浏览器不支持视频播放。
    </video>

    <!-- 视频控制栏 -->
    <div class="video-controls">
      <el-slider
        v-model="currentTime"
        :max="duration"
        :format-tooltip="formatTime"
        @change="handleSeek"
      ></el-slider>

      <div class="control-buttons">
        <el-button-group>
          <el-button
            :icon="playing ? VideoPause : VideoPlay"
            @click="togglePlay"
          ></el-button>

          <el-button
            :icon="muted ? Mute : Microphone"
            @click="toggleMute"
          ></el-button>
        </el-button-group>

        <div class="time-display">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>

        <el-slider
          v-model="volume"
          :max="100"
          :format-tooltip="value => `${value}%`"
          style="width: 100px"
        ></el-slider>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { VideoPlay, VideoPause, Microphone, Mute } from '@element-plus/icons-vue'

export default {
  name: 'VideoPlayer',

  props: {
    src: {
      type: String,
      required: true
    },
    subtitleUrl: {
      type: String,
      default: ''
    },
    subtitleLang: {
      type: String,
      default: 'zh'
    },
    subtitleLabel: {
      type: String,
      default: '中文'
    }
  },

  setup(props, { emit }) {
    const videoRef = ref(null)
    const currentTime = ref(0)
    const duration = ref(0)
    const volume = ref(100)
    const playing = ref(false)
    const muted = ref(false)

    const videoType = computed(() => {
      const ext = props.src.split('.').pop()?.toLowerCase()
      switch (ext) {
        case 'mp4':
          return 'video/mp4'
        case 'webm':
          return 'video/webm'
        default:
          return 'video/mp4'
      }
    })

    // 方法
    const togglePlay = () => {
      if (!videoRef.value) return
      if (playing.value) {
        videoRef.value.pause()
      } else {
        videoRef.value.play()
      }
      playing.value = !playing.value
    }

    const toggleMute = () => {
      if (!videoRef.value) return
      videoRef.value.muted = !videoRef.value.muted
      muted.value = videoRef.value.muted
    }

    const handleTimeUpdate = () => {
      if (!videoRef.value) return
      currentTime.value = videoRef.value.currentTime
      emit('timeupdate', currentTime.value)
    }

    const handleMetadataLoaded = () => {
      if (!videoRef.value) return
      duration.value = videoRef.value.duration
      emit('loaded', {
        duration: duration.value,
        videoWidth: videoRef.value.videoWidth,
        videoHeight: videoRef.value.videoHeight
      })
    }

    const handleSeek = (value) => {
      if (!videoRef.value) return
      videoRef.value.currentTime = value
    }

    const formatTime = (seconds) => {
      if (!seconds) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    // 监听音量变化
    watch(volume, (newValue) => {
      if (!videoRef.value) return
      videoRef.value.volume = newValue / 100
    })

    // 监听src变化
    watch(() => props.src, () => {
      if (!videoRef.value) return
      videoRef.value.load()
    })

    return {
      videoRef,
      currentTime,
      duration,
      volume,
      playing,
      muted,
      videoType,
      VideoPlay,
      VideoPause,
      Microphone,
      Mute,
      togglePlay,
      toggleMute,
      handleTimeUpdate,
      handleMetadataLoaded,
      handleSeek,
      formatTime
    }
  }
}
</script>

<style scoped>
.video-player {
  width: 100%;
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-element {
  width: 100%;
  height: auto;
  display: block;
}

.video-controls {
  padding: 10px;
  background: rgba(0, 0, 0, 0.7);
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  color: white;
}

.control-buttons {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.time-display {
  margin: 0 15px;
  font-family: monospace;
}

:deep(.el-slider) {
  margin-right: 20px;
}

:deep(.el-slider__runway) {
  background-color: rgba(255, 255, 255, 0.2);
}

:deep(.el-slider__bar) {
  background-color: var(--el-color-primary);
}

:deep(.el-slider__button) {
  border-color: var(--el-color-primary);
}
</style>
