// ─── Workspace types ────────────────────────────────────

export interface Workspace {
  id: string;
  name: string;
  research_question: string;
  target_venue: string | null;
  stage: WorkspaceStage;
  corpus_count: number;
  created_at: string;
}

export type WorkspaceStage =
  | "discover"
  | "deep-read"
  | "compare"
  | "synthesize"
  | "write";

export type CorpusShelf = "core" | "opposing" | "background" | "methods";

export interface ResearchIntent {
  id: string;
  question: string;
  status: "active" | "resolved" | "parked";
  linked_paper_ids: string[];
  evidence_ids: string[];
}
