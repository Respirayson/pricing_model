"""Pydantic schemas for pricing agent data models."""

from datetime import date
from enum import Enum
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ListingType(str, Enum):
    """Types of data listings."""
    RETAIL_LOOKUP = "retail_lookup"
    BULK_DUMP = "bulk_dump"
    ACCOUNT_ACCESS = "account_access"
    DOCUMENT_SCAN = "document_scan"


class DataType(str, Enum):
    """Types of data being sold."""
    CONTACT = "contact"
    PII_CORE = "pii_core"
    FULLZ = "fullz"
    CREDIT_CARD = "credit_card"
    BANK_LOGIN = "bank_login"
    GOV_ID_SCAN = "gov_id_scan"
    MEDICAL_RECORD = "medical_record"
    CONSUMER_ACCOUNT = "consumer_account"
    CORPORATE_ACCESS = "corporate_access"
    TELECOM_SUBSCRIPTION = "telecom_subscription"
    TELECOM_PROFILE = "telecom_profile"
    OTHER = "other"


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    CNY = "CNY"
    GBP = "GBP"


class PriceEvidence(BaseModel):
    """Evidence of a price found in a document."""
    
    # Source information
    source_id: str = Field(description="Unique identifier for the source document")
    source_url: Optional[HttpUrl] = Field(default=None, description="URL of the source document")
    source_title: Optional[str] = Field(default=None, description="Title of the source document")
    published_date: Optional[date] = Field(default=None, description="Publication date of the source")
    
    # Data classification
    data_type: DataType = Field(description="Type of data being priced")
    listing_type: ListingType = Field(description="Type of listing")
    region: Optional[str] = Field(default=None, description="Geographic region (e.g., 'US', 'CN', 'EU')")
    
    # Item details
    item_desc: Optional[str] = Field(default=None, description="Description of the item")
    price_value: float = Field(description="Price value")
    currency: Currency = Field(description="Currency of the price")
    units: Literal["per_record", "per_account", "per_dataset"] = Field(description="Pricing units")
    
    # Quality and packaging
    quality_notes: Optional[str] = Field(default=None, description="Notes about data quality")
    packaging: Optional[str] = Field(default=None, description="How the data is packaged")
    
    # Price range (for bulk listings)
    sample_size: Optional[int] = Field(default=None, description="Number of records in sample")
    price_low: Optional[float] = Field(default=None, description="Lowest price in range")
    price_high: Optional[float] = Field(default=None, description="Highest price in range")
    
    # Provenance
    snippet: Optional[str] = Field(default=None, description="Text snippet containing the price")
    snippet_offsets: Optional[List[int]] = Field(default=None, description="Character offsets of snippet in source")
    
    # Extraction metadata
    extractor_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence in extraction")


class PriceBenchRow(BaseModel):
    """Aggregated pricing benchmark for a specific data type and listing type."""
    
    data_type: DataType = Field(description="Type of data")
    listing_type: ListingType = Field(description="Type of listing")
    region: Optional[str] = Field(default=None, description="Geographic region")
    
    # Statistics
    n: int = Field(description="Number of price points")
    p10: float = Field(description="10th percentile price")
    p50: float = Field(description="50th percentile (median) price")
    p90: float = Field(description="90th percentile price")
    
    # Metadata
    last_seen: Optional[date] = Field(default=None, description="Most recent price observation")
    sources: List[str] = Field(default_factory=list, description="Source document IDs")


class ItemSpec(BaseModel):
    """Specification for pricing estimation."""
    
    data_type: DataType = Field(description="Primary data type")
    region: Optional[str] = Field(default=None, description="Geographic region")
    components: List[DataType] = Field(default_factory=list, description="Additional data components")
    listing_type: ListingType = Field(default=ListingType.RETAIL_LOOKUP, description="Listing type")
    features: Dict[str, Any] = Field(default_factory=dict, description="Feature modifiers")


class EstimationResult(BaseModel):
    """Result of price estimation."""
    
    base_sum: float = Field(description="Sum of base component prices")
    est_price: float = Field(description="Final estimated price")
    modifiers_applied: Dict[str, float] = Field(description="Modifier factors applied")
    components_used: List[DataType] = Field(description="Data types used in estimation")
    confidence: float = Field(description="Confidence in the estimate")


class ContentPriceEstimate(BaseModel):
    """Price estimate for content-based API query valuation."""
    
    estimate_id: str = Field(description="Unique identifier for this estimate")
    query_id: str = Field(description="References input query_id")
    estimated_at: str = Field(description="ISO 8601 timestamp of estimation")
    model_version: str = Field(description="Pricing model version", default="log-linear-v1.0")
    
    # Price estimate
    price_point_usd: float = Field(description="Point estimate in USD")
    price_low_usd: float = Field(description="Lower bound of 95% CI")
    price_high_usd: float = Field(description="Upper bound of 95% CI")
    confidence: float = Field(description="Model confidence (0-1)", ge=0.0, le=1.0)
    
    # Variable scores (LLM-inferred)
    variable_scores: Dict[str, Dict[str, Any]] = Field(description="LLM-inferred content variable scores")
    
    # Anchors and validation
    anchors_used: List[Dict[str, Any]] = Field(default_factory=list, description="Market anchors used")
    flags: List[str] = Field(default_factory=list, description="Warnings/alerts")
    
    # Inferred metadata
    data_type: str = Field(description="Inferred data type")
    region: str = Field(description="Inferred or provided region")
    
    # Provenance
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Model execution metadata")


class VoIPriceEstimate(BaseModel):
    """
    Bayesian Value-of-Information price estimate.
    
    Based on Bergemann, Bonatti & Smolin (2018), "The Design and Price of Information",
    American Economic Review 108(1): 1-48.
    """
    
    estimate_id: str = Field(description="Unique identifier for this estimate")
    query_id: str = Field(description="References input query_id")
    estimated_at: str = Field(description="ISO 8601 timestamp of estimation")
    model_version: str = Field(description="VoI model version", default="voi-bergemann-v1.0")
    
    # Core VoI results
    V_ex_ante: float = Field(description="Value of information in utility units", ge=0.0)
    USD_estimate: float = Field(description="Normalized USD price estimate", ge=0.0)
    price_low_usd: float = Field(description="Lower bound of 95% CI", ge=0.0)
    price_high_usd: float = Field(description="Upper bound of 95% CI", ge=0.0)
    confidence: float = Field(description="Model confidence (0-1)", ge=0.0, le=1.0)
    
    # Posterior parameters (action-conditional)
    posteriors: Dict[str, Dict[str, float]] = Field(
        description="Posterior parameters for each attacker action (P_success, R_expected, C_cost, detection_risk)"
    )
    
    # Decision analysis
    optimal_action_prior: str = Field(description="Optimal action without information signal")
    optimal_action_posterior: str = Field(description="Optimal action with information signal")
    
    # Supporting data
    anchors_used: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Market anchor prices used for USD normalization"
    )
    simulation_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Monte Carlo simulation statistics"
    )
    flags: List[str] = Field(default_factory=list, description="Warnings/alerts")
    
    # Metadata
    data_type: str = Field(description="Data type classification")
    region: str = Field(description="Geographic region")
    freshness_days: float = Field(description="Data age in days", ge=0.0)
    freshness_factor: float = Field(description="Exponential freshness decay factor", ge=0.0, le=1.0)
    
    # Provenance
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Model execution metadata and theoretical references"
    )