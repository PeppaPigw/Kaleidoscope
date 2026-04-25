<script setup lang="ts">
/**
 * KsTranslateBtn — Small button to translate an abstract on demand.
 *
 * Shows a compact translate icon+label. On click, calls the LLM API.
 * Displays loading state and cached result.
 */
import { Languages } from "lucide-vue-next";

const { t, translate, getCached, setCached, isPending } = useTranslation();

const props = defineProps<{
  /** The abstract / text to translate */
  text: string;
  /** Optional paper ID for persisting translation */
  paperId?: string;
  /** Pre-loaded translation from database */
  abstractZh?: string;
}>();

const emit = defineEmits<{
  translated: [result: string];
}>();

const translated = ref("");
const showTranslation = ref(false);

const loading = computed(() => isPending(props.text));

// Pre-load translation from database if available
watch(
  () => props.abstractZh,
  (zh) => {
    if (zh && props.text) {
      setCached(props.text, zh);
      translated.value = zh;
    }
  },
  { immediate: true },
);

// Auto-load cached
watch(
  () => props.text,
  (t) => {
    const cached = getCached(t);
    if (cached) {
      translated.value = cached;
    }
  },
  { immediate: true },
);

async function handleTranslate() {
  if (translated.value) {
    // Toggle visibility if already translated
    showTranslation.value = !showTranslation.value;
    return;
  }
  showTranslation.value = true;
  const result = await translate(props.text, {
    paperId: props.paperId,
    fieldType: "abstract",
  });
  if (result) {
    translated.value = result;
    emit("translated", result);
  }
}
</script>

<template>
  <div class="ks-translate-btn-wrap">
    <button
      type="button"
      class="ks-translate-btn"
      :class="{
        'ks-translate-btn--active': showTranslation && translated,
        'ks-translate-btn--loading': loading,
      }"
      :aria-label="
        translated
          ? showTranslation
            ? t('hideTranslation')
            : t('showTranslation')
          : t('translateAbstract')
      "
      @click.stop.prevent="handleTranslate"
    >
      <Languages :size="13" :stroke-width="2" />
      <span v-if="loading" class="ks-translate-btn__label">{{
        t("translating")
      }}</span>
      <span
        v-else-if="translated && showTranslation"
        class="ks-translate-btn__label"
        >{{ t("hideTranslation") }}</span
      >
      <span v-else class="ks-translate-btn__label">{{
        t("translateAbstract")
      }}</span>
    </button>

    <!-- Translation result -->
    <Transition name="ks-fade-slide">
      <div v-if="showTranslation && translated" class="ks-translate-result">
        <p class="ks-translate-result__text">{{ translated }}</p>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.ks-translate-btn-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-translate-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(13, 115, 119, 0.06);
  border: 1px solid rgba(13, 115, 119, 0.15);
  border-radius: 4px;
  color: var(--color-primary);
  cursor: pointer;
  font: 500 0.6875rem / 1 var(--font-sans);
  white-space: nowrap;
  transition: all var(--duration-fast) var(--ease-smooth);
  align-self: flex-start;
}

.ks-translate-btn:hover {
  background: rgba(13, 115, 119, 0.12);
  border-color: var(--color-primary);
}

.ks-translate-btn--active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.ks-translate-btn--active:hover {
  background: var(--color-primary-dark, #0a8a8e);
}

.ks-translate-btn--loading {
  opacity: 0.8;
  cursor: wait;
}

.ks-translate-btn--loading .ks-translate-btn__label {
  animation: ks-pulse-text 1.5s ease-in-out infinite;
}

@keyframes ks-pulse-text {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

.ks-translate-result {
  padding: 10px 12px;
  background: rgba(13, 115, 119, 0.04);
  border-left: 2px solid var(--color-primary);
  border-radius: 0 4px 4px 0;
}

.ks-translate-result__text {
  font: 400 0.875rem / 1.65 var(--font-sans);
  color: var(--color-text);
}

/* Transition */
.ks-fade-slide-enter-active {
  transition:
    opacity 0.2s var(--ease-smooth),
    transform 0.2s var(--ease-smooth);
}
.ks-fade-slide-leave-active {
  transition:
    opacity 0.15s var(--ease-smooth),
    transform 0.15s var(--ease-smooth);
}
.ks-fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
.ks-fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
