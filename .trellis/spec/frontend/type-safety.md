# Type Safety

> TypeScript conventions for Kaleidoscope frontend.

---

## Configuration

**Strict mode enabled** in `tsconfig.json`:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true
  }
}
```

---

## API Types — Mirror Backend Schemas

Frontend types must match backend Pydantic schemas:

```typescript
// types/paper.ts

export interface Paper {
  id: string;
  doi: string | null;
  arxiv_id: string | null;
  title: string;
  abstract: string | null;
  published_at: string | null;
  paper_type: PaperType;
  oa_status: OAStatus;
  authors: Author[];
  venue: Venue | null;
  citation_count: number;
  provenance: Record<string, ProvenanceInfo>;
}

export interface Author {
  id: string;
  display_name: string;
  orcid: string | null;
  institution: Institution | null;
  h_index: number | null;
}

export interface ProvenanceInfo {
  source: "publisher" | "crossref" | "openalex" | "gpt-4o" | "claude" | "user";
  confidence: number;
  timestamp: string;
}

export type PaperType = "article" | "review" | "preprint" | "conference" | "book_chapter";
export type OAStatus = "gold" | "green" | "bronze" | "closed";
```

### Search Types

```typescript
// types/search.ts

export interface SearchQuery {
  q: string;
  mode: "keyword" | "semantic" | "hybrid" | "graph";
  filters?: SearchFilters;
  page?: number;
  per_page?: number;
}

export interface SearchFilters {
  year_from?: number;
  year_to?: number;
  venue_ids?: string[];
  author_ids?: string[];
  oa_status?: OAStatus[];
  paper_type?: PaperType[];
}

export interface SearchResult {
  items: PaperSearchHit[];
  total: number;
  page: number;
  per_page: number;
}

export interface PaperSearchHit extends Paper {
  score: number;
  highlights: Record<string, string[]>;
}
```

---

## API Client — Typed Fetch

```typescript
// lib/api-client.ts

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiClient {
  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(path, BASE_URL);
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    const res = await fetch(url.toString());
    if (!res.ok) throw new ApiError(res.status, await res.json());
    return res.json() as Promise<T>;
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new ApiError(res.status, await res.json());
    return res.json() as Promise<T>;
  }
}

export const apiClient = new ApiClient();
```

---

## Rules

1. **No `any`** — use `unknown` if type is truly unknown, then narrow
2. **No type assertions** (`as`) — prefer type guards
3. **Export all types** — from `types/` directory
4. **Mirror backend** — types must match Pydantic schemas exactly
5. **Discriminated unions** for state:
   ```typescript
   type SearchState =
     | { status: "idle" }
     | { status: "loading" }
     | { status: "success"; data: SearchResult }
     | { status: "error"; error: ApiError };
   ```
