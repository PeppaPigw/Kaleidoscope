<script setup lang="ts">
import {
  LayoutDashboard,
  Compass,
  Search,
  BookOpen,
  Network,
  FolderOpen,
  FlaskConical,
  PenTool,
  Flower2,
  Settings,
  ChevronLeft,
} from 'lucide-vue-next'

const route = useRoute()

const collapsed = ref(false)

interface NavItem {
  label: string
  icon: typeof LayoutDashboard
  to: string
  section?: string
}

const navigation: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/dashboard', section: 'HOME' },
  { label: 'Discover', icon: Compass, to: '/discover', section: 'EXPLORE' },
  { label: 'Search', icon: Search, to: '/search' },
  { label: 'Insights', icon: Network, to: '/insights/landscape' },
  { label: 'Workspaces', icon: FolderOpen, to: '/workspaces', section: 'RESEARCH' },
  { label: 'Evidence Lab', icon: FlaskConical, to: '/analysis/evidence' },
  { label: 'Synthesis', icon: BookOpen, to: '/synthesis' },
  { label: 'Writing', icon: PenTool, to: '/writing', section: 'CREATE' },
  { label: 'Knowledge', icon: Flower2, to: '/knowledge' },
]

function isActive(item: NavItem): boolean {
  return route.path.startsWith(item.to)
}

function getSectionBefore(index: number): string | undefined {
  return navigation[index]?.section
}
</script>

<template>
  <aside
    :class="['ks-sidebar', { 'ks-sidebar--collapsed': collapsed }]"
    role="navigation"
    aria-label="Main navigation"
  >
    <!-- Logo -->
    <div class="ks-sidebar__logo">
      <span class="ks-sidebar__logo-mark">K</span>
      <Transition name="ks-fade">
        <span v-if="!collapsed" class="ks-sidebar__logo-text">Kaleidoscope</span>
      </Transition>
    </div>

    <!-- Navigation -->
    <nav class="ks-sidebar__nav">
      <template v-for="(item, index) in navigation" :key="item.to">
        <!-- Section label -->
        <span
          v-if="!collapsed && getSectionBefore(index)"
          class="ks-sidebar__section"
        >
          {{ getSectionBefore(index) }}
        </span>

        <NuxtLink
          :to="item.to"
          :class="['ks-sidebar__item', { 'ks-sidebar__item--active': isActive(item) }]"
          :aria-label="item.label"
        >
          <component :is="item.icon" :size="20" :stroke-width="1.8" />
          <Transition name="ks-fade">
            <span v-if="!collapsed" class="ks-sidebar__item-label">{{ item.label }}</span>
          </Transition>
          <span v-if="isActive(item)" class="ks-sidebar__active-indicator" />
        </NuxtLink>
      </template>
    </nav>

    <!-- Bottom -->
    <div class="ks-sidebar__footer">
      <NuxtLink to="/admin" class="ks-sidebar__item" aria-label="Settings">
        <Settings :size="20" :stroke-width="1.8" />
        <Transition name="ks-fade">
          <span v-if="!collapsed" class="ks-sidebar__item-label">Settings</span>
        </Transition>
      </NuxtLink>

      <button
        class="ks-sidebar__collapse-btn"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="collapsed = !collapsed"
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
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: 30;
  transition: width var(--duration-normal) var(--ease-smooth);
  overflow: hidden;
}

.ks-sidebar--collapsed {
  width: 64px;
}

/* ─── Logo ─────────────────────────────────────────────── */
.ks-sidebar__logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 24px;
  white-space: nowrap;
}

.ks-sidebar__logo-mark {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-bg);
  font: 600 1.125rem / 1 var(--font-display);
  border-radius: 2px;
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
  transition: background-color var(--duration-fast) var(--ease-smooth),
              color var(--duration-fast) var(--ease-smooth);
  cursor: pointer;
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
  transition: background-color var(--duration-fast) var(--ease-smooth),
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
@media (max-width: 768px) {
  .ks-sidebar {
    transform: translateX(-100%);
  }
}
</style>
