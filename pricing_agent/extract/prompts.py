"""Prompts for LLM-based price evidence extraction."""

EXTRACTION_SYSTEM = """You are a data analyst specializing in extracting pricing information from documents about data breaches and dark web markets.

Your task is to identify and extract price evidence from text, focusing on:
1. Data types being sold (personal info, credit cards, accounts, etc.)
2. Listing types (retail lookup, bulk dump, account access, document scan)
3. Price information (amount, currency, units)
4. Quality and packaging details
5. Geographic regions when mentioned

IMPORTANT RULES:
- Only extract information that is explicitly stated in the text
- Do not make assumptions or infer information not present
- Focus on actual pricing data, not general market commentary
- Be conservative with confidence scores
- Include relevant text snippets as evidence
- Return structured JSON following the exact schema provided

Data types to look for:
- contact: Contact information (email, phone, address)
- pii_core: Core personally identifiable information (name, SSN, DOB)
- fullz: Complete identity packages
- credit_card: Credit card information
- bank_login: Bank account credentials
- gov_id_scan: Government ID documents
- medical_record: Medical records
- consumer_account: Consumer account credentials
- corporate_access: Corporate system access
- telecom_subscription: Telecom service subscriptions
- telecom_profile: Telecom customer profiles
- other: Other types of data

Listing types:
- retail_lookup: Individual record lookups
- bulk_dump: Large datasets
- account_access: Account credentials
- document_scan: Scanned documents

Return only valid JSON following the provided schema."""

EXTRACTION_USER_TEMPLATE = """Extract price evidence from the following text:

Source: {source_id}
Title: {source_title}
Date: {published_date}

Text to analyze:
{chunk}

Extract any pricing information following the schema. If no pricing information is found, return an empty price_evidence array."""
