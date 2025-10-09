# Pricing Agent

A Python package for analyzing dark web pricing documents and estimating data breach pricing based on structured evidence. This tool processes curated local documents (PDFs, HTML, Markdown) to extract pricing intelligence and build pricing models.

## Features

- **Document Processing**: Extract text from PDFs, HTML, and Markdown files
- **Price Extraction**: Use regex and LLM-based extraction to find pricing information
- **Currency Normalization**: Convert prices to USD using historical exchange rates
- **Price Benchmarking**: Build statistical benchmarks (p10/p50/p90) by data type and region
- **Price Estimation**: Rule-based pricing model with transparent modifiers
- **CLI Interface**: Easy-to-use command-line tools for pipeline execution

## Environment Variables

The application requires the following environment variables:

- `LLM_API_KEY`: Your LLM provider API key (required for LLM-based pricing)
- `LLM_MODEL`: LLM model to use (optional, defaults to "gpt-4.1-nano")

You can set these in a `.env` file (copy from `.env.example`) or as system environment variables.

## Installation

### Quick Setup (Recommended)

```bash
# 1. Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 2. Install all dependencies
python -m pip install -r requirements.txt

# 3. Install package in development mode
python -m pip install -e .

# 4. Set up environment variables
cp .env.example .env
# Edit .env file and add your LLM_API_KEY
# Or set it directly:
export LLM_API_KEY="your-openai-api-key-here"
# On Windows:
set LLM_API_KEY=your-openai-api-key-here

# 5. Run setup script (optional)
python setup_environment.py
```

### Manual Installation

```bash
# Clone the repository
git clone <repository-url>
cd pricing_model

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install pydantic click requests beautifulsoup4 openai

# Install in development mode
pip install -e .
```

## Quick Start

### 1. Prepare Your Documents

Create a `repo_docs/` directory and add your source documents:

```bash
mkdir repo_docs
# Add your PDF, HTML, or Markdown files here
```

### 2. Run the Pipeline

**Important**: You need to provide your LLM API key to run the pipeline.

```bash
# Run the full pipeline with API key
python -m pricing_agent.cli run-pipeline ./repo_docs evidence.json bench.json --api-key YOUR_API_KEY

# Or set environment variable
export LLM_API_KEY="your-api-key-here"
python -m pricing_agent.cli run-pipeline ./repo_docs evidence.json bench.json
```

**Expected Output:**
```
Starting pricing pipeline...
Initialized GPTInvoker with model gpt-4.1-nano
Processing documents in ./repo_docs...
  Processing: document1.md
  Processing: document2.md
  ...
Extracted 340 price evidence entries
Saved evidence to evidence.json
Built benchmark with 80 rows
Saved benchmark to bench.json
Pipeline completed successfully!
```

### 3. View Your Benchmark Data

```bash
# Show benchmark statistics
python -m pricing_agent.cli show-benchmark bench.json
```

### 4. Estimate Prices

The system provides multiple ways to estimate prices:

#### Method 1: Rule-Based Pricing (Traditional)

```bash
# Basic rule-based estimation
python -m pricing_agent.cli demo-estimate bench.json --data-type credit_card

# Full customization
python -m pricing_agent.cli demo-estimate bench.json \
  --data-type credit_card \
  --region ANY \
  --freshness-days 10 \
  --completeness full \
  --exclusivity single_seller \
  --seller-reputation escrow_guarantee \
  --demand normal \
  --vip-add 5
```

#### Method 2: LLM-Based Pricing Agent (Advanced)

```bash
# LLM-based price determination with market analysis
python -m pricing_agent.cli llm-estimate bench.json \
  --data-type credit_card \
  --use-llm \
  --api-key YOUR_API_KEY

# Full LLM pricing with customization
python -m pricing_agent.cli llm-estimate bench.json \
  --data-type credit_card \
  --region ANY \
  --freshness-days 5 \
  --completeness full \
  --exclusivity single_seller \
  --seller-reputation escrow_guarantee \
  --demand high \
  --vip-add 10 \
  --use-llm \
  --api-key YOUR_API_KEY
```

**LLM Pricing Agent Features:**
- 🤖 **Intelligent Analysis**: Uses LLM to analyze market conditions and data quality
- 📊 **Market Context**: Considers current trends, law enforcement pressure, market sentiment
- 🎯 **Detailed Reasoning**: Provides comprehensive explanation for price determination
- 📈 **Benchmark Comparison**: Compares to historical data and provides percentile rankings
- 🔄 **Hybrid Approach**: Combines rule-based and LLM-based estimates for accuracy

#### Method 2: Python Script

Create a file called `estimate_example.py`:

