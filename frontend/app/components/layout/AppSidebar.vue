<script setup lang="ts">
/* eslint-disable vue/html-self-closing */
import {
  LayoutDashboard,
  Compass,
  Search,
  BookOpen,
  Network,
  FolderOpen,
  FlaskConical,
  BarChart3,
  PenTool,
  Flower2,
  Settings,
  ChevronLeft,
  Bookmark,
  Rss,
  Braces,
} from "lucide-vue-next";

import { isSidebarItemActive } from "./sidebarActive";

const route = useRoute();
const { t } = useTranslation();
const {
  isMobile,
  mobileOpen,
  sidebarCollapsed,
  closeMobileSidebar,
  toggleSidebar,
} = useAppShell();

interface NavItem {
  labelKey: keyof typeof import("~/composables/useTranslation").UI_LABELS.en;
  icon: typeof LayoutDashboard;
  to: string;
  sectionKey?: keyof typeof import("~/composables/useTranslation").UI_LABELS.en;
}

const navDefinition: NavItem[] = [
  {
    labelKey: "dashboard",
    icon: LayoutDashboard,
    to: "/dashboard",
    sectionKey: "home",
  },
  {
    labelKey: "discover",
    icon: Compass,
    to: "/discover",
    sectionKey: "explore",
  },
  { labelKey: "search", icon: Search, to: "/search" },
  { labelKey: "insights", icon: Network, to: "/insights/landscape" },
  {
    labelKey: "workspaces",
    icon: FolderOpen,
    to: "/workspaces",
    sectionKey: "research",
  },
  { labelKey: "collections", icon: Bookmark, to: "/collections" },
  { labelKey: "evidenceLab", icon: FlaskConical, to: "/analysis/evidence" },
  { labelKey: "analytics", icon: BarChart3, to: "/analysis" },
  { labelKey: "synthesis", icon: BookOpen, to: "/synthesis" },
  { labelKey: "writing", icon: PenTool, to: "/writing", sectionKey: "create" },
  { labelKey: "knowledge", icon: Flower2, to: "/knowledge" },
  { labelKey: "subscriptions", icon: Rss, to: "/settings/subscriptions" },
  {
    labelKey: "apiDocs",
    icon: Braces,
    to: "/api-docs",
    sectionKey: "developer",
  },
];

const navPaths = navDefinition.map((item) => item.to);

function isActive(item: NavItem): boolean {
  return isSidebarItemActive(route.path, item.to, navPaths);
}

function getSectionBefore(index: number): string | undefined {
  const key = navDefinition[index]?.sectionKey;
  return key ? t(key) : undefined;
}

const collapsed = computed(() => !isMobile.value && sidebarCollapsed.value);

const sidebarToggleLabel = computed(() => {
  if (isMobile.value) {
    return mobileOpen.value ? "Close sidebar" : "Open sidebar";
  }
  return collapsed.value ? "Expand sidebar" : "Collapse sidebar";
});

function handleNavClick() {
  if (isMobile.value) {
    closeMobileSidebar();
  }
}
</script>

<template>
  <aside
    :class="[
      'ks-sidebar',
      {
        'ks-sidebar--collapsed': collapsed,
        'ks-sidebar--mobile-open': mobileOpen,
      },
    ]"
    role="navigation"
    aria-label="Main navigation"
  >
    <!-- Logo -->
    <div class="ks-sidebar__logo">
      <img
        src="/brand/kaleidoscope-icon-rounded.png"
        alt=""
        aria-hidden="true"
        class="ks-sidebar__logo-mark"
      />
      <Transition name="ks-fade">
        <span v-if="!collapsed" class="ks-sidebar__logo-text"
          >Kaleidoscope</span
        >
      </Transition>
      <button
        v-if="isMobile"
        type="button"
        class="ks-sidebar__mobile-close"
        aria-label="Close sidebar"
        @click="closeMobileSidebar()"
      >
        ×
      </button>
    </div>

    <!-- Navigation -->
    <nav class="ks-sidebar__nav">
      <template v-for="(item, index) in navDefinition" :key="item.to">
        <!-- Section label -->
        <span
          v-if="!collapsed && getSectionBefore(index)"
          class="ks-sidebar__section"
        >
          {{ getSectionBefore(index) }}
        </span>

        <NuxtLink
          :to="item.to"
          prefetch-on="interaction"
          :class="[
            'ks-sidebar__item',
            { 'ks-sidebar__item--active': isActive(item) },
          ]"
          :aria-label="t(item.labelKey)"
          @click="handleNavClick"
        >
          <component :is="item.icon" :size="20" :stroke-width="1.8" />
          <Transition name="ks-fade">
            <span v-if="!collapsed" class="ks-sidebar__item-label">{{
              t(item.labelKey)
            }}</span>
          </Transition>
          <span v-if="isActive(item)" class="ks-sidebar__active-indicator" />
        </NuxtLink>
      </template>
    </nav>

    <!-- Bottom -->
    <div class="ks-sidebar__footer">
      <NuxtLink
        to="/admin"
        prefetch-on="interaction"
        class="ks-sidebar__item"
        :aria-label="t('admin')"
        @click="handleNavClick"
      >
        <Settings :size="20" :stroke-width="1.8" />
        <Transition name="ks-fade">
          <span v-if="!collapsed" class="ks-sidebar__item-label">{{
            t("admin")
          }}</span>
        </Transition>
      </NuxtLink>

      <button
        class="ks-sidebar__collapse-btn"
        :aria-label="sidebarToggleLabel"
        @click="toggleSidebar()"
      >
        <ChevronLeft
          :size="18"
          :stroke-width="2"
          :class="{ 'ks-sidebar__collapse-icon--flip': collapsed }"
        />
      </button>
    </div>
  </aside>
