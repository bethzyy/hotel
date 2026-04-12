// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  // SPA mode — no SSR, outputs static files for Flask to serve
  ssr: false,

  modules: ['@pinia/nuxt'],

  css: [
    'bootstrap/dist/css/bootstrap.min.css',
    'bootstrap-icons/font/bootstrap-icons.css',
    '~/assets/css/variables.css',
    '~/assets/css/main.css',
  ],

  runtimeConfig: {
    public: {
      apiBase: '/api',  // Same-origin — no proxy needed
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

  // Generate output directory (nuxt generate → .output/public)
  nitro: {
    prerender: {
      crawlLinks: false,
      routes: ['/'],
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
