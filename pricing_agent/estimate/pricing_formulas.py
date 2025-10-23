"""Pricing formulas for content-based API valuation."""

import math
from typing import Dict, Tuple, Any


class LogLinearPricingModel:
    """Log-linear hedonic pricing model."""
    
    def __init__(self, model_params: Dict[str, Any]):
        """
        Initialize with learned model parameters.
        
        Args:
            model_params: Dict with keys:
                - "alpha": intercept
                - "betas": dict mapping variable names to coefficients
                - "covariance": dict mapping variable names to variances (optional)
        """
        self.alpha = model_params.get("alpha", 3.12)
        self.betas = model_params.get("betas", self._default_betas())
        self.covariance = model_params.get("covariance", {})
        self.variable_names = list(self.betas.keys())
    
    @staticmethod
    def _default_betas() -> Dict[str, float]:
        """Default learned coefficients."""
        return {
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
        }
    
    def estimate_price(self, variable_scores: Dict[str, Dict[str, Any]]) -> Tuple[float, float, float]:
        """
        Estimate price using log-linear model.
        
        Args:
            variable_scores: Dict mapping variable names to {"score": float, ...}
            
        Returns:
            Tuple of (price_point, price_low, price_high)
        """
        # Compute log-price
        ln_price = self.alpha
        for var_name, beta in self.betas.items():
            if var_name in variable_scores:
                score = variable_scores[var_name]["score"]
                ln_price += beta * score
        
        # Estimate uncertainty
        variance = 0.0
        for var_name in self.variable_names:
            if var_name in variable_scores:
                score = variable_scores[var_name]["score"]
                var_coef = self.covariance.get(var_name, 0.01)  # Default small variance
                variance += var_coef * (score ** 2)
        
        std_dev = math.sqrt(max(variance, 0.01))  # Ensure positive
        
        # Compute price with confidence interval (95% CI = ±1.96 std devs)
        price_point = math.exp(ln_price)
        price_low = math.exp(ln_price - 1.96 * std_dev)
        price_high = math.exp(ln_price + 1.96 * std_dev)
        
        return price_point, price_low, price_high


class MultiplicativePricingModel:
    """Multiplicative cascade pricing model."""
    
    def __init__(self, base_anchors: Dict[str, float]):
        """
        Initialize with base anchor prices.
        
        Args:
            base_anchors: Dict mapping data_type to base price
        """
        self.base_anchors = base_anchors
    
    def estimate_price(self, variable_scores: Dict[str, Dict[str, Any]], 
                      data_type: str = "telecom_profile") -> float:
        """
        Estimate price using multiplicative model.
        
        Args:
            variable_scores: Dict mapping variable names to {"score": float, ...}
            data_type: Data type key for base anchor
            
        Returns:
            Estimated price (single point)
        """
        base = self.base_anchors.get(data_type, 50.0)
        
        # Define multiplier functions
        multipliers = {
            "target": lambda x: 0.5 + 0.15 * x,
            "sensitivity": lambda x: 0.6 + 0.10 * x,
            "completeness": lambda x: 0.5 + 0.10 * x,
            "freshness": lambda x: 0.3 + 0.07 * x,
            "rarity": lambda x: 0.7 + 0.08 * x,
            "exploitability": lambda x: 0.6 + 0.12 * x,
            "volume": lambda x: 0.8 + 0.02 * x,
            "packaging": lambda x: 0.9 + 0.02 * x,
            "seller_reputation": lambda x: 0.85 + 0.03 * x,
            "legal_risk": lambda x: 1.0 - 0.03 * (10 - x)  # Inverse
        }
        
        price = base
        for var_name, mult_func in multipliers.items():
            if var_name in variable_scores:
                score = variable_scores[var_name]["score"]
                price *= mult_func(score)
        
        return price


