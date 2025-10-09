"""LLM-based pricing agent for comprehensive price determination."""

import json
from typing import Dict, Any, Optional, List
from ..extract.llm_client import LLMClient
from ..schemas import ItemSpec, DataType, ListingType, PriceEvidence


class LLMPricingAgent:
    """LLM-based agent that determines exact prices for data items."""
    
    def __init__(self, llm_client: LLMClient, benchmark_data: List[Dict[str, Any]]):
        """
        Initialize LLM pricing agent.
        
        Args:
            llm_client: LLM client for price determination
            benchmark_data: Historical benchmark data for context
        """
        self.llm_client = llm_client
        self.benchmark_data = benchmark_data
    
    def determine_price(self, item_spec: ItemSpec, market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use LLM to determine exact price for a given data item.
        
        Args:
            item_spec: Specification of the data item to price
            market_context: Additional market context (optional)
            
        Returns:
            Dictionary with price determination and reasoning
        """
        relevant_benchmarks = self._get_relevant_benchmarks(item_spec)
        
        prompt = self._build_pricing_prompt(item_spec, relevant_benchmarks, market_context)
        
        result = self.llm_client.json_extract(
            system_prompt=self._get_pricing_system_prompt(),
            user_prompt=prompt,
            schema=self._get_pricing_schema()
        )
        
        if not result or not isinstance(result, dict):
            raise Exception("LLM returned invalid result")
        
        if not result.get("determined_price") or not result.get("confidence"):
            raise Exception("LLM returned invalid result")
        return result
    
    
    def _get_relevant_benchmarks(self, item_spec: ItemSpec) -> List[Dict[str, Any]]:
        """Get relevant benchmark data for the item specification."""
        relevant = []
        
        for benchmark in self.benchmark_data:
            # Match by data type
            if benchmark.get('data_type') == item_spec.data_type.value:
                relevant.append(benchmark)
            # Match by listing type
            elif benchmark.get('listing_type') == item_spec.listing_type.value:
                relevant.append(benchmark)
            # Match by region
            elif benchmark.get('region') == item_spec.region:
                relevant.append(benchmark)
        
        return relevant[:10]  # Limit to top 10 most relevant
    
    def _build_pricing_prompt(self, item_spec: ItemSpec, benchmarks: List[Dict[str, Any]], 
                            market_context: Optional[Dict[str, Any]]) -> str:
        """Build comprehensive pricing prompt."""
        
        prompt = f"""Determine the exact market price for the following data item:

ITEM SPECIFICATION:
- Data Type: {item_spec.data_type.value}
- Listing Type: {item_spec.listing_type.value}
- Region: {item_spec.region}
- Features: {json.dumps(item_spec.features, indent=2)}

RELEVANT HISTORICAL DATA:
{json.dumps(benchmarks, indent=2)}

MARKET CONTEXT:
{json.dumps(market_context or {}, indent=2)}

Please analyze the item specification, consider the historical pricing data, and determine the most accurate market price. Consider factors like:
- Data quality and completeness
- Market demand and supply
- Seller reputation and trust
- Data freshness and exclusivity
- Regional variations
- Current market trends

RESPOND WITH ONLY A JSON OBJECT containing your price determination. The JSON must include:
- determined_price: the exact price as a number
- confidence: confidence level (0.0 to 1.0)
- reasoning: detailed explanation as a string
- key_factors: array of key factors that influenced pricing
- price_range: object with min_price and max_price
- market_conditions: object with demand_level, supply_level, market_trend
- quality_assessment: object with data_quality, completeness, freshness, exclusivity
- comparison_to_benchmarks: object with vs_median, vs_p10, vs_p90, percentile_rank

Do not include any text outside the JSON object."""
        
        return prompt
    
    def _get_pricing_system_prompt(self) -> str:
        """Get system prompt for pricing agent."""
        return """You are an expert dark web market analyst specializing in data pricing. Your task is to determine the most accurate market price for data items based on:

1. Historical pricing data and benchmarks
2. Current market conditions and trends
3. Data quality and characteristics
4. Seller reputation and trust factors
5. Regional and temporal variations

You have deep knowledge of:
- Dark web market dynamics
- Data valuation principles
- Price elasticity and demand factors
- Quality assessment metrics
- Market psychology and behavior

IMPORTANT: You must respond with ONLY a valid JSON object that matches the required schema. Do not include any explanatory text, markdown formatting, or additional commentary outside the JSON. Your response should start with { and end with }.

Provide accurate, well-reasoned price determinations that reflect real market conditions. Consider both quantitative factors (historical prices, quality metrics) and qualitative factors (market sentiment, exclusivity, trust)."""
    
    def _get_pricing_schema(self) -> Dict[str, Any]:
        """Get JSON schema for pricing response."""
        return {
            "type": "object",
            "properties": {
                "determined_price": {
                    "type": "number",
                    "description": "The exact market price determined for the item"
                },
                "price_range": {
                    "type": "object",
                    "properties": {
                        "min_price": {"type": "number"},
                        "max_price": {"type": "number"}
                    },
                    "description": "Confidence range for the price"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence in the price determination (0-1)"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed reasoning for the price determination"
                },
                "key_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key factors that influenced the pricing decision"
                },
                "market_conditions": {
                    "type": "object",
                    "properties": {
                        "demand_level": {"type": "string"},
                        "supply_level": {"type": "string"},
                        "market_trend": {"type": "string"}
                    },
                    "description": "Current market conditions assessment"
                },
                "quality_assessment": {
                    "type": "object",
                    "properties": {
                        "data_quality": {"type": "string"},
                        "completeness": {"type": "string"},
                        "freshness": {"type": "string"},
                        "exclusivity": {"type": "string"}
                    },
                    "description": "Assessment of data quality factors"
                },
                "comparison_to_benchmarks": {
                    "type": "object",
                    "properties": {
                        "vs_median": {"type": "number"},
                        "vs_p10": {"type": "number"},
                        "vs_p90": {"type": "number"},
                        "percentile_rank": {"type": "number"}
                    },
                    "description": "Comparison to historical benchmark data"
                }
            },
            "required": ["determined_price", "confidence", "reasoning", "key_factors"]
        }


class HybridPricingAgent:
    """Hybrid agent combining rule-based and LLM-based pricing."""
    
    def __init__(self, rule_estimator, llm_agent: LLMPricingAgent):
        """
        Initialize hybrid pricing agent.
        
        Args:
            rule_estimator: Rule-based price estimator
            llm_agent: LLM-based pricing agent
        """
        self.rule_estimator = rule_estimator
        self.llm_agent = llm_agent
    
    def estimate_price(self, item_spec: ItemSpec, use_llm: bool = True, 
                      market_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Estimate price using hybrid approach.
        
        Args:
            item_spec: Item specification
            use_llm: Whether to use LLM agent (default: True)
            market_context: Additional market context
            
        Returns:
            Comprehensive pricing result
        """
        # Get rule-based estimate
        rule_result = self.rule_estimator.estimate(item_spec)
        
        result = {
            "rule_based_price": rule_result.est_price,
            "rule_based_confidence": rule_result.confidence,
            "rule_based_modifiers": rule_result.modifiers_applied,
            "components_used": [dt.value for dt in rule_result.components_used]
        }
        
        if use_llm:
            # Get LLM-based estimate
            llm_result = self.llm_agent.determine_price(item_spec, market_context)
            
            llm_price = llm_result.get("determined_price")
            llm_confidence = llm_result.get("confidence", 0.0)
            
            result.update({
                "llm_determined_price": llm_price,
                "llm_confidence": llm_confidence,
                "llm_reasoning": llm_result.get("reasoning"),
                "llm_key_factors": llm_result.get("key_factors", []),
                "price_range": llm_result.get("price_range"),
                "market_conditions": llm_result.get("market_conditions"),
                "quality_assessment": llm_result.get("quality_assessment"),
                "comparison_to_benchmarks": llm_result.get("comparison_to_benchmarks")
            })
            
            # Calculate hybrid price (weighted average)
            if llm_price is not None and llm_confidence > 0.1:
                # Use LLM result if it's valid and has some confidence
                rule_weight = 0.3
                llm_weight = 0.7
                hybrid_price = (rule_result.est_price * rule_weight + llm_price * llm_weight)
                result["pricing_method"] = "hybrid"
            else:
                hybrid_price = rule_result.est_price
                result["pricing_method"] = "rule_based_fallback"
            
            result["hybrid_price"] = hybrid_price
        else:
            result["pricing_method"] = "rule_based"
        
        return result
