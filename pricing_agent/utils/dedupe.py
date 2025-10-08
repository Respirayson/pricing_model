"""Deduplication utilities for price evidence."""

from typing import List, Set
from ..schemas import PriceEvidence


def deduplicate_evidence(evidence: List[PriceEvidence]) -> List[PriceEvidence]:
    """
    Remove duplicate price evidence based on content similarity.
    
    Args:
        evidence: List of price evidence
        
    Returns:
        Deduplicated list of evidence
    """
    if not evidence:
        return []
    
    # Simple deduplication based on key fields
    seen: Set[str] = set()
    deduplicated = []
    
    for ev in evidence:
        # Create a key based on important fields
        key = _create_evidence_key(ev)
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(ev)
    
    return deduplicated


def _create_evidence_key(ev: PriceEvidence) -> str:
    """Create a key for deduplication."""
    # Use source, data type, listing type, and price as key
    key_parts = [
        ev.source_id,
        ev.data_type.value,
        ev.listing_type.value,
        str(ev.price_value),
        ev.currency.value,
        ev.units,
    ]
    
    # Add region if present
    if ev.region:
        key_parts.append(ev.region)
    
    return "|".join(key_parts)


def merge_similar_evidence(evidence: List[PriceEvidence]) -> List[PriceEvidence]:
    """
    Merge similar evidence entries (e.g., price ranges).
    
    Args:
        evidence: List of price evidence
        
    Returns:
        List with merged evidence
    """
    # TODO: Implement more sophisticated merging
    # For now, just return deduplicated evidence
    return deduplicate_evidence(evidence)
