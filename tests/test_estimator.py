"""Tests for price estimator."""

import pytest
from pricing_agent.schemas import (
    PriceBenchRow, ItemSpec, DataType, ListingType
)
from pricing_agent.estimate.estimator import PriceEstimator


def create_test_benchmark():
    """Create test price benchmark."""
    return [
        PriceBenchRow(
            data_type=DataType.TELECOM_PROFILE,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="CN",
            n=10,
            p10=5.0,
            p50=10.0,
            p90=20.0,
            last_seen=None,
            sources=["source1", "source2"]
        ),
        PriceBenchRow(
            data_type=DataType.CONTACT,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="CN",
            n=5,
            p10=2.0,
            p50=5.0,
            p90=8.0,
            last_seen=None,
            sources=["source3"]
        ),
        PriceBenchRow(
            data_type=DataType.PII_CORE,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="ANY",
            n=15,
            p10=3.0,
            p50=7.0,
            p90=12.0,
            last_seen=None,
            sources=["source4", "source5"]
        ),
    ]


def test_estimator_creation():
    """Test creating price estimator."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    assert len(estimator.bench) == 3


def test_simple_estimation():
    """Test simple price estimation."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    
    spec = ItemSpec(
        data_type=DataType.TELECOM_PROFILE,
        region="CN",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={}
    )
    
    result = estimator.estimate(spec)
    
    assert result.base_sum == 10.0  # p50 for telecom_profile in CN
    assert result.est_price == 10.0  # No modifiers applied
    assert result.components_used == [DataType.TELECOM_PROFILE]
    assert result.confidence > 0.0


def test_estimation_with_components():
    """Test estimation with additional components."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    
    spec = ItemSpec(
        data_type=DataType.TELECOM_PROFILE,
        region="CN",
        components=[DataType.CONTACT, DataType.PII_CORE],
        listing_type=ListingType.RETAIL_LOOKUP,
        features={}
    )
    
    result = estimator.estimate(spec)
    
    # Base sum should include all components
    expected_base = 10.0 + 5.0 + 7.0  # telecom_profile + contact + pii_core
    assert result.base_sum == expected_base
    assert len(result.components_used) == 3


def test_estimation_with_modifiers():
    """Test estimation with modifiers."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    
    spec = ItemSpec(
        data_type=DataType.TELECOM_PROFILE,
        region="CN",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={
            "freshness_days": 10,  # factor = 1.0
            "completeness": "full",  # factor = 1.2
            "exclusivity": "single_seller",  # factor = 1.5
            "vip_add": 5.0
        }
    )
    
    result = estimator.estimate(spec)
    
    # Expected: 10.0 * 1.0 * 1.2 * 1.5 + 5.0 = 23.0
    expected_price = 10.0 * 1.0 * 1.2 * 1.5 + 5.0
    assert abs(result.est_price - expected_price) < 0.01
    assert result.base_sum == 10.0


def test_estimation_no_data():
    """Test estimation when no benchmark data is available."""
    bench = []  # Empty benchmark
    estimator = PriceEstimator(bench)
    
    spec = ItemSpec(
        data_type=DataType.CREDIT_CARD,
        region="US",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={}
    )
    
    result = estimator.estimate(spec)
    
    assert result.base_sum == 0.0
    assert result.est_price == 0.0
    assert result.confidence == 0.0
    # Components are still tracked even if no benchmark data is found
    assert len(result.components_used) == 1


def test_estimation_region_fallback():
    """Test estimation with region fallback to ANY."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    
    # Request US region, but only CN and ANY available
    spec = ItemSpec(
        data_type=DataType.PII_CORE,
        region="US",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={}
    )
    
    result = estimator.estimate(spec)
    
    # Should use ANY region data
    assert result.base_sum == 7.0  # p50 for PII_CORE in ANY region
    assert result.components_used == [DataType.PII_CORE]


def test_confidence_calculation():
    """Test confidence calculation."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    
    # High confidence: exact match with good data
    spec1 = ItemSpec(
        data_type=DataType.TELECOM_PROFILE,
        region="CN",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={}
    )
    
    result1 = estimator.estimate(spec1)
    assert result1.confidence > 0.5
    
    # Lower confidence: no exact match
    spec2 = ItemSpec(
        data_type=DataType.CREDIT_CARD,
        region="US",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={}
    )
    
    result2 = estimator.estimate(spec2)
    assert result2.confidence == 0.0


def test_modifiers_applied_tracking():
    """Test that applied modifiers are tracked correctly."""
    bench = create_test_benchmark()
    estimator = PriceEstimator(bench)
    
    spec = ItemSpec(
        data_type=DataType.TELECOM_PROFILE,
        region="CN",
        listing_type=ListingType.RETAIL_LOOKUP,
        features={
            "freshness_days": 100,
            "completeness": "fragment",
            "exclusivity": "widely_leaked",
            "seller_reputation": "escrow_guarantee",
            "demand": "spike",
            "vip_add": 10.0
        }
    )
    
    result = estimator.estimate(spec)
    
    # Check that modifiers are tracked
    assert "freshness" in result.modifiers_applied
    assert "completeness" in result.modifiers_applied
    assert "exclusivity" in result.modifiers_applied
    assert "reputation" in result.modifiers_applied
    assert "demand" in result.modifiers_applied
    assert "vip_add" in result.modifiers_applied
    
    # Check specific values
    assert result.modifiers_applied["freshness"] == 0.5  # 100 days
    assert result.modifiers_applied["completeness"] == 0.4  # fragment
    assert result.modifiers_applied["exclusivity"] == 0.5  # widely_leaked
