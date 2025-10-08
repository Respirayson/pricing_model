"""Tests for Pydantic schemas."""

import pytest
from datetime import date
from pricing_agent.schemas import (
    PriceEvidence, PriceBenchRow, ItemSpec, EstimationResult,
    DataType, ListingType, Currency
)


def test_price_evidence_creation():
    """Test creating PriceEvidence objects."""
    evidence = PriceEvidence(
        source_id="test_source",
        data_type=DataType.TELECOM_PROFILE,
        listing_type=ListingType.RETAIL_LOOKUP,
        price_value=25.0,
        currency=Currency.USD,
        units="per_record"
    )
    
    assert evidence.source_id == "test_source"
    assert evidence.data_type == DataType.TELECOM_PROFILE
    assert evidence.price_value == 25.0
    assert evidence.currency == Currency.USD


def test_price_evidence_validation():
    """Test PriceEvidence validation."""
    # Test valid evidence
    evidence = PriceEvidence(
        source_id="test",
        data_type=DataType.CONTACT,
        listing_type=ListingType.BULK_DUMP,
        price_value=10.0,
        currency=Currency.EUR,
        units="per_record"
    )
    assert evidence.price_value == 10.0
    
    # Test confidence bounds
    evidence = PriceEvidence(
        source_id="test",
        data_type=DataType.CONTACT,
        listing_type=ListingType.BULK_DUMP,
        price_value=10.0,
        currency=Currency.USD,
        units="per_record",
        extractor_confidence=0.5
    )
    assert evidence.extractor_confidence == 0.5


def test_price_bench_row_creation():
    """Test creating PriceBenchRow objects."""
    bench_row = PriceBenchRow(
        data_type=DataType.CREDIT_CARD,
        listing_type=ListingType.RETAIL_LOOKUP,
        region="US",
        n=100,
        p10=5.0,
        p50=10.0,
        p90=20.0,
        last_seen=date(2024, 1, 1),
        sources=["source1", "source2"]
    )
    
    assert bench_row.data_type == DataType.CREDIT_CARD
    assert bench_row.n == 100
    assert bench_row.p50 == 10.0


def test_item_spec_creation():
    """Test creating ItemSpec objects."""
    spec = ItemSpec(
        data_type=DataType.TELECOM_PROFILE,
        region="CN",
        components=[DataType.CONTACT, DataType.PII_CORE],
        listing_type=ListingType.RETAIL_LOOKUP,
        features={
            "freshness_days": 30,
            "completeness": "full"
        }
    )
    
    assert spec.data_type == DataType.TELECOM_PROFILE
    assert spec.region == "CN"
    assert len(spec.components) == 2
    assert spec.features["freshness_days"] == 30


def test_estimation_result_creation():
    """Test creating EstimationResult objects."""
    result = EstimationResult(
        base_sum=50.0,
        est_price=75.0,
        modifiers_applied={"freshness": 1.0, "completeness": 1.2},
        components_used=[DataType.TELECOM_PROFILE],
        confidence=0.8
    )
    
    assert result.base_sum == 50.0
    assert result.est_price == 75.0
    assert result.confidence == 0.8


def test_enum_values():
    """Test enum values are correct."""
    assert DataType.TELECOM_PROFILE.value == "telecom_profile"
    assert ListingType.RETAIL_LOOKUP.value == "retail_lookup"
    assert Currency.USD.value == "USD"


def test_schema_serialization():
    """Test schema serialization to dict."""
    evidence = PriceEvidence(
        source_id="test",
        data_type=DataType.CONTACT,
        listing_type=ListingType.BULK_DUMP,
        price_value=15.0,
        currency=Currency.USD,
        units="per_record"
    )
    
    data = evidence.model_dump()
    assert isinstance(data, dict)
    assert data["source_id"] == "test"
    assert data["price_value"] == 15.0
    
    # Test round-trip
    evidence2 = PriceEvidence.model_validate(data)
    assert evidence2.source_id == evidence.source_id
    assert evidence2.price_value == evidence.price_value
