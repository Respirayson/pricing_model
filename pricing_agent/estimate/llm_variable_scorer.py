"""LLM-based variable scorer for content-based pricing."""

import json
from typing import Dict, Any


SCORING_PROMPT_TEMPLATE = """You are an expert in dark web data market economics. Analyze the ACTUAL CONTENT of this telecom API response to estimate its black/gray-market resale value.

CRITICAL: Read and analyze the ACTUAL DATA VALUES, not just field names. Consider what an attacker could DO with this specific information.

Score on 10 attributes (0-10 scale):

1. Target Importance (0=anonymous, 10=high-value VIP)
   - READ the name, job_title, account_tier, employer fields
   - Consider: Is this a corporate executive? Government official? Celebrity? Or just "John Doe"?
   - High scores: CEO, CFO, CTO, government positions, "VIP" tier accounts
   - Low scores: generic names, no job info, basic consumer accounts

2. Sensitivity (0=minimal, 10=extremely sensitive)
   - ANALYZE what's exposed: just billing totals? Or real-time location traces? Call partners? SMS content?
   - Consider: Could this enable stalking, blackmail, or targeted attacks?
   - High scores: real-time GPS coordinates, call graphs revealing contacts, message content
   - Low scores: aggregated billing stats, anonymized usage metrics

3. Completeness (0=minimal fragment, 10=comprehensive dossier)
   - COUNT how many identity/behavior dimensions are covered
   - Full profile = name + location + call history + contacts + billing + device info
   - Partial = just name + phone, or just location ping

4. Freshness (0=stale/archived, 10=real-time/recent)
   - CALCULATE age from timestamps
   - 10: <24 hours old (real-time tracking)
   - 7: <7 days (recent activity)
   - 5: <30 days (moderately current)
   - 2: <6 months (historical)
   - 0: >1 year (stale archive)

5. Rarity (0=commodity bulk data, 10=unique exclusive leak)
   - ASSESS: Is this special access? One-time leak? Or mass-scraped public data?
   - Look for: "exclusive", "pre-release", unique internal IDs, restricted access indicators
   - High scores: insider access, unreleased datasets, VIP-only data
   - Low scores: bulk scrapes, widely circulated dumps

6. Exploitability (0=passive intelligence, 10=direct account takeover)
   - IDENTIFY actionable attack vectors
   - 10: account_access_token, session_id, password, sim_iccid (enables SIM swap)
   - 7: 2FA bypass info, security questions, PINs
   - 5: name+address+phone (phishing, social engineering)
   - 2: aggregated statistics, metadata only

7. Volume (0=single record, 10=massive batch)
   - COUNT records returned in this single API call
   - 10: 100+ individuals' data
   - 7: 50-99 records
   - 5: 10-49 records
   - 2: 2-9 records
   - 1: single target

8. Packaging (0=corrupted/unusable, 10=clean structured data)
   - ASSESS data quality and usability
   - 10: Clean JSON with labeled fields, no errors
   - 7: CSV with headers, mostly complete
   - 5: Unstructured text, requires parsing
   - 2: Corrupted, missing critical fields

9. SellerReputation (0=anonymous new seller, 10=established verified seller)
   - CHECK for reputation signals in metadata
   - Look for: "verified", "escrow", "trusted_seller" flags
   - Default to 5 (neutral) if no indicators present

10. LegalRisk (0=maximum enforcement risk, 10=minimal legal consequences)
    - IDENTIFY jurisdiction from phone codes, location, or region fields
    - 0-2: US, EU, UK, Japan (aggressive cybercrime prosecution)
    - 5: China, Russia, India (selective enforcement)
    - 8-10: Low-regulation jurisdictions, no extradition
    - HIGHER legal risk = LOWER attacker profit = LOWER price

API RESPONSE TO ANALYZE:
{api_response_json}

Think step-by-step:
1. Who is the target? (read name, title, account info)
2. What sensitive data is exposed? (read actual location coords, call partners)
3. How complete is the profile?
4. How fresh is the data? (calculate timestamp age)
5. Is this rare/exclusive?
6. What attacks does this enable?
7. How many records?
8. Is the data clean/usable?
9. Any seller reputation signals?
10. What jurisdiction creates legal risk?

OUTPUT (valid JSON only):
{{
  "target": {{"score": X.X, "justification": "Brief analysis of WHO this target is and why valuable/not"}},
  "sensitivity": {{"score": Y.Y, "justification": "What sensitive data is exposed and attack potential"}},
  "completeness": {{"score": Z.Z, "justification": "What dimensions of identity/behavior are covered"}},
  "freshness": {{"score": A.A, "justification": "Data age and time-value decay"}},
  "rarity": {{"score": B.B, "justification": "Exclusivity and scarcity assessment"}},
  "exploitability": {{"score": C.C, "justification": "Direct attack vectors enabled"}},
  "volume": {{"score": D.D, "justification": "Number of records/targets covered"}},
  "packaging": {{"score": E.E, "justification": "Data format and usability quality"}},
  "seller_reputation": {{"score": F.F, "justification": "Reputation signals detected (or default neutral)"}},
  "legal_risk": {{"score": G.G, "justification": "Jurisdiction and enforcement risk"}}
}}"""


