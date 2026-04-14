<script setup lang="ts">
/**
 * TranslatableTitle — Displays a paper title with optional auto-translation.
 *
 * When locale is 'zh', automatically fetches a Chinese translation
 * and shows it as small gray text below the original English title.
 */

const { isZh, translate, getCached, setCached, isPending } = useTranslation()

const props = defineProps<{
  /** Original (English) title text */
  text: string
  /** HTML tag for the title. Default: 'h4' */
  tag?: string
  /** Extra CSS class for the title element */
  titleClass?: string
  /** Optional paper ID for persisting translation */
  paperId?: string
  /** Pre-loaded translation from database */
  titleZh?: string
}>()

// ─── Auto-translate when locale switches to 'zh' ────────────
const translatedText = ref('')

// Pre-load translation from database if available
watch(
  () => props.titleZh,
  (zh) => {
    if (zh && props.text) {
      setCached(props.text, zh)
      if (isZh.value) {
        translatedText.value = zh
      }
    }
  },
  { immediate: true }
)

watch(
  () => [isZh.value, props.text],
  async ([zh]) => {
    if (!zh || !props.text) {
      translatedText.value = ''
      return
    }
    // Check cache first (includes pre-loaded translations)
    const cached = getCached(props.text)
    if (cached) {
      translatedText.value = cached
      return
    }
    // Fetch translation with optional persistence
    const result = await translate(props.text, {
      paperId: props.paperId,
      fieldType: 'title',
    })
    translatedText.value = result
  },
  { immediate: true },
)

const isLoading = computed(() => isPending(props.text))
</script>

<template>
  <div class="ks-translatable-title">
    <component :is="tag || 'h4'" :class="titleClass">
      <slot>{{ text }}</slot>
    </component>
    <span v-if="isZh && isLoading" class="ks-translatable-title__translation ks-translatable-title__translation--loading">
      翻译中…
    </span>
    <span v-else-if="isZh && translatedText" class="ks-translatable-title__translation">
      {{ translatedText }}
    </span>
  </div>
</template>

<style scoped>
.ks-translatable-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-translatable-title__translation {
  font: 400 0.75rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  opacity: 0.8;
  padding-left: 1px;
}

.ks-translatable-title__translation--loading {
  color: var(--color-primary);
  font-style: italic;
  animation: ks-pulse 1.5s ease-in-out infinite;
}

@keyframes ks-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
</style>
