// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  modules: ['@pinia/nuxt'],

  css: [
    'bootstrap/dist/css/bootstrap.min.css',
    'bootstrap-icons/font/bootstrap-icons.css',
    '~/assets/css/variables.css',
    '~/assets/css/main.css',
  ],

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:5000/api',
      siteName: process.env.NUXT_PUBLIC_SITE_NAME || '酒店搜索比价',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || '',
    },
  },

  vite: {
    server: {
      fs: {
        allow: ['.', 'node_modules'],
      },
    },
  },

  // SSR rendering rules
  routeRules: {
    '/': { swr: 3600 }, // ISR 1h for homepage
    '/results': { ssr: true },
    '/detail/**': { ssr: true },
    '/booking': { ssr: false },
    '/order': { ssr: false },
    '/login': { ssr: false },
    '/favorites': { ssr: false },
  },

  // Dev server proxy to Flask API (avoids CORS in development)
  // Nitro devProxy strips the matched prefix, so target includes /api
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://localhost:5000/api',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },

  components: [
    {
      path: '~/components',
      pathPrefix: false,
    },
  ],

  app: {
    head: {
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
      ],
      meta: [
        { name: 'referrer', content: 'no-referrer' },
      ],
    },
  },
})
