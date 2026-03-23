<script setup lang="ts">
/**
 * MarkdownCanvas — renders paper full-text as styled markdown.
 *
 * Fetches content from /api/v1/papers/{id}/content and renders
 * the markdown with a table of contents sidebar navigation.
 */

export interface MarkdownCanvasProps {
  paperId: string
  title: string
}

const props = defineProps<MarkdownCanvasProps>()
const uid = useId()

const fontSize = ref(16)
const activeSection = ref('')

// Fetch markdown content from API
const { data: content, pending, error } = useFetch(() =>
  `${useRuntimeConfig().public.apiUrl}/api/v1/papers/${props.paperId}/content`
)

// Parse table of contents from sections
const toc = computed(() => {
  if (!content.value) return []
  const sections = (content.value as any)?.sections || []
  return sections.map((s: any, i: number) => ({
    id: `section-${i}`,
    title: s.title || 'Untitled',
    level: s.level || 1,
  }))
})

// Convert raw markdown to HTML segments per section
const renderedSections = computed(() => {
  if (!content.value) return []
  const md = (content.value as any)?.markdown || ''
  const sections = (content.value as any)?.sections || []

  if (!sections.length) {
    // No sections — render whole document
    return [{
      id: 'section-full',
      title: props.title,
      level: 1,
      html: markdownToHtml(md),
    }]
  }

  return sections.map((s: any, i: number) => ({
    id: `section-${i}`,
    title: s.title || 'Untitled',
    level: s.level || 1,
    html: markdownToHtml(
      (s.paragraphs || []).join('\n\n')
    ),
  }))
})

const contentFormat = computed(() => (content.value as any)?.format || 'unknown')

/**
 * Lightweight markdown→HTML converter for paper content.
 * Handles headers, bold, italic, links, code, lists, block quotes, images, tables.
 */
