# Hook Guidelines

> Custom hook patterns for Kaleidoscope frontend.

---

## Data Fetching — TanStack Query

All server data fetching goes through **TanStack Query** (React Query):

```tsx
// hooks/use-papers.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

// Fetch paper by ID
export function usePaper(id: string) {
  return useQuery({
    queryKey: ["paper", id],
    queryFn: () => apiClient.get<Paper>(`/api/v1/papers/${id}`),
  });
}

// Search papers
export function useSearchPapers(query: SearchQuery) {
  return useQuery({
    queryKey: ["papers", "search", query],
    queryFn: () => apiClient.post<SearchResult>("/api/v1/search", query),
    enabled: !!query.q,  // Don't fetch without query
    keepPreviousData: true,
  });
}

// Import paper (mutation)
export function useImportPaper() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (req: PaperImportRequest) =>
      apiClient.post<Paper>("/api/v1/papers/import", req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["papers"] });
    },
  });
}
```

---

## Query Key Convention

```typescript
// Pattern: [entity, ...identifiers, ...filters]
["paper", paperId]                     // Single paper
["papers", "search", { q, mode }]      // Search results
["papers", "collection", collectionId] // Papers in collection
["graph", "citations", paperId]        // Citation graph
["authors", authorId]                  // Author profile
["trends", { topic, timeRange }]       // Trend data
```

---

## Search Hook Pattern

```tsx
// hooks/use-search.ts
export function useSearch() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [filters, setFilters] = useState<SearchFilters>({});
  
  const debouncedQuery = useDebounce(query, 300);
  
  const results = useSearchPapers({
    q: debouncedQuery,
    mode,
    filters,
    page: 1,
    per_page: 20,
  });
  
  return { query, setQuery, mode, setMode, filters, setFilters, results };
}
```

---

## Rules

1. **One hook file per feature domain** — `use-papers.ts`, `use-search.ts`, `use-graph.ts`
2. **Always use query keys** — consistent naming enables proper cache invalidation
3. **Debounce user input** — 300ms for search, 500ms for heavy operations
4. **Handle loading/error** — every hook consumer must handle all 3 states
5. **Prefer `enabled` over conditional calls** — don't use `if` around `useQuery`
