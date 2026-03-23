# Frontend Development Guidelines

> Conventions for Kaleidoscope's Vue 3 + Nuxt 3 frontend.

---

## Overview

Kaleidoscope frontend is a **Nuxt 3.19** (Vue 3.5) application with a **magazine/editorial aesthetic**. It communicates with the FastAPI backend via REST API, powered by Nuxt's built-in `$fetch`/`useFetch`.

**Design Language**: Editorial style inspired by Vogue, Kinfolk, Monocle — content-first, serif typography, warm cream palette, paper-like layouts with controlled white space.

**Key Features**:
- PDF reader with semantic annotation layers (PDF.js)
- Hybrid search interface (keyword + semantic + graph + claim-first)
- Citation/concept graph visualization (Cytoscape.js + D3.js)
- Theme river & trend analytics (D3.js + ECharts)
- Research workspace with drag-and-drop corpus management
- Cross-paper synthesis studio with evidence traceability
- Writing studio with Tiptap rich text editor
- Knowledge garden with spaced review

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Nuxt app directory, module organization | ✅ Filled |
| [Component Guidelines](./component-guidelines.md) | Component patterns, composition, design system | ✅ Filled |
| [Hook Guidelines](./hook-guidelines.md) | Composables, data fetching, mutation patterns | ✅ Filled |
| [State Management](./state-management.md) | Server state, client state, URL state | ✅ Filled |
| [Quality Guidelines](./quality-guidelines.md) | Linting, testing, accessibility | ✅ Filled |
| [Type Safety](./type-safety.md) | TypeScript patterns, API type generation | ✅ Filled |

---

## Tech Stack

### Core Framework

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Framework | **Nuxt** | 3.19 | SSR, file-based routing, auto-imports, SEO, built-in `$fetch` |
| View Layer | **Vue** | 3.5+ | Built-in transition system ideal for 4 motion categories; SFC template syntax natural for editorial layouts |
| Language | **TypeScript** | 5.7+ (strict) | Type safety across frontend |
| Package Manager | **pnpm** | 9.x | Fast, disk-efficient, strict dependency resolution |

### Styling & Design System

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Utility CSS | **Tailwind CSS** | v4 | CSS-first config integrates natively with design tokens; JIT compilation |
| Design Tokens | **CSS Custom Properties** | — | `--ks-primary`, `--ks-bg`, etc. defined in `:root`, consumed by both Tailwind and custom CSS |
| Custom CSS | **Vanilla CSS** | — | Drop Caps, Pull Quotes, Margin Notes, baseline grids, multi-column layouts — editorial elements that transcend utility classes |
| Icons | **Lucide Vue Next** | latest | Consistent, tree-shakeable icon set |
| Fonts | **@fontsource** | — | Self-hosted: Playfair Display, Source Serif Pro, Inter, JetBrains Mono |

### UI Components

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Headless Primitives | **Reka UI** | latest | Accessible, unstyled component primitives (successor to Radix Vue). Full control over magazine styling |
| Custom Design System | **`components/ks/`** | — | All 133+ components custom-built on Reka primitives with editorial styling. NOT shadcn-vue — too opinionated for magazine feel |

### Animation & Motion

| Category | Technology | Version | Role |
|----------|-----------|---------|------|
| Page Transitions | **Vue `<Transition>`** | built-in | `page-handoff` — entering/leaving pages |
| Complex Timelines | **GSAP** | 3.12 | Theme river animation, graph morphing, staggered reveals, scroll-linked effects |
| Declarative Motion | **@vueuse/motion** | 2.x | `paper-reveal` & `analytic-focus` — component-level declarative animations |
| System Feedback | **Vue `<Transition>`** | built-in | `system-feedback` — save/error/confirm flash effects |

**Motion Architecture**:
```
page-handoff    → Vue <Transition> + Nuxt page transitions
paper-reveal    → @vueuse/motion (v-motion directives)
analytic-focus  → CSS transitions (160ms, --ks-ease-focus)
system-feedback → Vue <Transition> + CSS keyframes (560ms)
```

### Data Visualization

| Category | Technology | Version | Scope |
|----------|-----------|---------|-------|
| Network Graphs | **Cytoscape.js** | 3.30 | Citation graph, concept atlas, collaboration atlas — interactive node-link diagrams |
| Bespoke Viz | **D3.js** | 7.x | Theme river, venue ecology, burst moments — custom narrative visualizations |
| Standard Charts | **ECharts** | 5.5 (vue-echarts) | Trend snapshots, citation behavior curves, pipeline quality metrics — standard chart library |

