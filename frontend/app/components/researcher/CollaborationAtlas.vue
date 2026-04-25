<script setup lang="ts">
/**
 * CollaborationAtlas — Visual map of research collaborators.
 *
 * Displays co-author network as a card grid with collaboration
 * intensity and shared paper counts.
 */

export interface Collaborator {
  id: string;
  name: string;
  affiliation: string;
  sharedPapers: number;
  lastCollabYear: number;
  intensity: "high" | "medium" | "low";
}

export interface CollaborationAtlasProps {
  collaborators: Collaborator[];
}

defineProps<CollaborationAtlasProps>();
defineEmits<{ "collaborator-click": [collaborator: Collaborator] }>();

const uid = useId();
</script>

<template>
  <section
    class="ks-collab-atlas ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <h2 :id="`${uid}-title`" class="ks-type-section-title">
      Collaboration Atlas
    </h2>
    <p
      class="ks-type-body-sm"
      style="color: var(--color-secondary); margin-bottom: 16px"
    >
      {{ collaborators.length }} collaborators
    </p>

    <div class="ks-collab-atlas__grid">
      <button
        v-for="c in collaborators"
        :key="c.id"
        type="button"
        class="ks-card ks-collab-atlas__card"
        :aria-label="`${c.name}, ${c.sharedPapers} shared papers`"
        @click="$emit('collaborator-click', c)"
      >
        <div class="ks-collab-atlas__card-header">
          <div
            :class="[
              'ks-collab-atlas__intensity',
              `ks-collab-atlas__intensity--${c.intensity}`,
            ]"
            :aria-label="`${c.intensity} collaboration`"
          />
          <span class="ks-collab-atlas__name">{{ c.name }}</span>
        </div>
        <span class="ks-type-data" style="color: var(--color-secondary)">{{
          c.affiliation
        }}</span>
        <div class="ks-collab-atlas__card-footer">
          <span
            class="ks-type-data"
            style="color: var(--color-primary); font-weight: 700"
            >{{ c.sharedPapers }} papers</span
          >
          <span class="ks-type-data">last {{ c.lastCollabYear }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-collab-atlas__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.ks-collab-atlas__card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  text-align: left;
  cursor: pointer;
  transition:
    transform var(--duration-normal) var(--ease-spring),
    box-shadow var(--duration-normal) var(--ease-smooth);
}

.ks-collab-atlas__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(26, 26, 26, 0.06);
}

.ks-collab-atlas__card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-collab-atlas__card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-collab-atlas__intensity {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ks-collab-atlas__intensity--high {
  background: var(--color-primary);
}
.ks-collab-atlas__intensity--medium {
  background: var(--color-accent-decorative);
}
.ks-collab-atlas__intensity--low {
  background: var(--color-border);
}

.ks-collab-atlas__name {
  font: 600 0.9375rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-collab-atlas__card-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  padding-top: 6px;
  border-top: 1px solid var(--color-border);
}
</style>
