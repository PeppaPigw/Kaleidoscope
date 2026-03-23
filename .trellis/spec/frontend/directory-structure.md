# Frontend Directory Structure

> How the Kaleidoscope frontend is organized (Nuxt 3 App Directory).

---

## Directory Layout

```
frontend/
├── app/                              # Nuxt App Directory
│   ├── app.vue                       # Root app (providers, global layout)
│   ├── error.vue                     # Global error page
│   │
│   ├── layouts/                      # Layout templates
│   │   ├── default.vue               # Main layout (sidebar + topbar)
│   │   ├── reader.vue                # Reader layout (fullscreen, minimal chrome)
│   │   ├── writing.vue               # Writing layout (wide canvas, evidence drawer)
│   │   └── auth.vue                  # Auth layout (centered, minimal)
│   │
│   ├── pages/                        # File-based routing
│   │   ├── index.vue                 # → /dashboard (redirect)
│   │   ├── dashboard.vue             # Dashboard — morning briefing cover
│   │   │
│   │   ├── discover/
│   │   │   └── index.vue             # Discovery Explorer
│   │   ├── search.vue                # Search Results
│   │   │
│   │   ├── papers/
│   │   │   └── [paperId].vue         # Paper Profile
│   │   ├── reader/
│   │   │   └── [paperId].vue         # Smart Reader (uses reader layout)
│   │   │
│   │   ├── researchers/
│   │   │   ├── index.vue             # Researcher search/browse
│   │   │   └── [researcherId].vue    # Researcher Intelligence
│   │   │
│   │   ├── analysis/
│   │   │   └── evidence.vue          # Evidence & Methods Lab
│   │   │
│   │   ├── insights/
│   │   │   └── landscape.vue         # Graph & Trends
│   │   │
│   │   ├── workspaces/
│   │   │   ├── index.vue             # Workspace list
│   │   │   └── [workspaceId].vue     # Research Workspace
│   │   │
│   │   ├── synthesis.vue             # Synthesis Studio
│   │   │
│   │   ├── writing.vue               # Writing Studio (uses writing layout)
│   │   │
│   │   ├── knowledge.vue             # Knowledge Garden
│   │   │
│   │   ├── team.vue                  # Team Collaboration Hub
│   │   ├── automation.vue            # Automation Center
│   │   ├── admin.vue                 # Admin & Quality Center
│   │   │
│   │   └── (auth)/
│   │       ├── login.vue
│   │       └── register.vue
│   │
│   ├── middleware/                    # Route middleware
│   │   ├── auth.ts                   # Authentication guard
│   │   └── workspace.ts              # Workspace context loader
│   │
│   └── plugins/                      # Nuxt plugins
│       ├── gsap.client.ts            # GSAP registration (client-only)
│       ├── cytoscape.client.ts       # Cytoscape.js registration
│       └── pdf.client.ts             # PDF.js worker registration
│
├── components/                       # Auto-imported components
│   ├── ks/                           # Kaleidoscope Design System
│   │   ├── KsCard.vue                # Base card (editorial border, 2px radius)
│   │   ├── KsButton.vue              # Button (square corners, teal/white)
│   │   ├── KsTag.vue                 # Tag/badge
│   │   ├── KsSkeleton.vue            # Loading skeleton (warm pulse)
│   │   ├── KsDropCap.vue             # Editorial drop cap
│   │   ├── KsPullQuote.vue           # Editorial pull quote
│   │   ├── KsMarginNote.vue          # Editorial margin note
│   │   ├── KsPageHeader.vue          # Sticky running page header
│   │   ├── KsSectionDivider.vue      # Decorative section divider
│   │   ├── KsFullBleed.vue           # Full-bleed image container
│   │   ├── KsResearchIntent.vue      # Cross-page Research Intent Card
│   │   ├── KsEvidenceCard.vue        # Cross-page Evidence Card
│   │   ├── KsDraftTarget.vue         # Cross-page Draft Target
│   │   └── KsProvenanceDrawer.vue    # Global provenance drawer
│   │
│   ├── dashboard/                    # Dashboard page components
│   │   ├── DashboardHero.vue
│   │   ├── BriefingStrip.vue
│   │   ├── ReadingShelf.vue
│   │   ├── TrendSnapshot.vue
│   │   ├── ResearchAlerts.vue
│   │   └── WatchlistHub.vue
│   │
│   ├── discover/                     # Discovery Explorer
│   │   ├── TopicsWall.vue
│   │   ├── QueryComposer.vue
│   │   ├── FacetWall.vue
│   │   └── RecommendationStream.vue
│   │
│   ├── search/                       # Search components
│   │   ├── QueryRibbon.vue
│   │   ├── PrecisionFilters.vue
│   │   ├── ResultStack.vue
│   │   ├── ClaimSearch.vue           # Claim-first search mode
│   │   └── CompareStrip.vue
│   │
│   ├── paper/                        # Paper Profile
│   │   ├── PaperFolio.vue
│   │   ├── ThesisLine.vue
│   │   ├── ClaimsLedger.vue
│   │   ├── MethodsResultsSlice.vue
│   │   ├── FigureGallery.vue
│   │   ├── SupplementRail.vue
│   │   ├── ReproductionStatus.vue
│   │   └── RelatedConstellation.vue
│   │
│   ├── reader/                       # Smart Reader
│   │   ├── ReadingCanvas.vue         # PDF.js wrapper
│   │   ├── OutlineSpine.vue
│   │   ├── Marginalia.vue
│   │   ├── SemanticHighlights.vue
│   │   ├── FigureIntelligence.vue
│   │   ├── ParagraphQA.vue
│   │   ├── QuoteToDraft.vue
│   │   └── ReadingModes.vue
│   │
│   ├── researcher/                   # Researcher Intelligence
│   │   ├── ResearcherHero.vue
│   │   ├── TopicEvolution.vue
│   │   ├── CollaborationAtlas.vue
│   │   └── SignatureShelf.vue
│   │
│   ├── evidence/                     # Evidence & Methods Lab
│   │   ├── RQHeader.vue
│   │   ├── MethodsDissection.vue
│   │   ├── ResultsMatrix.vue
│   │   ├── ChartInspector.vue
│   │   └── ContradictionsPanel.vue
│   │
│   ├── graph/                        # Graph & Trends
│   │   ├── ThemeRiver.vue            # D3.js theme river
│   │   ├── CitationGraph.vue         # Cytoscape.js network
│   │   ├── BurstMoments.vue
│   │   ├── OpportunityLens.vue
│   │   └── SotaLens.vue
│   │
│   ├── workspace/                    # Research Workspace
│   │   ├── ProjectCover.vue
│   │   ├── CorpusShelf.vue
│   │   ├── RQBoard.vue
│   │   ├── WorkflowTimeline.vue
│   │   └── IngestionDock.vue
│   │
│   ├── synthesis/                    # Synthesis Studio
│   │   ├── SynthesisPrompt.vue
│   │   ├── ComparisonMatrix.vue
│   │   ├── ThemeClusters.vue
│   │   ├── ConsensusTension.vue
│   │   └── NarrativeCards.vue
│   │
│   ├── writing/                      # Writing Studio
│   │   ├── ManuscriptOverview.vue
│   │   ├── OutlineBoard.vue
│   │   ├── DraftCanvas.vue           # Tiptap editor wrapper
│   │   ├── EvidenceDrawer.vue
│   │   ├── CitationRail.vue
│   │   └── RevisionLayer.vue
│   │
│   ├── knowledge/                    # Knowledge Garden
│   │   ├── GardenIndex.vue
│   │   ├── NoteWall.vue
│   │   ├── ConceptAtlas.vue
│   │   ├── LearningLayer.vue
│   │   └── ReviewRhythm.vue
│   │
│   ├── charts/                       # ECharts wrappers
│   │   ├── TrendChart.vue
│   │   ├── PublicationTimeline.vue
│   │   └── CitationBehavior.vue
│   │
│   └── layout/                       # Layout components
│       ├── AppSidebar.vue
│       ├── AppTopbar.vue
│       ├── AppBreadcrumbs.vue
│       └── AppCommandPalette.vue
│
├── composables/                      # Auto-imported composables
│   ├── usePapers.ts                  # Paper CRUD + search
│   ├── useSearch.ts                  # Search with debounce + claim mode
│   ├── useReader.ts                  # PDF state, highlights, annotations
│   ├── useWorkspace.ts               # Workspace CRUD + corpus
│   ├── useSynthesis.ts               # Cross-paper comparison
│   ├── useWriting.ts                 # Manuscript state + evidence
│   ├── useKnowledge.ts               # Notes, backlinks, review
│   ├── useGraph.ts                   # Citation/concept graph data
│   ├── useResearcher.ts              # Author profiles + watchlist
│   ├── useEvidence.ts                # Claims, methods, evidence cards
│   ├── useProvenance.ts              # AI field provenance
│   └── useMotion.ts                  # Shared animation composable
│
├── stores/                           # Pinia stores
│   ├── preferences.ts               # Theme, font size, reading mode
│   ├── workspace.ts                  # Active workspace context
│   ├── reader.ts                     # Reader session state
│   └── notifications.ts             # Research alerts + system alerts
│
├── types/                            # TypeScript type definitions
│   ├── paper.ts                      # Paper, Author, Venue, Claim
│   ├── search.ts                     # SearchQuery, SearchResult, ClaimHit
│   ├── graph.ts                      # Graph node/edge types
│   ├── workspace.ts                  # Workspace, Corpus, RQ
│   ├── evidence.ts                   # Evidence, Method, Result
│   ├── writing.ts                    # Manuscript, Chapter, Draft
│   ├── knowledge.ts                  # Note, Concept, Backlink
│   └── api.ts                        # API response wrappers
│
├── utils/                            # Utility functions
│   ├── format.ts                     # Date, number, citation formatting
│   ├── color.ts                      # Design token helpers
│   └── provenance.ts                 # Provenance display helpers
│
├── assets/
│   ├── css/
│   │   ├── tokens.css                # Design tokens (@theme block for Tailwind v4)
│   │   ├── editorial.css             # Drop cap, pull quote, margin note, dividers
│   │   ├── motion.css                # 4 motion category keyframes
│   │   └── typography.css            # Font imports, baseline grid, text styles
│   └── fonts/                        # Self-hosted font files (Playfair, Source Serif, Inter, JetBrains)
│
├── public/
│   ├── pdf.worker.min.mjs            # PDF.js web worker
│   └── favicon.svg
│
├── server/                           # Nuxt server routes (API proxy if needed)
│   └── api/
│       └── [...].ts                  # Proxy to FastAPI backend
│
├── nuxt.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── .eslintrc.cjs
└── package.json
```

