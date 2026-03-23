<script setup lang="ts">
/**
 * QueryComposer — Natural-language research frontier input.
 *
 * Provides a rich textarea for composing discovery queries in natural language
 * ("Describe a research frontier, not just keywords"), suggestion chips,
 * and a submit CTA.
 */

export interface QueryComposerProps {
  /** Placeholder text for the textarea */
  placeholder?: string
  /** Suggestion chips displayed below */
  suggestions?: string[]
  /** Model value for v-model support */
  modelValue?: string
}

const props = withDefaults(defineProps<QueryComposerProps>(), {
  placeholder: 'Describe a research frontier to discover papers...',
  suggestions: () => [],
  modelValue: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'submit': [query: string]
  'suggestion-click': [suggestion: string]
}>()

const uid = useId()

function handleInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLTextAreaElement).value)
}

function handleSuggestionClick(s: string) {
  emit('update:modelValue', s)
  emit('suggestion-click', s)
}

function handleSubmit() {
  if (props.modelValue.trim()) {
    emit('submit', props.modelValue.trim())
  }
}
</script>

<template>
  <section
    class="ks-query-composer ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-1"
    :aria-labelledby="`${uid}-title`"
  >
    <h3 :id="`${uid}-title`" class="ks-type-section-title">Compose Discovery</h3>
    <form class="ks-query-composer__form" @submit.prevent="handleSubmit">
      <label :for="`${uid}-input`" class="ks-type-body-sm ks-query-composer__desc">
        Describe a research frontier, not just keywords.
      </label>
      <textarea
        :id="`${uid}-input`"
        :value="modelValue"
        class="ks-query-composer__input"
        :placeholder="placeholder"
        rows="5"
        @input="handleInput"
      />
      <div v-if="suggestions.length > 0" class="ks-query-composer__suggestions">
        <button
          v-for="s in suggestions"
          :key="s"
          type="button"
          class="ks-query-composer__chip"
          @click="handleSuggestionClick(s)"
        >
          {{ s }}
        </button>
      </div>
      <KsButton
        variant="primary"
        class="ks-query-composer__cta"
        :disabled="!modelValue.trim()"
        type="submit"
      >
        Discover papers →
      </KsButton>
    </form>
  </section>
</template>

<style scoped>
.ks-query-composer {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-query-composer__desc {
  color: var(--color-secondary);
  margin-bottom: 4px;
}

.ks-query-composer__form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-query-composer__input {
  width: 100%;
  padding: 16px;
  background: rgba(250, 250, 247, 0.86);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  font: 400 1rem / 1.6 var(--font-serif);
  color: var(--color-text);
  resize: none;
  transition: border-color var(--duration-fast) var(--ease-smooth),
              box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-query-composer__input:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(13, 115, 119, 0.08);
}

.ks-query-composer__input::placeholder {
  color: rgba(107, 107, 107, 0.7);
  font-style: italic;
}

.ks-query-composer__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.ks-query-composer__chip {
  padding: 4px 10px;
  background: rgba(13, 115, 119, 0.08);
  border: none;
  border-radius: 2px;
  font: 600 0.6875rem / 1.2 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth),
              transform var(--duration-fast) var(--ease-spring);
}

.ks-query-composer__chip:hover {
  background: rgba(13, 115, 119, 0.14);
  transform: translateY(-1px);
}

.ks-query-composer__chip:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.ks-query-composer__cta {
  margin-top: 8px;
  align-self: stretch;
}
</style>
