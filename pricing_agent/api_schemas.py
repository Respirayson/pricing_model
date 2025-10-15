from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from .schemas import DataType


class APIParameter(BaseModel):
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    required: bool = Field(default=False, description="Whether parameter is required")
    description: Optional[str] = Field(default=None, description="Parameter description")


class APIField(BaseModel):
    name: str = Field(description="Field name")
    type: str = Field(description="Field type")
    description: Optional[str] = Field(default=None, description="Field description")
    is_array: bool = Field(default=False, description="Whether field is an array")


class APIDefinition(BaseModel):
    api_id: str = Field(description="Unique identifier for the API")
    name: str = Field(description="Human-readable API name")
    description: Optional[str] = Field(default=None, description="API description")
    
    # Input/Output structure
    input_params: List[APIParameter] = Field(default_factory=list, description="Input parameters")
    output_fields: List[APIField] = Field(default_factory=list, description="Output fields")
    
    # Metadata
    category: Optional[str] = Field(default=None, description="API category (e.g., customer, document, telecom)")
    region: Optional[str] = Field(default="ANY", description="Geographic region")
    
    # Original source
    raw_definition: Optional[str] = Field(default=None, description="Raw API definition text")


class APIPricingResult(BaseModel):
    api_id: str = Field(description="API identifier")
    api_name: str = Field(description="API name")
    
    # Pricing
    estimated_revenue_per_call: float = Field(description="Estimated revenue per API call in USD")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the estimate")
    
    # Analysis
    data_types_exposed: List[DataType] = Field(description="Types of personal data exposed by this API")
    sensitivity_level: str = Field(description="Overall data sensitivity (low/medium/high/critical)")
    data_completeness: str = Field(description="How complete the exposed data is")
    
    # Market intelligence
    market_demand: str = Field(description="Estimated market demand for this data")
    use_cases: List[str] = Field(default_factory=list, description="Common use cases for this API data")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors affecting pricing")
    
    # Detailed reasoning
    reasoning: str = Field(description="Detailed explanation of pricing decision")
    key_value_drivers: List[str] = Field(default_factory=list, description="Key factors driving the value")
    
    # Price range
    min_revenue_per_call: Optional[float] = Field(default=None, description="Minimum expected revenue")
    max_revenue_per_call: Optional[float] = Field(default=None, description="Maximum expected revenue")
    
    # Comparison data (can be strings or full benchmark objects)
    comparable_data_items: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="Comparable benchmark data items")


class APIBatchPricingResult(BaseModel):
    total_apis: int = Field(description="Total number of APIs analyzed")
    results: List[APIPricingResult] = Field(description="Individual API pricing results")
    
    # Summary statistics
    total_potential_revenue: float = Field(description="Total potential revenue across all APIs")
    average_revenue_per_call: float = Field(description="Average revenue per API call")
    highest_value_api: Optional[str] = Field(default=None, description="API with highest revenue potential")
    lowest_value_api: Optional[str] = Field(default=None, description="API with lowest revenue potential")
    
    # Category breakdown
    revenue_by_category: Dict[str, float] = Field(default_factory=dict, description="Revenue grouped by API category")
    revenue_by_sensitivity: Dict[str, float] = Field(default_factory=dict, description="Revenue grouped by sensitivity level")

