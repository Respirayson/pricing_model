"""Command-line interface for the pricing agent."""

import json
import sys
from pathlib import Path
from typing import List

import click

from .config import Config
from .schemas import ItemSpec, DataType, ListingType
from .ingest import iter_docs, extract_text, chunk_text
from .extract import sniff_prices, LLMClient, EvidenceExtractor
from .aggregate import build_price_bench
from .estimate import PriceEstimator
from .estimate.llm_pricing_agent import LLMPricingAgent, HybridPricingAgent
from .estimate.api_pricing_agent import APIPricingAgent
from .extract.llm_client import LLMClient
from .utils.io import save_evidence, save_benchmark, load_benchmark
from .ingest.loader import scrape_and_save_web_content
from .ingest.api_parser import load_apis_from_file


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """Pricing Agent - Analyze dark web pricing documents and estimate data breach prices."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config.from_env()


@cli.command()
@click.argument('repo_docs', type=click.Path(exists=True))
@click.argument('evidence_output', type=click.Path())
@click.argument('benchmark_output', type=click.Path())
@click.option('--api-key', help='LLM API key')
@click.pass_context
def run_pipeline(ctx, repo_docs, evidence_output, benchmark_output, api_key):
    """Run the full pipeline: ingest -> extract -> aggregate."""
    config = ctx.obj['config']
    
    if api_key:
        config.llm_api_key = api_key
    
    click.echo("Starting pricing pipeline...")
    
    # Initialize LLM client
    llm_client = LLMClient(config.llm_api_key, config.llm_model)
    extractor = EvidenceExtractor(llm_client)
    
    # Collect all evidence
    all_evidence = []
    
    click.echo(f"Processing documents in {repo_docs}...")
    
    for doc_info in iter_docs(repo_docs):
        click.echo(f"  Processing: {doc_info['file_name']}")
        
        # Extract text
        text = extract_text(doc_info)
        if not text:
            click.echo(f"    Warning: Could not extract text from {doc_info['file_name']}")
            continue
        
        # Chunk text
        chunks = chunk_text(text, config.chunk_size, config.chunk_overlap)
        
        # Extract evidence from each chunk
        for i, chunk in enumerate(chunks):
            # Quick regex check for price mentions
            price_mentions = sniff_prices(chunk)
            if not price_mentions:
                continue
            
            # Extract structured evidence
            evidence = extractor.extract_from_chunk(doc_info, chunk)
            all_evidence.extend(evidence)
    
    click.echo(f"Extracted {len(all_evidence)} price evidence entries")
    
    # Save evidence
    save_evidence(all_evidence, evidence_output)
    click.echo(f"Saved evidence to {evidence_output}")
    
    # Build benchmark
    benchmark = build_price_bench(all_evidence)
    click.echo(f"Built benchmark with {len(benchmark)} rows")
    
    # Save benchmark
    save_benchmark(benchmark, benchmark_output)
    click.echo(f"Saved benchmark to {benchmark_output}")
    
    click.echo("Pipeline completed successfully!")


@cli.command()
@click.argument('benchmark_file', type=click.Path(exists=True))
@click.option('--data-type', default='telecom_profile', help='Data type to estimate')
@click.option('--region', default='CN', help='Geographic region')
@click.option('--freshness-days', default=20, help='Days since data was created')
@click.option('--completeness', default='full', help='Data completeness level')
@click.option('--exclusivity', default='single_seller', help='Data exclusivity')
@click.option('--seller-reputation', default='escrow_guarantee', help='Seller reputation')
@click.option('--demand', default='normal', help='Market demand level')
@click.option('--vip-add', default=10.0, help='VIP premium to add')
@click.pass_context
def rule_estimate(ctx, benchmark_file, data_type, region, freshness_days, 
                 completeness, exclusivity, seller_reputation, demand, vip_add):
    """Run a demo price estimation."""
    config = ctx.obj['config']
    
    click.echo("Loading benchmark...")
    benchmark = load_benchmark(benchmark_file)
    
    if not benchmark:
        click.echo("Warning: Empty benchmark, estimation will be 0.0")
    
    # Create estimator
    estimator = PriceEstimator(benchmark)
    
    # Create item specification
    try:
        data_type_enum = DataType(data_type)
    except ValueError:
        click.echo(f"Error: Invalid data type '{data_type}'")
        click.echo(f"Valid types: {[dt.value for dt in DataType]}")
        sys.exit(1)
    
    spec = ItemSpec(
        data_type=data_type_enum,
        region=region,
        listing_type=ListingType.RETAIL_LOOKUP,
        features={
            "freshness_days": freshness_days,
            "completeness": completeness,
            "exclusivity": exclusivity,
            "seller_reputation": seller_reputation,
            "demand": demand,
            "vip_add": vip_add,
        }
    )
    
    # Estimate price
    click.echo("Estimating price...")
    result = estimator.estimate(spec)
    
    # Output result
    output = {
        "base_sum": result.base_sum,
        "est_price": result.est_price,
        "modifiers_applied": result.modifiers_applied,
        "components_used": [dt.value for dt in result.components_used],
        "confidence": result.confidence,
        "spec": {
            "data_type": spec.data_type.value,
            "region": spec.region,
            "features": spec.features
        }
    }
    
    click.echo(json.dumps(output, indent=2))


@cli.command()
@click.argument('benchmark_file', type=click.Path(exists=True))
@click.option('--data-type', default='credit_card', help='Data type to estimate')
@click.option('--region', default='ANY', help='Geographic region')
@click.option('--freshness-days', default=30, help='Days since data was created')
@click.option('--completeness', default='standard', help='Data completeness level')
@click.option('--exclusivity', default='limited', help='Data exclusivity')
@click.option('--seller-reputation', default='verified', help='Seller reputation')
@click.option('--demand', default='normal', help='Market demand level')
@click.option('--vip-add', default=0.0, help='VIP premium to add')
@click.option('--api-key', help='LLM API key for LLM pricing agent')
@click.pass_context
def llm_estimate(ctx, benchmark_file, data_type, region, freshness_days, 
                completeness, exclusivity, seller_reputation, demand, vip_add, 
                api_key):
    """Run LLM-based price estimation."""
    config = ctx.obj['config']
    
    if not api_key:
        api_key = config.llm_api_key
    
    if not api_key:
        click.echo("Error: API key required for LLM pricing agent. Use --api-key or set LLM_API_KEY environment variable.")
        sys.exit(1)
    
    click.echo("Loading benchmark...")
    benchmark = load_benchmark(benchmark_file)
    
    if not benchmark:
        click.echo("Warning: Empty benchmark, estimation will be 0.0")
    
    # Create rule-based estimator
    estimator = PriceEstimator(benchmark)
    
    # Create item specification
    try:
        data_type_enum = DataType(data_type)
    except ValueError:
        click.echo(f"Error: Invalid data type '{data_type}'")
        click.echo(f"Valid types: {[dt.value for dt in DataType]}")
        sys.exit(1)
    
    spec = ItemSpec(
        data_type=data_type_enum,
        region=region,
        listing_type=ListingType.RETAIL_LOOKUP,
        features={
            "freshness_days": freshness_days,
            "completeness": completeness,
            "exclusivity": exclusivity,
            "seller_reputation": seller_reputation,
            "demand": demand,
            "vip_add": vip_add,
        }
    )
    
    click.echo("Initializing LLM pricing agent...")
    
    # Load benchmark as raw JSON for LLM context
    import json
    with open(benchmark_file, 'r') as f:
        benchmark_raw = json.load(f)
    
    # Initialize LLM client and agent
    llm_client = LLMClient(api_key, config.llm_model)
    llm_agent = LLMPricingAgent(llm_client, benchmark_raw)
    hybrid_agent = HybridPricingAgent(estimator, llm_agent)
    
    # Market context
    market_context = {
        'current_trend': 'stable',
        'recent_breaches': 'normal_activity',
        'law_enforcement': 'moderate_pressure',
        'market_sentiment': 'neutral'
    }
    
    # Get hybrid estimate
    result = hybrid_agent.estimate_price(spec, market_context=market_context)
    
    # Output comprehensive result with clear final price
    final_price = result.get("llm_determined_price", result.get("hybrid_price", 0))
    
    output = {
        "FINAL_PRICE": final_price,
        "currency": "USD",
        "confidence": result.get("llm_confidence", result.get("rule_based_confidence", 0.0)),
        "analysis": {
            "reasoning": result.get("llm_reasoning"),
            "key_factors": result.get("llm_key_factors", []),
            "market_sentiment": result.get("market_sentiment")
        },
        "market_intelligence": {
            "market_conditions": result.get("market_conditions"),
            "quality_assessment": result.get("quality_assessment"),
            "price_range": result.get("price_range")
        },
        "benchmark_comparison": result.get("comparison_to_benchmarks"),
        "item_specification": {
            "data_type": spec.data_type.value,
            "region": spec.region,
            "freshness_days": spec.features.get("freshness_days"),
            "completeness": spec.features.get("completeness"),
            "exclusivity": spec.features.get("exclusivity")
        }
    }
    click.echo(json.dumps(output, indent=2))


@cli.command()
@click.argument('benchmark_file', type=click.Path(exists=True))
@click.pass_context
def show_benchmark(ctx, benchmark_file):
    """Show benchmark statistics."""
    benchmark = load_benchmark(benchmark_file)
    
    if not benchmark:
        click.echo("Benchmark is empty")
        return
    
    click.echo(f"Benchmark contains {len(benchmark)} rows:")
    click.echo()
    
    for row in benchmark:
        click.echo(f"  {row.data_type.value} | {row.listing_type.value} | {row.region or 'ANY'}")
        click.echo(f"    n={row.n}, p10=${row.p10:.2f}, p50=${row.p50:.2f}, p90=${row.p90:.2f}")
        if row.last_seen:
            click.echo(f"    Last seen: {row.last_seen}")
        click.echo()


@cli.command()
@click.option('--output-dir', default='repo_docs', help='Directory to save scraped content')
@click.option('--delay', default=2.0, help='Delay between requests in seconds')
@click.pass_context
def scrape_web(ctx, output_dir, delay):
    """Scrape pricing data from web sources."""
    click.echo("Starting web scraping...")
    
    try:
        saved_files = scrape_and_save_web_content(output_dir)
        
        if saved_files:
            click.echo(f"Successfully scraped {len(saved_files)} sources:")
            for file_path in saved_files:
                click.echo(f"  - {file_path}")
        else:
            click.echo("No content was scraped (all URLs are placeholders)")
            click.echo("To scrape real content, update the URLs in pricing_agent/ingest/web_scraper.py")
            
    except Exception as e:
        click.echo(f"Error during web scraping: {e}")
        raise click.Abort()


@cli.command()
@click.argument('api_definition_file', type=click.Path(exists=True))
@click.option('--api-key', help='LLM API key')
@click.option('--benchmark-file', type=click.Path(), help='Benchmark file for reference pricing')
@click.option('--output', '-o', type=click.Path(), help='Output file for results (JSON)')
@click.option('--limit', type=int, help='Limit number of APIs to analyze')
@click.pass_context
def price_apis(ctx, api_definition_file, api_key, benchmark_file, output, limit):
    """Estimate potential revenue per API call using LLM analysis."""
    config = ctx.obj['config']
    
    if api_key:
        config.llm_api_key = api_key
    
    if not config.llm_api_key:
        click.echo("Error: API key required. Use --api-key or set LLM_API_KEY environment variable.")
        sys.exit(1)
    
    if not benchmark_file:
        click.echo("Error: Benchmark file required. Use --benchmark-file")
        sys.exit(1)
    
    click.echo(f"Loading API definitions from {api_definition_file}...")
    
    # Load API definitions
    try:
        api_definitions = load_apis_from_file(api_definition_file)
        click.echo(f"Loaded {len(api_definitions)} API definitions")
    except Exception as e:
        click.echo(f"Error loading API definitions: {e}")
        raise click.Abort()
    
    if not api_definitions:
        click.echo("No API definitions found in file")
        return
    
    # Limit if requested
    if limit:
        api_definitions = api_definitions[:limit]
        click.echo(f"Limiting analysis to first {limit} APIs")
    
    # Load benchmark data if available
    benchmark_data = []
    if benchmark_file:
        click.echo(f"Loading benchmark data from {benchmark_file}...")
        try:
            with open(benchmark_file, 'r') as f:
                benchmark_data = json.load(f)
            click.echo(f"Loaded {len(benchmark_data)} benchmark entries")
        except Exception as e:
            click.echo(f"Warning: Could not load benchmark data: {e}")
    
    # Initialize LLM client and API pricing agent
    click.echo("Initializing API pricing agent...")
    llm_client = LLMClient(config.llm_api_key, config.llm_model)
    api_pricing_agent = APIPricingAgent(llm_client, benchmark_data)
    
    # Market context
    market_context = {
        'market_type': 'data_monetization',
        'regions': ['global', 'APAC', 'CN'],
        'use_cases': ['marketing', 'fraud', 'competitive_intelligence', 'identity_verification']
    }
    
    # Analyze APIs
    click.echo("\nAnalyzing APIs...\n")
    
    try:
        batch_result = api_pricing_agent.batch_estimate(api_definitions, market_context)
        
        # Display results
        click.echo("=" * 80)
        click.echo("API PRICING ANALYSIS RESULTS")
        click.echo("=" * 80)
        click.echo()
        
        click.echo(f"Total APIs Analyzed: {batch_result.total_apis}")
        click.echo(f"Total Potential Revenue: ${batch_result.total_potential_revenue:.2f}")
        click.echo(f"Average Revenue per Call: ${batch_result.average_revenue_per_call:.2f}")
        click.echo()
        
        if batch_result.highest_value_api:
            click.echo(f"Highest Value API: {batch_result.highest_value_api}")
        if batch_result.lowest_value_api:
            click.echo(f"Lowest Value API: {batch_result.lowest_value_api}")
        click.echo()
        
        # Revenue by sensitivity
        if batch_result.revenue_by_sensitivity:
            click.echo("Revenue by Sensitivity Level:")
            for sensitivity, revenue in sorted(batch_result.revenue_by_sensitivity.items()):
                click.echo(f"  {sensitivity}: ${revenue:.2f}")
            click.echo()
        
        # Individual API results
        click.echo("-" * 80)
        click.echo("INDIVIDUAL API RESULTS")
        click.echo("-" * 80)
        click.echo()
        
        for result in batch_result.results:
            click.echo(f"API: {result.api_name}")
            click.echo(f"  Revenue per Call: ${result.estimated_revenue_per_call:.2f}")
            click.echo(f"  Confidence: {result.confidence:.2%}")
            click.echo(f"  Sensitivity: {result.sensitivity_level}")
            click.echo(f"  Data Completeness: {result.data_completeness}")
            click.echo(f"  Market Demand: {result.market_demand}")
            
            if result.data_types_exposed:
                data_types_str = ", ".join([dt.value for dt in result.data_types_exposed])
                click.echo(f"  Data Types: {data_types_str}")
            
            if result.key_value_drivers:
                click.echo(f"  Key Value Drivers:")
                for driver in result.key_value_drivers:
                    click.echo(f"    - {driver}")
            
            if result.min_revenue_per_call is not None and result.max_revenue_per_call is not None:
                click.echo(f"  Price Range: ${result.min_revenue_per_call:.2f} - ${result.max_revenue_per_call:.2f}")
            
            if result.comparable_data_items:
                click.echo(f"  Comparable Benchmarks:")
                for item in result.comparable_data_items[:3]:
                    if isinstance(item, str):
                        click.echo(f"    - {item}")
                    else:
                        data_type = item.get('data_type', 'unknown')
                        p50 = item.get('p50', 0)
                        listing = item.get('listing_type', 'unknown')
                        click.echo(f"    - {data_type} ({listing}): ${p50:.2f}")
            
            click.echo()
        
        # Save to file if requested
        if output:
            click.echo(f"Saving results to {output}...")
            output_data = {
                "summary": {
                    "total_apis": batch_result.total_apis,
                    "total_potential_revenue": batch_result.total_potential_revenue,
                    "average_revenue_per_call": batch_result.average_revenue_per_call,
                    "highest_value_api": batch_result.highest_value_api,
                    "lowest_value_api": batch_result.lowest_value_api,
                    "revenue_by_sensitivity": batch_result.revenue_by_sensitivity
                },
                "api_results": [
                    {
                        "api_id": r.api_id,
                        "api_name": r.api_name,
                        "estimated_revenue_per_call": r.estimated_revenue_per_call,
                        "confidence": r.confidence,
                        "sensitivity_level": r.sensitivity_level,
                        "data_completeness": r.data_completeness,
                        "market_demand": r.market_demand,
                        "data_types_exposed": [dt.value for dt in r.data_types_exposed],
                        "use_cases": r.use_cases,
                        "risk_factors": r.risk_factors,
                        "reasoning": r.reasoning,
                        "key_value_drivers": r.key_value_drivers,
                        "min_revenue_per_call": r.min_revenue_per_call,
                        "max_revenue_per_call": r.max_revenue_per_call
                    }
                    for r in batch_result.results
                ]
            }
            
            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            click.echo(f"Results saved to {output}")
        
        click.echo("\nAnalysis complete!")
        
    except Exception as e:
        click.echo(f"Error during API pricing analysis: {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()


if __name__ == '__main__':
    cli()
