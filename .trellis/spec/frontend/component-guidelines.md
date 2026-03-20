# Component Guidelines

> Component patterns and composition rules for Kaleidoscope frontend.

---

## Component Library

Use **shadcn/ui** as the base component library. Install components on demand:

```bash
npx shadcn-ui@latest add button dialog card input
```

Customize via `components/ui/` — these are owned by the project, not a node_module.

---

## Component Patterns

### Server vs Client Components

```tsx
// ✅ Default: Server Components for data-heavy pages
// app/papers/page.tsx (Server Component)
export default async function PapersPage() {
  const papers = await fetchPapers();  // Server-side fetch
  return <PaperList papers={papers} />;
}

// ✅ Client Components only when needed (interactivity, hooks)
// components/search/search-bar.tsx
"use client";
export function SearchBar() {
  const [query, setQuery] = useState("");
  ...
}
```

### Composition Over Props

```tsx
// ✅ Good — composable
<PaperCard paper={paper}>
  <PaperCard.Metadata />
  <PaperCard.Summary level="abstract" />
  <PaperCard.Actions onSave={handleSave} />
</PaperCard>

// ❌ Bad — too many props
<PaperCard
  paper={paper}
  showMetadata={true}
  summaryLevel="abstract"
  onSave={handleSave}
  showActions={true}
/>
```

### Loading & Error States

Every data-dependent component must handle 3 states:

```tsx
function PaperDetail({ id }: { id: string }) {
  const { data, isLoading, error } = usePaper(id);
  
  if (isLoading) return <PaperDetailSkeleton />;
  if (error) return <ErrorAlert message={error.message} />;
  return <PaperDetailView paper={data} />;
}
```

---

## Visualization Components

### Citation Graph (Cytoscape.js)

```tsx
// components/graph/citation-graph.tsx
"use client";
import CytoscapeComponent from "react-cytoscapejs";

export function CitationGraph({ paperId }: { paperId: string }) {
  const { data } = useCitationGraph(paperId);
  return (
    <CytoscapeComponent
      elements={data.elements}
      layout={{ name: "cose" }}
      style={{ width: "100%", height: "600px" }}
    />
  );
}
```

### Trend Charts (ECharts)

```tsx
// components/charts/trend-chart.tsx  
"use client";
import ReactECharts from "echarts-for-react";

export function TrendChart({ data }: { data: TrendData }) {
  const option = buildTrendOption(data);
  return <ReactECharts option={option} style={{ height: 400 }} />;
}
```

---

## Rules

1. **One component per file** — no multi-component files
2. **Feature-grouped** — `components/paper/`, not `components/cards/`
3. **Props interface at top** — always define and export props type
4. **No inline styles** — use Tailwind classes only
5. **Skeleton for every loading state** — no spinners for content areas
