"""Main price estimator."""

from typing import List, Dict, Any
from ..schemas import PriceBenchRow, ItemSpec, EstimationResult, DataType, ListingType
from ..aggregate.aggregator import get_benchmark_for_spec
from .rule_model import apply_modifiers


class PriceEstimator:
    """Estimates prices based on benchmarks and modifiers."""
    
    def __init__(self, bench: List[PriceBenchRow]):
        """
        Initialize estimator with price benchmark.
        
        Args:
            bench: List of price benchmark rows
        """
        self.bench = bench
    
    def estimate(self, spec: ItemSpec) -> EstimationResult:
        """
        Estimate price for given item specification.
        
        Args:
            spec: Item specification
            
        Returns:
            Estimation result
        """
        # Get base components
        base_sum, components_used = self.pick_base_components(spec)
        
        # Apply modifiers
        est_price = apply_modifiers(base_sum, spec.features)
        
        # Calculate confidence based on available data
        confidence = self._calculate_confidence(spec, components_used)
        
        # Extract modifiers applied
        modifiers_applied = self._extract_modifiers_applied(spec.features)
        
        return EstimationResult(
            base_sum=base_sum,
            est_price=est_price,
            modifiers_applied=modifiers_applied,
            components_used=components_used,
            confidence=confidence
        )
    
    def pick_base_components(self, spec: ItemSpec) -> tuple[float, List[DataType]]:
        """
        Pick base price components for the specification.
        
        Args:
            spec: Item specification
            
        Returns:
            Tuple of (base_sum, components_used)
        """
        base_sum = 0.0
        components_used = []
        
        # Add primary data type
        primary_price = self._get_component_price(spec.data_type, spec.listing_type, spec.region)
        if primary_price is not None:
            base_sum += primary_price
            components_used.append(spec.data_type)
        
        # Add additional components
        for component in spec.components:
            if component != spec.data_type:  # Avoid double counting
                component_price = self._get_component_price(component, spec.listing_type, spec.region)
                if component_price is not None:
                    base_sum += component_price
                    components_used.append(component)
        
        return base_sum, components_used
    
    def _get_component_price(self, data_type: DataType, listing_type: ListingType, region: str = None) -> float:
        """Get price for a specific component."""
        bench_row = get_benchmark_for_spec(self.bench, data_type, listing_type, region)
        if bench_row:
            return bench_row.p50  # Use median price
        return 0.0
    
    def _calculate_confidence(self, spec: ItemSpec, components_used: List[DataType]) -> float:
        """Calculate confidence in the estimate."""
        if not components_used:
            return 0.0
        
        # Check if we actually found benchmark data for any components
        has_benchmark_data = False
        for component in components_used:
            bench_row = get_benchmark_for_spec(self.bench, component, spec.listing_type, spec.region)
            if bench_row and bench_row.n > 0:
                has_benchmark_data = True
                break
        
        if not has_benchmark_data:
            return 0.0
        
        # Base confidence on how many components we found data for
        component_coverage = len(components_used) / (1 + len(spec.components))
        
        # Adjust for data availability
        data_availability = 0.0
        for component in components_used:
            bench_row = get_benchmark_for_spec(self.bench, component, spec.listing_type, spec.region)
            if bench_row and bench_row.n > 0:
                # Higher confidence for more data points
                data_availability += min(1.0, bench_row.n / 10.0)
        
        data_availability /= len(components_used)
        
        # Combine factors
        confidence = (component_coverage * 0.6 + data_availability * 0.4)
        return min(1.0, confidence)
    
    def _extract_modifiers_applied(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Extract the modifiers that were applied."""
        modifiers = {}
        
        # Import modifier functions
        from ..aggregate.modifiers import (
            freshness_factor, completeness_factor, exclusivity_factor,
            packaging_factor, reputation_factor, demand_factor
        )
        
        if "freshness_days" in features:
            modifiers["freshness"] = freshness_factor(features["freshness_days"])
        
        if "completeness" in features:
            modifiers["completeness"] = completeness_factor(features["completeness"])
        
        if "exclusivity" in features:
            modifiers["exclusivity"] = exclusivity_factor(features["exclusivity"])
        
        if "listing_type" in features:
            modifiers["packaging"] = packaging_factor(features["listing_type"])
        
        if "seller_reputation" in features:
            modifiers["reputation"] = reputation_factor(features["seller_reputation"])
        
        if "demand" in features:
            modifiers["demand"] = demand_factor(features["demand"])
        
        if "vip_add" in features:
            modifiers["vip_add"] = features["vip_add"]
        
        return modifiers
