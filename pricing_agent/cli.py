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
from .utils.io import save_evidence, save_benchmark, load_benchmark
from .ingest.loader import scrape_and_save_web_content


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
def demo_estimate(ctx, benchmark_file, data_type, region, freshness_days, 
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


if __name__ == '__main__':
    cli()
