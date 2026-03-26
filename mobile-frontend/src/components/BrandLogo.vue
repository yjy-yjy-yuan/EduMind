<template>
  <div class="brand-logo" :class="{ 'brand-logo--compact': compact }" :style="wrapperStyle">
    <div class="brand-logo__frame">
      <img class="brand-logo__image" :src="logoSrc" alt="EduMind Logo" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import logoSrc from '@/assets/edumind-logo.png'

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

.brand-logo__frame {
  width: 100%;
  padding: 8px;
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(255, 249, 244, 0.94), rgba(245, 237, 230, 0.9)),
    rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.62);
  box-shadow:
    0 16px 28px rgba(102, 87, 117, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.78);
  overflow: hidden;
}

.brand-logo--compact .brand-logo__frame {
  padding: 6px;
  border-radius: 22px;
  box-shadow:
    0 12px 22px rgba(102, 87, 117, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.brand-logo__image {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  border-radius: 18px;
  flex-shrink: 0;
  box-shadow: 0 8px 18px rgba(139, 121, 157, 0.08);
}

.brand-logo--compact .brand-logo__image {
  border-radius: 16px;
}
</style>
