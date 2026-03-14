<template>
  <div class="brand-logo" :class="{ 'brand-logo--compact': compact }" :style="wrapperStyle">
    <img class="brand-logo__image" :src="logoSrc" alt="EduMind Logo" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import logoSrc from '@/assets/edumind-logo.svg'

const props = defineProps({
  width: {
    type: Number,
    default: 168
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const wrapperStyle = computed(() => ({
  width: `${props.width}px`
}))
</script>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 168px;
  max-width: 100%;
  flex: 0 0 auto;
  min-width: 0;
}

.brand-logo--compact {
  width: 132px;
}

.brand-logo__image {
  width: 100%;
  height: auto;
  object-fit: contain;
  aspect-ratio: 1 / 1;
  flex-shrink: 0;
  filter: drop-shadow(0 10px 24px rgba(28, 112, 143, 0.12));
}
</style>
