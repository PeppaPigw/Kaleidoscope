<script setup lang="ts">
/**
 * ProjectCover — Workspace header card.
 */

export interface ProjectCoverProps {
  name: string;
  description: string;
  paperCount: number;
  memberCount: number;
  lastUpdated: string;
  status: "active" | "archived" | "draft";
}

defineProps<ProjectCoverProps>();
defineEmits<{ settings: [] }>();

const uid = useId();

type TagVariant = "success" | "neutral" | "warning";

function statusVariant(s: ProjectCoverProps["status"]): TagVariant {
  const map: Record<ProjectCoverProps["status"], TagVariant> = {
    active: "success",
    archived: "neutral",
    draft: "warning",
  };
  return map[s];
}
</script>

<template>
  <header
    class="ks-project-cover ks-motion-paper-reveal"
    :aria-labelledby="`${uid}-title`"
  >
    <div class="ks-project-cover__main">
      <div class="ks-project-cover__heading">
        <h1 :id="`${uid}-title`" class="ks-project-cover__name">{{ name }}</h1>
        <KsTag :variant="statusVariant(status)">{{ status }}</KsTag>
      </div>
      <p class="ks-type-body-sm" style="color: var(--color-secondary)">
        {{ description }}
      </p>
    </div>
    <div class="ks-project-cover__stats">
      <div class="ks-project-cover__stat">
        <span class="ks-project-cover__stat-value">{{ paperCount }}</span>
        <span class="ks-type-data">papers</span>
      </div>
      <div class="ks-project-cover__stat">
        <span class="ks-project-cover__stat-value">{{ memberCount }}</span>
        <span class="ks-type-data">members</span>
      </div>
      <div class="ks-project-cover__stat">
        <span class="ks-type-data">Updated {{ lastUpdated }}</span>
      </div>
      <KsButton variant="secondary" @click="$emit('settings')"
        >⚙ Settings</KsButton
      >
    </div>
  </header>
</template>

<style scoped>
.ks-project-cover {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  padding: 24px 0;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.ks-project-cover__heading {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-project-cover__name {
  font: 700 1.75rem / 1.2 var(--font-display);
  color: var(--color-text);
}

.ks-project-cover__stats {
  display: flex;
  align-items: center;
  gap: 20px;
}

.ks-project-cover__stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ks-project-cover__stat-value {
  font: 700 1.25rem / 1 var(--font-mono);
  color: var(--color-primary);
}
</style>
