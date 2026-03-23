# State Management

> How state is managed across the Kaleidoscope frontend (Vue 3 / Nuxt 3).

---

## State Categories

| Category | Tool | Examples |
|----------|------|---------|
| **Server State** | Nuxt `useFetch` / `useAsyncData` | Paper data, search results, graph data, workspace corpus |
| **URL State** | Nuxt `useRoute` / `navigateTo` | Search query, filters, page number, reading mode |
| **UI State** | Vue `ref` / `reactive` | Modal open/close, sidebar collapse, panel resize |
| **Form State** | VeeValidate + Zod (or plain `ref`) | Import form, annotation editor, synthesis prompt |
| **Global Client State** | Pinia 3 (persisted) | Reading preferences, theme, active workspace |
| **Cross-component Event** | Vue `provide` / `inject` | Provenance drawer trigger, evidence card selection |

---

## Principles

### 1. Server State First

Most "state" in Kaleidoscope is server data. Use `useFetch` — don't duplicate:

```vue
<script setup lang="ts">
// ✅ Good — server state via useFetch
const { data: papers } = await useFetch('/api/v1/papers')

// ❌ Bad — duplicating server data
const papers = ref([])
onMounted(async () => {
  papers.value = await $fetch('/api/v1/papers')
})
</script>
```

### 2. URL State for Shareable State

Search queries, filters, view modes should live in the URL:

```vue
<script setup lang="ts">
// ✅ Good — state in URL, shareable, SSR-friendly
const route = useRoute()
const query = computed(() => route.query.q as string ?? '')
const mode = computed(() => route.query.mode as SearchMode ?? 'hybrid')

function updateSearch(q: string) {
  navigateTo({ query: { ...route.query, q } })
}
</script>
```

### 3. Minimal Global Client State (Pinia)

Only use Pinia for truly global, client-only preferences:

```typescript
// stores/preferences.ts
export const usePreferences = defineStore('preferences', () => {
  const theme = ref<'light' | 'dark'>('light')
  const readerFontSize = ref(16)
  const readingMode = ref<'focus' | 'evidence' | 'methods' | 'skim'>('focus')
  const sidebarCollapsed = ref(false)

  return { theme, readerFontSize, readingMode, sidebarCollapsed }
}, {
  persist: true, // persisted to localStorage via pinia-plugin-persistedstate
})
```

```typescript
// stores/workspace.ts
export const useWorkspaceStore = defineStore('workspace', () => {
  const activeWorkspaceId = ref<string | null>(null)
  const recentWorkspaces = ref<string[]>([])

  function setActive(id: string) {
    activeWorkspaceId.value = id
    recentWorkspaces.value = [id, ...recentWorkspaces.value.filter(w => w !== id)].slice(0, 5)
  }

  return { activeWorkspaceId, recentWorkspaces, setActive }
}, {
  persist: true,
})
```

### 4. Cross-Component Communication (Provide/Inject)

For features like the Provenance Drawer that can be triggered from any page:

```typescript
// Provide in app.vue or layout
const provenanceState = useProvenance()
provide('provenance', provenanceState)

// Inject in any child component
const { showProvenance } = inject('provenance')!
```

---

## Rules

1. **Default to server state** — if data comes from API, use `useFetch`
2. **URL for navigation state** — search, filters, page, view mode
3. **No prop drilling >3 levels** — extract to composable or use `provide`/`inject`
4. **No Vuex** — Pinia 3 for the rare global client state needs
5. **Persist sparingly** — only user preferences, not data
6. **`computed` for derived state** — never store derived values in `ref`
