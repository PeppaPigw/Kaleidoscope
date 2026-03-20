# Frontend Development Guidelines

> Conventions for Kaleidoscope's Next.js + React frontend.

---

## Overview

Kaleidoscope frontend is a **Next.js 14+** (App Router) application styled with **Tailwind CSS**. It communicates with the FastAPI backend via REST API.

**Key Features**:
- PDF reader with section-aware navigation
- Hybrid search interface (keyword + semantic + graph)
- Citation graph visualization (Cytoscape.js)
- Trend analytics dashboard (ECharts)
- Collection management and annotation

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Next.js app router layout, module organization | ✅ Filled |
| [Component Guidelines](./component-guidelines.md) | Component patterns, composition, UI library | ✅ Filled |
| [Hook Guidelines](./hook-guidelines.md) | Data fetching, search hooks, mutation patterns | ✅ Filled |
| [State Management](./state-management.md) | Server state, client state, URL state | ✅ Filled |
| [Quality Guidelines](./quality-guidelines.md) | Linting, testing, accessibility | ✅ Filled |
| [Type Safety](./type-safety.md) | TypeScript patterns, API type generation | ✅ Filled |

---

## Tech Stack

| Category | Technology | Rationale |
|----------|-----------|-----------|
| Framework | Next.js 14+ (App Router) | SSR, server components, file-based routing |
| Language | TypeScript (strict) | Type safety across frontend |
| Styling | Tailwind CSS | Rapid UI development |
| UI Components | shadcn/ui | Accessible, customizable component primitives |
| Data Fetching | TanStack Query (React Query) | Caching, background refetch, optimistic updates |
| Forms | React Hook Form + Zod | Validation, performance |
| PDF | PDF.js (react-pdf) | PDF rendering in browser |
| Graph Viz | Cytoscape.js | Interactive citation/co-authorship graphs |
| Charts | ECharts (echarts-for-react) | Rich chart library for trend analysis |
| Icons | Lucide React | Consistent icon set |

---

## Quick Reference

### Dev Commands
```bash
npm run dev          # Start dev server (Next.js)
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript compiler check
```

---

**Language**: All code comments, variable names, and documentation in **English**.
