<script setup lang="ts">
/**
 * MonitorRibbon — System health sidebar showing pipeline status.
 *
 * Displays real-time status of backend services (GROBID, Neo4j, CrossRef, etc.)
 * with value, detail, and OK/ALERT badges. Uses teal-top card accent.
 */

export interface MonitorItem {
  system: string
  value: string
  detail: string
  status: 'ok' | 'warning' | 'error'
}

export interface MonitorRibbonProps {
  monitors: MonitorItem[]
}

defineProps<MonitorRibbonProps>()

const uid = useId()

const statusTagVariant: Record<MonitorItem['status'], 'primary' | 'accent' | 'warning'> = {
  ok: 'primary',
  warning: 'accent',
  error: 'warning',
}

const statusLabel: Record<MonitorItem['status'], string> = {
  ok: 'OK',
  warning: 'ALERT',
  error: 'ERROR',
}
</script>

<template>
  <section
    class="ks-monitor-ribbon ks-card ks-card--teal-top ks-motion-paper-reveal ks-motion-paper-reveal--delay-1"
    :aria-labelledby="`${uid}-title`"
  >
    <h3 :id="`${uid}-title`" class="ks-type-eyebrow ks-monitor-ribbon__title">
      SYSTEM MONITOR
    </h3>
    <div class="ks-monitor-ribbon__list" role="list">
      <div
        v-for="item in monitors"
        :key="item.system"
        :class="[
          'ks-monitor-ribbon__item',
          { 'ks-monitor-ribbon__item--warning': item.status === 'warning' },
          { 'ks-monitor-ribbon__item--error': item.status === 'error' },
        ]"
        role="listitem"
      >
        <div class="ks-monitor-ribbon__item-row">
          <span class="ks-monitor-ribbon__item-value">{{ item.value }}</span>
          <KsTag :variant="statusTagVariant[item.status]">
            {{ statusLabel[item.status] }}
          </KsTag>
        </div>
        <span class="ks-type-label ks-monitor-ribbon__item-system">
          {{ item.system }}
        </span>
        <span class="ks-type-data">
          {{ item.detail }}
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ks-monitor-ribbon {
  display: flex;
  flex-direction: column;
}

.ks-monitor-ribbon__title {
  color: var(--color-primary);
  padding: 20px 24px 0;
}

.ks-monitor-ribbon__list {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 12px 24px 24px;
  gap: 0;
}

.ks-monitor-ribbon__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 0;
  border-bottom: 1px solid var(--color-border);
}

.ks-monitor-ribbon__item:last-child {
  border-bottom: none;
}

.ks-monitor-ribbon__item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ks-monitor-ribbon__item-value {
  font: 600 1.75rem / 1.1 var(--font-display);
  color: var(--color-text);
}

.ks-monitor-ribbon__item-system {
  font-weight: 600;
  color: var(--color-text);
}
</style>
