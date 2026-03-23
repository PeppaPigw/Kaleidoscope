# Type Safety

> TypeScript conventions for Kaleidoscope frontend (Vue 3 / Nuxt 3).

---

## Configuration

**Strict mode enabled** via Nuxt auto-configured `tsconfig.json`:
```json
{
  "extends": "./.nuxt/tsconfig.json",
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

---

## API Types — Mirror Backend Schemas

Frontend types must match backend Pydantic schemas:

```typescript
// types/paper.ts

export interface Paper {
  id: string
  doi: string | null
  arxiv_id: string | null
  title: string
  abstract: string | null
  published_at: string | null
  paper_type: PaperType
  oa_status: OAStatus
  authors: Author[]
  venue: Venue | null
  citation_count: number
  provenance: Record<string, ProvenanceInfo>
}

export interface Author {
  id: string
  display_name: string
  orcid: string | null
  institution: Institution | null
  h_index: number | null
}

export interface ProvenanceInfo {
  source: 'publisher' | 'crossref' | 'openalex' | 'gpt-4o' | 'claude' | 'user'
  confidence: number
  timestamp: string
}

export type PaperType = 'article' | 'review' | 'preprint' | 'conference' | 'book_chapter'
export type OAStatus = 'gold' | 'green' | 'bronze' | 'closed'
```

### Evidence Types

```typescript
// types/evidence.ts

export interface EvidenceCard {
  id: string
  text: string
  source_paper_id: string
  page: number
  section: string
  claim_type: 'claim' | 'method' | 'result' | 'limitation' | 'dataset' | 'metric'
  confidence: number
  provenance: ProvenanceInfo
  timestamp: string
}

export interface Claim {
  id: string
  text: string
  evidence: EvidenceCard[]
  counter_evidence: EvidenceCard[]
  strength: 'strong' | 'moderate' | 'weak' | 'contested'
}
```

### Search Types

```typescript
// types/search.ts

export interface SearchQuery {
  q: string
  mode: 'keyword' | 'semantic' | 'hybrid' | 'graph' | 'claim'
  filters?: SearchFilters
  page?: number
  per_page?: number
}

export interface SearchFilters {
  year_from?: number
  year_to?: number
  venue_ids?: string[]
  author_ids?: string[]
  oa_status?: OAStatus[]
  paper_type?: PaperType[]
}

export interface SearchResult {
  items: PaperSearchHit[]
  total: number
  page: number
  per_page: number
}

export interface PaperSearchHit extends Paper {
  score: number
  highlights: Record<string, string[]>
}

// Claim-first search result
export interface ClaimSearchResult {
  items: ClaimHit[]
  total: number
}

export interface ClaimHit {
  claim: Claim
  supporting_papers: number
  confidence: number
  contradicted: boolean
}
```

### Workspace Types

```typescript
// types/workspace.ts

export interface Workspace {
  id: string
  name: string
  research_question: string
  target_venue: string | null
  stage: WorkspaceStage
  corpus_count: number
  created_at: string
}

export type WorkspaceStage = 'discover' | 'deep-read' | 'compare' | 'synthesize' | 'write'

export type CorpusShelf = 'core' | 'opposing' | 'background' | 'methods'

export interface ResearchIntent {
  id: string
  question: string
  status: 'active' | 'resolved' | 'parked'
  linked_paper_ids: string[]
  evidence_ids: string[]
}
```

---

## API Client — Nuxt `$fetch`

Nuxt provides `$fetch` (built on ofetch) globally. No separate client needed:

```typescript
// composables/useApi.ts

// For mutations (imperative)
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiUrl

  return {
    async get<T>(path: string) {
      return $fetch<T>(path, { baseURL })
    },
    async post<T>(path: string, body: unknown) {
      return $fetch<T>(path, { baseURL, method: 'POST', body })
    },
    async patch<T>(path: string, body: unknown) {
      return $fetch<T>(path, { baseURL, method: 'PATCH', body })
    },
    async del(path: string) {
      return $fetch(path, { baseURL, method: 'DELETE' })
    },
  }
}
```

---

## Zod Validation

```typescript
// types/schemas.ts
import { z } from 'zod'

export const PaperImportSchema = z.object({
  doi: z.string().optional(),
  arxiv_id: z.string().optional(),
  url: z.string().url().optional(),
  pdf_file: z.instanceof(File).optional(),
}).refine(data => data.doi || data.arxiv_id || data.url || data.pdf_file, {
  message: 'At least one identifier or file is required',
})

export type PaperImportInput = z.infer<typeof PaperImportSchema>
```

---

## Discriminated Unions for State

```typescript
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'pending' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

// Used in composables
const searchState = ref<FetchState<SearchResult>>({ status: 'idle' })
```

---

## Rules

1. **No `any`** — use `unknown` if type is truly unknown, then narrow
2. **No type assertions** (`as`) — prefer type guards
3. **Export all types** — from `types/` directory
4. **Mirror backend** — types must match Pydantic schemas exactly
5. **Zod for runtime validation** — especially for user input and API responses
6. **`defineProps<T>()`** — always typed props in components
7. **`defineEmits<T>()`** — always typed emits
