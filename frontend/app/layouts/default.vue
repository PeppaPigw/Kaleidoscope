<script setup lang="ts">
// Default layout — sidebar + topbar chrome
</script>

<template>
  <div class="ks-layout">
    <LayoutAppSidebar />
    <div class="ks-layout__main">
      <LayoutAppTopbar />
      <main class="ks-layout__content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.ks-layout {
  display: flex;
  min-height: 100dvh;
  background: var(--color-bg);
}

.ks-layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--duration-normal) var(--ease-smooth);
}

.ks-layout__content {
  flex: 1;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 28px 36px;
}

@media (max-width: 1280px) {
  .ks-layout__content {
    padding: 24px 28px;
  }
}

@media (max-width: 768px) {
  .ks-layout__main {
    margin-left: 0;
  }

  .ks-layout__content {
    padding: 16px 24px;
  }
}
</style>
