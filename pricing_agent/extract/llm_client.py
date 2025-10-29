import json
import os
import sys
from typing import Dict, Any, Optional
from .prompts import EXTRACTION_SYSTEM, EXTRACTION_USER_TEMPLATE


class LLMClient:
    """Provider-agnostic LLM client for structured extraction."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-nano"):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key for LLM provider
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model
        self._invoker = None
        
        # Initialize GPTInvoker if API key is available
        if self.api_key:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
                sys.path.insert(0, project_root)
                
                cwd = os.getcwd()
                if cwd not in sys.path:
                    sys.path.insert(0, cwd)
                
                from gpt_invoker import GPTInvoker
                self._invoker = GPTInvoker(
                    model=self.model,
                    api_key=self.api_key,
                    api_host="https://yunwu.ai/v1",
                    temperature=0.1,
                    max_tokens=12000,
                    write_to_cache=False,
                    read_from_cache=False,
                )
                print(f"Initialized GPTInvoker with model {model}")
            except ImportError:
                print("Warning: GPTInvoker not found. Please ensure gpt_invoker.py is in your Python path.")
                print("Falling back to stub implementation.")
            except Exception as e:
                print(f"Error initializing GPTInvoker: {e}")
                print("Falling back to stub implementation.")
    
    def json_extract(self, system_prompt: str, user_prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data using LLM with function calling.
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt with the text to analyze
            schema: JSON schema for the expected output
            
        Returns:
            Extracted data as dictionary
        """
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self._invoker.generate(messages)
            try:
                result = self._invoker.extract_json(response)
                return result
            except:
                # If JSON extraction fails, try to parse manually
                try:
                    # Look for JSON in the response with more flexible patterns
                    import re
                    
                    # Try to find JSON block with ```json markers first
                    json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
                    if json_block_match:
                        result = json.loads(json_block_match.group(1))
                        return result
                    
                    # Try to find any JSON object in the response
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return result
                    
                    # Try to find JSON starting from the first { and ending at the last }
                    start_idx = response.find('{')
                    end_idx = response.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx+1]
                        result = json.loads(json_str)
                        return result
                        
                except Exception:
                    pass
                
                # Return empty result if parsing fails
                return {
                    "price_evidence": [],
                    "confidence": 0.0,
                    "extraction_notes": f"Failed to parse LLM response: {response[:200]}..."
                }
                
        except ValueError as e:
            if "Finish reason is not 'stop'" in str(e):
                print(f"Warning: LLM response truncated due to token limit. Consider increasing max_tokens.")
                return {
                    "price_evidence": [],
                    "confidence": 0.0,
                    "extraction_notes": f"LLM response truncated: {str(e)}"
                }
            else:
                print(f"Error calling LLM: {e}")
                return {
                    "price_evidence": [],
                    "confidence": 0.0,
                    "extraction_notes": f"LLM call failed: {str(e)}"
                }
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {
                "price_evidence": [],
                "confidence": 0.0,
                "extraction_notes": f"LLM call failed: {str(e)}"
            }
    
    def extract_price_evidence(self, chunk: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract price evidence from a text chunk.
        
        Args:
            chunk: Text chunk to analyze
            metadata: Document metadata
            
        Returns:
            Structured price evidence
        """
        user_prompt = EXTRACTION_USER_TEMPLATE.format(
            source_id=metadata.get('source_id', 'unknown'),
            source_title=metadata.get('source_title', 'Unknown'),
            published_date=metadata.get('published_date', 'Unknown'),
            chunk=chunk
        )
        
        schema = {
            "type": "object",
            "properties": {
                "price_evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "data_type": {"type": "string"},
                            "listing_type": {"type": "string"},
                            "region": {"type": "string"},
                            "price_value": {"type": "number"},
                            "currency": {"type": "string"},
                            "units": {"type": "string"},
                            "item_desc": {"type": "string"},
                            "quality_notes": {"type": "string"},
                            "packaging": {"type": "string"},
                            "sample_size": {"type": "integer"},
                            "price_low": {"type": "number"},
                            "price_high": {"type": "number"},
                            "snippet": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        return self.json_extract(EXTRACTION_SYSTEM, user_prompt, schema)
