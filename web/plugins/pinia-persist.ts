import { createPersistedState } from 'pinia-plugin-persistedstate'

export default defineNuxtPlugin((nuxtApp) => {
  // Only register persist plugin on client — SSR has no window/localStorage
  if (import.meta.client) {
    nuxtApp.$pinia.use(createPersistedState())
  }
})
