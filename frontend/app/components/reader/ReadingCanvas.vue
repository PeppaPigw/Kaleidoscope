<script setup lang="ts">
/**
 * ReadingCanvas — PDF viewer placeholder with page navigation.
 *
 * In production this wraps PDF.js; for now renders a styled placeholder
 * with page navigation, zoom, and fullscreen controls.
 */

export interface ReadingCanvasProps {
  documentUrl: string
  currentPage: number
  totalPages: number
  title: string
}

const props = defineProps<ReadingCanvasProps>()
defineEmits<{
  'page-change': [page: number]
  'zoom-change': [level: number]
  'toggle-fullscreen': []
}>()

const uid = useId()
const zoomLevel = ref(100)
</script>

<template>
  <div class="ks-reading-canvas" :aria-labelledby="`${uid}-title`">
    <div class="ks-reading-canvas__toolbar">
      <div class="ks-reading-canvas__nav">
        <KsButton
          variant="secondary"
          :disabled="currentPage <= 1"
          aria-label="Previous page"
          @click="$emit('page-change', currentPage - 1)"
        >
          ‹
        </KsButton>
        <span class="ks-type-data">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <KsButton
          variant="secondary"
          :disabled="currentPage >= totalPages"
          aria-label="Next page"
          @click="$emit('page-change', currentPage + 1)"
        >
          ›
        </KsButton>
      </div>

      <div class="ks-reading-canvas__zoom">
        <KsButton variant="secondary" aria-label="Zoom out" @click="zoomLevel = Math.max(50, zoomLevel - 10); $emit('zoom-change', zoomLevel)">−</KsButton>
        <span class="ks-type-data">{{ zoomLevel }}%</span>
        <KsButton variant="secondary" aria-label="Zoom in" @click="zoomLevel = Math.min(200, zoomLevel + 10); $emit('zoom-change', zoomLevel)">+</KsButton>
        <KsButton variant="secondary" aria-label="Toggle fullscreen" @click="$emit('toggle-fullscreen')">⛶</KsButton>
      </div>
    </div>

    <div class="ks-reading-canvas__viewport">
      <div class="ks-reading-canvas__page-placeholder">
        <div class="ks-reading-canvas__page-icon" aria-hidden="true">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/>
          </svg>
        </div>
        <h3 :id="`${uid}-title`" class="ks-reading-canvas__title">{{ title }}</h3>
        <p class="ks-type-body-sm" style="color: var(--color-secondary); margin-top: 8px;">
          PDF rendering will be available with PDF.js integration
        </p>
        <p class="ks-type-data" style="color: var(--color-primary); margin-top: 16px;">
          {{ documentUrl }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ks-reading-canvas {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-bg);
}

.ks-reading-canvas__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid var(--color-border);
  background: rgba(250, 250, 247, 0.6);
  flex-wrap: wrap;
  gap: 8px;
}

.ks-reading-canvas__nav,
.ks-reading-canvas__zoom {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-reading-canvas__viewport {
  min-height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 20px,
    rgba(196, 163, 90, 0.02) 20px,
    rgba(196, 163, 90, 0.02) 40px
  );
}

.ks-reading-canvas__page-placeholder {
  text-align: center;
  padding: 48px;
}

.ks-reading-canvas__page-icon {
  color: var(--color-secondary);
  margin-bottom: 16px;
}

.ks-reading-canvas__title {
  font: 600 1.25rem / 1.3 var(--font-serif);
  color: var(--color-text);
}
</style>
