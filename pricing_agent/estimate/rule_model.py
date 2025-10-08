"""Rule-based pricing model."""

from typing import Dict, Any
from ..aggregate.modifiers import apply_all_modifiers


def apply_modifiers(base_sum: float, features: Dict[str, Any]) -> float:
    """
    Apply pricing modifiers to base sum.
    
    Args:
        base_sum: Base price sum from benchmark
        features: Feature dictionary with modifier values
        
    Returns:
        Final estimated price
    """
    vip_add = features.get("vip_add", 0.0)
    return apply_all_modifiers(base_sum, features, vip_add)
