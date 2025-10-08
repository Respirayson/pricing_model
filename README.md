# Pricing Agent

A Python package for analyzing dark web pricing documents and estimating data breach pricing based on structured evidence. This tool processes curated local documents (PDFs, HTML, Markdown) to extract pricing intelligence and build pricing models.

## ⚠️ Important Notice

This tool is designed for **security research and threat intelligence purposes only**. It operates exclusively on local, curated documents and does not access illicit markets or scrape dark web content. All analysis is performed on publicly available sources such as industry reports, news articles, and court filings.

## Features

- **Document Processing**: Extract text from PDFs, HTML, and Markdown files
- **Price Extraction**: Use regex and LLM-based extraction to find pricing information
- **Currency Normalization**: Convert prices to USD using historical exchange rates
- **Price Benchmarking**: Build statistical benchmarks (p10/p50/p90) by data type and region
- **Price Estimation**: Rule-based pricing model with transparent modifiers
- **CLI Interface**: Easy-to-use command-line tools for pipeline execution

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

# 4. Set your OpenAI API key
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

```bash
# Run the full pipeline: ingest -> extract -> aggregate
python -m pricing_agent.cli run_pipeline ./repo_docs evidence.json bench.json

# View the benchmark
python -m pricing_agent.cli show_benchmark bench.json
```

### 3. Estimate Prices

```bash
# Run a demo estimation
python -m pricing_agent.cli demo_estimate bench.json

# Custom estimation
python -m pricing_agent.cli demo_estimate bench.json \
  --data-type telecom_profile \
  --region CN \
  --freshness-days 20 \
  --completeness full \
  --exclusivity single_seller \
  --seller-reputation escrow_guarantee \
  --demand normal \
  --vip-add 10
```

## Data Types

The system recognizes the following data types:

- `contact`: Contact information (email, phone, address)
- `pii_core`: Core personally identifiable information (name, SSN, DOB)
- `fullz`: Complete identity packages
- `credit_card`: Credit card information
- `bank_login`: Bank account credentials
- `gov_id_scan`: Government ID documents
- `medical_record`: Medical records
- `consumer_account`: Consumer account credentials
- `corporate_access`: Corporate system access
- `telecom_subscription`: Telecom service subscriptions
- `telecom_profile`: Telecom customer profiles
- `other`: Other types of data

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

## Price Formula

```
Final Price = [Σ Base Components] × Freshness × Completeness × Exclusivity × Packaging × Reputation × Demand + VIP_add
```

Where:
- Base Components come from price benchmark medians (p50)
- All modifiers are multiplicative except VIP_add (additive)
- Final price is guaranteed to be non-negative

## Configuration

Set environment variables for configuration:

```bash
export LLM_API_KEY="your-api-key"
export LLM_MODEL="gpt-4"
export CHUNK_SIZE=3000
export CHUNK_OVERLAP=200
export MIN_CONFIDENCE=0.5
```

## Testing

Run the test suite:

```bash
pytest tests/
```

## Architecture

```
pricing_agent/
├── ingest/          # Document loading and text extraction
├── extract/         # Price detection and LLM extraction
├── normalize/       # Currency conversion and field mapping
├── aggregate/       # Benchmark building and modifiers
├── estimate/        # Price estimation models
├── eval/           # Evaluation metrics and harness
├── utils/          # Utility functions
└── cli.py          # Command-line interface
```

## Data Contracts

The system uses Pydantic v2 models for data validation:

- `PriceEvidence`: Individual price observations
- `PriceBenchRow`: Aggregated benchmark statistics
- `ItemSpec`: Specification for price estimation
- `EstimationResult`: Result of price estimation

## LLM Integration

The system includes a provider-agnostic LLM client with function calling support. Currently implemented as a stub - you'll need to provide your API key and implement the actual LLM calls.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is for educational and research purposes. Please ensure compliance with all applicable laws and regulations when using this tool.

## Disclaimer

This tool is provided for security research and threat intelligence purposes only. Users are responsible for ensuring compliance with all applicable laws and regulations. The authors do not endorse or encourage any illegal activities.
