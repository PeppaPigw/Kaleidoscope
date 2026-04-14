<script setup lang="ts">
// Auth layout — full-screen, no sidebar or topbar
</script>

<template>
  <div class="ks-auth-layout">
    <slot />
  </div>
</template>

<style scoped>
.ks-auth-layout {
  min-height: 100dvh;
  display: flex;
  background: var(--color-bg);
}
</style>
