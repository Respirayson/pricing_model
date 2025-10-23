# CLI Commands

## Quick Reference

| Command | Purpose | API Key Required |
|---------|---------|------------------|
| `run-pipeline` | Extract pricing data from documents | ✅ Yes (for LLM extraction) |
| `rule-estimate` | Rule-based price estimation | ❌ No |
| `llm-estimate` | LLM-based price estimation | ✅ Yes |
| `content-estimate` | **Deep content analysis of API responses** | ✅ **Yes (Required)** |
| `price-apis` | Analyze API endpoints | ✅ Yes |

---

## Pipeline Commands

> **Note:** You don't need to pass `--api-key` every time if you've set it as an environment variable.  
> 
> **PowerShell (Windows):**
> ```powershell
> $env:LLM_API_KEY="your-openai-api-key-here"
> ```
> 
> **Bash/Zsh (Mac/Linux):**
> ```bash
> export LLM_API_KEY="your-openai-api-key-here"
> ```
> 
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

## Content-Based Pricing Commands

**NEW:** LLM-powered deep content analysis - reads and understands actual data values, not just field names.

### Content Estimate (Single Query)

**Requirements:**
- API key (LLM required for content analysis)
- GPTInvoker properly configured (`pip install colorlog` if needed)

```bash
# Set API key (REQUIRED)
$env:LLM_API_KEY="your-api-key-here"

# Estimate value of telecom API query using deep content analysis
python -m pricing_agent.cli content-estimate test_vip_location_query.json

# Save detailed output with LLM justifications
python -m pricing_agent.cli content-estimate test_vip_location_query.json --output result.json

# Use custom model parameters (optional)
python -m pricing_agent.cli content-estimate your_query.json --model-params data/model_params.json
```

**What the LLM analyzes:**
- Reads actual data values (e.g., `"job_title": "CFO"` → high-value target)
- Understands context (corporate executive vs. anonymous user)
- Analyzes attack potential (location enables stalking)
- Calculates timestamp freshness (recent vs. stale data)
- Identifies legal jurisdiction and enforcement risk

**Example outputs:**
- VIP location query: ~$150 (Target: 9/10, Sensitivity: 8.5/10)
- Bulk billing query: ~$45 (Target: 2/10, Sensitivity: 1/10)

## API Pricing Commands

### Price APIs
```bash
pricing-agent price-apis fake_apis.md --api-key YOUR_KEY --benchmark-file bench.json
```

### Price APIs (save output)
```bash
pricing-agent price-apis fake_apis.md --api-key YOUR_KEY --benchmark-file bench.json --output results.json
```

---

## Troubleshooting

### Content-Estimate Errors

**Error: "LLM is required for content-based pricing"**
- **Cause:** API key not set or GPTInvoker unavailable
- **Fix:** 
  ```bash
  # Set API key
  $env:LLM_API_KEY="your-key"
  
  # Install missing dependency
  pip install colorlog
  ```

**Error: "Content analysis failed after 3 attempts"**
- **Cause:** LLM API connection issues or invalid response
- **Fix:** Check your API key is valid and has credits

**Error: "ModuleNotFoundError: No module named 'colorlog'"**
- **Fix:** `pip install colorlog`

### Performance Notes

- **Content-estimate:** ~3-5 seconds per query (LLM analysis)
- **Cost:** ~$0.01 per query (varies by LLM provider)
- **Accuracy:** 85-90% (vs. 60-70% with heuristics)

### Best Practices

1. **Batch processing:** Set API key once at session start
   ```bash
   $env:LLM_API_KEY="your-key"
   # Now run multiple queries without resetting
   ```

2. **Save outputs:** Always use `--output` to keep analysis results
   ```bash
   python -m pricing_agent.cli content-estimate query.json -o result.json
   ```

3. **Review justifications:** Check LLM reasoning in variable_scores for quality assurance
