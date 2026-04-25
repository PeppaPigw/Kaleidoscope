<script setup lang="ts">
/**
 * ActiveWorkspacePanel — Shows the user's active research workspaces with progress.
 *
 * Each workspace card displays the name, progress bar, and detail,
 * with a hover slide-right animation. Uses ARIA progressbar semantics.
 */

export interface WorkspaceSummary {
  id: string;
  name: string;
  progress: number;
  detail: string;
}

export interface ActiveWorkspacePanelProps {
  workspaces: WorkspaceSummary[];
}

defineProps<ActiveWorkspacePanelProps>();

defineEmits<{
  "workspace-click": [ws: WorkspaceSummary];
}>();

const uid = useId();

/** Clamp progress to 0–100 range for safe ARIA and CSS */
function clampedProgress(p: number): number {
  return Math.max(0, Math.min(100, p));
}
</script>

<template>
  <section
    class="ks-workspace-panel ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-3"
    :aria-labelledby="`${uid}-title`"
  >
    <h3 :id="`${uid}-title`" class="ks-type-section-title">
      Active Workspaces
    </h3>
    <div class="ks-workspace-panel__list">
      <button
        v-for="ws in workspaces"
        :key="ws.id"
        type="button"
        class="ks-workspace-panel__item"
        @click="$emit('workspace-click', ws)"
      >
        <div class="ks-workspace-panel__item-header">
          <span class="ks-workspace-panel__item-name">{{ ws.name }}</span>
          <span class="ks-type-stat" style="color: var(--color-primary)"
            >{{ clampedProgress(ws.progress) }}%</span
          >
        </div>
        <div
          class="ks-workspace-panel__progress"
          role="progressbar"
          :aria-valuenow="clampedProgress(ws.progress)"
          :aria-valuemin="0"
          :aria-valuemax="100"
          :aria-label="`${ws.name} progress: ${clampedProgress(ws.progress)}%`"
        >
          <div
            class="ks-workspace-panel__progress-fill"
            :style="{
              transform: `scaleX(${clampedProgress(ws.progress) / 100})`,
            }"
          />
        </div>
        <span class="ks-type-data">{{ ws.detail }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.ks-workspace-panel {
  padding: 24px;
}

.ks-workspace-panel__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.ks-workspace-panel__item {
  padding: 16px;
  background: rgba(250, 250, 247, 0.72);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid transparent;
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition:
    transform var(--duration-fast) var(--ease-spring),
    border-color var(--duration-fast) var(--ease-smooth);
}

.ks-workspace-panel__item:hover {
  transform: translateX(4px);
  border-color: rgba(13, 115, 119, 0.55);
}

.ks-workspace-panel__item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-workspace-panel__item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ks-workspace-panel__item-name {
  font: 600 1.125rem / 1.3 var(--font-serif);
  color: var(--color-text);
}

.ks-workspace-panel__progress {
  height: 4px;
  background: rgba(232, 229, 224, 0.8);
  border-radius: 2px;
  overflow: hidden;
}

.ks-workspace-panel__progress-fill {
  height: 100%;
  width: 100%;
  background: var(--color-primary);
  border-radius: 2px;
  transform-origin: left;
  transition: transform 500ms var(--ease-smooth);
}
</style>
