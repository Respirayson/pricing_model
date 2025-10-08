"""Date utilities for the pricing agent."""

from datetime import date, datetime
from typing import Optional


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in various formats.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed date or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m",
        "%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def format_date(d: date) -> str:
    """
    Format date as ISO string.
    
    Args:
        d: Date to format
        
    Returns:
        ISO formatted date string
    """
    return d.isoformat()


def days_since(date_obj: date) -> int:
    """
    Calculate days since given date.
    
    Args:
        date_obj: Date to calculate from
        
    Returns:
        Number of days since the date
    """
    today = date.today()
    return (today - date_obj).days


def is_recent(date_obj: date, days: int = 30) -> bool:
    """
    Check if date is within recent days.
    
    Args:
        date_obj: Date to check
        days: Number of days to consider recent
        
    Returns:
        True if date is within recent days
    """
    return days_since(date_obj) <= days
