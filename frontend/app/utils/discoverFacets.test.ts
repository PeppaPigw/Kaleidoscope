import { describe, expect, it } from "vitest";

import {
  buildDiscoverFacetGroups,
  filterDiscoverResults,
  getDiscoverVenueLabel,
  getDiscoverYearLabel,
  normalizeDiscoverCategories,
} from "./discoverFacets";

describe("discoverFacets", () => {
  it("splits malformed category strings into discrete facet labels", () => {
    expect(
      normalizeDiscoverCategories(["cs.AI cs.LG", "cs.CV,cs.CL", " cs.AI "]),
    ).toEqual(["cs.AI", "cs.LG", "cs.CV", "cs.CL"]);
  });

  it("uses venue metadata instead of mislabeling authors as venues", () => {
    expect(
      getDiscoverVenueLabel({
        journal_name: "NeurIPS",
        venue: "Conference on Neural Information Processing Systems",
      }),
    ).toBe("NeurIPS");
    expect(
      getDiscoverVenueLabel({
        journal_name: null,
        venue: "Conference on Neural Information Processing Systems",
      }),
    ).toBe("Conference on Neural Information Processing Systems");
    expect(getDiscoverVenueLabel({ journal_name: null, venue: null })).toBe(
      "Unspecified venue",
    );
  });

  it("extracts years from both ISO and database-style publish timestamps", () => {
    expect(getDiscoverYearLabel({ publish_at: "2026-03-30 00:00:00" })).toBe(
      "2026",
    );
    expect(getDiscoverYearLabel({ publish_at: "2024-01-26T00:00:00" })).toBe(
      "2024",
    );
    expect(getDiscoverYearLabel({ publish_at: "invalid" })).toBeNull();
  });

  it("builds dynamic year, venue, and category facets from results", () => {
    const results = [
      {
        arxiv_id: "1",
        title: "Paper A",
        authors: ["Alice"],
        categories: ["cs.AI cs.LG"],
        citations: 80,
        score: 0.9,
        publish_at: "2026-03-30T00:00:00",
        venue: null,
        journal_name: "NeurIPS",
      },
      {
        arxiv_id: "2",
        title: "Paper B",
        authors: ["Bob"],
        categories: ["cs.CL", "cs.LG"],
        citations: 10,
        score: 0.8,
        publish_at: "2024-01-26T00:00:00",
        venue: "arXiv.org",
        journal_name: "ArXiv",
      },
    ];

    const groups = buildDiscoverFacetGroups(results, {
      activeYears: ["2026"],
      activeVenues: ["NeurIPS"],
      activeCategories: ["cs.LG"],
      impactMode: "high",
      searchMode: "hybrid",
    });

    expect(groups[0]).toEqual({
      title: "Year",
      options: [
        { label: "2026", count: 1, active: true },
        { label: "2024", count: 1, active: false },
      ],
    });
    expect(groups[1]?.options[0]).toEqual({
      label: "ArXiv",
      count: 1,
      active: false,
    });
    expect(groups[1]?.options[1]).toEqual({
      label: "NeurIPS",
      count: 1,
      active: true,
    });
    expect(groups[2]?.options[0]).toEqual({
      label: "cs.LG",
      count: 2,
      active: true,
    });
  });

  it("filters results by active facet selections", () => {
    const results = [
      {
        arxiv_id: "1",
        title: "Paper A",
        authors: ["Alice"],
        categories: ["cs.AI cs.LG"],
        citations: 80,
        score: 0.9,
        publish_at: "2026-03-30T00:00:00",
        venue: null,
        journal_name: "NeurIPS",
      },
      {
        arxiv_id: "2",
        title: "Paper B",
        authors: ["Bob"],
        categories: ["cs.CL"],
        citations: 10,
        score: 0.8,
        publish_at: "2024-01-26T00:00:00",
        venue: "arXiv.org",
        journal_name: "ArXiv",
      },
    ];

    const filtered = filterDiscoverResults(results, {
      activeYears: ["2026"],
      activeVenues: ["NeurIPS"],
      activeCategories: ["cs.AI"],
      impactMode: "high",
    });

    expect(filtered).toHaveLength(1);
    expect(filtered[0]?.arxiv_id).toBe("1");
  });
});
