import { defineStore } from 'pinia'

function formatDate(d: Date): string {
  return d.toISOString().split('T')[0]
}

function defaultDates() {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const dayAfter = new Date(today)
  dayAfter.setDate(dayAfter.getDate() + 2)
  return { checkIn: formatDate(tomorrow), checkOut: formatDate(dayAfter), checkInDate: formatDate(tomorrow) }
}

function isDateExpired(dateStr: string): boolean {
  if (!dateStr) return true
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(0, 0, 0, 0)
  return new Date(dateStr) < tomorrow
}

export const useSearchFormStore = defineStore('searchForm', {
  state: () => {
    const defaults = defaultDates()
    return {
      provider: 'tuniu' as string,
      // Tuniu
      cityName: '',
      checkIn: defaults.checkIn,
      checkOut: defaults.checkOut,
      keyword: '',
      // RollingGo
      place: '',
      placeType: '',
      checkInDate: defaults.checkInDate,
      stayNights: 1,
      // Common
      adultCount: 2,
      childCount: 0,
      // Advanced
      minStar: '',
      maxPrice: undefined as number | undefined,
      size: 20,
    }
  },

  actions: {
    /** Reset expired dates to defaults */
    validateDates() {
      if (isDateExpired(this.checkIn) || isDateExpired(this.checkOut)) {
        const d = defaultDates()
        this.checkIn = d.checkIn
        this.checkOut = d.checkOut
      }
      if (isDateExpired(this.checkInDate)) {
        this.checkInDate = defaultDates().checkInDate
      }
    },

    /** Save current provider choice */
    setProvider(id: string) {
      this.provider = id
    },
  },

  persist: {
    beforeHydrate: () => {
      // Nuke corrupted localStorage BEFORE it overwrites SSR-hydrated state
      try {
        const raw = localStorage.getItem('searchForm')
        if (!raw) return
        const data = JSON.parse(raw)
        const stringFields = ['provider', 'cityName', 'place', 'placeType', 'keyword',
                              'checkIn', 'checkOut', 'checkInDate', 'minStar']
        for (const f of stringFields) {
          const v = data[f]
          // Catch both actual objects AND the string "[object Object]"
          if (v !== null && v !== undefined && v !== '' &&
              (typeof v === 'object' || v === '[object Object]')) {
            console.warn(`[Store] Corrupted searchForm.${f}, clearing localStorage`)
            localStorage.removeItem('searchForm')
            return
          }
        }
      } catch {
        localStorage.removeItem('searchForm')
      }
    },
    afterHydrate: (ctx) => {
      const s = ctx.store
      const d = defaultDates()
      const dateRe = /^\d{4}-\d{2}-\d{2}$/
      if (typeof s.checkIn !== 'string' || !dateRe.test(s.checkIn)) s.checkIn = d.checkIn
      if (typeof s.checkOut !== 'string' || !dateRe.test(s.checkOut)) s.checkOut = d.checkOut
      if (typeof s.checkInDate !== 'string' || !dateRe.test(s.checkInDate)) s.checkInDate = d.checkInDate
      if (typeof s.cityName !== 'string') s.cityName = ''
      if (typeof s.place !== 'string') s.place = ''
      if (typeof s.placeType !== 'string') s.placeType = ''
      if (typeof s.keyword !== 'string') s.keyword = ''
      if (typeof s.minStar !== 'string') s.minStar = ''
      if (typeof s.provider !== 'string') s.provider = 'tuniu'
      if (typeof s.stayNights !== 'number' || s.stayNights < 1) s.stayNights = 1
      if (typeof s.adultCount !== 'number' || s.adultCount < 1) s.adultCount = 2
      if (typeof s.childCount !== 'number' || s.childCount < 0) s.childCount = 0
      if (typeof s.size !== 'number' || s.size < 1) s.size = 20
    },
  },
})