---

## Organization Rules

1. **Page components** (`app/pages/`) — Thin, compose feature components. No business logic. Define `definePageMeta` for layout/middleware.
2. **Feature components** (`components/{feature}/`) — Grouped by feature domain, not by type. Auto-imported by Nuxt.
3. **Design system** (`components/ks/`) — All `Ks`-prefixed components are the editorial design system. Built on Reka UI primitives.
4. **Composables** (`composables/`) — One file per feature domain. All data fetching via `useFetch`/`useAsyncData`. Auto-imported.
5. **Stores** (`stores/`) — Pinia stores for client-only global state. Minimal — most state is server state.
6. **Types** (`types/`) — Shared TypeScript types. Mirror backend Pydantic schemas.
7. **Assets** (`assets/css/`) — Design tokens, editorial CSS, motion keyframes. Imported globally.

---

## Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Components | `PascalCase` | `KsCard.vue`, `ReadingCanvas.vue` |
| Composables | `camelCase` with `use` prefix | `usePapers`, `useReader` |
| Stores | `camelCase` with `use` prefix | `usePreferences`, `useWorkspace` |
| Types | `PascalCase` | `Paper`, `SearchResult`, `EvidenceCard` |
| Files | `PascalCase` for `.vue`, `camelCase` for `.ts` | `KsCard.vue`, `usePapers.ts` |
| CSS classes | `ks-` prefix for design system | `.ks-card`, `.ks-drop-cap`, `.ks-pull-quote` |
| Pages | `kebab-case` | `dashboard.vue`, `[paperId].vue` |
