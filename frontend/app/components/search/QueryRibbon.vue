<script setup lang="ts">
/**
 * QueryRibbon — Sticky search query bar at top of search results.
 *
 * Contains the search input, mode switcher (keyword / semantic / claim),
 * and quick stats (result count + search time).
 */

export type SearchMode = "keyword" | "semantic" | "claim";

export interface QueryRibbonProps {
  modelValue?: string;
  mode?: SearchMode;
  resultCount?: number;
  searchTimeMs?: number;
}

const props = withDefaults(defineProps<QueryRibbonProps>(), {
  modelValue: "",
  mode: "keyword",
  resultCount: 0,
  searchTimeMs: 0,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  "update:mode": [mode: SearchMode];
  submit: [query: string];
}>();

const uid = useId();
const modes: { value: SearchMode; label: string }[] = [
  { value: "keyword", label: "Keyword" },
  { value: "semantic", label: "Semantic" },
  { value: "claim", label: "Claim-first" },
];

function handleInput(e: Event) {
  emit("update:modelValue", (e.target as HTMLInputElement).value);
}

function handleSubmit() {
  if (props.modelValue.trim()) {
    emit("submit", props.modelValue.trim());
  }
}
</script>

<template>
  <div class="ks-query-ribbon">
    <form class="ks-query-ribbon__form" @submit.prevent="handleSubmit">
      <label :for="`${uid}-input`" class="sr-only">Search query</label>
      <div class="ks-query-ribbon__input-wrap">
        <svg
          class="ks-query-ribbon__icon"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          :id="`${uid}-input`"
          type="search"
          class="ks-query-ribbon__input"
          :value="modelValue"
          placeholder="Search papers, claims, authors..."
          @input="handleInput"
        >
      </div>
      <div
        class="ks-query-ribbon__modes"
        role="radiogroup"
        aria-label="Search mode"
      >
        <button
          v-for="m in modes"
          :key="m.value"
          type="button"
          role="radio"
          :aria-checked="mode === m.value"
          :class="[
            'ks-query-ribbon__mode',
            { 'ks-query-ribbon__mode--active': mode === m.value },
          ]"
          @click="emit('update:mode', m.value)"
        >
          {{ m.label }}
        </button>
      </div>
      <KsButton variant="primary" type="submit" :disabled="!modelValue.trim()">
        Search
      </KsButton>
    </form>
    <div v-if="resultCount > 0" class="ks-query-ribbon__stats">
      <span class="ks-type-data" style="color: var(--color-primary)">
        {{ resultCount.toLocaleString() }} results
      </span>
      <span class="ks-type-data">
        {{ (searchTimeMs / 1000).toFixed(2) }}s
      </span>
    </div>
  </div>
</template>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.ks-query-ribbon {
  position: sticky;
  top: 64px;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 24px;
  background: var(--color-glass-bg);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border);
}

.ks-query-ribbon__form {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-query-ribbon__input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-query-ribbon__input-wrap:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(13, 115, 119, 0.08);
}

.ks-query-ribbon__icon {
  color: var(--color-secondary);
  flex-shrink: 0;
}

.ks-query-ribbon__input {
  flex: 1;
  border: none;
  background: none;
  font: 400 1rem / 1.4 var(--font-serif);
  color: var(--color-text);
  outline: none;
}

.ks-query-ribbon__input::placeholder {
  color: rgba(107, 107, 107, 0.6);
  font-style: italic;
}

.ks-query-ribbon__modes {
  display: flex;
  gap: 2px;
  padding: 2px;
  background: var(--color-bg);
  border-radius: var(--radius-card);
}

.ks-query-ribbon__mode {
  padding: 6px 12px;
  border: none;
  border-radius: 2px;
  background: none;
  font: 600 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-query-ribbon__mode:hover {
  color: var(--color-text);
}

.ks-query-ribbon__mode--active {
  background: var(--color-surface);
  color: var(--color-primary);
  box-shadow: 0 1px 3px rgba(26, 26, 26, 0.06);
}

.ks-query-ribbon__mode:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-query-ribbon__stats {
  display: flex;
  gap: 16px;
  padding-left: 42px;
}

@media (max-width: 768px) {
  .ks-query-ribbon__form {
    flex-wrap: wrap;
  }
  .ks-query-ribbon__modes {
    order: 3;
    width: 100%;
  }
  .ks-query-ribbon__stats {
    padding-left: 0;
  }
}
</style>
