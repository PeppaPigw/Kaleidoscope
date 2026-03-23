<script setup lang="ts">
/**
 * PaperImportUrl — quick URL import card for the dashboard.
 *
 * Lets users paste a PDF/HTML URL and import it via MinerU.
 * Shows status feedback during the async extraction.
 */

const apiUrl = useRuntimeConfig().public.apiUrl

const url = ref('')
const title = ref('')
const isHtml = ref(false)
const importing = ref(false)
const result = ref<{
  status: 'idle' | 'importing' | 'success' | 'error'
  paperId?: string
  message?: string
  markdownLength?: number
  sections?: number
}>({ status: 'idle' })

const showAdvanced = ref(false)

const isValidUrl = computed(() => {
  try {
    new URL(url.value)
    return true
  } catch {
    return false
  }
})

// Auto-detect HTML vs PDF from URL
watch(url, (v) => {
  if (v && !v.toLowerCase().endsWith('.pdf') && (
    v.includes('arxiv.org/abs') ||
    v.includes('html') ||
    v.includes('aclanthology.org') ||
    v.includes('openreview.net')
  )) {
    isHtml.value = true
  } else {
    isHtml.value = false
  }
})

async function handleImport() {
  if (!isValidUrl.value || importing.value) return

  importing.value = true
  result.value = { status: 'importing' }

  try {
    const resp = await $fetch<{
      paper_id: string
      title: string
      status: string
      error?: string
      markdown_length?: number
      sections?: number
    }>(`${apiUrl}/api/v1/papers/import-url`, {
      method: 'POST',
      body: {
        url: url.value,
        title: title.value || undefined,
        is_html: isHtml.value,
      },
    })

    result.value = {
      status: 'success',
      paperId: resp.paper_id,
      message: `Imported "${resp.title}" — ${resp.markdown_length?.toLocaleString() || '?'} chars`,
      markdownLength: resp.markdown_length ?? undefined,
      sections: resp.sections ?? undefined,
    }
    // Clear form
    url.value = ''
    title.value = ''
  } catch (err: any) {
    const detail = err?.data?.detail || err?.message || 'Import failed'
    result.value = {
      status: 'error',
      message: detail,
    }
  } finally {
    importing.value = false
  }
}

function goToPaper() {
  if (result.value.paperId) {
    navigateTo(`/reader/${result.value.paperId}`)
  }
}
</script>

<template>
  <div class="ks-import">
    <div class="ks-import__header">
      <h3 class="ks-import__title">Import Paper</h3>
      <span class="ks-import__badge">URL</span>
    </div>

    <form class="ks-import__form" @submit.prevent="handleImport">
      <div class="ks-import__field">
        <input
          id="import-url-input"
          v-model="url"
          type="url"
          class="ks-import__input"
          placeholder="https://arxiv.org/pdf/2401.00001 or HTML page URL"
          :disabled="importing"
          autocomplete="off"
        />
      </div>

      <button
        type="button"
        class="ks-import__toggle"
        @click="showAdvanced = !showAdvanced"
      >
        {{ showAdvanced ? '▾' : '▸' }} Options
      </button>

      <div v-if="showAdvanced" class="ks-import__advanced">
        <input
          v-model="title"
          type="text"
          class="ks-import__input ks-import__input--sm"
          placeholder="Custom title (optional)"
          :disabled="importing"
        />
        <label class="ks-import__checkbox">
          <input v-model="isHtml" type="checkbox" :disabled="importing" />
          <span>HTML source (auto-detected)</span>
        </label>
      </div>

      <button
        id="import-submit-btn"
        type="submit"
        class="ks-import__submit"
        :disabled="!isValidUrl || importing"
      >
        <span v-if="importing" class="ks-import__spinner" aria-hidden="true" />
        {{ importing ? 'Extracting…' : 'Import & Extract' }}
      </button>
    </form>

    <!-- Status -->
    <Transition name="ks-fade">
      <div
        v-if="result.status !== 'idle'"
        :class="['ks-import__status', `ks-import__status--${result.status}`]"
      >
        <template v-if="result.status === 'importing'">
          <span class="ks-import__spinner" /> Extracting content via MinerU…
        </template>
        <template v-else-if="result.status === 'success'">
          <span>✓ {{ result.message }}</span>
          <div v-if="result.sections" class="ks-import__meta">
            {{ result.sections }} sections · {{ (result.markdownLength ?? 0).toLocaleString() }} chars
          </div>
          <button class="ks-import__link" @click="goToPaper">Open in Reader →</button>
        </template>
        <template v-else-if="result.status === 'error'">
          <span>✗ {{ result.message }}</span>
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.ks-import {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: 20px;
  background: var(--color-bg);
}

.ks-import__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ks-import__title {
  font: 600 1rem / 1.2 var(--font-serif);
  color: var(--color-text);
}

.ks-import__badge {
  font: 500 0.65rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border: 1px solid var(--color-primary);
  border-radius: 3px;
  color: var(--color-primary);
}

.ks-import__form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ks-import__field {
  position: relative;
}

.ks-import__input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font: 400 0.875rem / 1.4 var(--font-body);
  color: var(--color-text);
  background: var(--color-bg);
  transition: border-color var(--duration-fast) var(--ease-smooth);
  box-sizing: border-box;
}
.ks-import__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(196, 163, 90, 0.15);
}
.ks-import__input--sm {
  font-size: 0.8rem;
  padding: 7px 12px;
}

.ks-import__toggle {
  border: none;
  background: none;
  font: 400 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
  cursor: pointer;
  text-align: left;
  padding: 0;
}
.ks-import__toggle:hover {
  color: var(--color-text);
}

.ks-import__advanced {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
}

.ks-import__checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font: 400 0.8rem / 1 var(--font-body);
  color: var(--color-secondary);
  cursor: pointer;
}
.ks-import__checkbox input {
  accent-color: var(--color-primary);
}

.ks-import__submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font: 600 0.85rem / 1 var(--font-body);
  color: #fff;
  background: var(--color-primary);
  cursor: pointer;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}
.ks-import__submit:hover:not(:disabled) {
  opacity: 0.9;
}
.ks-import__submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ks-import__spinner {
  display: inline-block;
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: ks-spin 0.6s linear infinite;
}
@keyframes ks-spin {
  to { transform: rotate(360deg); }
}

.ks-import__status {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 6px;
  font: 400 0.85rem / 1.4 var(--font-body);
}
.ks-import__status--importing {
  background: rgba(196, 163, 90, 0.08);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}
.ks-import__status--success {
  background: rgba(34, 139, 34, 0.06);
  color: #228b22;
}
.ks-import__status--error {
  background: rgba(200, 50, 50, 0.06);
  color: #c83232;
}

.ks-import__meta {
  font: 400 0.75rem / 1 var(--font-mono);
  color: var(--color-secondary);
  margin-top: 6px;
}

.ks-import__link {
  border: none;
  background: none;
  font: 600 0.8rem / 1 var(--font-body);
  color: var(--color-primary);
  cursor: pointer;
  margin-top: 8px;
  padding: 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.ks-fade-enter-active,
.ks-fade-leave-active {
  transition: opacity var(--duration-normal) var(--ease-smooth);
}
.ks-fade-enter-from,
.ks-fade-leave-to {
  opacity: 0;
}
</style>
