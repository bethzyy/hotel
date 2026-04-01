/**
 * Lightweight analytics tracking composable
 *
 * Features:
 * - Auto pageview tracking via route changes
 * - Manual event tracking (search, view_hotel, compare, click_book, favorite)
 * - Batch event buffering (flush at 10 events or 5 seconds)
 * - sendBeacon fallback on page unload
 */

const BUFFER_SIZE = 10
const FLUSH_INTERVAL = 5000

interface TrackingEvent {
  event_type: string
  event_data?: Record<string, unknown>
  page?: string
  timestamp?: number
}

export const useTracking = () => {
  const config = useRuntimeConfig()
  let buffer: TrackingEvent[] = []
  let flushTimer: ReturnType<typeof setInterval> | null = null
  let initialized = false

  function getSessionId(): string {
    return getSessionIdGlobal()
  }

  function getBaseUrl(): string {
    return config.public.apiBase || '/api'
  }

  async function flush(): Promise<void> {
    if (buffer.length === 0) return

    const events = [...buffer]
    buffer = []

    try {
      const auth = useAuthStore()
      await $fetch(`${getBaseUrl()}/events/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
          ...(auth.deviceFingerprint ? { 'X-Device-Fingerprint': auth.deviceFingerprint } : {}),
          'X-Session-ID': getSessionId(),
        },
        body: events,
      })
    } catch {
      // Silently fail - tracking should never break the app
      // Put events back in buffer for retry
      buffer = [...events, ...buffer].slice(0, BUFFER_SIZE * 2)
    }
  }

  function startFlushTimer(): void {
    if (flushTimer) return
    flushTimer = setInterval(flush, FLUSH_INTERVAL)
  }

  function track(event: TrackingEvent): void {
    if (!import.meta.client) return

    buffer.push({
      ...event,
      timestamp: event.timestamp || Date.now(),
      page: event.page || window.location.pathname,
    })

    if (buffer.length >= BUFFER_SIZE) {
      flush()
    }
  }

  function trackPageview(path?: string): void {
    track({
      event_type: 'pageview',
      page: path || window.location.pathname,
      event_data: {
        referrer: document.referrer || undefined,
        title: document.title,
      },
    })
  }

  function trackSearch(data: {
    provider?: string
    place?: string
    checkIn?: string
    checkOut?: string
    resultCount?: number
  }): void {
    track({
      event_type: 'search',
      event_data: data,
    })
  }

  function trackViewHotel(data: {
    hotelId: string
    hotelName?: string
    provider?: string
    price?: number
  }): void {
    track({
      event_type: 'view_hotel',
      event_data: data,
    })
  }

  function trackCompare(data: {
    hotelId?: string
    providerCount?: number
    lowestPrice?: number
  }): void {
    track({
      event_type: 'compare',
      event_data: data,
    })
  }

  function trackClickBook(data: {
    hotelId?: string
    hotelName?: string
    provider?: string
    targetUrl?: string
  }): void {
    track({
      event_type: 'click_book',
      event_data: data,
    })
  }

  function trackFavorite(data: {
    hotelId: string
    action: 'added' | 'removed'
  }): void {
    track({
      event_type: 'favorite',
      event_data: data,
    })
  }

  function init(): void {
    if (!import.meta.client || initialized) return
    initialized = true

    startFlushTimer()

    // Auto pageview tracking
    const router = useRouter()
    router.afterEach((to) => {
      trackPageview(to.fullPath)
    })

    // Track initial pageview
    trackPageview()

    // Flush on page unload using sendBeacon
    window.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        flush()
      }
    })

    window.addEventListener('beforeunload', () => {
      if (buffer.length > 0) {
        const auth = useAuthStore()
        const events = [...buffer]
        buffer = []
        const blob = new Blob([JSON.stringify(events)], { type: 'application/json' })
        navigator.sendBeacon(
          `${getBaseUrl()}/events/track`,
          new Request(blob, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
              ...(auth.deviceFingerprint ? { 'X-Device-Fingerprint': auth.deviceFingerprint } : {}),
              'X-Session-ID': getSessionId(),
            },
          })
        )
      }
    })
  }

  return {
    init,
    track,
    trackPageview,
    trackSearch,
    trackViewHotel,
    trackCompare,
    trackClickBook,
    trackFavorite,
    flush,
  }
}

// Singleton session ID getter
function getSessionIdGlobal(): string {
  if (!import.meta.client) return ''

  const SESSION_KEY = 'analytics_session_id'
  const SESSION_TIMEOUT = 30 * 60 * 1000

  const stored = sessionStorage.getItem(SESSION_KEY)
  if (stored) {
    try {
      const { id, lastActivity } = JSON.parse(stored)
      if (Date.now() - lastActivity < SESSION_TIMEOUT) {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({ id, lastActivity: Date.now() }))
        return id
      }
    } catch {
      // Invalid data, generate new
    }
  }

  const newId = Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map(b => b.toString(36).padStart(2, '0'))
    .join('')
    .substring(0, 32)
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ id: newId, lastActivity: Date.now() }))
  return newId
}
