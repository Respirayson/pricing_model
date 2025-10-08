"""Currency normalization utilities."""

from datetime import date
from typing import Dict, Optional
from ..schemas import Currency


# Simple static FX rates (in practice, you'd use a real FX service)
FX_RATES: Dict[str, Dict[str, float]] = {
    "2024-01-01": {
        "EUR": 0.85,
        "CNY": 7.2,
        "GBP": 0.79,
    },
    "2024-06-01": {
        "EUR": 0.92,
        "CNY": 7.1,
        "GBP": 0.78,
    },
    "2024-12-01": {
        "EUR": 0.91,
        "CNY": 7.0,
        "GBP": 0.79,
    },
}


def to_usd(amount: float, currency: Currency, when: Optional[date] = None) -> float:
    """
    Convert amount to USD using historical exchange rates.
    
    Args:
        amount: Amount to convert
        currency: Source currency
        when: Date for historical rate (defaults to most recent)
        
    Returns:
        Amount in USD
    """
    if currency == Currency.USD:
        return amount
    
    # Use provided date or default to most recent
    if when:
        date_key = when.strftime("%Y-%m-01")  # Use first of month
    else:
        date_key = "2024-12-01"  # Most recent rate
    
    # Find the closest available rate
    if date_key not in FX_RATES:
        # Use most recent available rate
        date_key = max(FX_RATES.keys())
    
    rate = FX_RATES[date_key].get(currency.value, 1.0)
    return amount / rate


def get_fx_rate(currency: Currency, when: Optional[date] = None) -> float:
    """
    Get exchange rate for currency to USD.
    
    Args:
        currency: Source currency
        when: Date for historical rate
        
    Returns:
        Exchange rate (amount of currency per USD)
    """
    if currency == Currency.USD:
        return 1.0
    
    if when:
        date_key = when.strftime("%Y-%m-01")
    else:
        date_key = "2024-12-01"
    
    if date_key not in FX_RATES:
        date_key = max(FX_RATES.keys())
    
    return FX_RATES[date_key].get(currency.value, 1.0)
