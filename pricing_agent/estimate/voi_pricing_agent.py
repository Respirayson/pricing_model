import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from .voi_model import VoIModel
from .ex_post_inference import ExPostInference


class VoIPricingAgent:
    """
    VoI-based pricing agent for API data valuation.
    
    Pipeline:
    1. API response --> ex-post inference
    2. ex-post parameters --> Monte Carlo VoI estimation
    3. VoI --> USD price normalization
    """
    
    def __init__(
        self,
        llm_client,
        model_params: Optional[Dict[str, Any]] = None,
        anchor_prices: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize VoI pricing agent."""
        self.llm = llm_client
        
        # Initialize VoI model with custom or default parameters
        model_params = model_params or {}
        self.voi_model = VoIModel(
            risk_aversion=model_params.get("risk_aversion", 0.5),
            detection_penalty=model_params.get("detection_penalty", -1000.0),
            freshness_decay_lambda=model_params.get("freshness_decay_lambda", 0.1),
            n_simulations=model_params.get("n_simulations", 10000)
        )
        
        # Initialize ex-post inference engine
        self.ex_post_inference = ExPostInference(llm_client)
        
        # Load or use provided anchor prices
        self.anchor_prices = anchor_prices or self._default_anchors()
    
    def estimate_price(
        self,
        api_response: Dict[str, Any],
        query_id: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Estimate price for API response."""
        # Generate IDs
        query_id = query_id or str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Extract metadata
        metadata = metadata or {}
        freshness_days = metadata.get("freshness_days", 0.0)
        data_type = metadata.get("data_type", "telecom_profile")
        region = metadata.get("region", "unknown")
        
        # infer ex-post parameters from API signal
        ex_post_params = self.ex_post_inference.infer_ex_post(api_response)
        
        # estimate V_ex_ante via Monte Carlo
        voi_result = self.voi_model.estimate_V_ex_ante(
            ex_post_params=ex_post_params,
            freshness_days=freshness_days,
            signal_strength=0.7
        )
        
        # normalize to USD using market anchors
        usd_estimate, anchor_confidence, anchors_used = self.voi_model.normalize_to_usd(
            V_ex_ante=voi_result["V_ex_ante"],
            anchors=self.anchor_prices,
            data_type=data_type
        )
        
        # combine confidences (take minimum for conservative estimate)
        overall_confidence = min(voi_result["confidence"], anchor_confidence)
        
        # Collect warnings/flags
        flags = []
        if voi_result["V_ex_ante"] <= 0:
            flags.append("non_positive_voi_zero_price")
        if overall_confidence < 0.4:
            flags.append("low_confidence_estimate")
        if freshness_days > 30:
            flags.append("stale_data_significant_decay")
        if not anchors_used:
            flags.append("no_market_anchors_rule_of_thumb_pricing")
        
        # Format ex-post parameters for output
        ex_post_dict = {
            "P_success": {action.value: prob for action, prob in ex_post_params.P_success.items()},
            "R_expected": {action.value: rev for action, rev in ex_post_params.R_expected.items()},
            "C_cost": {action.value: cost for action, cost in ex_post_params.C_cost.items()},
            "detection_risk": {action.value: risk for action, risk in ex_post_params.detection_risk.items()}
        }
        
        # Build result dictionary
        result = {
            # Identifiers
            "query_id": query_id,
            "estimated_at": timestamp,
            "model_version": "voi-bergemann-v1.0",
            
            # Core VoI results
            "V_ex_ante": voi_result["V_ex_ante"],
            "USD_estimate": max(0.0, usd_estimate),
            "confidence": overall_confidence,
            
            # Ex-post parameters
            "ex_post_params": ex_post_dict,
            
            # Decision analysis
            "optimal_action_ex_ante": voi_result["optimal_action_ex_ante"],
            "optimal_action_ex_post": voi_result["optimal_action_ex_post"],
            
            # Supporting data
            "anchors_used": anchors_used,
            "simulation_stats": voi_result["simulation_stats"],
            "flags": flags,
            
            # Metadata
            "data_type": data_type,
            "region": region,
            "freshness_days": freshness_days,
            "freshness_factor": voi_result["freshness_factor"],
            
            # Provenance
            "provenance": {
                "n_simulations": voi_result["simulation_stats"]["n_simulations"],
                "risk_aversion": self.voi_model.risk_aversion,
                "detection_penalty": self.voi_model.detection_penalty,
            }
        }
        
        return result
    
    def _default_anchors(self) -> List[Dict[str, Any]]:
        """
        Default market anchor prices from dark web research.
        
        These anchors are derived from academic studies and public reports on
        dark web data pricing (e.g., Privacy Affairs, Comparitech, SOCRadar).
        They serve to calibrate the VoI utility scale to observable USD prices.
        
        Returns:
            List of anchor price observations
        """
        return [
            {
                "data_type": "telecom_profile",
                "price": 50.0,
                "estimated_voi": 400.0,
                "source": "privacy_affairs_2023",
                "description": "Telecom subscriber profile with location history"
            },
            {
                "data_type": "telecom_profile",
                "price": 85.0,
                "estimated_voi": 650.0,
                "source": "comparitech_2024",
                "description": "Premium telecom data with real-time tracking"
            },
            {
                "data_type": "telecom_subscription",
                "price": 25.0,
                "estimated_voi": 200.0,
                "source": "socradar_2024",
                "description": "Basic subscription data without location"
            },
            {
                "data_type": "pii_core",
                "price": 15.0,
                "estimated_voi": 150.0,
                "source": "privacy_affairs_2023",
                "description": "Name, phone, email (no location or tracking)"
            },
            {
                "data_type": "fullz",
                "price": 200.0,
                "estimated_voi": 1500.0,
                "source": "comparitech_2024",
                "description": "Full identity package (SSN, DOB, address, banking)"
            },
            {
                "data_type": "contact",
                "price": 5.0,
                "estimated_voi": 50.0,
                "source": "socradar_2024",
                "description": "Basic contact information only"
            },
            {
                "data_type": "corporate_access",
                "price": 500.0,
                "estimated_voi": 5000.0,
                "source": "deepstrike_2025",
                "description": "Corporate VPN access or admin credentials"
            }
        ]
    
    def batch_estimate(
        self,
        api_responses: List[Dict[str, Any]],
        query_ids: Optional[List[str]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch estimation for multiple API responses.
        
        Args:
            api_responses: List of API response dictionaries
            query_ids: Optional list of query IDs
            metadata_list: Optional list of metadata dicts
            
        Returns:
            List of VoI estimation results
        """
        results = []
        n = len(api_responses)
        
        query_ids = query_ids or [None] * n
        metadata_list = metadata_list or [None] * n
        
        for i, (api_response, query_id, metadata) in enumerate(zip(api_responses, query_ids, metadata_list)):
            print(f"Processing batch item {i+1}/{n}...")
            result = self.estimate_price(api_response, query_id, metadata)
            results.append(result)
        
        return results