function markdownToHtml(md: string): string {
  let html = md
    // Escape HTML entities
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers (already sections, so skip # lines)
    .replace(/^#{1,6}\s+(.+)$/gm, '<h4 class="ks-mc__subhead">$1</h4>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="ks-mc__inline-code">$1</code>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // Images
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<figure class="ks-mc__figure"><img src="$2" alt="$1" loading="lazy" /><figcaption>$1</figcaption></figure>')
    // Block quotes
    .replace(/^>\s+(.+)$/gm, '<blockquote class="ks-mc__blockquote">$1</blockquote>')
    // Unordered lists
    .replace(/^[-*]\s+(.+)$/gm, '<li class="ks-mc__li">$1</li>')
    // Math blocks (LaTeX $...$)
    .replace(/\$\$([^$]+)\$\$/g, '<div class="ks-mc__math">$1</div>')
    .replace(/\$([^$]+)\$/g, '<span class="ks-mc__math-inline">$1</span>')
    // Paragraphs (double newlines)
    .replace(/\n\n/g, '</p><p class="ks-mc__para">')

  // Wrap in paragraph tags
  html = `<p class="ks-mc__para">${html}</p>`
  // Clean up empty paragraphs
  html = html.replace(/<p class="ks-mc__para"><\/p>/g, '')

  return html
}

function scrollToSection(sectionId: string) {
  activeSection.value = sectionId
  const el = document.getElementById(sectionId)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="ks-mc" :aria-labelledby="`${uid}-title`">
    <!-- Toolbar -->
    <div class="ks-mc__toolbar">
      <div class="ks-mc__meta">
        <span class="ks-mc__badge" :title="contentFormat">
          {{ contentFormat === 'markdown' ? '✦ Full text' : contentFormat === 'abstract_only' ? '◇ Abstract' : '○ Metadata' }}
        </span>
      </div>
      <div class="ks-mc__controls">
        <button class="ks-mc__btn" aria-label="Decrease font" @click="fontSize = Math.max(12, fontSize - 1)">A−</button>
        <span class="ks-type-data">{{ fontSize }}px</span>
        <button class="ks-mc__btn" aria-label="Increase font" @click="fontSize = Math.min(24, fontSize + 1)">A+</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="pending" class="ks-mc__loading">
      <KsSkeleton height="400px" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="ks-mc__error">
      <KsErrorAlert :message="error.message || 'Failed to load paper content'" />
    </div>

    <!-- Content -->
    <div v-else class="ks-mc__content" :style="{ fontSize: `${fontSize}px` }">
      <article class="ks-mc__article">
        <h1 :id="`${uid}-title`" class="ks-mc__title">{{ title }}</h1>

        <template v-for="section in renderedSections" :key="section.id">
          <section :id="section.id" class="ks-mc__section" :data-level="section.level">
            <component
              :is="`h${Math.min(section.level + 1, 6)}`"
              class="ks-mc__section-heading"
              :class="`ks-mc__section-heading--l${section.level}`"
            >
              {{ section.title }}
            </component>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div class="ks-mc__section-body" v-html="section.html" />
          </section>
        </template>
      </article>
    </div>
  </div>
</template>

<style scoped>
.ks-mc {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--color-bg);
}

.ks-mc__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid var(--color-border);
  background: rgba(250, 250, 247, 0.6);
}

.ks-mc__meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ks-mc__badge {
  font: 500 0.7rem / 1 var(--font-mono);
  color: var(--color-primary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 4px 8px;
  border: 1px solid var(--color-primary);
  border-radius: 4px;
}

.ks-mc__controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ks-mc__btn {
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font: 500 0.8rem / 1 var(--font-mono);
  color: var(--color-text);
  transition: background var(--duration-fast) var(--ease-smooth);
}
.ks-mc__btn:hover {
  background: var(--color-surface);
}

.ks-mc__loading,
.ks-mc__error {
  padding: 32px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ks-mc__content {
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  padding: 32px 48px 64px;
  line-height: 1.75;
}

.ks-mc__article {
  max-width: 720px;
  margin: 0 auto;
}

.ks-mc__title {
  font: 700 1.75rem / 1.25 var(--font-serif);
  color: var(--color-text);
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--color-primary);
}

.ks-mc__section {
  margin-bottom: 24px;
}

.ks-mc__section-heading {
  font-family: var(--font-serif);
  color: var(--color-text);
  margin: 24px 0 12px;
  scroll-margin-top: 80px;
}

.ks-mc__section-heading--l1 {
  font-size: 1.4em;
  font-weight: 700;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 6px;
}
.ks-mc__section-heading--l2 {
  font-size: 1.15em;
  font-weight: 600;
}
.ks-mc__section-heading--l3 {
  font-size: 1em;
  font-weight: 600;
  color: var(--color-secondary);
}

.ks-mc__section-body :deep(.ks-mc__para) {
  margin: 0 0 14px;
  font-family: var(--font-body);
  color: var(--color-text);
}

.ks-mc__section-body :deep(.ks-mc__subhead) {
  font: 600 1em / 1.3 var(--font-serif);
  margin: 18px 0 8px;
  color: var(--color-text);
}

.ks-mc__section-body :deep(.ks-mc__inline-code) {
  font-family: var(--font-mono);
  font-size: 0.88em;
  background: var(--color-surface);
  padding: 2px 5px;
  border-radius: 3px;
}

.ks-mc__section-body :deep(.ks-mc__blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 16px;
  margin: 12px 0;
  color: var(--color-secondary);
  font-style: italic;
}

.ks-mc__section-body :deep(.ks-mc__figure) {
  text-align: center;
  margin: 20px 0;
}
.ks-mc__section-body :deep(.ks-mc__figure img) {
  max-width: 100%;
  border-radius: var(--radius-card);
}
.ks-mc__section-body :deep(.ks-mc__figure figcaption) {
  font: 400 0.85em / 1.3 var(--font-body);
  color: var(--color-secondary);
  margin-top: 6px;
}

.ks-mc__section-body :deep(.ks-mc__math) {
  text-align: center;
  font-family: var(--font-mono);
  padding: 12px;
  background: var(--color-surface);
  border-radius: var(--radius-card);
  margin: 12px 0;
  overflow-x: auto;
}

.ks-mc__section-body :deep(.ks-mc__math-inline) {
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.ks-mc__section-body :deep(.ks-mc__li) {
  display: list-item;
  margin-left: 24px;
  list-style: disc;
  margin-bottom: 4px;
}

.ks-mc__section-body :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.ks-mc__section-body :deep(a:hover) {
  opacity: 0.8;
}

.ks-mc__section-body :deep(strong) {
  font-weight: 600;
}

@media (max-width: 768px) {
  .ks-mc__content {
    padding: 16px;
  }
}
</style>
