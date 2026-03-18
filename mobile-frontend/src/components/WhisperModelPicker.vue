<template>
  <div class="picker">
    <div class="picker-heading">
      <span class="picker-title">{{ title }}</span>
    </div>
    <label class="picker-field">
      <div class="picker-control">
        <div class="picker-display" :class="{ 'picker-display--disabled': disabled }" aria-hidden="true">
          <span class="picker-display__value">{{ currentLabel }}</span>
          <div class="picker-advantage">
            <span class="picker-advantage__label">优势</span>
            <span class="picker-advantage__text">{{ currentHighlight }}</span>
          </div>
        </div>
        <select class="picker-select" :value="model" :disabled="disabled" @change="handleChange">
          <option v-for="option in availableOptions" :key="option.value" :value="option.value">
            {{ optionText(option) }}
          </option>
        </select>
        <span class="picker-chevron" aria-hidden="true"></span>
      </div>
    </label>
    <div v-if="hint" class="picker-hint">{{ hint }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getWhisperModelOptions, whisperModelHighlight } from '@/services/processingSettings'

const props = defineProps({
  model: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: 'Whisper 模型'
  },
  options: {
    type: Array,
    default: () => []
  },
  hint: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select'])

const handleChange = (event) => {
  emit('select', String(event?.target?.value || props.model))
}

const availableOptions = computed(() => (props.options?.length ? props.options : getWhisperModelOptions()))
const currentLabel = computed(() => {
  const normalized = String(props.model || '').trim().toLowerCase()
  return availableOptions.value.find((option) => option.value === normalized)?.label || normalized || 'base'
})
const currentHighlight = computed(() => whisperModelHighlight(props.model))

const optionHighlight = (option) => {
  const rawHighlight = String(option?.highlight || whisperModelHighlight(option?.value)).trim()
  return rawHighlight.split('，')[0].replace(/[。！？!?]+$/g, '')
}

const optionText = (option) => {
  const label = String(option?.label || option?.value || '').trim().toLowerCase()
  const highlight = optionHighlight(option)
  return highlight ? `${label} · ${highlight}` : label
}
</script>

<style scoped>
.picker {
  display: grid;
  gap: 6px;
}

.picker-heading {
  display: block;
}

.picker-field {
  display: block;
}

.picker-title {
  font-size: 13px;
  font-weight: 900;
  color: #1f2a37;
}

.picker-hint {
  font-size: 12px;
  color: var(--muted);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.picker-advantage {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--muted);
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.picker-advantage__label {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 10px;
  font-weight: 900;
  color: var(--primary-deep);
  background: rgba(21, 141, 178, 0.1);
}

.picker-advantage__text {
  min-width: 0;
}

.picker-control {
  position: relative;
}

.picker-display {
  display: grid;
  gap: 10px;
  border: 1px solid rgba(32, 42, 55, 0.12);
  border-radius: 16px;
  padding: 12px 42px 12px 14px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 250, 253, 0.94)),
    rgba(255, 255, 255, 0.96);
  box-shadow: inset 0 -1px 0 rgba(32, 42, 55, 0.06);
}

.picker-display--disabled {
  opacity: 0.6;
}

.picker-display__value {
  font-size: 15px;
  font-weight: 800;
  line-height: 1.2;
  color: #2563d8;
}

.picker-select {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  appearance: none;
  -webkit-appearance: none;
  opacity: 0;
  cursor: pointer;
}

.picker-select:disabled {
  cursor: not-allowed;
}

.picker-chevron {
  position: absolute;
  top: 22px;
  right: 14px;
  width: 10px;
  height: 10px;
  border-right: 2px solid #2563d8;
  border-bottom: 2px solid #2563d8;
  transform: rotate(45deg);
  pointer-events: none;
}
</style>
