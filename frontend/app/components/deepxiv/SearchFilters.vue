<script setup lang="ts">
/**
 * SearchFilters -- Filter panel for DeepXiv search queries.
 *
 * Contains inputs for categories (comma-separated), author names,
 * date range pickers, and minimum citation count. Uses v-model pattern.
 */

export interface DeepXivFilters {
  categories: string
  date_from: string
  date_to: string
  min_citation: number
  authors: string
}

export interface SearchFiltersProps {
  modelValue: DeepXivFilters
}

const props = defineProps<SearchFiltersProps>()

const emit = defineEmits<{
  'update:modelValue': [value: DeepXivFilters]
}>()

function update(field: keyof DeepXivFilters, value: string | number) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>

<template>
  <div class="ks-search-filters">
    <div class="ks-search-filters__field">
      <label class="ks-search-filters__label" for="dx-categories">Categories</label>
      <input
        id="dx-categories"
        type="text"
        class="ks-search-filters__input"
        placeholder="cs.AI, cs.CL, stat.ML"
        :value="modelValue.categories"
        @input="update('categories', ($event.target as HTMLInputElement).value)"
      >
    </div>

    <div class="ks-search-filters__field">
      <label class="ks-search-filters__label" for="dx-authors">Authors</label>
      <input
        id="dx-authors"
        type="text"
        class="ks-search-filters__input"
        placeholder="Author names"
        :value="modelValue.authors"
        @input="update('authors', ($event.target as HTMLInputElement).value)"
      >
    </div>

    <div class="ks-search-filters__row">
      <div class="ks-search-filters__field">
        <label class="ks-search-filters__label" for="dx-date-from">From</label>
        <input
          id="dx-date-from"
          type="date"
          class="ks-search-filters__input"
          :value="modelValue.date_from"
          @input="update('date_from', ($event.target as HTMLInputElement).value)"
        >
      </div>

      <div class="ks-search-filters__field">
        <label class="ks-search-filters__label" for="dx-date-to">To</label>
        <input
          id="dx-date-to"
          type="date"
          class="ks-search-filters__input"
          :value="modelValue.date_to"
          @input="update('date_to', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </div>

    <div class="ks-search-filters__field">
      <label class="ks-search-filters__label" for="dx-min-citation">Min citations</label>
      <input
        id="dx-min-citation"
        type="number"
        class="ks-search-filters__input ks-search-filters__input--narrow"
        min="0"
        :value="modelValue.min_citation"
        @input="update('min_citation', Number(($event.target as HTMLInputElement).value))"
      >
    </div>
  </div>
</template>

<style scoped>
.ks-search-filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
}

.ks-search-filters__row {
  display: flex;
  gap: 12px;
}

.ks-search-filters__row .ks-search-filters__field {
  flex: 1;
}

.ks-search-filters__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-search-filters__label {
  font: 600 0.6875rem / 1.2 var(--font-sans);
  color: var(--color-text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ks-search-filters__input {
  padding: 8px 10px;
  font: 400 0.875rem / 1.3 var(--font-sans);
  color: var(--color-text);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-search-filters__input::placeholder {
  color: var(--color-secondary);
}

.ks-search-filters__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.ks-search-filters__input--narrow {
  max-width: 120px;
}

@media (max-width: 480px) {
  .ks-search-filters__row {
    flex-direction: column;
  }
}
</style>
