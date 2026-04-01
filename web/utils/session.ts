/**
 * Session management utility
 * Generates and manages session IDs for analytics tracking
 */

const SESSION_KEY = 'analytics_session_id'
const SESSION_TIMEOUT = 30 * 60 * 1000 // 30 minutes

function generateSessionId(): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map(b => b.toString(36).padStart(2, '0'))
    .join('')
    .substring(0, 32)
}

export function getSessionId(): string {
  if (!import.meta.client) return ''

  const stored = sessionStorage.getItem(SESSION_KEY)
  if (stored) {
    try {
      const { id, lastActivity } = JSON.parse(stored)
      if (Date.now() - lastActivity < SESSION_TIMEOUT) {
        // Update last activity
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({ id, lastActivity: Date.now() }))
        return id
      }
    } catch {
      // Invalid data, generate new
    }
  }

  const newId = generateSessionId()
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ id: newId, lastActivity: Date.now() }))
  return newId
}
