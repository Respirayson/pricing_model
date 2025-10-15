# Pricing Agent

A Python framework for analyzing dark web pricing data and estimating the value of exposed personal data. Includes both **data item pricing** (individual records) and **API-level pricing** (revenue per API call).

## Features

### Data Pricing Framework
- Extract pricing intelligence from documents (PDFs, HTML, Markdown)
- Build statistical benchmarks by data type and region
- Rule-based and LLM-based price estimation
- Currency normalization and confidence scoring

### API Pricing Framework
- Analyze API endpoints to estimate revenue potential per call
- Identify what personal data APIs expose
- Leverage existing benchmark data for accurate estimates
- Batch processing for multiple APIs

## Installation

```bash
# Clone and navigate to repo
cd /Users/SG4083/Desktop/pricing_model

# Activate virtual environment
source venv/bin/activate

# Install dependencies (already done)
pip install -e .

# Set API key
export LLM_API_KEY="your-openai-api-key-here"
```

## Quick Start

### Data Pricing

```bash
# 1. Run full pipeline (ingest → extract → aggregate)
pricing-agent run-pipeline repo_docs/ evidence.json bench.json

# 2. View benchmarks
pricing-agent show-benchmark bench.json

# 3. Estimate price (rule-based)
pricing-agent rule-estimate bench.json --data-type credit_card --region ANY

# 4. Estimate price (LLM-based)
pricing-agent llm-estimate bench.json --data-type credit_card
```

### API Pricing

```bash
# 1. Price APIs with benchmarks
pricing-agent price-apis fake_apis.md --benchmark-file bench.json --limit 3

# 2. Full analysis with output
pricing-agent price-apis fake_apis.md --benchmark-file bench.json --output results.json
```

## CLI Commands

See `CLI_COMMANDS.md` for full command reference.

### Pipeline Commands

```bash
# Full pipeline
pricing-agent run-pipeline repo_docs/ evidence.json bench.json

# Web scraping
# Add new sources to real_sources.py

pricing-agent scrape-web --output-dir repo_docs
```

### Data Pricing Commands

```bash
# Rule-based estimation
pricing-agent rule-estimate bench.json --data-type telecom_profile --region CN

# LLM-based estimation
pricing-agent llm-estimate bench.json --data-type credit_card

# Show benchmarks
pricing-agent show-benchmark bench.json
```

### API Pricing Commands

```bash
# Price APIs (with benchmarks recommended)
pricing-agent price-apis fake_apis.md --benchmark-file bench.json

# Save output
pricing-agent price-apis fake_apis.md --benchmark-file bench.json --output results.json

# Test with subset
pricing-agent price-apis fake_apis.md --limit 3
```

## Data Types

The system recognizes these data types based on extracted benchmarks:

**High Value:**
- `credit_card` - Credit card information
- `fullz` - Complete identity packages
- `bank_login` - Bank account credentials
- `gov_id_scan` - Government ID documents
- `medical_record` - Medical records

**Standard:**
- `consumer_account` - Consumer account credentials
- `corporate_access` - Corporate system access
- `pii_core` - Core PII
- `contact` - Contact information
- `telecom_profile` - Telecom customer profiles
- `telecom_subscription` - Telecom subscription data

## Pricing Models

### Rule-Based Model

```
Final Price = [Base Price] × Freshness × Completeness × Exclusivity × 
              Packaging × Reputation × Demand + VIP_Premium
```

### LLM-Based Model

Uses language models to:
- Analyze market conditions and data quality
- Compare against historical benchmarks
- Provide detailed reasoning and confidence scores
- Consider current market trends

### API Pricing Model

Analyzes API endpoints to estimate revenue per call by:
- Identifying exposed personal data types
- Mapping to benchmark pricing
- Considering data sensitivity and completeness
- Factoring in market demand and use cases

## Architecture

