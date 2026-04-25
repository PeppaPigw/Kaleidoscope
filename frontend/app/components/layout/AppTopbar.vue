<script setup lang="ts">
import {
  Search,
  Command,
  Bell,
  User,
  Menu,
  X,
  Settings,
  Moon,
  Sun,
  LogOut,
  Languages,
} from "lucide-vue-next";
import { useEventListener } from "@vueuse/core";

const { isZh, t, toggleLocale } = useTranslation();
const { isMobile, mobileOpen, sidebarCollapsed, toggleSidebar } = useAppShell();
const { isDark, toggleTheme } = useTheme();

const route = useRoute();

const showSearch = ref(false);
const searchInput = ref("");
const searchInputRef = ref<HTMLInputElement | null>(null);

// ─── Notification state ─────────────────────────────────────
interface Notification {
  id: string;
  title: string;
  detail: string;
  time: string;
  read: boolean;
  link: string;
}

const showNotifications = ref(false);
const notifications = ref<Notification[]>([
  {
    id: "n1",
    title: "3 new papers ingested",
    detail: "Nature MI RSS synced — 3 papers matched your filters.",
    time: "8 min ago",
    read: false,
    link: "/discover",
  },
  {
    id: "n2",
    title: "Conflict detected",
    detail: "MedQA SOTA claim contradicts external validation results.",
    time: "24 min ago",
    read: false,
    link: "/analysis/evidence",
  },
  {
    id: "n3",
    title: "Workspace update",
    detail: "Clinical Reasoning Review: 2 papers annotated by collaborator.",
    time: "1h ago",
    read: false,
    link: "/workspaces/ws-1",
  },
  {
    id: "n4",
    title: "Code release tracked",
    detail: "BenchLab-128K GitHub repository linked successfully.",
    time: "2h ago",
    read: true,
    link: "/discover",
  },
]);

const unreadCount = computed(
  () => notifications.value.filter((n) => !n.read).length,
);

function handleNotificationClick(notification: Notification) {
  notification.read = true;
  showNotifications.value = false;
  navigateTo(notification.link);
}

function markAllRead() {
  notifications.value.forEach((n) => {
    n.read = true;
  });
}

// ─── Profile state ──────────────────────────────────────────
const showProfile = ref(false);

function handleProfileNavigate(path: string) {
  showProfile.value = false;
  navigateTo(path);
}

function handleSignOut() {
  showProfile.value = false;
  if (import.meta.client) {
    localStorage.removeItem("ks_access_token");
    localStorage.removeItem("ks_user_id");
  }
  navigateTo("/login");
}

// ─── Close dropdowns on outside click ───────────────────────
const notifRef = ref<HTMLElement | null>(null);
const profileRef = ref<HTMLElement | null>(null);

useEventListener(document, "click", (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (
    showNotifications.value &&
    notifRef.value &&
    !notifRef.value.contains(target)
  ) {
    showNotifications.value = false;
  }
  if (
    showProfile.value &&
    profileRef.value &&
    !profileRef.value.contains(target)
  ) {
    showProfile.value = false;
  }
});

// ─── Shared logic from original ─────────────────────────────
const pageTitle = computed(() => {
  return (route.meta.title as string) || "Kaleidoscope";
});

const sidebarToggleLabel = computed(() => {
  if (isMobile.value) {
    return mobileOpen.value ? "Close navigation" : "Open navigation";
  }
  return sidebarCollapsed.value ? "Expand navigation" : "Collapse navigation";
});

function handleSearchKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") showSearch.value = false;
}

function handleSearchSubmit() {
  const query = searchInput.value.trim();
  if (!query) return;
  showSearch.value = false;
  navigateTo({
    path: "/discover",
    query: { tab: "search", q: query },
  });
  searchInput.value = "";
}

useEventListener(document, "keydown", (e: KeyboardEvent) => {
  const target = e.target as HTMLElement;
  if (
    target.isContentEditable ||
    target.tagName === "INPUT" ||
    target.tagName === "TEXTAREA"
  )
    return;
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    showSearch.value = !showSearch.value;
  }
});

watch(showSearch, (open) => {
  if (open) {
    nextTick(() => searchInputRef.value?.focus());
  }
});
</script>

