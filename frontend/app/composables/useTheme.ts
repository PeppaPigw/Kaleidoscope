/**
 * Theme management composable
 * Handles system detection, localStorage persistence, and theme toggling
 */

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "ks-theme-preference";
const HTML_CLASS = "ks-dark";

// Shared state across all instances
const isDark = ref(false);
const preference = ref<Theme>("system");
let initialized = false;

export function useTheme() {
  // Detect system theme preference
  function getSystemTheme(): "light" | "dark" {
    if (import.meta.client && window.matchMedia) {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    }
    return "light";
  }

  // Calculate effective theme based on preference
  function getEffectiveTheme(): "light" | "dark" {
    if (preference.value === "system") {
      return getSystemTheme();
    }
    return preference.value;
  }

  // Apply theme to DOM
  function applyTheme(theme: "light" | "dark") {
    if (import.meta.client) {
      const html = document.documentElement;
      if (theme === "dark") {
        html.classList.add(HTML_CLASS);
      } else {
        html.classList.remove(HTML_CLASS);
      }
      isDark.value = theme === "dark";
    }
  }

  // Load saved preference from localStorage
  function loadPreference(): Theme {
    if (import.meta.client) {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "light" || saved === "dark" || saved === "system") {
        return saved;
      }
    }
    return "system";
  }

  // Save preference to localStorage
  function savePreference(theme: Theme) {
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, theme);
    }
  }

  // Toggle between light and dark (sets explicit preference)
  function toggleTheme() {
    const newPreference: Theme = isDark.value ? "light" : "dark";
    preference.value = newPreference;
    savePreference(newPreference);
    applyTheme(getEffectiveTheme());
  }

  // Set explicit theme preference
  function setTheme(theme: Theme) {
    preference.value = theme;
    savePreference(theme);
    applyTheme(getEffectiveTheme());
  }

  // Initialize theme on mount
  function initTheme() {
    if (import.meta.client && !initialized) {
      initialized = true;
      preference.value = loadPreference();
      applyTheme(getEffectiveTheme());

      // Listen for system theme changes
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = () => {
        if (preference.value === "system") {
          applyTheme(getEffectiveTheme());
        }
      };

      // Modern browsers
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener("change", handleChange);
      } else {
        // Fallback for older browsers
        mediaQuery.addListener(handleChange);
      }

      // Cleanup on unmount
      onUnmounted(() => {
        if (mediaQuery.removeEventListener) {
          mediaQuery.removeEventListener("change", handleChange);
        } else {
          mediaQuery.removeListener(handleChange);
        }
      });
    }
  }

  return {
    isDark,
    preference,
    toggleTheme,
    setTheme,
    initTheme,
  };
}
