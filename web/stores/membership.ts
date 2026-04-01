import { defineStore } from 'pinia'
import type { Membership, PaymentPlan } from '~/types/api'

interface MembershipState {
  tier: 'free' | 'basic' | 'premium'
  expiresAt: string | null
  isMember: boolean
  searchRemaining: number
  searchLimit: number
  plans: PaymentPlan[]
  loaded: boolean
}

export const useMembershipStore = defineStore('membership', {
  state: (): MembershipState => ({
    tier: 'free',
    expiresAt: null,
    isMember: false,
    searchRemaining: 10,
    searchLimit: 10,
    plans: [],
    loaded: false,
  }),

  getters: {
    isUnlimited: (state) => state.searchRemaining === -1,
    canSearch: (state) => state.searchRemaining === -1 || state.searchRemaining > 0,
    tierLabel: (state) => {
      const labels: Record<string, string> = { free: '免费用户', basic: '基础会员', premium: '高级会员' }
      return labels[state.tier] || '免费用户'
    },
  },

  actions: {
    async fetchInfo() {
      const auth = useAuthStore()
      if (!auth.isAuthenticated) {
        this.tier = 'free'
        this.isMember = false
        this.searchRemaining = 5 // Anonymous limit
        this.searchLimit = 5
        this.loaded = true
        return
      }

      try {
        const { get } = useApi()
        const data = await get<Membership>('/membership/info')
        this.tier = data.tier
        this.expiresAt = data.expires_at
        this.isMember = data.is_member
        this.searchRemaining = data.search_remaining
        this.searchLimit = data.search_limit
        this.loaded = true
      } catch {
        // Silently fail
        this.loaded = true
      }
    },

    async fetchPlans() {
      if (this.plans.length > 0) return
      try {
        const { get } = useApi()
        const data = await get<{ plans: PaymentPlan[] }>('/payment/plans')
        this.plans = data.plans || []
      } catch {
        // Use default plans
        this.plans = [
          {
            id: 'monthly',
            name: '月度会员',
            price: 19.9,
            currency: 'CNY',
            days: 30,
            features: ['无限搜索次数', '价格变动提醒', '历史价格分析', '优先客服支持'],
          },
          {
            id: 'yearly',
            name: '年度会员',
            price: 199,
            currency: 'CNY',
            days: 365,
            features: ['无限搜索次数', '价格变动提醒', '历史价格分析', '优先客服支持'],
          },
        ]
      }
    },

    decrementSearch() {
      if (this.searchRemaining > 0) {
        this.searchRemaining--
      }
    },

    updateFromAuth(membership?: {
      tier: string
      expires_at: string | null
      is_member: boolean
      search_remaining: number
    }) {
      if (membership) {
        this.tier = membership.tier as MembershipState['tier']
        this.expiresAt = membership.expires_at
        this.isMember = membership.is_member
        this.searchRemaining = membership.search_remaining
        this.loaded = true
      }
    },
  },
})
