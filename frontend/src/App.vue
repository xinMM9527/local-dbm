<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#1677ff' } }">
    <router-view />
  </a-config-provider>
</template>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
