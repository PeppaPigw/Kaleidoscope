import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

describe("useUserPreferences", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal("ref", ref);
    vi.stubGlobal("useRuntimeConfig", () => ({
      public: { apiUrl: "http://127.0.0.1:8000" },
    }));
    vi.stubGlobal("$fetch", fetchMock);
    vi.stubGlobal("localStorage", { getItem: vi.fn(() => null) });
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("normalizes duplicate category, keyword, and author entries", async () => {
    const { normalizeUserPreferences } = await import("./useUserPreferences");

    expect(
      normalizeUserPreferences({
        subscribed_categories: ["cs.AI", " cs.AI ", "stat.ML"],
        keywords: ["RAG", " rag ", "", "Agents"],
        tracked_authors: ["Yann LeCun", "yann lecun", "  ", "Andrej Karpathy"],
        research_facets: {
          task: ["Generation", " generation ", "Controlled Generation"],
          domain: ["Computational Chemistry", "computational chemistry"],
          method: ["Neural Networks"],
          application: ["Drug Discovery", "drug discovery"],
          data_object: ["High-Dimensional Data"],
          paper_type: ["Framework Paper", "framework paper"],
          evaluation_quality: ["Ablation Study", "ablation study"],
        },
        interests_set: true,
      }),
    ).toEqual({
      subscribed_categories: ["cs.AI", "stat.ML"],
      keywords: ["RAG", "Agents"],
      tracked_authors: ["Yann LeCun", "Andrej Karpathy"],
      research_facets: {
        task: ["Generation", "Controlled Generation"],
        domain: ["Computational Chemistry"],
        method: ["Neural Networks"],
        application: ["Drug Discovery"],
        data_object: ["High-Dimensional Data"],
        paper_type: ["Framework Paper"],
        evaluation_quality: ["Ablation Study"],
      },
      interests_set: true,
    });
  });

  it("normalizes loaded preferences and caches the first successful fetch", async () => {
    fetchMock.mockResolvedValue({
      subscribed_categories: ["cs.AI", " cs.AI ", "stat.ML"],
      keywords: ["RAG", " rag ", "", "Agents"],
      tracked_authors: ["Yann LeCun", "yann lecun"],
      research_facets: {
        task: ["Generation", " generation "],
        domain: ["Computational Chemistry", "computational chemistry"],
      },
      interests_set: true,
    });

    const { useUserPreferences } = await import("./useUserPreferences");
    const { loadPreferences, loaded } = useUserPreferences();

    const first = await loadPreferences();
    const second = await loadPreferences();

    expect(first).toEqual({
      subscribed_categories: ["cs.AI", "stat.ML"],
      keywords: ["RAG", "Agents"],
      tracked_authors: ["Yann LeCun"],
      research_facets: {
        task: ["Generation"],
        domain: ["Computational Chemistry"],
        method: [],
        application: [],
        data_object: [],
        paper_type: [],
        evaluation_quality: [],
      },
      interests_set: true,
    });
    expect(second).toEqual(first);
    expect(loaded.value).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("sends a normalized save payload and rethrows save failures", async () => {
    const error = new Error("save failed");
    fetchMock.mockRejectedValueOnce(error);
    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const { useUserPreferences } = await import("./useUserPreferences");
    const { savePreferences, loaded, preferences } = useUserPreferences();

    await expect(
      savePreferences({
        subscribed_categories: [" stat.ML ", "stat.ML"],
        keywords: ["Diffusion Models", "diffusion models", ""],
        tracked_authors: ["Yann LeCun", "yann lecun"],
        research_facets: {
          task: ["Controlled Generation", "controlled generation"],
          domain: ["Computational Chemistry", "computational chemistry"],
          method: [],
          application: ["Drug Discovery"],
          data_object: [],
          paper_type: ["Framework Paper"],
          evaluation_quality: ["Ablation Study"],
        },
        interests_set: true,
      }),
    ).rejects.toThrow("save failed");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/users/me/preferences",
      expect.objectContaining({
        method: "PUT",
        body: {
          subscribed_categories: ["stat.ML"],
          keywords: ["Diffusion Models"],
          tracked_authors: ["Yann LeCun"],
          research_facets: {
            task: ["Controlled Generation"],
            domain: ["Computational Chemistry"],
            method: [],
            application: ["Drug Discovery"],
            data_object: [],
            paper_type: ["Framework Paper"],
            evaluation_quality: ["Ablation Study"],
          },
          interests_set: true,
        },
        headers: { "X-API-Key": "sk-kaleidoscope" },
      }),
    );
    expect(preferences.value).toEqual({
      subscribed_categories: ["stat.ML"],
      keywords: ["Diffusion Models"],
      tracked_authors: ["Yann LeCun"],
      research_facets: {
        task: ["Controlled Generation"],
        domain: ["Computational Chemistry"],
        method: [],
        application: ["Drug Discovery"],
        data_object: [],
        paper_type: ["Framework Paper"],
        evaluation_quality: ["Ablation Study"],
      },
      interests_set: true,
    });
    expect(loaded.value).toBe(false);
    expect(errorSpy).toHaveBeenCalled();
  });
});
