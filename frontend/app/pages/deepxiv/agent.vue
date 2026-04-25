<script setup lang="ts">
/**
 * Redirect /deepxiv/agent to /discover with AI drawer open
 */
definePageMeta({
  middleware: defineNuxtRouteMiddleware(() => {
    return navigateTo("/discover?agent=open", { redirectCode: 301 });
  }),
});
</script>

<template>
  <div />
</template>