class LLMVariableScorer:
    """LLM-based scorer for content pricing variables."""
    
    def __init__(self, llm_client):
        """
        Initialize scorer with LLM client.
        
        Args:
            llm_client: LLMClient instance from pricing_agent.extract.llm_client
        """
        self.llm = llm_client
        self.variable_names = [
            "target", "sensitivity", "completeness", "freshness", 
            "rarity", "exploitability", "volume", "packaging",
            "seller_reputation", "legal_risk"
        ]
    
    def score_api_response(self, api_response: Dict[str, Any], max_retries: int = 3) -> Dict[str, Dict[str, Any]]:
        """
        Score API response using LLM (REQUIRED - no fallback).
        
        Args:
            api_response: API response dict to score
            max_retries: Number of retry attempts
            
        Returns:
            Dict mapping variable names to {"score": float, "justification": str}
            
        Raises:
            RuntimeError: If LLM is unavailable or all retries fail
        """
        if not self.llm or not self.llm._invoker:
            raise RuntimeError(
                "LLM is required for content-based pricing. "
                "Please set LLM_API_KEY environment variable and ensure GPTInvoker is available. "
                "Install missing dependencies: pip install colorlog"
            )
        
        prompt = SCORING_PROMPT_TEMPLATE.format(
            api_response_json=json.dumps(api_response, indent=2)
        )
        
        # Try calling LLM with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                # Use the existing json_extract method
                system_prompt = "You are an expert data market analyst specializing in content-based valuation. Analyze the actual data values, not just field names. Provide only valid JSON output."
                schema = {
                    "type": "object",
                    "properties": {
                        var: {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "justification": {"type": "string"}
                            }
                        } for var in self.variable_names
                    }
                }
                
                result = self.llm.json_extract(system_prompt, prompt, schema)
                
                # Validate the result
                if self._validate_scores(result):
                    return result
                else:
                    last_error = "Invalid scores returned from LLM"
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1}: Invalid LLM output, retrying...")
                    
            except Exception as e:
                last_error = str(e)
                print(f"LLM scoring attempt {attempt + 1}/{max_retries} failed: {e}")
        
        # All retries failed
        raise RuntimeError(
            f"Content analysis failed after {max_retries} attempts. "
            f"Last error: {last_error}. "
            f"Ensure LLM_API_KEY is set and GPTInvoker is properly configured."
        )
    
    def _validate_scores(self, scores: Dict) -> bool:
        """Validate that all scores are present and in valid range."""
        if not scores or not isinstance(scores, dict):
            return False
            
        for var in self.variable_names:
            if var not in scores:
                return False
            if "score" not in scores[var]:
                return False
            score = scores[var]["score"]
            if not isinstance(score, (int, float)) or score < 0 or score > 10:
                return False
            if "justification" not in scores[var]:
                scores[var]["justification"] = "No justification provided"
        
        return True