```python
from pricing_agent.estimate.estimator import PriceEstimator
from pricing_agent.schemas import ItemSpec, DataType, ListingType
from pricing_agent.utils.io import load_benchmark

# Load your benchmark
benchmark = load_benchmark('bench.json')
estimator = PriceEstimator(benchmark)

# Create specification for high-quality credit card
spec = ItemSpec(
    data_type=DataType.CREDIT_CARD,
    region='ANY',
    listing_type=ListingType.RETAIL_LOOKUP,
    features={
        'freshness_days': 5,      # Very fresh
        'completeness': 'full',   # Complete data
        'exclusivity': 'single_seller',  # Rare
        'seller_reputation': 'escrow_guarantee',  # Trusted
        'demand': 'high',         # High demand
        'vip_add': 10.0          # VIP premium
    }
)

# Estimate price
result = estimator.estimate(spec)

print(f"Base Price: ${result.base_sum:.2f}")
print(f"Final Price: ${result.est_price:.2f}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Modifiers Applied: {result.modifiers_applied}")
```

Run the script:
```bash
python estimate_example.py
```

#### Method 3: Interactive Python

```python
# Start Python and run interactively
python

# In Python:
from pricing_agent.estimate.estimator import PriceEstimator
from pricing_agent.schemas import ItemSpec, DataType, ListingType
from pricing_agent.utils.io import load_benchmark

# Load benchmark
benchmark = load_benchmark('bench.json')
estimator = PriceEstimator(benchmark)

# Quick credit card estimate
spec = ItemSpec(
    data_type=DataType.CREDIT_CARD,
    region='ANY',
    listing_type=ListingType.RETAIL_LOOKUP,
    features={'freshness_days': 30, 'completeness': 'standard', 'exclusivity': 'limited', 'seller_reputation': 'verified', 'demand': 'normal', 'vip_add': 0.0}
)

result = estimator.estimate(spec)
print(f"Credit Card Price: ${result.est_price:.2f}")
```

## Data Types

The system recognizes the following data types (based on your extracted benchmark):

### Primary Data Types
- **`credit_card`**: Credit card information ($1-$310, median ~$22-65)
- **`fullz`**: Complete identity packages ($8-$6,500, median ~$14-25)
- **`bank_login`**: Bank account credentials ($10-$2,200, median ~$50-500)
- **`gov_id_scan`**: Government ID documents ($150-$50M, median ~$100-200)
- **`medical_record`**: Medical records ($180-$400, median ~$180-400)

### Secondary Data Types
- **`consumer_account`**: Consumer account credentials ($14-$120, median ~$14-20)
- **`corporate_access`**: Corporate system access ($1,000)
- **`pii_core`**: Core personally identifiable information ($200)
- **`contact`**: Contact information ($50)
- **`other`**: Other types of data ($60-$1,700, median ~$60-425)

### Price Ranges (from your benchmark)
- **Credit Cards**: $1-$310 (most common: $17.36-$65)
- **Fullz**: $8-$6,500 (most common: $14-$25)
- **Bank Logins**: $10-$2,200 (most common: $50-$500)
- **Government IDs**: $150-$50,000,000 (most common: $100-$200)
- **Medical Records**: $180-$400

## Listing Types

- `retail_lookup`: Individual record lookups
- `bulk_dump`: Large datasets
- `account_access`: Account credentials
- `document_scan`: Scanned documents

## Price Modifiers

The pricing model applies the following modifiers:

### Freshness Factor
- < 30 days: 1.0 (no change)
- 1-6 months: 0.5
- > 6 months: 0.2

### Completeness Factor
- Fragment: 0.4
- Standard: 1.0
- Full: 1.2

### Exclusivity Factor
- Widely leaked: 0.5
- Limited: 1.0
- Single seller: 1.5

### Packaging Factor
- Retail lookup: 1.5
- Bulk dump: 0.3
- Account access: 1.0
- Document scan: 1.2

### Reputation Factor
- Unknown: 0.9
- Verified: 1.0
- Escrow guarantee: 1.2

### Demand Factor
- Low: 0.8
- Normal: 1.0
- High: 1.1
- Spike: 1.3

## Pricing Models

### Rule-Based Pricing Model

```
Final Price = [Σ Base Components] × Freshness × Completeness × Exclusivity × Packaging × Reputation × Demand + VIP_add
```

Where:
- Base Components come from price benchmark medians (p50)
- All modifiers are multiplicative except VIP_add (additive)
- Final price is guaranteed to be non-negative

### LLM-Based Pricing Agent

The LLM pricing agent provides a comprehensive approach that:

1. **Analyzes Market Context**: Considers current trends, law enforcement pressure, market sentiment
2. **Evaluates Data Quality**: Assesses completeness, freshness, exclusivity, and seller reputation
3. **Compares to Benchmarks**: Uses historical data to provide percentile rankings
4. **Provides Reasoning**: Explains the price determination with detailed analysis
5. **Offers Confidence Scoring**: Indicates reliability of the price estimate

**LLM Agent Output Includes:**
- Determined price with confidence range
- Detailed reasoning and key factors
- Market conditions assessment
- Quality evaluation
- Comparison to historical benchmarks
- Hybrid pricing (combines rule-based + LLM estimates)

## Example Workflow Commands

Here's a complete end-to-end workflow showing how to use the pricing agent:

### 1. Web Scraping Dark Web Pricing Data

```bash
# Scrape dark web pricing information from configured sources
python -m pricing_agent.cli scrape-web --output-dir ./repo_docs --delay 2.0
```

