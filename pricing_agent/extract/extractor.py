"""Main extractor for converting chunks to price evidence."""

from typing import List, Dict, Any, Optional
from ..schemas import PriceEvidence, DataType, ListingType, Currency
from .llm_client import LLMClient


class EvidenceExtractor:
    """Extracts price evidence from text chunks using LLM."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize the evidence extractor.
        
        Args:
            llm_client: LLM client for extraction
        """
        self.llm_client = llm_client
    
    def extract_from_chunk(self, metadata: Dict[str, Any], chunk: str) -> List[PriceEvidence]:
        """
        Extract price evidence from a text chunk.
        
        Args:
            metadata: Document metadata
            chunk: Text chunk to analyze
            
        Returns:
            List of price evidence objects
        """
        try:
            # Get structured extraction from LLM
            result = self.llm_client.extract_price_evidence(chunk, metadata)
            
            evidence_list = []
            for item in result.get('price_evidence', []):
                try:
                    evidence = self._create_price_evidence(item, metadata, chunk)
                    if evidence:
                        evidence_list.append(evidence)
                except Exception as e:
                    print(f"Warning: Failed to create price evidence from item {item}: {e}")
                    continue
            
            return evidence_list
            
        except Exception as e:
            print(f"Error extracting evidence from chunk: {e}")
            return []
    
    def _create_price_evidence(self, item: Dict[str, Any], metadata: Dict[str, Any], chunk: str) -> Optional[PriceEvidence]:
        """
        Create a PriceEvidence object from extracted item.
        
        Args:
            item: Extracted item data
            metadata: Document metadata
            chunk: Original text chunk
            
        Returns:
            PriceEvidence object or None if invalid
        """
        try:
            # Validate and convert data type
            data_type_str = (item.get('data_type') or '').lower()
            data_type = self._parse_data_type(data_type_str)
            if not data_type:
                return None
            
            # Validate and convert listing type
            listing_type_str = (item.get('listing_type') or '').lower()
            listing_type = self._parse_listing_type(listing_type_str)
            if not listing_type:
                return None
            
            # Validate and convert currency
            currency_str = (item.get('currency') or 'USD').upper()
            currency = self._parse_currency(currency_str)
            
            # Validate price value
            price_value_raw = item.get('price_value')
            if price_value_raw is None:
                return None
            
            try:
                price_value = float(price_value_raw)
                if price_value <= 0:
                    return None
            except (ValueError, TypeError):
                return None
            
            # Validate and fix units
            units = item.get('units', 'per_record')
            if units not in ['per_record', 'per_account', 'per_dataset']:
                # Map common invalid units to valid ones
                if 'card' in units.lower() or 'credit' in units.lower():
                    units = 'per_record'
                elif 'account' in units.lower():
                    units = 'per_account'
                elif 'bulk' in units.lower() or 'dump' in units.lower():
                    units = 'per_dataset'
                else:
                    units = 'per_record'  # Default fallback
            
            # Create snippet from chunk (simplified)
            snippet = self._extract_snippet(chunk, item.get('snippet', ''))
            
            return PriceEvidence(
                source_id=metadata.get('source_id', 'unknown'),
                source_url=metadata.get('source_url'),
                source_title=metadata.get('source_title'),
                published_date=metadata.get('published_date'),
                data_type=data_type,
                listing_type=listing_type,
                region=item.get('region'),
                item_desc=item.get('item_desc'),
                price_value=price_value,
                currency=currency,
                units=units,
                quality_notes=item.get('quality_notes'),
                packaging=item.get('packaging'),
                sample_size=self._safe_int(item.get('sample_size')),
                price_low=self._safe_float(item.get('price_low')),
                price_high=self._safe_float(item.get('price_high')),
                snippet=snippet,
                extractor_confidence=self._safe_float(item.get('confidence'), 0.7)
            )
            
        except Exception as e:
            print(f"Error creating price evidence: {e}")
            return None
    
    def _parse_data_type(self, data_type_str: str) -> Optional[DataType]:
        """Parse data type string to enum."""
        mapping = {
            'contact': DataType.CONTACT,
            'pii_core': DataType.PII_CORE,
            'fullz': DataType.FULLZ,
            'credit_card': DataType.CREDIT_CARD,
            'bank_login': DataType.BANK_LOGIN,
            'gov_id_scan': DataType.GOV_ID_SCAN,
            'medical_record': DataType.MEDICAL_RECORD,
            'consumer_account': DataType.CONSUMER_ACCOUNT,
            'corporate_access': DataType.CORPORATE_ACCESS,
            'telecom_subscription': DataType.TELECOM_SUBSCRIPTION,
            'telecom_profile': DataType.TELECOM_PROFILE,
            'other': DataType.OTHER,
        }
        return mapping.get(data_type_str)
    
    def _parse_listing_type(self, listing_type_str: str) -> Optional[ListingType]:
        """Parse listing type string to enum."""
        mapping = {
            'retail_lookup': ListingType.RETAIL_LOOKUP,
            'bulk_dump': ListingType.BULK_DUMP,
            'account_access': ListingType.ACCOUNT_ACCESS,
            'document_scan': ListingType.DOCUMENT_SCAN,
        }
        return mapping.get(listing_type_str)
    
    def _parse_currency(self, currency_str: str) -> Currency:
        """Parse currency string to enum."""
        mapping = {
            'USD': Currency.USD,
            'EUR': Currency.EUR,
            'CNY': Currency.CNY,
            'GBP': Currency.GBP,
        }
        return mapping.get(currency_str, Currency.USD)
    
    def _extract_snippet(self, chunk: str, suggested_snippet: str) -> str:
        """Extract relevant snippet from chunk."""
        if suggested_snippet and len(suggested_snippet) < 500:
            return suggested_snippet
        
        # Fallback: return first 200 characters of chunk
        return chunk[:200] + "..." if len(chunk) > 200 else chunk
    
    def _safe_float(self, value, default=None):
        """Safely convert value to float."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=None):
        """Safely convert value to int."""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
