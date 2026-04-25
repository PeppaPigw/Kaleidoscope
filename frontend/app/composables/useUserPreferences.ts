/**
 * useUserPreferences — singleton composable for managing user preferences.
 *
 * Caches preferences in module scope so the API is only called once per
 * session. Provides loadPreferences() and savePreferences() helpers.
 */

import {
  EMPTY_RESEARCH_FACETS,
  normalizeResearchFacetPreferences,
  type ResearchFacetPreferences,
} from "../utils/researchFacets";

export interface UserPreferences {
  subscribed_categories: string[];
  keywords: string[];
  tracked_authors: string[];
  research_facets: ResearchFacetPreferences;
  interests_set: boolean;
  [key: string]: unknown;
}

const DEFAULT_PREFERENCES: UserPreferences = {
  subscribed_categories: [],
  keywords: [],
  tracked_authors: [],
  research_facets: { ...EMPTY_RESEARCH_FACETS },
  interests_set: false,
};

function normalizeStringList(
  value: unknown,
  options: { caseInsensitive?: boolean } = {},
): string[] {
  if (!Array.isArray(value)) return [];
  const caseInsensitive = options.caseInsensitive === true;

  const normalized: string[] = [];
  const seen = new Set<string>();

  for (const entry of value) {
    const cleaned = String(entry ?? "").trim();
    if (!cleaned) continue;
    const key = caseInsensitive ? cleaned.toLocaleLowerCase() : cleaned;
    if (seen.has(key)) continue;
    seen.add(key);
    normalized.push(cleaned);
  }

  return normalized;
}

export function normalizeUserPreferences(
  input?: Partial<UserPreferences> | null,
): UserPreferences {
  const source = input ?? {};
  return {
    ...DEFAULT_PREFERENCES,
    ...source,
    subscribed_categories: normalizeStringList(source.subscribed_categories),
    keywords: normalizeStringList(source.keywords, { caseInsensitive: true }),
    tracked_authors: normalizeStringList(source.tracked_authors, {
      caseInsensitive: true,
    }),
    research_facets: normalizeResearchFacetPreferences(source.research_facets),
    interests_set: source.interests_set === true,
  };
}

// ─── Singleton state ─────────────────────────────────────────
const preferences = ref<UserPreferences>({ ...DEFAULT_PREFERENCES });
const loading = ref(false);
const loaded = ref(false);

export function useUserPreferences() {
  const config = useRuntimeConfig();
  const apiBase = config.public.apiUrl as string;

  function _authHeader(): Record<string, string> {
    if (import.meta.client) {
      const token = localStorage.getItem("ks_access_token");
      if (token && token !== "single-user-mode") {
        return { Authorization: `Bearer ${token}` };
      }
    }
    return {};
  }

  async function loadPreferences(): Promise<UserPreferences> {
    if (loaded.value) return preferences.value;
    loading.value = true;
    try {
      const data = await $fetch<UserPreferences>(
        `${apiBase}/api/v1/users/me/preferences`,
        { headers: _authHeader() },
      );
      preferences.value = normalizeUserPreferences(data);
      loaded.value = true;
    } catch (e) {
      console.error("[useUserPreferences] load error:", e);
      throw e;
    } finally {
      loading.value = false;
    }
    return preferences.value;
  }

  async function savePreferences(
    patch: Partial<UserPreferences>,
  ): Promise<UserPreferences> {
    const merged = normalizeUserPreferences({ ...preferences.value, ...patch });
    preferences.value = merged;
    try {
      const data = await $fetch<UserPreferences>(
        `${apiBase}/api/v1/users/me/preferences`,
        {
          method: "PUT",
          body: merged,
          headers: _authHeader(),
        },
      );
      preferences.value = normalizeUserPreferences(data);
      loaded.value = true;
    } catch (e) {
      console.error("[useUserPreferences] save error:", e);
      throw e;
    }
    return preferences.value;
  }

  return {
    preferences,
    loading,
    loaded,
    loadPreferences,
    savePreferences,
  };
}
