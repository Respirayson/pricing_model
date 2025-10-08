"""Aggregator for building price benchmarks from evidence."""

import statistics
from datetime import date
from typing import List, Dict, Tuple
from ..schemas import PriceEvidence, PriceBenchRow, DataType, ListingType
from ..normalize.currency import to_usd


def build_price_bench(evidence: List[PriceEvidence]) -> List[PriceBenchRow]:
    """
    Build price benchmark from evidence.
    
    Args:
        evidence: List of price evidence
        
    Returns:
        List of aggregated price benchmark rows
    """
    # Group evidence by data_type, listing_type, and region
    groups = _group_evidence(evidence)
    
    bench_rows = []
    for (data_type, listing_type, region), group_evidence in groups.items():
        if not group_evidence:
            continue
            
        # Convert all prices to USD
        usd_prices = []
        sources = set()
        last_seen = None
        
        for ev in group_evidence:
            usd_price = to_usd(ev.price_value, ev.currency, ev.published_date)
            usd_prices.append(usd_price)
            sources.add(ev.source_id)
            
            if ev.published_date and (last_seen is None or ev.published_date > last_seen):
                last_seen = ev.published_date
        
        if not usd_prices:
            continue
        
        # Calculate percentiles
        usd_prices.sort()
        n = len(usd_prices)
        p10 = _percentile(usd_prices, 10)
        p50 = _percentile(usd_prices, 50)
        p90 = _percentile(usd_prices, 90)
        
        bench_row = PriceBenchRow(
            data_type=data_type,
            listing_type=listing_type,
            region=region,
            n=n,
            p10=p10,
            p50=p50,
            p90=p90,
            last_seen=last_seen,
            sources=list(sources)
        )
        
        bench_rows.append(bench_row)
    
    return bench_rows


def _group_evidence(evidence: List[PriceEvidence]) -> Dict[Tuple[DataType, ListingType, str], List[PriceEvidence]]:
    """Group evidence by data type, listing type, and region."""
    groups = {}
    
    for ev in evidence:
        # Use "ANY" for None region to group together
        region = ev.region or "ANY"
        key = (ev.data_type, ev.listing_type, region)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(ev)
    
    return groups


def _percentile(data: List[float], percentile: int) -> float:
    """Calculate percentile of sorted data."""
    if not data:
        return 0.0
    
    n = len(data)
    if n == 1:
        return data[0]
    
    # Use linear interpolation for percentiles
    k = (n - 1) * percentile / 100
    f = int(k)
    c = k - f
    
    if f + 1 < n:
        return data[f] * (1 - c) + data[f + 1] * c
    else:
        return data[f]


def get_benchmark_for_spec(bench: List[PriceBenchRow], data_type: DataType, 
                          listing_type: ListingType, region: str = None) -> PriceBenchRow:
    """
    Get benchmark row for specific data type, listing type, and region.
    
    Args:
        bench: List of benchmark rows
        data_type: Data type to match
        listing_type: Listing type to match
        region: Region to match (None for any)
        
    Returns:
        Matching benchmark row or None
    """
    # Try exact match first
    for row in bench:
        if (row.data_type == data_type and 
            row.listing_type == listing_type and 
            row.region == region):
            return row
    
    # Try with "ANY" region
    if region:
        for row in bench:
            if (row.data_type == data_type and 
                row.listing_type == listing_type and 
                row.region == "ANY"):
                return row
    
    return None
