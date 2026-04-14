<script setup lang="ts">
import { Menu, X } from "lucide-vue-next";

// Default layout — sidebar + topbar chrome
const route = useRoute();
const {
  isMobile,
  mobileOpen,
  sidebarCollapsed,
  toggleSidebar,
  closeMobileSidebar,
} = useAppShell();

const hideTopbar = computed(() => route.meta.hideTopbar === true);
const isFlushContent = computed(() => route.meta.flushContent === true);

const shellToggleLabel = computed(() => {
  if (isMobile.value) {
    return mobileOpen.value ? "Close navigation" : "Open navigation";
  }
  return sidebarCollapsed.value ? "Expand navigation" : "Collapse navigation";
});

watch(
  () => route.fullPath,
  () => {
    closeMobileSidebar();
  },
);
</script>

<template>
  <div class="ks-layout">
    <Transition name="ks-fade">
      <button
        v-if="hideTopbar && isMobile"
        class="ks-layout__mobile-toggle"
        :aria-label="shellToggleLabel"
        @click="toggleSidebar()"
      >
        <component :is="mobileOpen ? X : Menu" :size="18" :stroke-width="2" />
      </button>
    </Transition>
    <Transition name="ks-fade">
      <button
        v-if="isMobile && mobileOpen"
        class="ks-layout__scrim"
        aria-label="Close navigation"
        @click="closeMobileSidebar()"
      />
    </Transition>
    <LayoutAppSidebar />
    <div class="ks-layout__main">
      <LayoutAppTopbar v-if="!hideTopbar" />
      <main
        :class="[
          'ks-layout__content',
          {
            'ks-layout__content--flush': isFlushContent,
          },
        ]"
      >
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.ks-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100dvh;
  background: var(--color-bg);
}

.ks-layout__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100dvh;
  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.7),
      rgba(255, 255, 255, 0.45)
    ),
    var(--color-bg);
  border-left: 1px solid color-mix(in srgb, var(--color-border) 84%, white);
}

.ks-layout__content {
  flex: 1;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 28px 36px;
}

.ks-layout__content--flush {
  height: 100dvh;
  max-height: 100dvh;
  max-width: none;
  overflow: hidden;
  padding: 8px 10px;
}

.ks-layout__scrim {
  position: fixed;
  inset: 0;
  z-index: 44;
  border: none;
  background: rgba(26, 26, 26, 0.22);
  backdrop-filter: blur(2px);
}

.ks-layout__mobile-toggle {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 46;
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--color-text);
  box-shadow: 0 10px 24px rgba(26, 26, 26, 0.12);
  backdrop-filter: var(--ks-backdrop-blur);
}

@media (max-width: 1280px) {
  .ks-layout__content {
    padding: 24px 28px;
  }

  .ks-layout__content--flush {
    padding: 8px 10px;
  }
}

@media (max-width: 960px) {
  .ks-layout {
    display: block;
  }

  .ks-layout__content {
    padding: 16px 24px;
  }

  .ks-layout__content--flush {
    padding: 6px 8px;
  }

  .ks-layout__mobile-toggle {
    display: inline-flex;
  }
}
</style>
