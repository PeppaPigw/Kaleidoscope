# Component Guidelines

> Component patterns and composition rules for Kaleidoscope frontend (Vue 3 / Nuxt 3).

---

## Design System — `Ks` Components

All Kaleidoscope design system components live in `components/ks/` and are prefixed with `Ks`. They are built on **Reka UI** headless primitives for accessibility, with fully custom editorial styling.

### Editorial Components

```vue
<!-- components/ks/KsDropCap.vue -->
<template>
  <p class="ks-drop-cap"><slot /></p>
</template>

<style>
.ks-drop-cap::first-letter {
  float: left;
  font-family: var(--font-display);
  font-size: clamp(3.4rem, 6vw, 5rem);
  line-height: .8;
  font-weight: 600;
  color: var(--color-primary);
  margin: .08em .14em 0 0;
}
</style>
```

```vue
<!-- components/ks/KsPullQuote.vue -->
<template>
  <blockquote class="ks-pull-quote">
    <slot />
    <cite v-if="$slots.cite" class="ks-pull-quote__cite"><slot name="cite" /></cite>
  </blockquote>
</template>
```

### Reka UI Integration

```vue
<!-- components/ks/KsButton.vue -->
<script setup lang="ts">
import { Button } from 'reka-ui'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
})
</script>

<template>
  <Button
    :class="[
      'ks-btn',
      `ks-btn--${variant}`,
      `ks-btn--${size}`,
    ]"
  >
    <slot />
  </Button>
</template>

<style>
.ks-btn { height: 40px; padding: 0 16px; border-radius: 0; font-family: var(--font-sans); font-weight: 500; }
.ks-btn--primary { background: var(--color-primary); color: var(--color-bg); }
.ks-btn--secondary { background: var(--color-surface); color: var(--color-text); border: 1px solid var(--color-border); }
.ks-btn--ghost { background: transparent; color: var(--color-secondary); }
</style>
```

---

## Component Patterns

### Composition Over Props

```vue
<!-- ✅ Good — composable slots -->
<KsEvidenceCard :evidence="evidence">
  <template #meta>{{ evidence.source }}</template>
  <template #quote>{{ evidence.text }}</template>
  <template #actions>
    <KsButton variant="ghost" @click="sendToDraft">Quote to Draft</KsButton>
  </template>
</KsEvidenceCard>

<!-- ❌ Bad — too many props -->
<KsEvidenceCard
  :evidence="evidence"
  :show-meta="true"
  :show-actions="true"
  :action-label="'Quote to Draft'"
  @action="sendToDraft"
/>
```

### Loading, Error & Empty States

Every data-dependent component must handle 4 states:

```vue
<script setup lang="ts">
const { data: paper, status, error } = useFetch(`/api/v1/papers/${paperId}`)
</script>

<template>
  <!-- Loading: warm skeleton -->
  <KsSkeleton v-if="status === 'pending'" class="h-64" />

  <!-- Error: editorial error message -->
  <KsErrorAlert v-else-if="error" :message="error.message" />

  <!-- Empty: helpful guidance -->
  <KsEmptyState v-else-if="!paper" message="This paper hasn't been indexed yet." />

  <!-- Success: actual content -->
  <PaperDetailView v-else :paper="paper" />
</template>
```

---

## Visualization Components

### Citation Graph (Cytoscape.js)

```vue
<!-- components/graph/CitationGraph.vue -->
<script setup lang="ts">
const cyRef = ref<HTMLElement>()

onMounted(async () => {
  const cytoscape = (await import('cytoscape')).default
  const cy = cytoscape({
    container: cyRef.value,
    elements: props.elements,
    layout: { name: 'cose' },
    style: [
      { selector: 'node', style: { 'background-color': '#0D7377', 'label': 'data(label)' } },
      { selector: 'edge', style: { 'line-color': '#E8E5E0', 'curve-style': 'bezier' } },
    ],
  })
})
</script>

<template>
  <div ref="cyRef" class="w-full h-[600px]" />
</template>
```

### Theme River (D3.js)

```vue
<!-- components/graph/ThemeRiver.vue -->
<script setup lang="ts">
import * as d3 from 'd3'

const svgRef = ref<SVGSVGElement>()

onMounted(() => {
  const svg = d3.select(svgRef.value)
  // D3 stream graph implementation
})
</script>

<template>
  <svg ref="svgRef" class="w-full" :viewBox="`0 0 ${width} ${height}`" />
</template>
```

### Trend Charts (ECharts)

```vue
<!-- components/charts/TrendChart.vue -->
<script setup lang="ts">
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const option = computed(() => buildTrendOption(props.data))
</script>

<template>
  <VChart :option="option" :style="{ height: '400px' }" autoresize />
</template>
```

---

## Writing Studio (Tiptap)

```vue
<!-- components/writing/DraftCanvas.vue -->
<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'

const editor = useEditor({
  extensions: [
    StarterKit,
    // Custom extensions for evidence cards, citations, etc.
  ],
  content: props.initialContent,
  editorProps: {
    attributes: {
      class: 'ks-draft-canvas font-serif text-base leading-relaxed',
    },
  },
})
</script>

<template>
  <div class="ks-writing-container">
    <EditorContent :editor="editor" />
  </div>
</template>
```

---

## Client-Only Components

Heavy visualization libraries must be lazy-loaded (client-only):

```vue
<!-- In page or parent component -->
<ClientOnly>
  <CitationGraph :elements="graphData" />
  <template #fallback>
    <KsSkeleton class="h-[600px]" />
  </template>
</ClientOnly>
```

---

## Rules

1. **One component per file** — no multi-component files
2. **Feature-grouped** — `components/paper/`, not `components/cards/`
3. **Props interface at top** — always define typed props with `defineProps<T>()`
4. **No inline styles** — use Tailwind classes + design system CSS
5. **Skeleton for every loading state** — no spinners for content areas
6. **`Ks` prefix for design system** — all shared UI components start with `Ks`
7. **Client-only for heavy libs** — Cytoscape, D3, ECharts, PDF.js via `<ClientOnly>`
8. **Emits typed** — always use `defineEmits<T>()`
