"""Content-based pricing agent for telecom API queries."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..schemas import ContentPriceEstimate
from .llm_variable_scorer import LLMVariableScorer
from .pricing_formulas import LogLinearPricingModel, MultiplicativePricingModel


# Default model parameters (learned from calibration)
DEFAULT_MODEL_PARAMS = {
    "alpha": 3.12,
    "betas": {
        "target": 0.048,
        "sensitivity": 0.039,
        "completeness": 0.033,
        "freshness": 0.026,
        "rarity": 0.031,
        "exploitability": 0.044,
        "volume": 0.017,
        "packaging": 0.013,
        "seller_reputation": 0.019,
        "legal_risk": -0.018
    },
    "covariance": {
        "target": 0.002,
        "sensitivity": 0.0015,
        "completeness": 0.001,
        "freshness": 0.0008,
        "rarity": 0.001,
        "exploitability": 0.002,
        "volume": 0.0005,
        "packaging": 0.0003,
        "seller_reputation": 0.0006,
        "legal_risk": 0.0005
    }
}

# Default anchor prices by data type
DEFAULT_ANCHORS = [
    {
        "source": "SOCRadar 2024",
        "data_type": "location_query",
        "region": "US",
        "price_low_usd": 50,
        "price_high_usd": 200,
        "description": "Location query pricing range"
    },
    {
        "source": "DeepStrike 2025",
        "data_type": "telecom_profile",
        "region": "ANY",
        "price_low_usd": 10,
        "price_high_usd": 75,
        "description": "Telecom profile data"
    },
    {
        "source": "PrivacyAffairs 2023",
        "data_type": "account_access",
        "region": "ANY",
        "price_low_usd": 50,
        "price_high_usd": 150,
        "description": "Account access credentials"
    },
    {
        "source": "PrivacyAffairs 2023",
        "data_type": "call_detail_record",
        "region": "ANY",
        "price_low_usd": 30,
        "price_high_usd": 150,
        "description": "Call detail records"
    }
]


class ContentPricingAgent:
    """Main agent for content-based API query pricing."""
    
    def __init__(self, 
                 llm_client,
                 model_params: Optional[Dict] = None,
                 anchors: Optional[List[Dict]] = None):
        """
        Initialize content pricing agent.
        
        Args:
            llm_client: LLMClient instance
            model_params: Model parameters dict (uses defaults if None)
            anchors: List of price anchors (uses defaults if None)
        """
        self.scorer = LLMVariableScorer(llm_client)
        self.model_params = model_params or DEFAULT_MODEL_PARAMS
        self.log_linear_model = LogLinearPricingModel(self.model_params)
        self.anchors = anchors or DEFAULT_ANCHORS
        
        # Base anchors for multiplicative model
        base_anchors = {
            "location_query": 100.0,
            "telecom_profile": 40.0,
            "account_access": 80.0,
            "call_detail_record": 60.0,
            "billing_summary": 15.0,
            "subscriber_profile": 30.0
        }
        self.mult_model = MultiplicativePricingModel(base_anchors)
    
    def estimate_api_query_value(self, api_response: Dict[str, Any]) -> ContentPriceEstimate:
        """
        Main estimation pipeline.
        
        Args:
            api_response: API response dict with structure:
                {
                    "query_id": str,
                    "query_type": str,
                    "target_phone": str,
                    "timestamp": str (ISO 8601),
                    "payload": dict
                }
        
        Returns:
            ContentPriceEstimate with price and metadata
        """
        # Step 1: Score variables using LLM
        print("Scoring content variables...")
        variable_scores = self.scorer.score_api_response(api_response)
        
        # Step 2: Estimate price using log-linear model
        print("Computing price estimate...")
        price_point, price_low, price_high = self.log_linear_model.estimate_price(variable_scores)
        
        # Step 3: Infer data type and region
        data_type = self._infer_data_type(api_response)
        region = self._infer_region(api_response)
        
        # Step 4: Anchor cross-check and clipping
        price_point, price_low, price_high, anchors_used, flags = self._anchor_cross_check(
            price_point, price_low, price_high, data_type, region
        )
        
        # Step 5: Estimate confidence
        confidence = self._estimate_confidence(variable_scores, anchors_used, flags)
        
        # Step 6: Assemble output
        estimate = ContentPriceEstimate(
            estimate_id=str(uuid.uuid4()),
            query_id=api_response.get("query_id", "unknown"),
            estimated_at=datetime.utcnow().isoformat() + "Z",
            model_version="log-linear-v1.0",
            price_point_usd=round(price_point, 2),
            price_low_usd=round(price_low, 2),
            price_high_usd=round(price_high, 2),
            confidence=round(confidence, 2),
            variable_scores=variable_scores,
            anchors_used=anchors_used,
            flags=flags,
            data_type=data_type,
            region=region,
            provenance={
                "llm_model": "gpt-4.1-nano",
                "llm_temperature": 0.1,
                "regression_coefficients": self.model_params
            }
        )
        
        return estimate
    
    def _infer_data_type(self, api_response: Dict) -> str:
        """Infer data type from API response structure."""
        query_type = api_response.get("query_type", "")
        payload = api_response.get("payload", {})
        
        # Map query types to data types
        if query_type == "location_lookup" or "location" in payload:
            return "location_query"
        if query_type == "call_detail" or "call_logs" in payload or "call_history" in payload:
            return "call_detail_record"
        if query_type == "account_access" or "access_token" in payload or "account_access_token" in payload:
            return "account_access"
        if query_type == "billing_summary" or "billing_summary" in payload:
            return "billing_summary"
        if query_type == "subscriber_profile":
            return "subscriber_profile"
        
        # Default to telecom_profile
        return "telecom_profile"
    
    def _infer_region(self, api_response: Dict) -> str:
        """Extract region from phone number or location."""
        phone = api_response.get("target_phone", "")
        
        # Parse country code
        if phone.startswith("+1"):
            return "US"
        if phone.startswith("+86"):
            return "CN"
        if phone.startswith("+44"):
            return "UK"
        if phone.startswith("+33"):
            return "FR"
        if phone.startswith("+49"):
            return "DE"
        if phone.startswith("+91"):
            return "IN"
        if phone.startswith("+7"):
            return "RU"
        if phone.startswith("+81"):
            return "JP"
        if phone.startswith("+82"):
            return "KR"
        
        # Try to infer from payload
        payload = api_response.get("payload", {})
        if "country_code" in payload:
            return payload["country_code"]
        if "region" in payload:
            return payload["region"]
        
        return "ANY"
    
    def _anchor_cross_check(self, 
                           price_point: float,
                           price_low: float,
                           price_high: float,
                           data_type: str,
                           region: str) -> tuple:
        """
        Validate price against anchor bounds and clip if necessary.
        
        Returns:
            Tuple of (price_point, price_low, price_high, anchors_used, flags)
        """
        # Find relevant anchors
        relevant_anchors = [
            a for a in self.anchors
            if a["data_type"] == data_type and (a["region"] == region or a["region"] == "ANY")
        ]
        
        flags = []
        
        if not relevant_anchors:
            flags.append("no_anchors_found")
            return price_point, price_low, price_high, [], flags
        
        # Use the first matching anchor (or could average multiple)
        anchor = relevant_anchors[0]
        anchor_low = anchor["price_low_usd"]
        anchor_high = anchor["price_high_usd"]
        
        # Clip if outside reasonable bounds (allow 3x extrapolation)
        original_price = price_point
        
        if price_point < 0.3 * anchor_low:
            price_point = 0.5 * anchor_low
            flags.append("clipped_below_anchor")
        
        if price_point > 3 * anchor_high:
            price_point = 2 * anchor_high
            flags.append("clipped_above_anchor")
        
        # Adjust confidence bounds proportionally if clipped
        if price_point != original_price:
            ratio = price_point / original_price if original_price > 0 else 1.0
            price_low = max(price_low * ratio, 0.5 * price_point)
            price_high = min(price_high * ratio, 2.0 * price_point)
        
        # Ensure bounds are reasonable
        price_low = max(price_low, 0.5 * price_point)
        price_high = min(price_high, 2.5 * price_point)
        
        return price_point, price_low, price_high, relevant_anchors, flags
    
    def _estimate_confidence(self, 
                            variable_scores: Dict,
                            anchors_used: List,
                            flags: List[str]) -> float:
        """Heuristic confidence estimation."""
        base_confidence = 0.8 if anchors_used else 0.4
        
        # Penalize flags
        if "no_anchors_found" in flags:
            base_confidence = 0.3
        if "clipped_above_anchor" in flags or "clipped_below_anchor" in flags:
            base_confidence *= 0.85
        
        # Bonus for high-quality LLM justifications
        avg_justification_len = sum(
            len(v.get("justification", ""))
            for v in variable_scores.values()
        ) / max(len(variable_scores), 1)
        
        if avg_justification_len > 50:
            base_confidence *= 1.05
        
        return min(1.0, base_confidence)
    
    def _compute_freshness_days(self, timestamp_str: str) -> float:
        """Compute days since timestamp."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.utcnow()
            delta = now - timestamp
            return max(0, delta.days)
        except:
            return 30.0  # Default to moderate freshness


