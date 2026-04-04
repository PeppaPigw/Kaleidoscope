// ─── Paper types ────────────────────────────────────────

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

export interface Institution {
  id: string;
  name: string;
  country: string | null;
}

export interface Venue {
  id: string;
  name: string;
  type: "journal" | "conference" | "preprint" | "book";
  tier: string | null;
}

export interface ProvenanceInfo {
  source: "publisher" | "crossref" | "openalex" | "gpt-4o" | "claude" | "user";
  confidence: number;
  timestamp: string;
}

export type PaperType =
  | "article"
  | "review"
  | "preprint"
  | "conference"
  | "book_chapter";
export type OAStatus = "gold" | "green" | "bronze" | "closed";

export interface Claim {
  id: string;
  text: string;
  evidence: EvidenceCard[];
  counter_evidence: EvidenceCard[];
  strength: "strong" | "moderate" | "weak" | "contested";
}

export interface EvidenceCard {
  id: string;
  text: string;
  source_paper_id: string;
  page: number;
  section: string;
  claim_type:
    | "claim"
    | "method"
    | "result"
    | "limitation"
    | "dataset"
    | "metric";
  confidence: number;
  provenance: ProvenanceInfo;
  timestamp: string;
}
