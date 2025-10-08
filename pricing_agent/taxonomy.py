"""Taxonomy mapping for telecom data types."""

from typing import List, Dict, Set
from .schemas import DataType


# Mapping from telecom field names to data types
TELECOM_FIELD_MAPPING: Dict[str, List[DataType]] = {
    # Customer data
    "name": [DataType.PII_CORE, DataType.CONTACT],
    "phones": [DataType.CONTACT, DataType.TELECOM_PROFILE],
    "idcard": [DataType.GOV_ID_SCAN, DataType.PII_CORE],
    "info": [DataType.PII_CORE],
    "star": [DataType.TELECOM_PROFILE],  # Customer rating/status
    "contacts": [DataType.CONTACT],
    
    # Card data
    "card_id": [DataType.CREDIT_CARD],
    "card_info": [DataType.CREDIT_CARD],
    "bank_info": [DataType.BANK_LOGIN],
    
    # Subscription data
    "package_name": [DataType.TELECOM_SUBSCRIPTION],
    "fee": [DataType.TELECOM_SUBSCRIPTION],
    "subscription": [DataType.TELECOM_SUBSCRIPTION],
    
    # Order data
    "location": [DataType.CONTACT],
    "address": [DataType.CONTACT],
    "order_details": [DataType.OTHER],
    
    # Product data
    "product": [DataType.OTHER],
    "service": [DataType.OTHER],
}


def guess_types_from_fields(fields: List[str]) -> List[DataType]:
    """
    Guess data types from a list of field names.
    
    Args:
        fields: List of field names to analyze
        
    Returns:
        List of likely data types
    """
    found_types: Set[DataType] = set()
    
    for field in fields:
        field_lower = field.lower()
        
        # Direct mapping
        if field_lower in TELECOM_FIELD_MAPPING:
            found_types.update(TELECOM_FIELD_MAPPING[field_lower])
            continue
            
        # Pattern matching
        if any(keyword in field_lower for keyword in ["name", "full_name", "real_name"]):
            found_types.update([DataType.PII_CORE, DataType.CONTACT])
            
        if any(keyword in field_lower for keyword in ["phone", "mobile", "cell"]):
            found_types.update([DataType.CONTACT, DataType.TELECOM_PROFILE])
            
        if any(keyword in field_lower for keyword in ["id", "ssn", "passport", "license"]):
            found_types.update([DataType.GOV_ID_SCAN, DataType.PII_CORE])
            
        if any(keyword in field_lower for keyword in ["email", "address", "location"]):
            found_types.add(DataType.CONTACT)
            
        if any(keyword in field_lower for keyword in ["card", "credit", "debit"]):
            found_types.add(DataType.CREDIT_CARD)
            
        if any(keyword in field_lower for keyword in ["bank", "account", "routing"]):
            found_types.add(DataType.BANK_LOGIN)
            
        if any(keyword in field_lower for keyword in ["subscription", "plan", "package"]):
            found_types.add(DataType.TELECOM_SUBSCRIPTION)
            
        if any(keyword in field_lower for keyword in ["profile", "customer", "user"]):
            found_types.add(DataType.TELECOM_PROFILE)
    
    # If no specific types found, default to other
    if not found_types:
        found_types.add(DataType.OTHER)
        
    return list(found_types)


def get_telecom_data_components() -> Dict[str, List[DataType]]:
    """
    Get common telecom data component combinations.
    
    Returns:
        Dictionary mapping component names to their data types
    """
    return {
        "customer_basic": [DataType.PII_CORE, DataType.CONTACT],
        "customer_full": [DataType.PII_CORE, DataType.CONTACT, DataType.TELECOM_PROFILE],
        "customer_premium": [DataType.PII_CORE, DataType.CONTACT, DataType.TELECOM_PROFILE, DataType.GOV_ID_SCAN],
        "payment_info": [DataType.CREDIT_CARD, DataType.BANK_LOGIN],
        "subscription_data": [DataType.TELECOM_SUBSCRIPTION],
        "full_profile": [DataType.PII_CORE, DataType.CONTACT, DataType.TELECOM_PROFILE, DataType.TELECOM_SUBSCRIPTION],
    }
