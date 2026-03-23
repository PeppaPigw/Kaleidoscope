<script setup lang="ts">
/**
 * NoteWall — Grid of research notes/zettelkasten cards.
 */

export interface NoteCard {
  id: string
  title: string
  excerpt: string
  tags: string[]
  backlinkCount: number
  updatedAt: string
}

export interface NoteWallProps {
  notes: NoteCard[]
}

defineProps<NoteWallProps>()
defineEmits<{ 'note-click': [note: NoteCard] }>()

const uid = useId()
</script>

<template>
  <section class="ks-note-wall ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <h2 :id="`${uid}-title`" class="ks-type-section-title">Notes ({{ notes.length }})</h2>

    <div class="ks-note-wall__grid">
      <button
        v-for="note in notes"
        :key="note.id"
        type="button"
        class="ks-card ks-note-wall__card"
        @click="$emit('note-click', note)"
      >
        <h3 class="ks-note-wall__title">{{ note.title }}</h3>
        <p class="ks-note-wall__excerpt">{{ note.excerpt }}</p>
        <div class="ks-note-wall__tags">
          <KsTag v-for="tag in note.tags.slice(0, 3)" :key="tag" variant="neutral">{{ tag }}</KsTag>
        </div>
        <div class="ks-note-wall__footer">
          <span class="ks-type-data" style="color: var(--color-primary);">{{ note.backlinkCount }} links</span>
          <span class="ks-type-data">{{ note.updatedAt }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-note-wall__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.ks-note-wall__card {
  padding: 16px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-note-wall__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-note-wall__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-note-wall__title {
  font: 600 1rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-note-wall__excerpt {
  font: 400 0.8125rem / 1.5 var(--font-serif);
  color: var(--color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ks-note-wall__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-note-wall__footer {
  display: flex;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}
</style>
