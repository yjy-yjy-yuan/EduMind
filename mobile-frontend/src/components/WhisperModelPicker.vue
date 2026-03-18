<template>
  <div class="picker">
    <label class="picker-field">
      <span class="picker-title">{{ title }}</span>
      <div class="picker-control">
        <select class="picker-select" :value="model" :disabled="disabled" @change="handleChange">
          <option v-for="option in WHISPER_MODEL_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <span class="picker-chevron" aria-hidden="true"></span>
      </div>
    </label>
    <div v-if="hint" class="picker-hint">{{ hint }}</div>
  </div>
</template>

<script setup>
import { WHISPER_MODEL_OPTIONS } from '@/services/processingSettings'

const props = defineProps({
  model: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: 'Whisper 模型'
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
</script>

<style scoped>
.picker {
  display: grid;
  gap: 6px;
}

.picker-field {
  display: grid;
  gap: 8px;
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

.picker-control {
  position: relative;
}

.picker-select {
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid rgba(32, 42, 55, 0.12);
  border-radius: 16px;
  padding: 12px 42px 12px 14px;
  font-size: 15px;
  font-weight: 800;
  color: #2563d8;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 250, 253, 0.94)),
    rgba(255, 255, 255, 0.96);
  box-shadow: inset 0 -1px 0 rgba(32, 42, 55, 0.06);
}

.picker-select:disabled {
  opacity: 0.6;
}

.picker-chevron {
  position: absolute;
  top: 50%;
  right: 14px;
  width: 10px;
  height: 10px;
  margin-top: -7px;
  border-right: 2px solid #2563d8;
  border-bottom: 2px solid #2563d8;
  transform: rotate(45deg);
  pointer-events: none;
}
</style>