**Visualization Boundaries** (strict):
- D3 → custom/artistic/narrative viz only
- ECharts → standard charts (line, bar, scatter, heatmap)
- Cytoscape → network/graph only
- Never mix in the same component

### Content & Editing

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Rich Text Editor | **Tiptap** | 3.x | Writing Studio — ProseMirror-based, best Vue 3 support, collaborative editing ready, extensible with custom nodes for evidence cards |
| PDF Rendering | **PDF.js** | 4.x | Reading Canvas — academic PDF with custom annotation overlay. Direct wrapper (not vue-pdf-embed) for full control over highlight layers |
| Markdown | **@nuxt/content** | 3.x | Knowledge garden note rendering |

### State & Data

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| State Management | **Pinia** | 3.x | Vue's official state management — workspaces, reading state, preferences |
| Server State | **Nuxt `useFetch` / `useAsyncData`** | built-in | SSR-aware data fetching with caching — replaces TanStack Query |
| Form Validation | **Zod** | 4 | Runtime schema validation; API types aligned via OpenAPI/codegen from FastAPI |
| HTTP Client | **Nuxt `$fetch`** | built-in (ofetch) | Typed HTTP client — no separate axios/ofetch install needed |

### Interaction

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| Drag & Drop | **VueDraggable Plus** | latest | SortableJS-based — corpus shelf, evidence card ordering, workspace timeline |
| Virtual Scroll | **vue-virtual-scroller** | 2.x | Paper lists, search results (1000+ items) |
| Keyboard | **@vueuse/core** | latest | Keyboard shortcuts, focus management |

### Testing

| Category | Technology | Version | Scope |
|----------|-----------|---------|-------|
| Unit Testing | **Vitest** | 3.x | Composables, stores, utility functions |
| Component Testing | **@vue/test-utils** | 2.x | Component rendering, interaction |
| E2E Testing | **Playwright** | latest | Critical user flows (search → paper → reader → writing) |
| Coverage | **@vitest/coverage-v8** | — | Minimum 70% for composables, 50% for components |

### Auth & Real-time

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------||
| Authentication | **nuxt-auth-utils** | latest | Session-based auth integrated with FastAPI JWT |
| Real-time Sync | **Yjs** + **y-websocket** | latest | Collaborative editing in Writing Studio (Tiptap integration) |
| WebSocket | **Nuxt WebSocket** | — | Research alerts, job monitor live updates |

### Deployment & Runtime

| Category | Spec |
|----------|------|
| Node.js | 22 LTS |
| Nitro Preset | `node-server` (default) or `vercel` |
| SSR | Enabled for SEO pages (Dashboard, Discover, Paper Profile, Researcher) |
| CSR-only | Reader, Writing Studio, Synthesis (heavy client interaction) |
| Image Optimization | `@nuxt/image` + IPX (self-hosted) |
| SEO | `@nuxt/seo` — auto sitemap, OG tags, structured data for papers |

---

## Dev Commands

```bash
pnpm dev           # Nuxt dev server (http://localhost:3000)
pnpm build         # Production build
pnpm preview       # Preview production build
pnpm lint          # ESLint (with @nuxt/eslint)
pnpm type-check    # vue-tsc type checking
pnpm test          # Vitest unit/component tests
pnpm test:e2e      # Playwright E2E tests
pnpm generate      # Static site generation (if needed)
```

---

## Design Token Integration

```css
/* styles/tokens.css — imported by Tailwind v4 */
@theme {
  --color-primary: #0D7377;
  --color-bg: #FAFAF7;
  --color-surface: #FFFFFF;
  --color-text: #1A1A1A;
  --color-secondary: #6B6B6B;
  --color-accent: #C4A35A;
  --color-border: #E8E5E0;

  --font-display: "Playfair Display", serif;
  --font-serif: "Source Serif Pro", serif;
  --font-sans: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  --ease-page: cubic-bezier(.16, 1, .3, 1);
  --ease-focus: cubic-bezier(.22, 1, .36, 1);
  --ease-feedback: cubic-bezier(.2, .9, .2, 1);
}
```

Usage in templates:
```vue
<template>
  <h1 class="font-display text-4xl text-text">Kaleidoscope</h1>
  <p class="font-serif text-base text-secondary">Research reimagined</p>
</template>
```

---

**Language**: All code comments, variable names, and documentation in **English**.
