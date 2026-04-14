/**
 * useUserPreferences — singleton composable for managing user preferences.
 *
 * Caches preferences in module scope so the API is only called once per
 * session. Provides loadPreferences() and savePreferences() helpers.
 */

export interface UserPreferences {
  subscribed_categories: string[]
  keywords: string[]
  tracked_authors: string[]
  interests_set: boolean
  [key: string]: unknown
}

// ─── Singleton state ─────────────────────────────────────────
const preferences = ref<UserPreferences>({
  subscribed_categories: [],
  keywords: [],
  tracked_authors: [],
  interests_set: false,
})
const loading = ref(false)
const loaded = ref(false)

export function useUserPreferences() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl as string

  function _authHeader(): Record<string, string> {
    if (import.meta.client) {
      const token = localStorage.getItem('ks_access_token')
      if (token && token !== 'single-user-mode') {
        return { Authorization: `Bearer ${token}` }
      }
    }
    return {}
  }

  async function loadPreferences(): Promise<UserPreferences> {
    if (loaded.value) return preferences.value
    loading.value = true
    try {
      const data = await $fetch<UserPreferences>(
        `${apiBase}/api/v1/users/me/preferences`,
        { headers: _authHeader() },
      )
      preferences.value = {
        subscribed_categories: [],
        keywords: [],
        tracked_authors: [],
        interests_set: false,
        ...data,
      }
      loaded.value = true
    }
    catch (e) {
      console.error('[useUserPreferences] load error:', e)
    }
    finally {
      loading.value = false
    }
    return preferences.value
  }

  async function savePreferences(patch: Partial<UserPreferences>): Promise<void> {
    const merged: UserPreferences = { ...preferences.value, ...patch }
    preferences.value = merged
    try {
      const data = await $fetch<UserPreferences>(
        `${apiBase}/api/v1/users/me/preferences`,
        {
          method: 'PUT',
          body: merged,
          headers: _authHeader(),
        },
      )
      preferences.value = { subscribed_categories: [], keywords: [], tracked_authors: [], interests_set: false, ...data }
    }
    catch (e) {
      console.error('[useUserPreferences] save error:', e)
    }
  }

  return {
    preferences,
    loading,
    loaded,
    loadPreferences,
    savePreferences,
  }
}
