# Frontend Quality Guidelines

> Quality standards for Kaleidoscope frontend code (Vue 3 / Nuxt 3).

---

## Tooling

| Tool | Purpose | Command |
|------|---------|---------|
| **@nuxt/eslint** | Linting (ESLint + Vue rules) | `pnpm lint` |
| **vue-tsc** | Type checking | `pnpm type-check` |
| **Prettier** | Formatting | `pnpm format` |
| **Vitest** | Unit testing | `pnpm test` |
| **Playwright** | E2E testing | `pnpm test:e2e` |

---

## Accessibility

Kaleidoscope is a research tool used for extended periods. Accessibility matters:

1. **All interactive elements** must have `aria-label` or visible label (Reka UI provides this by default)
2. **Keyboard navigation** for all features (especially PDF reader, graph explorer, drag-and-drop)
3. **Color contrast** — WCAG AA minimum (4.5:1 for text). Verified: `#1A1A1A` on `#FAFAF7` = 14.2:1 ✅
4. **Focus indicators** — visible focus rings using `--color-primary` on all interactive elements
5. **Screen reader support** — semantic HTML, ARIA landmarks, `role` attributes
6. **Reduced motion** — `prefers-reduced-motion` media query disables all animations, keeps `opacity 100ms` transitions

---

## Performance

| Rule | Why | How |
|------|-----|-----|
| Lazy load heavy libs | Cytoscape.js, D3.js, ECharts, PDF.js are large | `<ClientOnly>` + dynamic `import()` |
| Virtualize long lists | Paper lists can be 1000+ items | `@vueuse/virtual` or `vue-virtual-scroller` |
| Image optimization | Figure thumbnails | Nuxt `<NuxtImg>` component |
| Debounce search | Reduce API calls | 300ms via `refDebounced` |
| Code-split by page | Each page loads only its deps | Nuxt auto code-splitting |
| Tree-shake ECharts | Only import used chart types | Manual `use()` registration |

---

## Forbidden Patterns

| Pattern | Why | Alternative |
|---------|-----|------------|
| `onMounted` + `fetch` for data | Not SSR-compatible, no cache | `useFetch` / `useAsyncData` |
| `any` type | Defeats TypeScript | `unknown` + type guards |
| Inline styles | Inconsistent, not responsive | Tailwind classes + design system CSS |
| `console.log` in production | Noise | Remove or use `useLogger` composable |
| Direct DOM manipulation | Conflicts with Vue reactivity | Use `ref` + template refs |
| Nested ternaries in template | Unreadable | `v-if`/`v-else-if`/`v-else` chain |
| Overriding Reka UI styles with `!important` | Fragile | Use design system CSS classes |
| `watch` + manual fetch | Race conditions | `useFetch` with `watch` option |

---

## Component Checklist

Before committing a component:
- [ ] TypeScript strict — no `any`, no `@ts-expect-error`
- [ ] Loading state with `<KsSkeleton />` (warm cream pulse)
- [ ] Error state with user-friendly editorial message
- [ ] Empty state with helpful guidance text
- [ ] Responsive: 1440px / 1280px / 768px breakpoints
- [ ] Keyboard accessible (tab order, Enter/Space activation)
- [ ] Unique `data-testid` for interactive elements
- [ ] `prefers-reduced-motion` respected for animations
- [ ] Design tokens used (never hardcoded colors/fonts)
- [ ] Provenance trigger on AI-generated fields

---

## Git Commit Convention

```
feat(reader): add semantic highlights layer
fix(search): debounce claim-first mode toggle
style(ks): align pull-quote typography with design tokens
refactor(workspace): extract corpus shelf composable
```
