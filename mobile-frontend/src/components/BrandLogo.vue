<template>
  <div
    class="brand-logo"
    :class="[`brand-logo--${variant}`, { 'brand-logo--compact': compact, 'brand-logo--rounded': rounded }]"
    :style="wrapperStyle"
  >
    <div class="brand-logo__frame">
      <img class="brand-logo__image" :src="resolvedLogoSrc" alt="EduMind Logo" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import logoMarkSrc from '@/assets/edumind-logo-icon.png'
import logoSrc from '@/assets/edumind-logo.png'

const props = defineProps({
  width: {
    type: Number,
    default: 168
  },
  variant: {
    type: String,
    default: 'framed'
  },
  compact: {
    type: Boolean,
    default: false
  },
  logoType: {
    type: String,
    default: 'full'
  },
  rounded: {
    type: Boolean,
    default: false
  }
})

const wrapperStyle = computed(() => ({
  width: `${props.width}px`
}))

const resolvedLogoSrc = computed(() => (props.logoType === 'mark' ? logoMarkSrc : logoSrc))
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
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(246, 240, 251, 0.96), rgba(233, 223, 245, 0.92)),
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
  height: 100%;
  display: block;
  object-fit: contain;
  object-position: center;
  border-radius: 18px;
  flex-shrink: 0;
  box-shadow: 0 8px 18px rgba(139, 121, 157, 0.08);
}

.brand-logo--compact .brand-logo__image {
  border-radius: 16px;
}

.brand-logo--plain .brand-logo__frame {
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.brand-logo--plain .brand-logo__image,
.brand-logo--compact.brand-logo--plain .brand-logo__image {
  border-radius: 0;
  box-shadow: none;
}

.brand-logo--rounded .brand-logo__frame {
  border-radius: 20px;
  overflow: hidden;
}

.brand-logo--compact.brand-logo--rounded .brand-logo__frame {
  border-radius: 18px;
}

.brand-logo--rounded .brand-logo__image,
.brand-logo--compact.brand-logo--rounded .brand-logo__image {
  border-radius: inherit;
}
</style>
