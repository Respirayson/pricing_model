# CLI Commands

## Pipeline Commands

> **Note:** You don’t need to pass `--api-key` every time if you’ve set it as an environment variable.  
> Run:
> ```bash
> export LLM_API_KEY="your-openai-api-key-here"
> ```
> The CLI will automatically detect this key.

### Full Pipeline (ingest → extract → aggregate)
```bash
pricing-agent run-pipeline repo_docs/ evidence.json bench.json --api-key YOUR_KEY
```

### Web Scraping
```bash
pricing-agent scrape-web --output-dir repo_docs
```

## Data Pricing Commands

### Demo Estimate (rule-based)
```bash
pricing-agent rule-estimate bench.json --data-type telecom_profile --region CN
```

### LLM Estimate
```bash
pricing-agent llm-estimate bench.json --api-key YOUR_KEY --data-type credit_card
```

### Show Benchmark
```bash
pricing-agent show-benchmark bench.json
```

## API Pricing Commands

### Price APIs
```bash
pricing-agent price-apis fake_apis.md --api-key YOUR_KEY --benchmark-file bench.json
```

### Price APIs (save output)
```bash
pricing-agent price-apis fake_apis.md --api-key YOUR_KEY --benchmark-file bench.json --output results.json
```
