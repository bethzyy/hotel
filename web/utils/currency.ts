const currencySymbols: Record<string, string> = {
  CNY: '¥',
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  KRW: '₩',
  THB: '฿',
  SGD: 'S$',
  HKD: 'HK$',
  TWD: 'NT$',
  AUD: 'A$',
  CAD: 'C$',
  MYR: 'RM',
}

export function getCurrencySymbol(currency?: string): string {
  return currencySymbols[currency || ''] || currency || '¥'
}

export function formatPrice(price: number | undefined, currency?: string): string {
  if (price == null) return '--'
  const symbol = getCurrencySymbol(currency)
  return `${symbol}${Number(price).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}
