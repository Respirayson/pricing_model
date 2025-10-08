"""Price modifiers for estimation."""

from typing import Union


def freshness_factor(days_old: int) -> float:
    """
    Calculate freshness modifier based on age of data.
    
    Args:
        days_old: Number of days since data was created/leaked
        
    Returns:
        Modifier factor (1.0 = no change)
    """
    if days_old <= 30:
        return 1.0
    elif days_old < 180:  # 6 months
        return 0.5
    else:
        return 0.2


def completeness_factor(level: str) -> float:
    """
    Calculate completeness modifier based on data completeness.
    
    Args:
        level: Completeness level ("fragment", "standard", "full")
        
    Returns:
        Modifier factor
    """
    mapping = {
        "fragment": 0.4,
        "standard": 1.0,
        "full": 1.2,
    }
    return mapping.get(level.lower(), 1.0)


def exclusivity_factor(kind: str) -> float:
    """
    Calculate exclusivity modifier based on data availability.
    
    Args:
        kind: Exclusivity type ("widely_leaked", "limited", "single_seller")
        
    Returns:
        Modifier factor
    """
    mapping = {
        "widely_leaked": 0.5,
        "limited": 1.0,
        "single_seller": 1.5,
    }
    return mapping.get(kind.lower(), 1.0)


def packaging_factor(listing_type: str) -> float:
    """
    Calculate packaging modifier based on listing type.
    
    Args:
        listing_type: Type of listing ("retail_lookup", "bulk_dump", "account_access", "document_scan")
        
    Returns:
        Modifier factor
    """
    mapping = {
        "retail_lookup": 1.5,
        "bulk_dump": 0.3,
        "account_access": 1.0,
        "document_scan": 1.2,
    }
    return mapping.get(listing_type.lower(), 1.0)


def reputation_factor(level: str) -> float:
    """
    Calculate reputation modifier based on seller reputation.
    
    Args:
        level: Reputation level ("unknown", "verified", "escrow_guarantee")
        
    Returns:
        Modifier factor
    """
    mapping = {
        "unknown": 0.9,
        "verified": 1.0,
        "escrow_guarantee": 1.2,
    }
    return mapping.get(level.lower(), 1.0)


def demand_factor(level: str) -> float:
    """
    Calculate demand modifier based on market demand.
    
    Args:
        level: Demand level ("low", "normal", "high", "spike")
        
    Returns:
        Modifier factor
    """
    mapping = {
        "low": 0.8,
        "normal": 1.0,
        "high": 1.1,
        "spike": 1.3,
    }
    return mapping.get(level.lower(), 1.0)


def apply_all_modifiers(base_sum: float, features: dict, vip_add: float = 0.0) -> float:
    """
    Apply all modifiers to base sum.
    
    Args:
        base_sum: Base price sum
        features: Feature dictionary with modifier values
        vip_add: Additional VIP premium
        
    Returns:
        Final estimated price
    """
    # Apply multiplicative modifiers
    final_price = base_sum
    
    # Freshness
    if "freshness_days" in features:
        final_price *= freshness_factor(features["freshness_days"])
    
    # Completeness
    if "completeness" in features:
        final_price *= completeness_factor(features["completeness"])
    
    # Exclusivity
    if "exclusivity" in features:
        final_price *= exclusivity_factor(features["exclusivity"])
    
    # Packaging (from listing type)
    if "listing_type" in features:
        final_price *= packaging_factor(features["listing_type"])
    
    # Reputation
    if "seller_reputation" in features:
        final_price *= reputation_factor(features["seller_reputation"])
    
    # Demand
    if "demand" in features:
        final_price *= demand_factor(features["demand"])
    
    # Add VIP premium
    final_price += vip_add
    
    return max(0.0, final_price)  # Ensure non-negative
