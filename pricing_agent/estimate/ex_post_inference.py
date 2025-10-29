import json
from typing import Dict, Any
from .voi_model import AttackerAction, ExPostParams


EX_POST_INFERENCE_PROMPT = """You are an expert in adversarial information economics and cybersecurity risk assessment. Analyze this telecom API response to estimate ex-post parameters for an attacker's decision model.

THEORETICAL FRAMEWORK:
You are inferring parameters for a Bayesian Value-of-Information model. The API response is a SIGNAL that updates an attacker's beliefs about:
1. Success probability P(success | action, signal)
2. Expected revenue R(action, signal)  
3. Execution cost C(action, signal)
4. Detection risk P(detection | action, signal)

ATTACKER ACTION SPACE:
- do_nothing: Take no action (baseline)
- guess_address: Guess physical address via public records or patterns
- phish_email: Send targeted phishing email
- resell_bulk: Resell data in bulk markets

API RESPONSE TO ANALYZE:
{api_response_json}

ANALYSIS INSTRUCTIONS:
For EACH action, estimate the following parameters based on what information the API response reveals:

1. P_SUCCESS (0.0 - 1.0): Action success probability
   - do_nothing: 1.0
   - guess_address: 0.2-0.8 (depends on info richness)
   - phish_email: 0.2-0.7 (depends on personalization data)
   - resell_bulk: 0.8-0.95

2. R_EXPECTED (USD): Expected revenue if action succeeds
   - do_nothing: $0
   - guess_address: $50-$300
   - phish_email: $200-$2000
   - resell_bulk: $10-$500
   
   Scale by target importance, data completeness, and freshness

3. C_COST (USD): Cost to execute action
   - do_nothing: $0
   - guess_address: $5-$30
   - phish_email: $20-$150
   - resell_bulk: $10-$50

4. DETECTION_RISK (0.0 - 1.0): Detection probability
   - do_nothing: 0.0
   - guess_address: 0.02-0.1
   - phish_email: 0.15-0.35
   - resell_bulk: 0.05-0.2
   
   Scale by jurisdiction, target defenses, and data source visibility

ANALYSIS RULES:
1. Read actual data values, not just field names
2. Minimal/empty API response → low P_success, low R_expected
3. High-value victim → high R_expected, high detection_risk
4. Partial address info → guess_address becomes viable
5. Email + name → phish_email viable
6. Bulk/generic data → resell_bulk optimal
7. Detection risk increases with victim importance and jurisdiction

For each action, estimate P_success, R_expected, C_cost, and detection_risk based on the available data.

OUTPUT FORMAT (valid JSON only):
{{
  "do_nothing": {{
    "P_success": 1.0,
    "R_expected": 0.0,
    "C_cost": 0.0,
    "detection_risk": 0.0,
    "reasoning": "Baseline action - no engagement"
  }},
  "guess_address": {{
    "P_success": <float 0-1>,
    "R_expected": <float USD>,
    "C_cost": <float USD>,
    "detection_risk": <float 0-1>,
    "reasoning": "..."
  }},
  "phish_email": {{
    "P_success": <float 0-1>,
    "R_expected": <float USD>,
    "C_cost": <float USD>,
    "detection_risk": <float 0-1>,
    "reasoning": "..."
  }},
  "resell_bulk": {{
    "P_success": <float 0-1>,
    "R_expected": <float USD>,
    "C_cost": <float USD>,
    "detection_risk": <float 0-1>,
    "reasoning": "..."
  }},
  "metadata": {{
    "target_assessment": "Brief summary of who the target is and their value",
    "data_quality": "Assessment of data completeness and freshness",
    "optimal_action_rationale": "Which action appears most profitable and why"
  }}
}}

Provide ONLY valid JSON. No additional text."""


class ExPostInference:
    """Extracts ex-post parameters from API responses using LLM."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    def infer_ex_post(self, api_response: Dict[str, Any], max_retries: int = 3) -> ExPostParams:
        """Call LLM to extract P_success, R_expected, C_cost, detection_risk for each action."""
        if not self.llm or not self.llm._invoker:
            raise RuntimeError(
                "LLM is required for ex-post inference. "
                "Please set LLM_API_KEY environment variable."
            )
        
        prompt = EX_POST_INFERENCE_PROMPT.format(
            api_response_json=json.dumps(api_response, indent=2)
        )
        
        last_error = None
        for attempt in range(max_retries):
            try:
                system_prompt = (
                    "You are an expert in adversarial information economics and "
                    "Bayesian decision theory. Analyze API responses to infer posterior "
                    "parameters for attacker utility functions. Provide only valid JSON output."
                )
                
                schema = {
                    "type": "object",
                    "properties": {
                        action.value: {
                            "type": "object",
                            "properties": {
                                "P_success": {"type": "number", "minimum": 0, "maximum": 1},
                                "R_expected": {"type": "number", "minimum": 0},
                                "C_cost": {"type": "number", "minimum": 0},
                                "detection_risk": {"type": "number", "minimum": 0, "maximum": 1},
                                "reasoning": {"type": "string"}
                            },
                            "required": ["P_success", "R_expected", "C_cost", "detection_risk"]
                        } for action in AttackerAction
                    },
                    "required": [action.value for action in AttackerAction]
                }
                
                result = self.llm.json_extract(system_prompt, prompt, schema)
                
                if self._validate_ex_post_output(result):
                    return self._parse_ex_post(result)
                else:
                    last_error = "Invalid ex-post parameters returned from LLM"
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1}: Invalid LLM output, retrying...")
                        
            except Exception as e:
                last_error = str(e)
                print(f"Ex-post inference attempt {attempt + 1}/{max_retries} failed: {e}")
        
        raise RuntimeError(f"Ex-post inference failed after {max_retries} attempts. Last error: {last_error}")
    
    def _validate_ex_post_output(self, output: Dict[str, Any]) -> bool:
        if not output or not isinstance(output, dict):
            return False
        
        for action in AttackerAction:
            if action.value not in output:
                return False
            
            params = output[action.value]
            required_keys = ["P_success", "R_expected", "C_cost", "detection_risk"]
            
            for key in required_keys:
                if key not in params:
                    return False
                if not isinstance(params[key], (int, float)):
                    return False
            
            # Validate ranges
            if not (0 <= params["P_success"] <= 1):
                return False
            if not (0 <= params["detection_risk"] <= 1):
                return False
            if params["R_expected"] < 0 or params["C_cost"] < 0:
                return False
        
        return True
    
    def _parse_ex_post(self, llm_output: Dict[str, Any]) -> ExPostParams:
        P_success = {}
        R_expected = {}
        C_cost = {}
        detection_risk = {}
        
        for action in AttackerAction:
            params = llm_output[action.value]
            P_success[action] = float(params["P_success"])
            R_expected[action] = float(params["R_expected"])
            C_cost[action] = float(params["C_cost"])
            detection_risk[action] = float(params["detection_risk"])
        
        return ExPostParams(
            P_success=P_success,
            R_expected=R_expected,
            C_cost=C_cost,
            detection_risk=detection_risk
        )

