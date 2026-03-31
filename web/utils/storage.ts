export function getDeviceFingerprint(): string {
  if (import.meta.client) {
    let fp = localStorage.getItem('device_fingerprint')
    if (!fp) {
      const ua = navigator.userAgent
      const screen = `${screen.width}x${screen.height}`
      const lang = navigator.language
      const raw = `${ua}|${screen}|${lang}|${Date.now()}`
      fp = Array.from(crypto.getRandomValues(new Uint8Array(16)))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
        .substring(0, 32)
      localStorage.setItem('device_fingerprint', fp)
    }
    return fp
  }
  return ''
}
