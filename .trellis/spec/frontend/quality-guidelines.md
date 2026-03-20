# Frontend Quality Guidelines

> Quality standards for Kaleidoscope frontend code.

---

## Tooling

| Tool | Purpose | Command |
|------|---------|---------|
| **ESLint** | Linting | `npm run lint` |
| **TypeScript** | Type checking | `npm run type-check` |
| **Prettier** | Formatting | `npm run format` |

---

## Accessibility

Kaleidoscope is a research tool used for extended periods. Accessibility matters:

1. **All interactive elements** must have `aria-label` or visible label
2. **Keyboard navigation** for all features (especially PDF reader)
3. **Color contrast** — WCAG AA minimum (4.5:1 for text)
4. **Focus indicators** — visible focus rings on all interactive elements
5. **Screen reader support** — semantic HTML, ARIA landmarks

---

## Performance

| Rule | Why | How |
|------|-----|-----|
| Lazy load heavy libs | Cytoscape.js, ECharts, PDF.js are large | `dynamic(() => import(...), { ssr: false })` |
| Virtualize long lists | Paper lists can be 1000+ items | `@tanstack/react-virtual` |
| Image optimization | Figure thumbnails | Next.js `<Image>` component |
| Debounce search | Reduce API calls | 300ms debounce |

---

## Forbidden Patterns

| Pattern | Why | Alternative |
|---------|-----|------------|
| `useEffect` for data fetching | Race conditions, no cache | TanStack Query |
| `any` type | Defeats TypeScript | `unknown` + type guards |
| Inline styles | Inconsistent, not responsive | Tailwind classes |
| `console.log` in production | Noise | Remove or use proper logging |
| Direct DOM manipulation | Conflicts with React | Use refs if needed |
| Nested ternaries in JSX | Unreadable | Extract to variables or early return |

---

## Component Checklist

Before committing a component:
- [ ] TypeScript strict — no `any`, no `@ts-ignore`
- [ ] Loading state with skeleton
- [ ] Error state with user-friendly message
- [ ] Empty state with helpful guidance
- [ ] Responsive on mobile (min-width: 375px)
- [ ] Keyboard accessible
- [ ] Unique `data-testid` for interactive elements
