import { useWindowSize } from "@vueuse/core";
import { useState } from "#imports";
import { computed, onMounted, watch } from "vue";

const SHELL_STORAGE_KEY = "ks-shell-sidebar-collapsed";
const MOBILE_BREAKPOINT = 960;
const SIDEBAR_EXPANDED_WIDTH = 280;
const SIDEBAR_COLLAPSED_WIDTH = 84;

function applySidebarWidth(width: number) {
  if (!import.meta.client) return;
  document.documentElement.style.setProperty("--sidebar-width", `${width}px`);
}

export function useAppShell() {
  const desktopCollapsed = useState<boolean>(
    "ks-shell-desktop-collapsed",
    () => false,
  );
  const mobileOpen = useState<boolean>("ks-shell-mobile-open", () => false);
  const preferencesLoaded = useState<boolean>(
    "ks-shell-preferences-loaded",
    () => false,
  );

  const { width } = useWindowSize();
  const isMobile = computed(() => width.value <= MOBILE_BREAKPOINT);

  const sidebarWidth = computed(() => {
    if (isMobile.value) return 0;
    return desktopCollapsed.value
      ? SIDEBAR_COLLAPSED_WIDTH
      : SIDEBAR_EXPANDED_WIDTH;
  });

  const sidebarCollapsed = computed(() => desktopCollapsed.value);

  function collapseSidebar() {
    desktopCollapsed.value = true;
  }

  function expandSidebar() {
    desktopCollapsed.value = false;
  }

  function toggleSidebar() {
    if (isMobile.value) {
      mobileOpen.value = !mobileOpen.value;
      return;
    }
    desktopCollapsed.value = !desktopCollapsed.value;
  }

  function closeMobileSidebar() {
    mobileOpen.value = false;
  }

  function openMobileSidebar() {
    mobileOpen.value = true;
  }

  if (import.meta.client) {
    onMounted(() => {
      if (!preferencesLoaded.value) {
        desktopCollapsed.value =
          localStorage.getItem(SHELL_STORAGE_KEY) === "1";
        preferencesLoaded.value = true;
      }
      applySidebarWidth(sidebarWidth.value);
    });

    watch(sidebarWidth, (value) => applySidebarWidth(value), {
      immediate: true,
    });

    watch(desktopCollapsed, (value) => {
      localStorage.setItem(SHELL_STORAGE_KEY, value ? "1" : "0");
    });
  }

  watch(isMobile, (mobile) => {
    if (mobile) {
      mobileOpen.value = false;
    }
  });

  return {
    isMobile,
    mobileOpen,
    sidebarCollapsed,
    sidebarWidth,
    collapseSidebar,
    expandSidebar,
    toggleSidebar,
    closeMobileSidebar,
    openMobileSidebar,
  };
}