<template>
  <header class="ks-topbar" role="banner">
    <!-- Left: Page identity -->
    <div class="ks-topbar__left">
      <button
        class="ks-topbar__shell-btn"
        :aria-label="sidebarToggleLabel"
        @click="toggleSidebar()"
      >
        <component
          :is="isMobile && mobileOpen ? X : Menu"
          :size="17"
          :stroke-width="2"
        />
      </button>
      <h1 class="ks-topbar__title">{{ pageTitle }}</h1>
    </div>

    <!-- Center: Quick search -->
    <div class="ks-topbar__center">
      <button
        class="ks-topbar__search-trigger"
        aria-label="Open search (⌘K)"
        @click="showSearch = true"
      >
        <Search :size="16" :stroke-width="2" />
        <span class="ks-topbar__search-placeholder"
          >Search papers, claims, authors…</span
        >
        <kbd class="ks-topbar__kbd"> <Command :size="11" />K </kbd>
      </button>
    </div>

    <!-- Right: Actions -->
    <div class="ks-topbar__right">
      <!-- Notification button -->
      <div ref="notifRef" class="ks-topbar__dropdown-wrap">
        <button
          class="ks-topbar__icon-btn"
          aria-label="Notifications"
          :aria-expanded="showNotifications"
          @click.stop="
            showNotifications = !showNotifications;
            showProfile = false;
          "
        >
          <Bell :size="18" :stroke-width="1.8" />
          <span v-if="unreadCount > 0" class="ks-topbar__notification-dot">
            {{ unreadCount }}
          </span>
        </button>

        <!-- Notification dropdown -->
        <Transition name="ks-fade">
          <div
            v-if="showNotifications"
            class="ks-topbar__dropdown ks-topbar__dropdown--notif"
            role="menu"
            aria-label="Notifications"
          >
            <div class="ks-topbar__dropdown-header">
              <span class="ks-type-label" style="font-weight: 600"
                >Notifications</span
              >
              <button
                v-if="unreadCount > 0"
                type="button"
                class="ks-topbar__dropdown-action"
                @click="markAllRead"
              >
                Mark all read
              </button>
            </div>
            <ul class="ks-topbar__notif-list">
              <li
                v-for="notif in notifications"
                :key="notif.id"
                :class="[
                  'ks-topbar__notif-item',
                  { 'ks-topbar__notif-item--unread': !notif.read },
                ]"
              >
                <button
                  type="button"
                  class="ks-topbar__notif-btn"
                  @click="handleNotificationClick(notif)"
                >
                  <span class="ks-topbar__notif-title">{{ notif.title }}</span>
                  <span class="ks-topbar__notif-detail">{{
                    notif.detail
                  }}</span>
                  <span class="ks-type-data">{{ notif.time }}</span>
                </button>
              </li>
            </ul>
          </div>
        </Transition>
      </div>

      <!-- Profile button -->
      <div ref="profileRef" class="ks-topbar__dropdown-wrap">
        <button
          class="ks-topbar__icon-btn"
          aria-label="Profile"
          :aria-expanded="showProfile"
          @click.stop="
            showProfile = !showProfile;
            showNotifications = false;
          "
        >
          <User :size="18" :stroke-width="1.8" />
        </button>

        <!-- Profile dropdown -->
        <Transition name="ks-fade">
          <div
            v-if="showProfile"
            class="ks-topbar__dropdown ks-topbar__dropdown--profile"
            role="menu"
            aria-label="Profile menu"
          >
            <div class="ks-topbar__profile-info">
              <div class="ks-topbar__profile-avatar">R</div>
              <div>
                <span class="ks-topbar__profile-name">Researcher</span>
                <span class="ks-type-data">researcher@lab.edu</span>
              </div>
            </div>
            <div class="ks-topbar__profile-divider" />
            <button
              type="button"
              class="ks-topbar__profile-item"
              @click="handleProfileNavigate('/workspaces')"
            >
              <Settings :size="16" :stroke-width="1.8" />
              {{ t("myWorkspaces") }}
            </button>
            <button
              type="button"
              class="ks-topbar__profile-item"
              @click="toggleTheme"
            >
              <component
                :is="isDark ? Sun : Moon"
                :size="16"
                :stroke-width="1.8"
              />
              {{ isDark ? t("lightMode") : t("darkMode") }}
            </button>
            <button
              type="button"
              class="ks-topbar__profile-item"
              @click="toggleLocale"
            >
              <Languages :size="16" :stroke-width="1.8" />
              <span>{{ isZh ? "Switch to English" : "切换为中文" }}</span>
              <span class="ks-topbar__lang-badge">{{
                isZh ? "ZH" : "EN"
              }}</span>
            </button>
            <div class="ks-topbar__profile-divider" />
            <button
              type="button"
              class="ks-topbar__profile-item ks-topbar__profile-item--danger"
              @click="handleSignOut"
            >
              <LogOut :size="16" :stroke-width="1.8" />
              {{ t("signOut") }}
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Search modal overlay -->
    <Teleport to="body">
      <Transition name="ks-fade">
        <div
          v-if="showSearch"
          class="ks-topbar__search-overlay"
          @click.self="showSearch = false"
        >
          <div
            class="ks-topbar__search-modal ks-motion-paper-reveal"
            role="dialog"
            aria-modal="true"
            aria-label="Quick search"
          >
            <div class="ks-topbar__search-input-wrap">
              <Search
                :size="18"
                :stroke-width="2"
                class="ks-topbar__search-icon"
              />
              <input
                ref="searchInputRef"
                v-model="searchInput"
                type="text"
                class="ks-topbar__search-input"
                placeholder="Search anything…"
                @keydown="handleSearchKeydown"
                @keydown.enter="handleSearchSubmit"
              />
            </div>
            <div class="ks-topbar__search-hint">
              <span class="ks-type-data"
                >Press Enter to search · Esc to close</span
              >
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </header>
</template>

