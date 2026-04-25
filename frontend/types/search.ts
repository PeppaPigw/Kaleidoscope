// ─── Search types ───────────────────────────────────────
import type { Paper, OAStatus, PaperType, Claim } from "./paper";

export type SearchMode = "keyword" | "semantic" | "hybrid" | "graph" | "claim";

export interface SearchQuery {
  q: string;
  mode: SearchMode;
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

export interface ClaimSearchResult {
  items: ClaimHit[];
  total: number;
}

export interface ClaimHit {
  claim: Claim;
  supporting_papers: number;
  confidence: number;
  contradicted: boolean;
}
