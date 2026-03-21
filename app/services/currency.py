"""
Currency conversion service for hotel price comparison.
Provides exchange rates and conversion utilities.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Hardcoded exchange rates (USD to CNY based on approximate market rates)
# These are fallback rates when real-time API is not available
# Update periodically for better accuracy
EXCHANGE_RATES = {
    'CNY': 1.0,
    'USD': 7.24,    # 1 USD = 7.24 CNY
    'EUR': 7.86,    # 1 EUR = 7.86 CNY
    'GBP': 9.21,    # 1 GBP = 9.21 CNY
    'HKD': 0.93,    # 1 HKD = 0.93 CNY
    'TWD': 0.22,    # 1 TWD = 0.22 CNY
    'JPY': 0.048,   # 1 JPY = 0.048 CNY
    'KRW': 0.0054,  # 1 KRW = 0.0054 CNY
    'SGD': 5.42,    # 1 SGD = 5.42 CNY
    'AUD': 4.68,    # 1 AUD = 4.68 CNY
    'THB': 0.21,    # 1 THB = 0.21 CNY
    'MYR': 1.62,    # 1 MYR = 1.62 CNY
}

# Currency symbol mapping for display
CURRENCY_SYMBOLS = {
    'CNY': '¥',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'HKD': 'HK$',
    'TWD': 'NT$',
    'JPY': '¥',
    'KRW': '₩',
    'SGD': 'S$',
    'AUD': 'A$',
    'THB': '฿',
    'MYR': 'RM',
}


def get_exchange_rate(currency: str) -> float:
    """
    Get exchange rate for a currency to CNY.

    Args:
        currency: Currency code (e.g., 'USD', 'EUR')

    Returns:
        Exchange rate to CNY (default 1.0 if unknown)
    """
    if not currency:
        return 1.0

    currency = currency.upper().strip()

    # Handle symbol inputs
    symbol_to_code = {v: k for k, v in CURRENCY_SYMBOLS.items()}
    if currency in symbol_to_code:
        currency = symbol_to_code[currency]

    return EXCHANGE_RATES.get(currency, 1.0)


def convert_to_cny(amount: Optional[float], from_currency: str) -> Optional[float]:
    """
    Convert an amount from a given currency to CNY.

    Args:
        amount: The amount to convert (can be None)
        from_currency: Source currency code

    Returns:
        Converted amount in CNY, or None if input is None
    """
    if amount is None:
        return None

    try:
        rate = get_exchange_rate(from_currency)
        result = round(amount * rate, 2)
        logger.debug(f"Currency conversion: {amount} {from_currency} = {result} CNY (rate: {rate})")
        return result
    except Exception as e:
        logger.warning(f"Currency conversion failed for {amount} {from_currency}: {e}")
        return amount  # Return original amount on error


def get_currency_symbol(currency: str) -> str:
    """
    Get the display symbol for a currency.

    Args:
        currency: Currency code or symbol

    Returns:
        Currency symbol for display
    """
    if not currency:
        return '¥'

    currency = currency.strip()

    # Already a known symbol
    if currency in CURRENCY_SYMBOLS.values():
        return currency

    # Look up by code
    return CURRENCY_SYMBOLS.get(currency.upper(), currency)


def format_price_with_cny(price: Optional[float], currency: str) -> str:
    """
    Format a price with CNY conversion if needed.

    Args:
        price: The price amount
        currency: Source currency code

    Returns:
        Formatted price string with CNY conversion if applicable
    """
    if price is None:
        return '暂无报价'

    symbol = get_currency_symbol(currency)

    if currency.upper() == 'CNY':
        return f"{symbol}{price}"

    # Convert to CNY for non-CNY currencies
    price_cny = convert_to_cny(price, currency)
    if price_cny is not None:
        return f"{symbol}{price} <small class=\"text-muted\">(≈¥{price_cny})</small>"

    return f"{symbol}{price}"
