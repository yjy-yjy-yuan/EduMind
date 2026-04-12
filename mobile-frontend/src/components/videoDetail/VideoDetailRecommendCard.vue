<template>
  <article class="vd-rec-card" @click="onCardClick">
    <div class="vd-rec-card__top">
      <span class="vd-rec-card__reason">{{ item.reasonLabel }}</span>
      <span class="vd-rec-card__badge" :class="item.sourceBadgeClass">{{ item.sourceLabel }}</span>
    </div>
    <h3 class="vd-rec-card__title">{{ item.title }}</h3>
    <div class="vd-rec-card__meta">
      <span v-if="item.timeText">{{ item.timeText }}</span>
      <span v-if="item.statusText">{{ item.statusText }}</span>
      <span v-if="item.subjectText">{{ item.subjectText }}</span>
    </div>
    <div v-if="item.importHint" class="vd-rec-card__hint">{{ item.importHint }}</div>
    <button
      type="button"
      class="vd-rec-card__action"
      :disabled="item.primaryActionDisabled"
      @click.stop="emitPrimary"
    >
      {{ item.primaryActionLabel }}
    </button>
  </article>
</template>

<script setup>
const props = defineProps({
  item: { type: Object, required: true }
})

const emit = defineEmits(['primary', 'open'])

const emitPrimary = () => {
  emit('primary', props.item)
}

const onCardClick = () => {
  emit('open', props.item)
}
</script>

<style scoped>
.vd-rec-card {
  border-radius: 16px;
  padding: 14px 14px 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f2fc 100%);
  border: 1px solid rgba(32, 42, 55, 0.08);
  box-shadow: 0 8px 20px rgba(101, 87, 117, 0.08);
  display: grid;
  gap: 8px;
  text-align: left;
}

.vd-rec-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.vd-rec-card__reason {
  font-size: 11px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(95, 71, 126, 0.12);
  color: #5f477e;
}

.vd-rec-card__badge {
  font-size: 11px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 999px;
}

.vd-rec-card__badge.badge--external {
  background: rgba(14, 116, 144, 0.12);
  color: #0e7490;
}

.vd-rec-card__badge.badge--mint {
  background: rgba(52, 211, 153, 0.15);
  color: #047857;
}

.vd-rec-card__badge.badge--soft {
  background: rgba(107, 91, 132, 0.12);
  color: #5f477e;
}

.vd-rec-card__title {
  margin: 0;
  font-size: 15px;
  font-weight: 900;
  line-height: 1.4;
  color: #0f172a;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.vd-rec-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}

.vd-rec-card__hint {
  font-size: 11px;
  color: #94a3b8;
  line-height: 1.4;
}

.vd-rec-card__action {
  margin-top: 4px;
  border: 0;
  border-radius: 14px;
  padding: 10px 14px;
  font-weight: 900;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #8b799d, #6b5b84);
}

.vd-rec-card__action:disabled {
  opacity: 0.45;
}
</style>
