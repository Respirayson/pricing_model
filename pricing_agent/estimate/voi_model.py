import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AttackerAction(Enum):
    DO_NOTHING = "do_nothing"
    GUESS_ADDRESS = "guess_address"
    PHISH_EMAIL = "phish_email"
    RESELL_BULK = "resell_bulk"


@dataclass
class VictimState:
    """Victim state parameters."""
    wealth: float
    defense_level: float
    sensitivity: float
    detection_capability: float
    asset_liquidity: float


@dataclass
class ExPostParams:
    """Ex-post parameters for each action (after observing signal)."""
    P_success: Dict[AttackerAction, float]
    R_expected: Dict[AttackerAction, float]
    C_cost: Dict[AttackerAction, float]
    detection_risk: Dict[AttackerAction, float]


class VoIModel:
    """Monte Carlo VoI estimator."""
    
    def __init__(
        self,
        risk_aversion: float = 0.5,
        detection_penalty: float = -1000.0,
        freshness_decay_lambda: float = 0.1,
        n_simulations: int = 10000
    ):
        self.risk_aversion = risk_aversion
        self.detection_penalty = detection_penalty # negative value
        self.freshness_decay_lambda = freshness_decay_lambda
        self.n_simulations = n_simulations
        self.prior_wealth_mu = 5.0
        self.prior_wealth_sigma = 2.5
        self.prior_defense_mu = 4.0
        self.prior_defense_sigma = 2.0
    
    def compute_utility(
        self,
        action: AttackerAction,
        state: VictimState,
        P_success: float,
        R_expected: float,
        C_cost: float,
        detection_risk: float
    ) -> float:
        if action == AttackerAction.DO_NOTHING:
            return 0.0
        
        revenue = P_success * R_expected
        
        if revenue > 0 and self.risk_aversion > 0:
            revenue_scaled = revenue / 1000.0
            revenue_utility = (revenue_scaled ** (1.0 - self.risk_aversion)) * 1000.0
        else:
            revenue_utility = revenue
        
        scaled_penalty = self.detection_penalty * (1.0 + revenue / 10000.0)
        detection_cost = detection_risk * scaled_penalty
        
        utility = revenue_utility - C_cost + detection_cost
        return utility
    
    def sample_ex_ante_state(self) -> VictimState:
        """Sample victim state from ex-ante distribution."""
        wealth = np.clip(np.random.normal(self.prior_wealth_mu, self.prior_wealth_sigma), 0, 10)
        defense = np.clip(np.random.normal(self.prior_defense_mu, self.prior_defense_sigma), 0, 10)
        sensitivity = np.random.beta(2, 5) * 10
        detection = np.random.beta(3, 7)
        liquidity = np.random.beta(5, 3)
        
        return VictimState(
            wealth=wealth,
            defense_level=defense,
            sensitivity=sensitivity,
            detection_capability=detection,
            asset_liquidity=liquidity
        )
    
    def sample_ex_post_state(self, ex_post_params: ExPostParams, signal_strength: float = 0.7) -> VictimState:
        """Sample victim state from ex-post distribution."""
        avg_revenue = np.mean(list(ex_post_params.R_expected.values()))
        wealth_signal = np.log1p(avg_revenue / 1000.0)
        
        avg_detection = np.mean(list(ex_post_params.detection_risk.values()))
        defense_signal = avg_detection * 10.0
        
        wealth_post_mu = signal_strength * wealth_signal + (1 - signal_strength) * self.prior_wealth_mu
        defense_post_mu = signal_strength * defense_signal + (1 - signal_strength) * self.prior_defense_mu
        
        wealth = np.clip(np.random.normal(wealth_post_mu, self.prior_wealth_sigma * 0.7), 0, 10)
        defense = np.clip(np.random.normal(defense_post_mu, self.prior_defense_sigma * 0.7), 0, 10)
        
        sensitivity = np.random.beta(2, 5) * 10
        detection = np.clip(np.random.beta(3, 7) + avg_detection * 0.3, 0, 1)
        liquidity = np.random.beta(5, 3)
        
        return VictimState(
            wealth=wealth,
            defense_level=defense,
            sensitivity=sensitivity,
            detection_capability=detection,
            asset_liquidity=liquidity
        )
    
    def estimate_V_ex_ante(
        self,
        ex_post_params: ExPostParams,
        freshness_days: float = 0.0,
        signal_strength: float = 0.7
    ) -> Dict[str, Any]:
        """Estimate V_ex_ante via Monte Carlo."""
        freshness_factor = math.exp(-self.freshness_decay_lambda * freshness_days)
        
        # Ex-ante: generic parameters (no specific signal)
        ex_ante_P_success = 0.3
        ex_ante_R_expected = 500.0
        ex_ante_C_cost = 100.0
        ex_ante_detection_risk = 0.1
        
        ex_ante_utilities = []
        for _ in range(self.n_simulations):
            state = self.sample_ex_ante_state()
            action_utilities = {}
            for action in AttackerAction:
                u = self.compute_utility(
                    action, state,
                    ex_ante_P_success,
                    ex_ante_R_expected,
                    ex_ante_C_cost,
                    ex_ante_detection_risk
                )
                action_utilities[action] = u
            max_utility = max(action_utilities.values())
            ex_ante_utilities.append(max_utility)
        
        ex_ante_utility = np.mean(ex_ante_utilities)
        optimal_action_ex_ante = max(
            AttackerAction,
            key=lambda a: np.mean([
                self.compute_utility(
                    a, self.sample_ex_ante_state(),
                    ex_ante_P_success,
                    ex_ante_R_expected,
                    ex_ante_C_cost,
                    ex_ante_detection_risk
                )
                for _ in range(1000)
            ])
        )
        
        ex_post_utilities = []
        action_counts = {action: 0 for action in AttackerAction}
        
        for _ in range(self.n_simulations):
            state = self.sample_ex_post_state(ex_post_params, signal_strength)
            action_utilities = {}
            
            # Only use actions explicitly in ex_post_params
            for action in AttackerAction:
                if action not in ex_post_params.P_success:
                    continue
                
                base_P_success = ex_post_params.P_success[action]
                base_R_expected = ex_post_params.R_expected[action]
                base_C_cost = ex_post_params.C_cost[action]
                base_detection_risk = ex_post_params.detection_risk[action]
                
                P_success = np.clip(np.random.normal(base_P_success, base_P_success * 0.15), 0.01, 0.99)
                R_expected = max(0, np.random.normal(base_R_expected, base_R_expected * 0.2))
                C_cost = base_C_cost  # Costs stay fixed
                detection_risk = np.clip(np.random.normal(base_detection_risk, base_detection_risk * 0.15), 0.0, 1.0)
                
                u = self.compute_utility(action, state, P_success, R_expected, C_cost, detection_risk)
                action_utilities[action] = u

            if action_utilities:  # Only if we have at least one action
                optimal_action = max(action_utilities, key=action_utilities.get)
                max_utility = action_utilities[optimal_action]
                ex_post_utilities.append(max_utility)
                action_counts[optimal_action] += 1
        
        ex_post_utility = np.mean(ex_post_utilities)
        optimal_action_ex_post = max(action_counts, key=action_counts.get)
        
        V_raw = ex_post_utility - ex_ante_utility
        V_ex_ante = V_raw * freshness_factor
        
        ex_ante_std = np.std(ex_ante_utilities)
        ex_post_std = np.std(ex_post_utilities)
        total_variance = ex_ante_std**2 + ex_post_std**2
        
        if V_ex_ante > 0:
            cv = math.sqrt(total_variance) / max(abs(V_ex_ante), 1.0)
            confidence = max(0.0, min(1.0, 1.0 - cv / 3.0))
        else:
            confidence = 0.0
        
        return {
            "V_ex_ante": max(0.0, V_ex_ante),
            "ex_ante_utility": ex_ante_utility,
            "ex_post_utility": ex_post_utility,
            "optimal_action_ex_ante": optimal_action_ex_ante.value,
            "optimal_action_ex_post": optimal_action_ex_post.value,
            "freshness_factor": freshness_factor,
            "confidence": confidence,
            "simulation_stats": {
                "n_simulations": self.n_simulations,
                "ex_ante_mean": ex_ante_utility,
                "ex_ante_std": ex_ante_std,
                "ex_post_mean": ex_post_utility,
                "ex_post_std": ex_post_std,
                "V_raw": V_raw,
                "action_distribution": {k.value: v/self.n_simulations for k, v in action_counts.items()}
            }
        }
    
    def normalize_to_usd(
        self, V_ex_ante: float, anchors: List[Dict[str, Any]], data_type: str = "telecom_profile"
    ) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Convert VoI (utility units) to USD using market anchor prices."""
        if not anchors:
            price_usd = V_ex_ante * 0.1
            confidence = 0.3
            return price_usd, confidence, []
        
        relevant_anchors = [a for a in anchors if a.get("data_type") == data_type]
        if not relevant_anchors:
            relevant_anchors = anchors
        
        anchor_prices = [a.get("price") for a in relevant_anchors]
        anchor_voi = [a.get("estimated_voi") for a in relevant_anchors]
        
        scaling_factors = [p / max(v, 1.0) for p, v in zip(anchor_prices, anchor_voi)]
        median_scale = np.median(scaling_factors)
        price_usd = V_ex_ante * median_scale
        
        if len(scaling_factors) > 1:
            scale_std = np.std(scaling_factors)
            scale_mean = np.mean(scaling_factors)
            cv = scale_std / max(scale_mean, 0.01)
            confidence = max(0.3, min(0.95, 1.0 - cv / 2.0))
        else:
            confidence = 0.5
        
        anchors_used = [
            {
                "data_type": a.get("data_type"),
                "price": a.get("price"),
                "estimated_voi": a.get("estimated_voi"),
                "source": a.get("source", "unknown")
            }
            for a in relevant_anchors[:5]
        ]
        
        return price_usd, confidence, anchors_used

