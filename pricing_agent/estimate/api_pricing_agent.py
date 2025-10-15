import json
from typing import Dict, Any, Optional, List
from ..extract.llm_client import LLMClient
from ..api_schemas import APIDefinition, APIPricingResult, APIBatchPricingResult
from ..schemas import DataType


class APIPricingAgent:
    """Estimates potential revenue per API call using LLM analysis."""
    
    def __init__(self, llm_client: LLMClient, benchmark_data: Optional[List[Dict[str, Any]]] = None):
        self.llm_client = llm_client
        self.benchmark_data = benchmark_data or []
    
    def estimate_api_revenue(self, api_def: APIDefinition, market_context: Optional[Dict[str, Any]] = None) -> APIPricingResult:
        prompt = self._build_api_pricing_prompt(api_def, market_context)
        result = self.llm_client.json_extract(
            system_prompt=self._get_system_prompt(),
            user_prompt=prompt,
            schema=self._get_pricing_schema()
        )
        
        if not result or not isinstance(result, dict):
            raise Exception("LLM returned invalid result")
        
        return self._convert_to_pricing_result(api_def, result)
    
    def batch_estimate(self, api_definitions: List[APIDefinition], 
                      market_context: Optional[Dict[str, Any]] = None) -> APIBatchPricingResult:
        results = []
        for api_def in api_definitions:
            try:
                result = self.estimate_api_revenue(api_def, market_context)
                results.append(result)
            except Exception as e:
                print(f"Error pricing API {api_def.api_id}: {e}")
                results.append(APIPricingResult(
                    api_id=api_def.api_id,
                    api_name=api_def.name,
                    estimated_revenue_per_call=0.0,
                    confidence=0.0,
                    data_types_exposed=[],
                    sensitivity_level="unknown",
                    data_completeness="unknown",
                    market_demand="unknown",
                    reasoning=f"Failed to analyze: {str(e)}"
                ))
        return self._calculate_batch_summary(results)
    
    def _build_api_pricing_prompt(self, api_def: APIDefinition, market_context: Optional[Dict[str, Any]]) -> str:
        input_params_str = "\n".join([
            f"  - {p.name} ({p.type}){' [required]' if p.required else ' [optional]'}: {p.description or 'N/A'}"
            for p in api_def.input_params
        ])
        
        output_fields_str = "\n".join([
            f"  - {f.name} ({f.type}){'[]' if f.is_array else ''}: {f.description or 'N/A'}"
            for f in api_def.output_fields
        ])
        
        benchmark_context = ""
        if self.benchmark_data:
            benchmark_context = f"\n\nHISTORICAL PERSONAL DATA PRICING (for reference):\n{json.dumps(self.benchmark_data[:10], indent=2)}"
        
        prompt = f"""Analyze this API and estimate the potential revenue that could be earned per API call.

API SPECIFICATION:
==================
API ID: {api_def.api_id}
API Name: {api_def.name}
Description: {api_def.description or 'N/A'}
Category: {api_def.category or 'N/A'}
Region: {api_def.region}

INPUT PARAMETERS:
{input_params_str or '  (none)'}

OUTPUT FIELDS:
{output_fields_str or '  (none)'}

{benchmark_context}

MARKET CONTEXT:
{json.dumps(market_context or {}, indent=2)}

ANALYSIS TASK:
==============
You are a data monetization expert analyzing API endpoints to estimate their revenue potential. 

Consider the following factors:

1. **Data Exposure Analysis**:
   - What types of personal/sensitive data does this API expose?
   - How complete is the data returned (partial vs. full profiles)?
   - What data types from the benchmark are most similar?

2. **Market Value Assessment**:
   - How valuable is this data to potential buyers (marketers, fraudsters, competitors)?
   - What legitimate or illegitimate use cases exist?
   - How does this compare to known pricing for similar data?

3. **Risk & Sensitivity**:
   - What is the sensitivity level of exposed data?
   - What are the legal/ethical risks of monetizing this data?
   - How identifiable is the information?

4. **Market Demand**:
   - What is the typical market demand for this type of data?
   - Are there specific industries that would pay for this?
   - Is this a high-frequency or low-frequency use case?

5. **Revenue Estimation**:
   - Based on the above factors, estimate the revenue per API call
   - Consider both legitimate monetization (data partnerships) and illicit markets
   - Use benchmark data as reference points where applicable

Provide your analysis as a structured JSON response with:
- estimated_revenue_per_call: Your estimated revenue in USD per call
- confidence: Your confidence level (0.0 to 1.0)
- data_types_exposed: List of data types exposed (use standard types: contact, pii_core, fullz, credit_card, bank_login, gov_id_scan, medical_record, consumer_account, corporate_access, telecom_subscription, telecom_profile, other)
- sensitivity_level: Overall sensitivity (low/medium/high/critical)
- data_completeness: Completeness level (minimal/partial/standard/comprehensive)
- market_demand: Demand level (low/moderate/high/very_high)
- use_cases: List of potential use cases for this data
- risk_factors: List of risk factors affecting pricing
- reasoning: Detailed explanation of your analysis
- key_value_drivers: List of key factors driving the value
- min_revenue_per_call: Minimum expected revenue (optional)
- max_revenue_per_call: Maximum expected revenue (optional)
- comparable_data_items: List of comparable data items from benchmark (optional)

IMPORTANT: Your response must be ONLY valid JSON, no additional text."""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        return """You are a data monetization expert analyzing API endpoints to estimate revenue potential per call.

Analyze APIs based on:
- Data types exposed and their market values
- Data sensitivity and completeness
- Market demand and use cases
- Real-world pricing benchmarks when available

Respond with ONLY valid JSON. No markdown, no extra text. Start with { and end with }."""
    
    def _get_pricing_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "estimated_revenue_per_call": {
                    "type": "number",
                    "description": "Estimated revenue per API call in USD"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence in the estimate"
                },
                "data_types_exposed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of personal data exposed"
                },
                "sensitivity_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Overall data sensitivity"
                },
                "data_completeness": {
                    "type": "string",
                    "enum": ["minimal", "partial", "standard", "comprehensive"],
                    "description": "How complete the exposed data is"
                },
                "market_demand": {
                    "type": "string",
                    "enum": ["low", "moderate", "high", "very_high"],
                    "description": "Market demand for this data"
                },
                "use_cases": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Potential use cases for this data"
                },
                "risk_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Risk factors affecting pricing"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Detailed explanation of pricing decision"
                },
                "key_value_drivers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key factors driving the value"
                },
                "min_revenue_per_call": {
                    "type": "number",
                    "description": "Minimum expected revenue"
                },
                "max_revenue_per_call": {
                    "type": "number",
                    "description": "Maximum expected revenue"
                },
                "comparable_data_items": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "object",
                                "properties": {
                                    "data_type": {"type": "string"},
                                    "listing_type": {"type": "string"},
                                    "region": {"type": "string"},
                                    "p50": {"type": "number"},
                                    "p10": {"type": "number"},
                                    "p90": {"type": "number"}
                                }
                            }
                        ]
                    },
                    "description": "Comparable benchmark data items (can be data type names or full benchmark objects)"
                }
            },
            "required": [
                "estimated_revenue_per_call",
                "confidence",
                "data_types_exposed",
                "sensitivity_level",
                "data_completeness",
                "market_demand",
                "reasoning"
            ]
        }
    
    def _convert_to_pricing_result(self, api_def: APIDefinition, llm_result: Dict[str, Any]) -> APIPricingResult:
        data_types_exposed = []
        for dt_str in llm_result.get("data_types_exposed", []):
            try:
                # exact match first
                data_types_exposed.append(DataType(dt_str.lower()))
            except ValueError:
                # map to closest match
                dt_str_lower = dt_str.lower()
                if "contact" in dt_str_lower:
                    data_types_exposed.append(DataType.CONTACT)
                elif "pii" in dt_str_lower or "personal" in dt_str_lower:
                    data_types_exposed.append(DataType.PII_CORE)
                elif "telecom" in dt_str_lower:
                    data_types_exposed.append(DataType.TELECOM_PROFILE)
                elif "credit" in dt_str_lower or "card" in dt_str_lower:
                    data_types_exposed.append(DataType.CREDIT_CARD)
                elif "bank" in dt_str_lower:
                    data_types_exposed.append(DataType.BANK_LOGIN)
                elif "id" in dt_str_lower or "document" in dt_str_lower:
                    data_types_exposed.append(DataType.GOV_ID_SCAN)
                else:
                    data_types_exposed.append(DataType.OTHER)
        
        return APIPricingResult(
            api_id=api_def.api_id,
            api_name=api_def.name,
            estimated_revenue_per_call=llm_result.get("estimated_revenue_per_call", 0.0),
            confidence=llm_result.get("confidence", 0.0),
            data_types_exposed=data_types_exposed,
            sensitivity_level=llm_result.get("sensitivity_level", "unknown"),
            data_completeness=llm_result.get("data_completeness", "unknown"),
            market_demand=llm_result.get("market_demand", "unknown"),
            use_cases=llm_result.get("use_cases", []),
            risk_factors=llm_result.get("risk_factors", []),
            reasoning=llm_result.get("reasoning", ""),
            key_value_drivers=llm_result.get("key_value_drivers", []),
            min_revenue_per_call=llm_result.get("min_revenue_per_call"),
            max_revenue_per_call=llm_result.get("max_revenue_per_call"),
            comparable_data_items=llm_result.get("comparable_data_items", [])
        )
    
    def _calculate_batch_summary(self, results: List[APIPricingResult]) -> APIBatchPricingResult:
        if not results:
            return APIBatchPricingResult(
                total_apis=0,
                results=[],
                total_potential_revenue=0.0,
                average_revenue_per_call=0.0
            )
        
        total_revenue = sum(r.estimated_revenue_per_call for r in results)
        avg_revenue = total_revenue / len(results)
        highest = max(results, key=lambda r: r.estimated_revenue_per_call)
        lowest = min(results, key=lambda r: r.estimated_revenue_per_call)
        
        revenue_by_sensitivity: Dict[str, float] = {}
        for result in results:
            sensitivity = result.sensitivity_level
            revenue_by_sensitivity[sensitivity] = revenue_by_sensitivity.get(sensitivity, 0.0) + result.estimated_revenue_per_call
        
        return APIBatchPricingResult(
            total_apis=len(results),
            results=results,
            total_potential_revenue=total_revenue,
            average_revenue_per_call=avg_revenue,
            highest_value_api=f"{highest.api_name} (${highest.estimated_revenue_per_call:.2f})",
            lowest_value_api=f"{lowest.api_name} (${lowest.estimated_revenue_per_call:.2f})",
            revenue_by_category={},  # Could be populated if APIs have categories
            revenue_by_sensitivity=revenue_by_sensitivity
        )

