<script setup lang="ts">
/**
 * ExportButton — local JSON / CSV export for Evidence Lab.
 */
import { ChevronDown, Download } from "lucide-vue-next";

export interface ExportButtonProps {
  filenameBase: string;
  jsonData: unknown;
  csvContent: string;
  disabled?: boolean;
}

const props = withDefaults(defineProps<ExportButtonProps>(), {
  disabled: false,
});

const open = ref(false);

function download(content: string, mimeType: string, extension: string) {
  if (!import.meta.client || props.disabled) return;

  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${props.filenameBase}.${extension}`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
  open.value = false;
}

function exportJson() {
  const text = JSON.stringify(props.jsonData, null, 2);
  download(text, "application/json;charset=utf-8", "json");
}

function exportCsv() {
  download(props.csvContent, "text/csv;charset=utf-8", "csv");
}
</script>

<template>
  <div class="ks-evidence-export">
    <KsButton
      variant="secondary"
      size="sm"
      :disabled="disabled"
      @click="open = !open"
    >
      <template #icon-left>
        <Download :size="14" />
      </template>
      Export
      <template #icon-right>
        <ChevronDown :size="14" />
      </template>
    </KsButton>

    <div v-if="open && !disabled" class="ks-evidence-export__menu">
      <button
        type="button"
        class="ks-evidence-export__item"
        @click="exportJson"
      >
        Export JSON
      </button>
      <button type="button" class="ks-evidence-export__item" @click="exportCsv">
        Export CSV
      </button>
    </div>
  </div>
</template>

<style scoped>
.ks-evidence-export {
  position: relative;
}

.ks-evidence-export__menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.12);
  padding: 6px;
  z-index: 10;
}

.ks-evidence-export__item {
  display: block;
  width: 100%;
  border: none;
  background: none;
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  color: var(--color-text);
  font: 400 0.875rem / 1.35 var(--font-serif);
  cursor: pointer;
}

.ks-evidence-export__item:hover {
  background: rgba(13, 115, 119, 0.08);
  color: var(--color-primary);
}
</style>
