<script setup lang="ts">
// Root app component — provides global layout shell and provenance drawer

// Initialize theme before first render to prevent flash
const { initTheme } = useTheme();

onMounted(() => {
  initTheme();
});
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<style>
/* App-level global styles are imported via nuxt.config.ts css array */
</style>