</template>

<style scoped>
.ks-sidebar {
  position: sticky;
  top: 0;
  width: 100%;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid color-mix(in srgb, var(--color-border) 84%, white);
  z-index: 30;
  transition:
    transform var(--duration-normal) var(--ease-smooth),
    width var(--duration-normal) var(--ease-smooth);
  overflow: hidden;
}

/* ─── Logo ─────────────────────────────────────────────── */
.ks-sidebar__logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 24px;
  white-space: nowrap;
}

.ks-sidebar__mobile-close {
  margin-left: auto;
  display: none;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: transparent;
  color: var(--color-secondary);
  font-size: 1.2rem;
  line-height: 1;
}

.ks-sidebar__logo-mark {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  display: block;
  object-fit: contain;
}

.ks-sidebar__logo-text {
  font: 600 1.125rem / 1 var(--font-display);
  color: var(--color-text);
  letter-spacing: -0.01em;
}

/* ─── Section label ────────────────────────────────────── */
.ks-sidebar__section {
  display: block;
  padding: 16px 20px 6px;
  font: 600 0.6875rem / 1 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-secondary);
  user-select: none;
  white-space: nowrap;
  min-height: 38px;
}

/* ─── Nav items ────────────────────────────────────────── */
.ks-sidebar__nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 8px;
  overflow-y: auto;
  overflow-x: hidden;
}

.ks-sidebar__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--color-secondary);
  text-decoration: none;
  white-space: nowrap;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
  cursor: pointer;
}

.ks-sidebar--collapsed .ks-sidebar__logo {
  justify-content: center;
  padding-inline: 10px;
}

.ks-sidebar--collapsed .ks-sidebar__nav {
  padding-inline: 6px;
}

.ks-sidebar--collapsed .ks-sidebar__item {
  justify-content: center;
  padding-inline: 0;
}

.ks-sidebar--collapsed .ks-sidebar__footer {
  padding-inline: 6px;
}

.ks-sidebar__item:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-sidebar__item--active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}

.ks-sidebar__item-label {
  font: 500 0.875rem / 1.4 var(--font-sans);
}

.ks-sidebar__active-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--color-primary);
  border-radius: 0 2px 2px 0;
}

/* ─── Footer ───────────────────────────────────────────── */
.ks-sidebar__footer {
  padding: 8px;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-sidebar__collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px;
  background: none;
  border: none;
  color: var(--color-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-sidebar__collapse-btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-sidebar__collapse-icon--flip {
  transform: rotate(180deg);
  transition: transform var(--duration-normal) var(--ease-smooth);
}

/* ─── Mobile ───────────────────────────────────────────── */
@media (max-width: 960px) {
  .ks-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: min(86vw, 320px);
    max-width: 320px;
    transform: translateX(-100%);
    z-index: 45;
    box-shadow: 24px 0 48px rgba(26, 26, 26, 0.18);
  }

  .ks-sidebar--mobile-open {
    transform: translateX(0);
  }

  .ks-sidebar__mobile-close {
    display: inline-flex;
  }
}
</style>
