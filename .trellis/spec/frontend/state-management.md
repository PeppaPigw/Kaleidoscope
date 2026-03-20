# State Management

> How state is managed across the Kaleidoscope frontend.

---

## State Categories

| Category | Tool | Examples |
|----------|------|---------|
| **Server State** | TanStack Query | Paper data, search results, graph data |
| **URL State** | Next.js `searchParams` | Search query, filters, page number |
| **UI State** | React `useState` | Modal open/close, sidebar collapse |
| **Form State** | React Hook Form | Import form, annotation editor |
| **Global Client State** | Zustand (if needed) | Reading preferences, theme |

---

## Principles

### 1. Server State First

Most "state" in Kaleidoscope is actually server data. Use TanStack Query — don't duplicate server data into client state:

```tsx
// ✅ Good — server state managed by React Query
const { data: papers } = useSearchPapers(query);

// ❌ Bad — duplicating server data
const [papers, setPapers] = useState([]);
useEffect(() => { fetchPapers().then(setPapers); }, []);
```

### 2. URL State for Shareable State

Search queries, filters, and current views should be in the URL:

```tsx
// ✅ Good — state in URL, shareable
// /search?q=quantum+computing&mode=semantic&year=2024
export default function SearchPage({ searchParams }) {
  const query = searchParams.q ?? "";
  const mode = searchParams.mode ?? "hybrid";
  ...
}
```

### 3. Minimal Global Client State

Only use Zustand for truly global, client-only preferences:

```tsx
// lib/stores/preferences-store.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PreferencesStore {
  theme: "light" | "dark";
  readerFontSize: number;
  setTheme: (theme: "light" | "dark") => void;
}

export const usePreferences = create<PreferencesStore>()(
  persist(
    (set) => ({
      theme: "dark",
      readerFontSize: 14,
      setTheme: (theme) => set({ theme }),
    }),
    { name: "kaleidoscope-preferences" }
  )
);
```

---

## Rules

1. **Default to server state** — if data comes from API, use TanStack Query
2. **URL for navigation state** — search, filters, page, view mode
3. **No prop drilling >3 levels** — extract to hook or use context
4. **No Redux** — Zustand for the rare global client state needs