<style scoped>
.ks-topbar {
  position: sticky;
  top: 0;
  /* Keep topbar menus above page-level sticky headers and ribbons. */
  z-index: 40;
  display: flex;
  align-items: center;
  gap: 16px;
  height: var(--topbar-height);
  padding: 0 32px;
  background: rgba(250, 250, 247, 0.92);
  backdrop-filter: var(--ks-backdrop-blur);
  border-bottom: 1px solid var(--color-border);
}

/* ─── Left ─────────────────────────────────────────────── */
.ks-topbar__left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.ks-topbar__shell-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--color-surface) 90%, white);
  color: var(--color-secondary);
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth),
    border-color var(--duration-fast) var(--ease-smooth);
}

.ks-topbar__shell-btn:hover {
  color: var(--color-primary);
  border-color: color-mix(
    in srgb,
    var(--color-primary) 28%,
    var(--color-border)
  );
  background: var(--color-primary-light);
}

.ks-topbar__title {
  font: 600 0.72rem / 1 var(--font-sans);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-secondary);
}

/* ─── Center — Search trigger ──────────────────────────── */
.ks-topbar__center {
  flex: 1;
  max-width: 480px;
  margin: 0 auto;
}

.ks-topbar__search-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-secondary);
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    box-shadow var(--duration-fast) var(--ease-smooth);
}

.ks-topbar__search-trigger:hover {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
}

.ks-topbar__search-placeholder {
  flex: 1;
  text-align: left;
  font: 400 0.8125rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-topbar__kbd {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  font: 500 0.6875rem / 1 var(--font-mono);
  color: var(--color-secondary);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
}

/* ─── Right ────────────────────────────────────────────── */
.ks-topbar__right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.ks-topbar__dropdown-wrap {
  position: relative;
}

.ks-topbar__icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--color-secondary);
  cursor: pointer;
  transition:
    background-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-topbar__icon-btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-topbar__notification-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--color-accent);
  border-radius: 10px;
  font: 600 0.625rem / 16px var(--font-mono);
  color: #fff;
  text-align: center;
}

/* ─── Dropdown base ────────────────────────────────────── */
.ks-topbar__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(26, 26, 26, 0.1);
  overflow: hidden;
  z-index: 50;
}

/* ─── Notification dropdown ────────────────────────────── */
.ks-topbar__dropdown--notif {
  width: 380px;
}

.ks-topbar__dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-border);
}

.ks-topbar__dropdown-action {
  background: none;
  border: none;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-primary);
  cursor: pointer;
}

.ks-topbar__dropdown-action:hover {
  text-decoration: underline;
}

.ks-topbar__notif-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 360px;
  overflow-y: auto;
}

.ks-topbar__notif-item {
  border-bottom: 1px solid var(--color-border);
}

.ks-topbar__notif-item:last-child {
  border-bottom: none;
}

.ks-topbar__notif-item--unread {
  background: rgba(13, 115, 119, 0.04);
}

.ks-topbar__notif-btn {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  padding: 12px 16px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-topbar__notif-btn:hover {
  background: rgba(13, 115, 119, 0.06);
}

.ks-topbar__notif-title {
  font: 600 0.8125rem / 1.3 var(--font-sans);
  color: var(--color-text);
}

.ks-topbar__notif-detail {
  font: 400 0.75rem / 1.4 var(--font-serif);
  color: var(--color-secondary);
}

/* ─── Profile dropdown ─────────────────────────────────── */
.ks-topbar__dropdown--profile {
  width: 240px;
  padding: 8px 0;
}

.ks-topbar__profile-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}

.ks-topbar__profile-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  font: 600 0.875rem / 1 var(--font-display);
  border-radius: 50%;
}

.ks-topbar__profile-name {
  display: block;
  font: 600 0.875rem / 1.3 var(--font-sans);
  color: var(--color-text);
}

.ks-topbar__profile-divider {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}

.ks-topbar__profile-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-smooth);
}

.ks-topbar__profile-item:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-topbar__profile-item--danger {
  color: #dc2626;
}

.ks-topbar__profile-item--danger:hover {
  background: rgba(220, 38, 38, 0.06);
  color: #dc2626;
}

.ks-topbar__lang-badge {
  margin-left: auto;
  padding: 1px 6px;
  font: 600 0.625rem / 1.4 var(--font-mono);
  color: var(--color-primary);
  background: rgba(13, 115, 119, 0.08);
  border-radius: 3px;
  letter-spacing: 0.04em;
}

/* ─── Search overlay ───────────────────────────────────── */
.ks-topbar__search-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 20vh;
  background: var(--color-overlay-dark);
  backdrop-filter: blur(4px);
}

.ks-topbar__search-modal {
  width: min(90vw, 560px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  box-shadow: var(--shadow-float);
  overflow: hidden;
}

.ks-topbar__search-input-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.ks-topbar__search-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

.ks-topbar__search-input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font: 400 1.125rem / 1.4 var(--font-serif);
  color: var(--color-text);
}

.ks-topbar__search-input::placeholder {
  color: var(--color-secondary);
}

.ks-topbar__search-hint {
  padding: 10px 20px;
  text-align: center;
}
</style>
