<script setup lang="ts">
/**
 * FigureGallery — Grid of key figures from the paper.
 *
 * Displays extracted figure thumbnails with captions.
 * Click to open in lightbox (future).
 */

export interface PaperFigure {
  id: string;
  number: number;
  caption: string;
  imageUrl: string;
}

export interface FigureGalleryProps {
  figures: PaperFigure[];
}

defineProps<FigureGalleryProps>();
defineEmits<{ "figure-click": [figure: PaperFigure] }>();

const uid = useId();
</script>

<template>
  <section
    class="ks-figure-gallery ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Figures</h2>

    <div class="ks-figure-gallery__grid">
      <button
        v-for="fig in figures"
        :key="fig.id"
        type="button"
        class="ks-figure-gallery__item"
        :aria-label="`Figure ${fig.number}: ${fig.caption}`"
        @click="$emit('figure-click', fig)"
      >
        <div class="ks-figure-gallery__img-wrap">
          <div class="ks-figure-gallery__placeholder" aria-hidden="true">
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1"
              opacity="0.3"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
          </div>
        </div>
        <div class="ks-figure-gallery__caption">
          <span class="ks-type-eyebrow" style="color: var(--color-accent)"
            >Fig. {{ fig.number }}</span
          >
          <span class="ks-type-body-sm">{{ fig.caption }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-figure-gallery__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.ks-figure-gallery__item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: 0;
  cursor: pointer;
  overflow: hidden;
  transition:
    transform var(--duration-normal) var(--ease-spring),
    box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-figure-gallery__item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-figure-gallery__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-figure-gallery__img-wrap {
  aspect-ratio: 4 / 3;
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ks-figure-gallery__placeholder {
  color: var(--color-secondary);
}

.ks-figure-gallery__caption {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  text-align: left;
}
</style>
