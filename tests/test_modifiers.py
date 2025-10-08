"""Tests for price modifiers."""

import pytest
from pricing_agent.aggregate.modifiers import (
    freshness_factor, completeness_factor, exclusivity_factor,
    packaging_factor, reputation_factor, demand_factor, apply_all_modifiers
)


def test_freshness_factor():
    """Test freshness factor calculations."""
    assert freshness_factor(10) == 1.0  # < 30 days
    assert freshness_factor(30) == 1.0  # exactly 30 days
    assert freshness_factor(100) == 0.5  # 1-6 months
    assert freshness_factor(200) == 0.2  # > 6 months


def test_completeness_factor():
    """Test completeness factor calculations."""
    assert completeness_factor("fragment") == 0.4
    assert completeness_factor("standard") == 1.0
    assert completeness_factor("full") == 1.2
    assert completeness_factor("unknown") == 1.0  # default


def test_exclusivity_factor():
    """Test exclusivity factor calculations."""
    assert exclusivity_factor("widely_leaked") == 0.5
    assert exclusivity_factor("limited") == 1.0
    assert exclusivity_factor("single_seller") == 1.5
    assert exclusivity_factor("unknown") == 1.0  # default


def test_packaging_factor():
    """Test packaging factor calculations."""
    assert packaging_factor("retail_lookup") == 1.5
    assert packaging_factor("bulk_dump") == 0.3
    assert packaging_factor("account_access") == 1.0
    assert packaging_factor("document_scan") == 1.2
    assert packaging_factor("unknown") == 1.0  # default


def test_reputation_factor():
    """Test reputation factor calculations."""
    assert reputation_factor("unknown") == 0.9
    assert reputation_factor("verified") == 1.0
    assert reputation_factor("escrow_guarantee") == 1.2
    assert reputation_factor("unknown_type") == 1.0  # default


def test_demand_factor():
    """Test demand factor calculations."""
    assert demand_factor("low") == 0.8
    assert demand_factor("normal") == 1.0
    assert demand_factor("high") == 1.1
    assert demand_factor("spike") == 1.3
    assert demand_factor("unknown") == 1.0  # default


def test_apply_all_modifiers():
    """Test applying all modifiers together."""
    features = {
        "freshness_days": 10,
        "completeness": "full",
        "exclusivity": "single_seller",
        "seller_reputation": "escrow_guarantee",
        "demand": "spike",
        "vip_add": 5.0
    }
    
    base_sum = 100.0
    result = apply_all_modifiers(base_sum, features, 5.0)
    
    # Calculate expected result
    expected = (base_sum * 
               1.0 *  # freshness (10 days)
               1.2 *  # completeness (full)
               1.5 *  # exclusivity (single_seller)
               1.2 *  # reputation (escrow_guarantee)
               1.3 +  # demand (spike)
               5.0)   # vip_add
    
    assert abs(result - expected) < 0.01


def test_apply_modifiers_minimal():
    """Test applying modifiers with minimal features."""
    features = {"freshness_days": 100}
    base_sum = 50.0
    
    result = apply_all_modifiers(base_sum, features, 0.0)
    expected = base_sum * 0.5  # freshness factor for 100 days
    
    assert abs(result - expected) < 0.01


def test_apply_modifiers_empty():
    """Test applying modifiers with empty features."""
    features = {}
    base_sum = 25.0
    
    result = apply_all_modifiers(base_sum, features, 0.0)
    assert result == base_sum  # No modifiers applied


def test_negative_price_protection():
    """Test that negative prices are prevented."""
    features = {
        "freshness_days": 1000,  # Very old
        "completeness": "fragment",
        "exclusivity": "widely_leaked",
        "demand": "low"
    }
    
    base_sum = 10.0
    result = apply_all_modifiers(base_sum, features, -100.0)  # Large negative VIP
    
    assert result >= 0.0  # Should not be negative
