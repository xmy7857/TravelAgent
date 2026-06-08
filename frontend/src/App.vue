<template>
  <div id="app">
    <a-layout style="min-height: 100vh">
      <a-layout-header style="background: #001529; padding: 0 50px; display: flex; align-items: center;">
        <div style="color: white; font-size: 24px; font-weight: bold; cursor: pointer;" @click="$router.push('/')">
          🌍 智能旅行助手
        </div>
      </a-layout-header>
      <a-layout-content style="padding: 0;">
        <router-view />
      </a-layout-content>
      <a-layout-footer style="text-align: center; background: #001529; color: rgba(255,255,255,0.6);">
        智能旅行助手 ©2026 - 基于AI Agent的个性化旅行规划
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif;
}
</style>
