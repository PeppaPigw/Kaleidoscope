# Frontend Directory Structure

> How the Kaleidoscope frontend is organized.

---

## Directory Layout

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout (providers, nav)
│   ├── page.tsx                  # Home / Dashboard
│   ├── (auth)/                   # Auth group
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── papers/
│   │   ├── page.tsx              # Paper list / search results
│   │   └── [id]/
│   │       ├── page.tsx          # Paper detail view
│   │       └── reader/page.tsx   # PDF reader view
│   ├── search/
│   │   └── page.tsx              # Advanced search
│   ├── collections/
│   │   ├── page.tsx              # Collection list
│   │   └── [id]/page.tsx         # Collection detail
│   ├── graph/
│   │   └── page.tsx              # Citation graph explorer
│   ├── trends/
│   │   └── page.tsx              # Trend analytics dashboard
│   ├── authors/
│   │   └── [id]/page.tsx         # Author profile
│   └── settings/
│       └── page.tsx              # User settings, subscriptions
│
├── components/
│   ├── ui/                       # shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   ├── paper/                    # Paper-specific components
│   │   ├── paper-card.tsx        # Paper list item
│   │   ├── paper-detail.tsx      # Full paper view
│   │   ├── paper-metadata.tsx    # Metadata display
│   │   └── paper-summary.tsx     # AI-generated summary levels
│   ├── search/                   # Search components
│   │   ├── search-bar.tsx        # Main search input
│   │   ├── search-filters.tsx    # Faceted filters sidebar
│   │   ├── search-results.tsx    # Results list
│   │   └── search-mode-toggle.tsx # keyword/semantic/hybrid toggle
│   ├── reader/                   # PDF reader components
│   │   ├── pdf-viewer.tsx        # PDF.js wrapper
│   │   ├── section-nav.tsx       # Section-aware TOC sidebar
│   │   ├── figure-sidebar.tsx    # Extracted figures panel
│   │   └── annotation-layer.tsx  # Highlights and notes overlay
│   ├── graph/                    # Graph visualization
│   │   ├── citation-graph.tsx    # Cytoscape.js citation network
│   │   ├── coauthor-graph.tsx    # Co-authorship network
│   │   └── graph-controls.tsx    # Zoom, filter, layout controls
│   ├── collection/               # Collection management
│   │   ├── collection-card.tsx
│   │   ├── tag-input.tsx
│   │   └── reading-status.tsx
│   ├── charts/                   # ECharts wrappers
│   │   ├── trend-chart.tsx
│   │   ├── topic-map.tsx
│   │   └── publication-timeline.tsx
│   └── layout/                   # Layout components
│       ├── navbar.tsx
│       ├── sidebar.tsx
│       └── breadcrumbs.tsx
│
├── hooks/                        # Custom React hooks
│   ├── use-papers.ts             # Paper CRUD + search
│   ├── use-search.ts             # Search with debounce
│   ├── use-collections.ts        # Collection management
│   ├── use-graph.ts              # Graph data fetching
│   └── use-pdf.ts                # PDF loading and parsing
│
├── lib/                          # Utilities and config
│   ├── api-client.ts             # Typed API client (fetch wrapper)
│   ├── constants.ts              # App-wide constants
│   └── utils.ts                  # Shared utilities
│
├── types/                        # TypeScript type definitions
│   ├── paper.ts                  # Paper, Author, Venue types
│   ├── search.ts                 # SearchQuery, SearchResult
│   ├── graph.ts                  # Graph node/edge types
│   └── api.ts                    # API response wrappers
│
├── styles/
│   └── globals.css               # Tailwind base + custom styles
│
├── public/
│   └── ...
│
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## Organization Rules

1. **Page components** (`app/`) — Thin, compose feature components. No business logic.
2. **Feature components** (`components/{feature}/`) — Grouped by feature domain, not by type.
3. **UI primitives** (`components/ui/`) — shadcn/ui components only. Don't modify heavily.
4. **Hooks** (`hooks/`) — One hook file per feature domain. All data fetching lives here.
5. **Types** (`types/`) — Shared TypeScript types. Mirror backend Pydantic schemas.

---

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Components | `PascalCase` | `PaperCard.tsx` → `paper-card.tsx` (file) |
| Hooks | `camelCase` with `use` prefix | `usePapers`, `useSearch` |
| Types | `PascalCase` | `Paper`, `SearchResult` |
| Files | `kebab-case` | `paper-card.tsx`, `search-filters.tsx` |
| CSS classes | Tailwind utilities | `className="flex items-center gap-2"` |
