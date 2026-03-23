<script setup lang="ts">
// Index page — redirect to dashboard
definePageMeta({
  layout: 'default',
})

navigateTo('/dashboard', { redirectCode: 301 })
</script>

<template>
  <div />
</template>
