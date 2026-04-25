<script setup lang="ts">
/**
 * Redirect /deepxiv to /discover
 */
definePageMeta({
  middleware: defineNuxtRouteMiddleware(() => {
    return navigateTo("/discover", { redirectCode: 301 });
  }),
});
</script>

<template>
  <div />
</template>