**Expected Output:**
```
Starting web scraping...
Successfully scraped 5 sources:
  - ./repo_docs/dark_web_prices_2023.html
  - ./repo_docs/breach_data_costs.html
  ...
```

### 2. Run the Complete Pipeline

```bash
# Process all documents, extract pricing evidence, and build benchmark
python -m pricing_agent.cli run-pipeline ./repo_docs evidence.json bench.json
```

**Expected Output:**
```
Starting pricing pipeline...
Initialized GPTInvoker with model gpt-4.1-nano
Processing documents in ./repo_docs...
  Processing: comparitech_dark_web_prices.md
  Processing: privacy_affairs_2023.md
  ...
Extracted 340 price evidence entries
Saved evidence to evidence.json
Built benchmark with 80 rows
Saved benchmark to bench.json
Pipeline completed successfully!
```

### 3. View Benchmark Statistics

```bash
# Display the extracted pricing benchmarks
python -m pricing_agent.cli show-benchmark bench.json
```

**Expected Output:**
```
Benchmark contains 80 rows:

  credit_card | retail_lookup | ANY
    n=45, p10=$17.36, p50=$65.00, p90=$310.00
    Last seen: 2023-12-15

  fullz | retail_lookup | ANY
    n=38, p10=$14.00, p50=$25.00, p90=$6500.00
    Last seen: 2023-12-15
  ...
```

### 4a. Rule-Based Price Estimation

```bash
# Basic price estimation using rule-based model
python -m pricing_agent.cli demo-estimate bench.json \
  --data-type credit_card \
  --region ANY \
  --freshness-days 10 \
  --completeness full \
  --exclusivity single_seller \
  --seller-reputation escrow_guarantee \
  --demand normal \
  --vip-add 5
```

**Expected Output:**
```json
{
  "base_sum": 65.00,
  "est_price": 142.35,
  "modifiers_applied": {
    "freshness": 1.0,
    "completeness": 1.2,
    "exclusivity": 1.5,
    "packaging": 1.5,
    "reputation": 1.2,
    "demand": 1.0
  },
  "components_used": ["credit_card"],
  "confidence": 0.85,
  "spec": {
    "data_type": "credit_card",
    "region": "ANY",
    "features": {
      "freshness_days": 10,
      "completeness": "full",
      "exclusivity": "single_seller",
      "seller_reputation": "escrow_guarantee",
      "demand": "normal",
      "vip_add": 5
    }
  }
}
```

### 4b. LLM-Based Price Estimation (Advanced)

```bash
# Use LLM-powered pricing agent with market analysis
python -m pricing_agent.cli llm-estimate bench.json \
  --data-type credit_card \
  --region ANY \
  --freshness-days 5 \
  --completeness full \
  --exclusivity single_seller \
  --seller-reputation escrow_guarantee \
  --demand high \
  --vip-add 10 \
  --use-llm \
  --api-key YOUR_API_KEY
```

**Expected Output:**
```json
{
  "pricing_method": "hybrid",
  "rule_based_price": 147.50,
  "llm_determined_price": 155.00,
  "hybrid_price": 151.25,
  "llm_confidence": 0.82,
  "llm_reasoning": "High-quality fresh credit card data with full information from trusted seller. Market shows strong demand. Premium justified by exclusivity and freshness.",
  "llm_key_factors": [
    "Data freshness (5 days) - very recent",
    "Full completeness with all card details",
    "Single seller exclusivity increases value",
    "Trusted seller with escrow guarantee",
    "High current demand in market"
  ],
  "price_range": {
    "low": 135.00,
    "high": 170.00
  },
  "market_conditions": {
    "current_trend": "stable",
    "law_enforcement": "moderate_pressure",
    "market_sentiment": "neutral"
  },
  "quality_assessment": {
    "data_quality_score": 0.9,
    "seller_trust_score": 0.85,
    "market_positioning": "premium"
  },
  "comparison_to_benchmarks": {
    "percentile": "75th",
    "above_median": true,
    "reasoning": "Price is above median due to premium quality factors"
  }
}
```

### Complete Workflow Example

```bash
# Complete end-to-end workflow in sequence:

# Step 1: Set API key
export LLM_API_KEY="your-openai-api-key-here"

# Step 2: Scrape web data (if you need fresh data)
python -m pricing_agent.cli scrape-web --output-dir ./repo_docs

# Step 3: Run the pipeline to build benchmarks
python -m pricing_agent.cli run-pipeline ./repo_docs evidence.json bench.json

# Step 4: View the benchmarks
python -m pricing_agent.cli show-benchmark bench.json

# Step 5: Estimate prices with LLM
python -m pricing_agent.cli llm-estimate bench.json \
  --data-type credit_card \
  --use-llm
```

## Configuration

### Required Setup

1. **Install Dependencies**:
```bash
pip install colorlog openai pydantic click requests beautifulsoup4
```

2. **Set API Key** (Required for pipeline):
```bash
export LLM_API_KEY="your-api-key-here"
# Or pass directly: --api-key YOUR_API_KEY
```
