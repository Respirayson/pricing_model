"""Regex-based price detection for initial triage."""

import re
from typing import List, Tuple


def sniff_prices(text: str) -> List[str]:
    """
    Find potential price mentions using regex patterns.
    
    Args:
        text: Text to search for prices
        
    Returns:
        List of matched price strings
    """
    # Currency symbols and codes
    currency_patterns = [
        r'\$',  # Dollar sign
        r'USD',  # USD
        r'EUR',  # Euro
        r'CNY',  # Chinese Yuan
        r'GBP',  # British Pound
        r'€',    # Euro symbol
        r'¥',    # Yen symbol
        r'£',    # Pound symbol
    ]
    
    # Amount patterns
    amount_patterns = [
        r'\d+\.?\d*',  # Numbers with optional decimal
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Formatted numbers
    ]
    
    # Price-related keywords
    price_keywords = [
        r'price', r'cost', r'fee', r'charge', r'rate',
        r'per\s+(?:record|account|dataset|item)',
        r'bulk', r'discount', r'wholesale',
    ]
    
    matches = []
    
    # Look for currency + amount combinations
    for currency_pattern in currency_patterns:
        for amount_pattern in amount_patterns:
            # Currency before amount
            pattern1 = f'({currency_pattern})\s*({amount_pattern})'
            matches.extend(re.findall(pattern1, text, re.IGNORECASE))
            
            # Amount before currency
            pattern2 = f'({amount_pattern})\s*({currency_pattern})'
            matches.extend(re.findall(pattern2, text, re.IGNORECASE))
    
    # Look for price keywords near amounts
    for keyword in price_keywords:
        for amount_pattern in amount_patterns:
            # Keyword before amount
            pattern1 = f'({keyword})\s*[:\-]?\s*({amount_pattern})'
            matches.extend(re.findall(pattern1, text, re.IGNORECASE))
            
            # Amount before keyword
            pattern2 = f'({amount_pattern})\s*[:\-]?\s*({keyword})'
            matches.extend(re.findall(pattern2, text, re.IGNORECASE))
    
    # Convert tuples to strings and deduplicate
    price_strings = []
    seen = set()
    
    for match in matches:
        if isinstance(match, tuple):
            price_str = ' '.join(str(m) for m in match if m)
        else:
            price_str = str(match)
        
        if price_str and price_str not in seen:
            price_strings.append(price_str)
            seen.add(price_str)
    
    return price_strings
