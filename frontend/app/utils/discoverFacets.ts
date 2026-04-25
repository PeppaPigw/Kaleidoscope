import type { DeepXivSearchResult } from "~/composables/useDeepXiv";

export interface DiscoverFacetOption {
  label: string;
  count: number;
  active: boolean;
}

export interface DiscoverFacetGroup {
  title: string;
  options: DiscoverFacetOption[];
}

export interface DiscoverFacetState {
  activeYears: string[];
  activeVenues: string[];
  activeCategories: string[];
  impactMode: "any" | "high";
  searchMode: "hybrid" | "bm25" | "vector";
}

const CATEGORY_SPLIT_RE = /[\s,]+/;

function sortByCountThenLabel(a: [string, number], b: [string, number]) {
  if (b[1] !== a[1]) return b[1] - a[1];
  return a[0].localeCompare(b[0]);
}

export function normalizeDiscoverCategories(
  categories: string[] | null | undefined,
): string[] {
  const normalized = new Set<string>();

  for (const category of categories ?? []) {
    for (const token of category.split(CATEGORY_SPLIT_RE)) {
      const trimmed = token.trim();
      if (!trimmed) continue;
      normalized.add(trimmed);
    }
  }

  return [...normalized];
}

export function getDiscoverVenueLabel(
  result: Pick<DeepXivSearchResult, "journal_name" | "venue">,
): string {
  const journalName = result.journal_name?.trim();
  if (journalName) return journalName;

  const venueName = result.venue?.trim();
  if (venueName) return venueName;

  return "Unspecified venue";
}

export function getDiscoverYearLabel(
  result: Pick<DeepXivSearchResult, "publish_at">,
): string | null {
  const rawValue = result.publish_at?.trim();
  if (!rawValue) return null;

  const yearMatch = rawValue.match(/^(\d{4})/);
  return yearMatch?.[1] ?? null;
}

export function filterDiscoverResults(
  results: DeepXivSearchResult[],
  state: Pick<
    DiscoverFacetState,
    "activeYears" | "activeVenues" | "activeCategories" | "impactMode"
  >,
): DeepXivSearchResult[] {
  return results.filter((result) => {
    const year = getDiscoverYearLabel(result);
    const venue = getDiscoverVenueLabel(result);
    const categories = normalizeDiscoverCategories(result.categories);

    if (
      state.activeYears.length > 0 &&
      (!year || !state.activeYears.includes(year))
    ) {
      return false;
    }

    if (state.activeVenues.length > 0 && !state.activeVenues.includes(venue)) {
      return false;
    }

    if (
      state.activeCategories.length > 0 &&
      !state.activeCategories.some((category) => categories.includes(category))
    ) {
      return false;
    }

    if (state.impactMode === "high" && result.citations < 50) {
      return false;
    }

    return true;
  });
}

export function buildDiscoverFacetGroups(
  results: DeepXivSearchResult[],
  state: DiscoverFacetState,
): DiscoverFacetGroup[] {
  const yearCounts = new Map<string, number>();
  const venueCounts = new Map<string, number>();
  const categoryCounts = new Map<string, number>();

  for (const result of results) {
    const year = getDiscoverYearLabel(result);
    if (year) {
      yearCounts.set(year, (yearCounts.get(year) ?? 0) + 1);
    }

    const venue = getDiscoverVenueLabel(result);
    venueCounts.set(venue, (venueCounts.get(venue) ?? 0) + 1);

    for (const category of normalizeDiscoverCategories(result.categories)) {
      categoryCounts.set(category, (categoryCounts.get(category) ?? 0) + 1);
    }
  }

  const yearOptions = [...yearCounts.entries()]
    .sort((a, b) => Number(b[0]) - Number(a[0]))
    .map(([label, count]) => ({
      label,
      count,
      active: state.activeYears.includes(label),
    }));

  const venueOptions = [...venueCounts.entries()]
    .sort(sortByCountThenLabel)
    .slice(0, 8)
    .map(([label, count]) => ({
      label,
      count,
      active: state.activeVenues.includes(label),
    }));

  const categoryOptions = [...categoryCounts.entries()]
    .sort(sortByCountThenLabel)
    .slice(0, 8)
    .map(([label, count]) => ({
      label,
      count,
      active: state.activeCategories.includes(label),
    }));

  return [
    { title: "Year", options: yearOptions },
    { title: "Venue", options: venueOptions },
    { title: "Category", options: categoryOptions },
    {
      title: "Impact",
      options: [
        {
          label: "High (50+ citations)",
          count: results.filter((result) => result.citations >= 50).length,
          active: state.impactMode === "high",
        },
        {
          label: "Any",
          count: results.length,
          active: state.impactMode === "any",
        },
      ],
    },
    {
      title: "Search Mode",
      options: [
        {
          label: "Hybrid",
          count: results.length,
          active: state.searchMode === "hybrid",
        },
        {
          label: "Semantic",
          count: results.length,
          active: state.searchMode === "vector",
        },
        {
          label: "Keyword",
          count: results.length,
          active: state.searchMode === "bm25",
        },
      ],
    },
  ];
}
