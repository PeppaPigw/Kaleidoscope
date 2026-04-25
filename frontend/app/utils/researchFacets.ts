export interface ResearchFacetPreferences {
  domain: string[];
  task: string[];
  method: string[];
  data_object: string[];
  application: string[];
  paper_type: string[];
  evaluation_quality: string[];
}

export type ResearchFacetKey = keyof ResearchFacetPreferences;

export interface ResearchFacetBucket {
  id: string;
  label: string;
  options: string[];
}

export interface ResearchFacetGroup {
  key: ResearchFacetKey;
  label: string;
  description: string;
  buckets: ResearchFacetBucket[];
}

interface ResearchFacetTaxonomy {
  TagSystem?: {
    UserTag?: {
      Domain?: unknown;
      Task?: unknown;
      Method?: unknown;
      Data_Object?: unknown;
      Application?: unknown;
    };
    MetaTag?: {
      "Paper Type"?: unknown;
      "Evaluation / Quality"?: unknown;
    };
  };
}

const RESEARCH_FACET_SPECS: Array<{
  key: ResearchFacetKey;
  label: string;
  description: string;
  section: "user" | "meta";
  path: string;
}> = [
  {
    key: "task",
    label: "Task",
    description: "What kind of problem or objective the paper focuses on.",
    section: "user",
    path: "Task",
  },
  {
    key: "domain",
    label: "Domain",
    description:
      "The scientific or technical field you want the dashboard to prioritize.",
    section: "user",
    path: "Domain",
  },
  {
    key: "method",
    label: "Method",
    description:
      "Modeling or algorithmic approaches that should shape recommendations.",
    section: "user",
    path: "Method",
  },
  {
    key: "application",
    label: "Application",
    description: "Real-world use cases that should guide personalization.",
    section: "user",
    path: "Application",
  },
  {
    key: "data_object",
    label: "Data / Object",
    description: "The kinds of data or scientific objects you care about most.",
    section: "user",
    path: "Data_Object",
  },
  {
    key: "paper_type",
    label: "Paper Type",
    description:
      "Preferred paper styles, such as empirical, framework, or benchmark work.",
    section: "meta",
    path: "Paper Type",
  },
  {
    key: "evaluation_quality",
    label: "Evaluation",
    description:
      "Evaluation signals that indicate the style of evidence you prefer.",
    section: "meta",
    path: "Evaluation / Quality",
  },
];

export const EMPTY_RESEARCH_FACETS: ResearchFacetPreferences = {
  domain: [],
  task: [],
  method: [],
  data_object: [],
  application: [],
  paper_type: [],
  evaluation_quality: [],
};

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];

  const normalized: string[] = [];
  const seen = new Set<string>();

  for (const entry of value) {
    const cleaned = String(entry ?? "").trim();
    if (!cleaned) continue;
    const key = cleaned.toLocaleLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    normalized.push(cleaned);
  }

  return normalized;
}

function prettifyBucketLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\band\b/g, "&");
}

function flattenTaxonomyNode(node: unknown): string[] {
  if (Array.isArray(node)) {
    return node
      .filter((entry): entry is string => typeof entry === "string")
      .map((entry) => entry.trim())
      .filter(Boolean);
  }

  if (!node || typeof node !== "object") return [];

  return Object.values(node).flatMap((value) => flattenTaxonomyNode(value));
}

function buildBuckets(node: unknown): ResearchFacetBucket[] {
  if (Array.isArray(node)) {
    const options = normalizeStringList(node);
    return options.length ? [{ id: "all", label: "All", options }] : [];
  }

  if (!node || typeof node !== "object") return [];

  return Object.entries(node)
    .map(([bucketId, value]) => ({
      id: bucketId,
      label: prettifyBucketLabel(bucketId),
      options: normalizeStringList(flattenTaxonomyNode(value)),
    }))
    .filter((bucket) => bucket.options.length > 0);
}

export function normalizeResearchFacetPreferences(
  input?: Partial<ResearchFacetPreferences> | null,
): ResearchFacetPreferences {
  const source = input ?? {};

  return {
    domain: normalizeStringList(source.domain),
    task: normalizeStringList(source.task),
    method: normalizeStringList(source.method),
    data_object: normalizeStringList(source.data_object),
    application: normalizeStringList(source.application),
    paper_type: normalizeStringList(source.paper_type),
    evaluation_quality: normalizeStringList(source.evaluation_quality),
  };
}

export function buildResearchFacetCatalog(
  taxonomy: ResearchFacetTaxonomy,
): ResearchFacetGroup[] {
  const tagSystem = taxonomy.TagSystem ?? {};
  const userTags = tagSystem.UserTag ?? {};
  const metaTags = tagSystem.MetaTag ?? {};

  return RESEARCH_FACET_SPECS.map((spec) => {
    const node =
      spec.section === "user"
        ? userTags[spec.path as keyof typeof userTags]
        : metaTags[spec.path as keyof typeof metaTags];

    return {
      key: spec.key,
      label: spec.label,
      description: spec.description,
      buckets: buildBuckets(node),
    };
  }).filter((group) => group.buckets.length > 0);
}

export function getResearchFacetSelectionCount(
  preferences: ResearchFacetPreferences | null | undefined,
): number {
  const normalized = normalizeResearchFacetPreferences(preferences);

  return Object.values(normalized).reduce(
    (sum, values) => sum + values.length,
    0,
  );
}

export function getResearchFacetTerms(
  preferences: ResearchFacetPreferences | null | undefined,
  limit: number = 6,
): string[] {
  const normalized = normalizeResearchFacetPreferences(preferences);
  const terms: string[] = [];
  const seen = new Set<string>();

  for (const key of [
    "task",
    "domain",
    "application",
    "method",
    "data_object",
    "paper_type",
    "evaluation_quality",
  ] as ResearchFacetKey[]) {
    for (const value of normalized[key]) {
      const normalizedValue = value.toLocaleLowerCase();
      if (seen.has(normalizedValue)) continue;
      seen.add(normalizedValue);
      terms.push(value);
      if (terms.length >= limit) return terms;
    }
  }

  return terms;
}

export function getResearchFacetSummary(
  preferences: ResearchFacetPreferences | null | undefined,
  limit: number = 3,
): string[] {
  return getResearchFacetTerms(preferences, limit);
}
