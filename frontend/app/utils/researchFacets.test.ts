import { describe, expect, it } from "vitest";

import {
  buildResearchFacetCatalog,
  getResearchFacetSelectionCount,
  getResearchFacetSummary,
  getResearchFacetTerms,
  normalizeResearchFacetPreferences,
} from "./researchFacets";

describe("researchFacets", () => {
  it("builds grouped facet catalog entries from the shared taxonomy shape", () => {
    const groups = buildResearchFacetCatalog({
      TagSystem: {
        UserTag: {
          Domain: {
            Computer_Science_and_AI: [
              "Artificial Intelligence",
              "Machine Learning",
            ],
          },
          Task: {
            NLP: ["Generation", "Controlled Generation"],
          },
          Method: {
            Deep_Learning: ["Neural Networks"],
          },
          Data_Object: {
            General: ["High-Dimensional Data"],
          },
          Application: {
            Life_Science: ["Drug Discovery"],
          },
        },
        MetaTag: {
          "Paper Type": ["Framework Paper", "Empirical Paper"],
          "Evaluation / Quality": ["Ablation Study"],
        },
      },
    });

    expect(groups.map((group) => group.key)).toEqual([
      "task",
      "domain",
      "method",
      "application",
      "data_object",
      "paper_type",
      "evaluation_quality",
    ]);
    expect(groups[0]?.buckets[0]).toEqual({
      id: "NLP",
      label: "NLP",
      options: ["Generation", "Controlled Generation"],
    });
    expect(groups[1]?.buckets[0]?.label).toBe("Computer Science & AI");
    expect(groups[5]?.buckets[0]).toEqual({
      id: "all",
      label: "All",
      options: ["Framework Paper", "Empirical Paper"],
    });
  });

  it("normalizes facet selections, counts them, and returns prioritized query terms", () => {
    const normalized = normalizeResearchFacetPreferences({
      task: ["Generation", " generation ", "Controlled Generation"],
      domain: ["Computational Chemistry", "computational chemistry"],
      method: ["Neural Networks"],
      application: ["Drug Discovery", "drug discovery"],
      data_object: ["High-Dimensional Data"],
      paper_type: ["Framework Paper", "framework paper"],
      evaluation_quality: ["Ablation Study", "ablation study"],
    });

    expect(normalized).toEqual({
      task: ["Generation", "Controlled Generation"],
      domain: ["Computational Chemistry"],
      method: ["Neural Networks"],
      application: ["Drug Discovery"],
      data_object: ["High-Dimensional Data"],
      paper_type: ["Framework Paper"],
      evaluation_quality: ["Ablation Study"],
    });
    expect(getResearchFacetSelectionCount(normalized)).toBe(8);
    expect(getResearchFacetTerms(normalized, 5)).toEqual([
      "Generation",
      "Controlled Generation",
      "Computational Chemistry",
      "Drug Discovery",
      "Neural Networks",
    ]);
    expect(getResearchFacetSummary(normalized, 3)).toEqual([
      "Generation",
      "Controlled Generation",
      "Computational Chemistry",
    ]);
  });
});
