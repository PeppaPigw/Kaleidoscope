export type SupplementItemType =
  | "code"
  | "dataset"
  | "weights"
  | "slides"
  | "appendix"
  | "video"
  | "demo";

export interface SupplementItem {
  id: string;
  label: string;
  type: SupplementItemType;
  url: string;
}
