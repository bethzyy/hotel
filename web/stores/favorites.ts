import { defineStore } from 'pinia'
import type { Favorite } from '~/types/api'

export const useFavoritesStore = defineStore('favorites', {
  state: () => ({
    count: 0,
    items: [] as Favorite[],
  }),

  actions: {
    async loadCount() {
      const { get } = useApi()
      try {
        const data = await get<{ favorites: Favorite[]; total: number }>('/favorites')
        this.count = data.total
        this.items = data.favorites
      } catch { /* ignore */ }
    },

    async toggle(hotelId: string, hotelData?: Record<string, unknown>) {
      const { post } = useApi()
      const data = await post<{ hotel_id: string; is_favorite: boolean; action: string }>('/favorites/toggle', {
        hotel_id: hotelId,
        ...hotelData,
      })
      this.count += data.is_favorite ? 1 : -1
      return data
    },

    async check(hotelId: string): Promise<boolean> {
      const { get } = useApi()
      const data = await get<{ hotel_id: string; is_favorite: boolean }>(`/favorites/${hotelId}`)
      return data.is_favorite
    },

    async loadAll() {
      const { get } = useApi()
      const data = await get<{ favorites: Favorite[]; total: number }>('/favorites')
      this.items = data.favorites
      this.count = data.total
    },

    async remove(hotelId: string) {
      const { del } = useApi()
      await del(`/favorites/${hotelId}`)
      this.count = Math.max(0, this.count - 1)
      this.items = this.items.filter(f => f.hotel_id !== hotelId)
    },
  },
})