```
pricing_agent/
├── ingest/          # Document loading, web scraping, API parsing
├── extract/         # Price extraction, LLM client
├── aggregate/       # Benchmark building, modifiers
├── estimate/        # Price estimators (rule-based, LLM, API)
├── normalize/       # Currency conversion
├── eval/            # Evaluation metrics
├── schemas.py       # Data models
└── cli.py           # Command-line interface
```

## How It Works

### Data Pricing Workflow

1. **Ingest**: Load documents from `repo_docs/`
2. **Extract**: Find pricing information using regex + LLM
3. **Aggregate**: Build statistical benchmarks (p10/p50/p90)
4. **Estimate**: Calculate prices using rules or LLM

### API Pricing Workflow

1. **Parse**: Load API definitions from markdown
2. **Analyze**: Identify exposed data types
3. **Reference**: Compare against benchmark pricing
4. **Estimate**: Calculate revenue per API call using LLM

## Example Usage

### Programmatic - Data Pricing

```python
from pricing_agent.estimate.estimator import PriceEstimator
from pricing_agent.schemas import ItemSpec, DataType, ListingType
from pricing_agent.utils.io import load_benchmark

benchmark = load_benchmark('bench.json')
estimator = PriceEstimator(benchmark)

spec = ItemSpec(
    data_type=DataType.CREDIT_CARD,
    region='ANY',
    listing_type=ListingType.RETAIL_LOOKUP,
    features={
        'freshness_days': 5,
        'completeness': 'full',
        'exclusivity': 'single_seller',
        'seller_reputation': 'escrow_guarantee',
        'demand': 'high',
        'vip_add': 10.0
    }
)

result = estimator.estimate(spec)
print(f"Price: ${result.est_price:.2f}")
```

### Programmatic - API Pricing

```python
from pricing_agent.extract.llm_client import LLMClient
from pricing_agent.estimate.api_pricing_agent import APIPricingAgent
from pricing_agent.ingest.api_parser import load_apis_from_file
import json

# Load APIs and benchmarks
apis = load_apis_from_file('fake_apis.md')
with open('bench.json') as f:
    benchmarks = json.load(f)

# Initialize agent
llm_client = LLMClient(api_key="YOUR_KEY")
agent = APIPricingAgent(llm_client, benchmarks)

# Analyze API
result = agent.estimate_api_revenue(apis[0])
print(f"API: {result.api_name}")
print(f"Revenue per call: ${result.estimated_revenue_per_call:.2f}")
print(f"Sensitivity: {result.sensitivity_level}")
```

## Configuration

### Environment Variables

```bash
# Required for LLM-based pricing
export LLM_API_KEY="your-openai-api-key-here"

# Optional (defaults to gpt-4.1-nano)
export LLM_MODEL="gpt-4.1-nano"
```

### API Definition Format

APIs are defined in markdown with Python dataclasses:

```markdown
# =========================================================
# 1) API Name
# =========================================================

```python
@dataclass
class APINameInput:
    param1: str
    param2: Optional[int] = None

@dataclass
class APINameOutput:
    field1: str
    field2: List[str]
```
```

## Key Differences

| Feature | Data Pricing | API Pricing |
|---------|-------------|-------------|
| **Input** | Data type specification | API definition (inputs/outputs) |
| **Output** | Price per record | Revenue per API call |
| **Use Case** | Breach valuation | API monetization risk |
| **Benchmark Usage** | Direct pricing | Reference for exposed data |

Both frameworks share:
- Same LLM client
- Same benchmark data
- Same data type taxonomy
- Same infrastructure

## Files

- `bench.json` - Pricing benchmarks (78 entries)
- `evidence.json` - Extracted price evidence
- `fake_apis.md` - Sample API definitions (14 APIs)
- `repo_docs/` - Source documents
- `CLI_COMMANDS.md` - Command reference

## Notes

- The API pricing framework **builds on top of** the data pricing framework
- Both use the same benchmark data for consistency
- LLM-based pricing requires API key
- Rule-based pricing works offline
- Benchmarks are created from your source documents
