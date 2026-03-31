import type { ApiResponse } from '~/types/api'

export const useApi = () => {
  const config = useRuntimeConfig()

  const apiFetch = $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      const auth = useAuthStore()
      if (auth.token) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${auth.token}`,
        }
      }
      if (auth.deviceFingerprint) {
        options.headers = {
          ...options.headers,
          'X-Device-Fingerprint': auth.deviceFingerprint,
        }
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        const auth = useAuthStore()
        auth.logout()
      }
    },
  })

  async function get<T = unknown>(url: string, params?: Record<string, string | number>): Promise<T> {
    const query = params ? '?' + new URLSearchParams(
      Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return apiFetch<ApiResponse<T>>(url + query).then(r => {
      if (!r.success) throw new Error(r.error || 'Request failed')
      return r.data as T
    })
  }

  async function post<T = unknown>(url: string, body?: unknown): Promise<T> {
    return apiFetch<ApiResponse<T>>(url, { method: 'POST', body }).then(r => {
      if (!r.success) throw new Error(r.error || 'Request failed')
      return r.data as T
    })
  }

  async function del<T = unknown>(url: string): Promise<T> {
    return apiFetch<ApiResponse<T>>(url, { method: 'DELETE' }).then(r => {
      if (!r.success) throw new Error(r.error || 'Request failed')
      return r.data as T
    })
  }

  return { apiFetch, get, post, del }
}
