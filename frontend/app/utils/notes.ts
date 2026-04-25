/**
 * Note types and localStorage helpers for the reader note-taking feature.
 */

export type NoteType = "highlight" | "manual" | "annotation";

export interface Note {
  id: string;
  type: NoteType;
  createdAt: number;
  /** Selected text from the reading area (highlight + annotation only). */
  selectedText?: string;
  /** User-written note content (manual + annotation only). */
  content?: string;
}

const storageKey = (paperId: string) => `ks-notes-${paperId}`;

export function loadNotes(paperId: string): Note[] {
  try {
    const raw = localStorage.getItem(storageKey(paperId));
    return raw ? (JSON.parse(raw) as Note[]) : [];
  } catch {
    return [];
  }
}

export function saveNotes(paperId: string, notes: Note[]): void {
  try {
    localStorage.setItem(storageKey(paperId), JSON.stringify(notes));
  } catch {
    // Ignore localStorage errors (quota exceeded, private mode, etc.)
  }
}
