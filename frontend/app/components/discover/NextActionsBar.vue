<script setup lang="ts">
/**
 * NextActionsBar — Fixed bottom toolbar for batch paper actions.
 *
 * Appears fixed at the bottom of the viewport when papers are selected.
 * Shows selection count and action buttons (Save, Compare, Add to Workspace, Export).
 */

export interface NextActionsBarProps {
  selectedCount: number;
}

defineProps<NextActionsBarProps>();

defineEmits<{
  save: [];
  compare: [];
  "add-to-workspace": [];
  "export-ris": [];
}>();
</script>

<template>
  <div
    :class="[
      'ks-next-actions-bar',
      { 'ks-next-actions-bar--active': selectedCount > 0 },
    ]"
    role="toolbar"
    aria-label="Paper actions"
  >
    <span class="ks-type-data" style="color: var(--color-primary)">
      {{ selectedCount }} selected
    </span>
    <div class="ks-next-actions-bar__actions">
      <KsButton
        variant="secondary"
        :disabled="selectedCount === 0"
        @click="$emit('save')"
      >
        Save
      </KsButton>
      <KsButton
        variant="secondary"
        :disabled="selectedCount === 0"
        @click="$emit('compare')"
      >
        Compare
      </KsButton>
      <KsButton
        variant="primary"
        :disabled="selectedCount === 0"
        @click="$emit('add-to-workspace')"
      >
        Add to Workspace
      </KsButton>
      <KsButton
        variant="secondary"
        class="ks-next-actions-bar__export"
        :disabled="selectedCount === 0"
        @click="$emit('export-ris')"
      >
        Export RIS
      </KsButton>
    </div>
  </div>
</template>

<style scoped>
.ks-next-actions-bar {
  position: fixed;
  bottom: 24px;
  left: calc(var(--sidebar-width) + 36px);
  right: 36px;
  max-width: 1600px;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--color-glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  transition:
    left var(--duration-normal) var(--ease-smooth),
    right var(--duration-normal) var(--ease-smooth),
    height var(--duration-normal) var(--ease-spring),
    box-shadow var(--duration-fast) var(--ease-smooth);
  z-index: 50;
}

.ks-next-actions-bar--active {
  min-height: 64px;
  box-shadow: var(--shadow-float);
}

.ks-next-actions-bar__actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 768px) {
  .ks-next-actions-bar {
    left: 16px;
    right: 16px;
    bottom: 16px;
  }

  .ks-next-actions-bar__actions {
    flex-wrap: wrap;
    gap: 6px;
  }

  .ks-next-actions-bar__export {
    display: none;
  }
}
</style>
