import { defineStore } from 'pinia'
import { getDeviceFingerprint } from '~/utils/storage'

interface AuthState {
  user: { id: number; phone: string; nickname?: string; avatar_url?: string } | null
  token: string | null
  deviceFingerprint: string
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    deviceFingerprint: '',
  }),

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
  },

  actions: {
    init() {
      if (import.meta.client) {
        this.token = localStorage.getItem('auth_token')
        this.deviceFingerprint = getDeviceFingerprint()
        try {
          const userStr = localStorage.getItem('auth_user')
          if (userStr) this.user = JSON.parse(userStr)
        } catch { /* ignore */ }
      }
    },

    setToken(token: string, user: AuthState['user']) {
      this.token = token
      this.user = user
      if (import.meta.client) {
        localStorage.setItem('auth_token', token)
        if (user) localStorage.setItem('auth_user', JSON.stringify(user))
      }
    },

    logout() {
      this.token = null
      this.user = null
      if (import.meta.client) {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
      }
    },

    async sendCode(phone: string): Promise<string> {
      const { post } = useApi()
      const data = await post<{ code: string }>('/auth/send-code', { phone })
      return data.code || ''
    },

    async login(phone: string, code: string) {
      const { post } = useApi()
      const data = await post<{ access_token: string; user: AuthState['user'] }>('/auth/login', { phone, code })
      this.setToken(data.access_token, data.user)
    },

    async checkAuth() {
      if (!this.token) {
        const { post } = useApi()
        try {
          const data = await post<{ authenticated: boolean; user?: AuthState['user']; device_fingerprint?: string }>('/auth/anonymous')
          if (data.device_fingerprint) {
            this.deviceFingerprint = data.device_fingerprint
          }
        } catch { /* ignore */ }
        return
      }
      const { get } = useApi()
      try {
        const data = await get<{ authenticated: boolean; user?: AuthState['user'] }>('/auth/me')
        if (data.authenticated && data.user) {
          this.user = data.user
          localStorage.setItem('auth_user', JSON.stringify(data.user))
        } else {
          this.logout()
        }
      } catch {
        this.logout()
      }
    },
  },
})
