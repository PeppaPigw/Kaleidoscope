<script setup lang="ts">
/**
 * Redirect /deepxiv/trending to /discover?tab=trending
 */
definePageMeta({
  middleware: defineNuxtRouteMiddleware(() => {
    return navigateTo("/discover?tab=trending", { redirectCode: 301 });
  }),
});
</script>

<template>
  <div />
</template>
