"""Tests for price aggregator."""

import pytest
from datetime import date
from pricing_agent.schemas import PriceEvidence, PriceBenchRow, DataType, ListingType, Currency
from pricing_agent.aggregate.aggregator import build_price_bench, get_benchmark_for_spec


def create_test_evidence():
    """Create test price evidence."""
    return [
        PriceEvidence(
            source_id="source1",
            data_type=DataType.TELECOM_PROFILE,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="US",
            price_value=10.0,
            currency=Currency.USD,
            units="per_record",
            published_date=date(2024, 1, 1)
        ),
        PriceEvidence(
            source_id="source2",
            data_type=DataType.TELECOM_PROFILE,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="US",
            price_value=20.0,
            currency=Currency.USD,
            units="per_record",
            published_date=date(2024, 1, 2)
        ),
        PriceEvidence(
            source_id="source3",
            data_type=DataType.TELECOM_PROFILE,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="US",
            price_value=30.0,
            currency=Currency.USD,
            units="per_record",
            published_date=date(2024, 1, 3)
        ),
        PriceEvidence(
            source_id="source4",
            data_type=DataType.CONTACT,
            listing_type=ListingType.BULK_DUMP,
            region="CN",
            price_value=5.0,
            currency=Currency.USD,
            units="per_record",
            published_date=date(2024, 1, 1)
        ),
    ]


def test_build_price_bench():
    """Test building price benchmark from evidence."""
    evidence = create_test_evidence()
    bench = build_price_bench(evidence)
    
    assert len(bench) == 2  # Two different data_type/listing_type/region combinations
    
    # Find telecom profile benchmark
    telecom_bench = None
    for row in bench:
        if (row.data_type == DataType.TELECOM_PROFILE and 
            row.listing_type == ListingType.RETAIL_LOOKUP and 
            row.region == "US"):
            telecom_bench = row
            break
    
    assert telecom_bench is not None
    assert telecom_bench.n == 3  # Three telecom profile entries
    # Percentiles for [10.0, 20.0, 30.0]
    assert telecom_bench.p10 == 12.0  # 10th percentile (interpolated)
    assert telecom_bench.p50 == 20.0  # 50th percentile (median)
    assert telecom_bench.p90 == 28.0  # 90th percentile (interpolated)
    assert telecom_bench.last_seen == date(2024, 1, 3)
    assert len(telecom_bench.sources) == 3


def test_build_price_bench_empty():
    """Test building benchmark with empty evidence."""
    bench = build_price_bench([])
    assert len(bench) == 0


def test_build_price_bench_single():
    """Test building benchmark with single evidence."""
    evidence = [create_test_evidence()[0]]
    bench = build_price_bench(evidence)
    
    assert len(bench) == 1
    row = bench[0]
    assert row.n == 1
    assert row.p10 == row.p50 == row.p90 == 10.0


def test_get_benchmark_for_spec():
    """Test getting benchmark for specific specification."""
    evidence = create_test_evidence()
    bench = build_price_bench(evidence)
    
    # Test exact match
    result = get_benchmark_for_spec(
        bench, DataType.TELECOM_PROFILE, ListingType.RETAIL_LOOKUP, "US"
    )
    assert result is not None
    assert result.data_type == DataType.TELECOM_PROFILE
    
    # Test no match
    result = get_benchmark_for_spec(
        bench, DataType.CREDIT_CARD, ListingType.RETAIL_LOOKUP, "US"
    )
    assert result is None
    
    # Test with None region - should not find exact match, but could find ANY region
    result = get_benchmark_for_spec(
        bench, DataType.TELECOM_PROFILE, ListingType.RETAIL_LOOKUP, None
    )
    # This should not find a match since we don't have ANY region data for telecom_profile
    assert result is None


def test_currency_conversion():
    """Test that currency conversion is applied."""
    evidence = [
        PriceEvidence(
            source_id="source1",
            data_type=DataType.CONTACT,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="US",
            price_value=10.0,
            currency=Currency.EUR,  # EUR price
            units="per_record",
            published_date=date(2024, 1, 1)
        ),
    ]
    
    bench = build_price_bench(evidence)
    assert len(bench) == 1
    
    # The price should be converted to USD (EUR rate ~0.91 in 2024)
    row = bench[0]
    assert row.p50 > 10.0  # Should be higher due to EUR->USD conversion


def test_region_grouping():
    """Test that different regions are grouped separately."""
    evidence = [
        PriceEvidence(
            source_id="source1",
            data_type=DataType.CONTACT,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="US",
            price_value=10.0,
            currency=Currency.USD,
            units="per_record"
        ),
        PriceEvidence(
            source_id="source2",
            data_type=DataType.CONTACT,
            listing_type=ListingType.RETAIL_LOOKUP,
            region="CN",
            price_value=20.0,
            currency=Currency.USD,
            units="per_record"
        ),
    ]
    
    bench = build_price_bench(evidence)
    assert len(bench) == 2  # Should be separate rows for US and CN
    
    # Check that regions are preserved
    regions = {row.region for row in bench}
    assert "US" in regions
    assert "CN" in regions
