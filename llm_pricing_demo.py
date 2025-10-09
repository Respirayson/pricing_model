import json
import os
import sys
from pricing_agent.estimate.estimator import PriceEstimator
from pricing_agent.estimate.llm_pricing_agent import LLMPricingAgent, HybridPricingAgent
from pricing_agent.schemas import ItemSpec, DataType, ListingType
from pricing_agent.extract.llm_client import LLMClient
from pricing_agent.utils.io import load_benchmark


def load_benchmark_raw(file_path):
    """Load benchmark data as raw JSON."""
    with open(file_path, 'r') as f:
        return json.load(f)


def demo_llm_pricing():
    """Demonstrate LLM-based pricing agent."""
    
    print("🤖 LLM-Based Pricing Agent Demo")
    print("=" * 50)
    
    # Initialize components
    print("Loading benchmark data...")
    benchmark = load_benchmark('bench.json')
    benchmark_raw = load_benchmark_raw('bench.json')
    
    # Initialize LLM client
    llm_client = LLMClient(os.getenv('LLM_API_KEY'), 'gpt-4.1-nano')
    
    # Initialize agents
    rule_estimator = PriceEstimator(benchmark)
    llm_agent = LLMPricingAgent(llm_client, benchmark_raw)
    hybrid_agent = HybridPricingAgent(rule_estimator, llm_agent)
    
    print(f"Loaded {len(benchmark)} benchmark rows")
    print()
    
    # Example 1: High-quality credit card
    print("1. High-Quality Credit Card Analysis:")
    print("-" * 40)
    
    spec1 = ItemSpec(
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
    
    market_context1 = {
        'current_trend': 'increasing',
        'recent_breaches': 'high_activity',
        'law_enforcement': 'moderate_pressure',
        'market_sentiment': 'bullish'
    }
    
    result1 = hybrid_agent.estimate_price(spec1, market_context=market_context1)
    
    print(f"Rule-based Price: ${result1['rule_based_price']:.2f}")
    llm_price = result1.get('llm_determined_price')
    print(f"LLM-determined Price: ${llm_price:.2f}" if llm_price is not None else "LLM-determined Price: N/A")
    hybrid_price = result1.get('hybrid_price')
    print(f"Hybrid Price: ${hybrid_price:.2f}" if hybrid_price is not None else "Hybrid Price: N/A")
    llm_confidence = result1.get('llm_confidence')
    print(f"LLM Confidence: {llm_confidence:.2f}" if llm_confidence is not None else "LLM Confidence: N/A")
    print(f"Key Factors: {', '.join(result1.get('llm_key_factors', []))}")
    print()
    
    # Example 2: Standard fullz
    print("2. Standard Fullz Analysis:")
    print("-" * 40)
    
    spec2 = ItemSpec(
        data_type=DataType.FULLZ,
        region='ANY',
        listing_type=ListingType.RETAIL_LOOKUP,
        features={
            'freshness_days': 30,
            'completeness': 'standard',
            'exclusivity': 'limited',
            'seller_reputation': 'verified',
            'demand': 'normal',
            'vip_add': 0.0
        }
    )
    
    market_context2 = {
        'current_trend': 'stable',
        'recent_breaches': 'normal_activity',
        'law_enforcement': 'low_pressure',
        'market_sentiment': 'neutral'
    }
    
    result2 = hybrid_agent.estimate_price(spec2, market_context=market_context2)
    
    print(f"Rule-based Price: ${result2['rule_based_price']:.2f}")
    llm_price = result2.get('llm_determined_price')
    print(f"LLM-determined Price: ${llm_price:.2f}" if llm_price is not None else "LLM-determined Price: N/A")
    hybrid_price = result2.get('hybrid_price')
    print(f"Hybrid Price: ${hybrid_price:.2f}" if hybrid_price is not None else "Hybrid Price: N/A")
    llm_confidence = result2.get('llm_confidence')
    print(f"LLM Confidence: {llm_confidence:.2f}" if llm_confidence is not None else "LLM Confidence: N/A")
    print(f"Key Factors: {', '.join(result2.get('llm_key_factors', []))}")
    print()
    
    # Example 3: Premium bank login
    print("3. Premium Bank Login Analysis:")
    print("-" * 40)
    
    spec3 = ItemSpec(
        data_type=DataType.BANK_LOGIN,
        region='ANY',
        listing_type=ListingType.ACCOUNT_ACCESS,
        features={
            'freshness_days': 10,
            'completeness': 'full',
            'exclusivity': 'single_seller',
            'seller_reputation': 'escrow_guarantee',
            'demand': 'high',
            'vip_add': 50.0
        }
    )
    
    market_context3 = {
        'current_trend': 'increasing',
        'recent_breaches': 'high_activity',
        'law_enforcement': 'high_pressure',
        'market_sentiment': 'cautious'
    }
    
    result3 = hybrid_agent.estimate_price(spec3, market_context=market_context3)
    
    print(f"Rule-based Price: ${result3['rule_based_price']:.2f}")
    llm_price = result3.get('llm_determined_price')
    print(f"LLM-determined Price: ${llm_price:.2f}" if llm_price is not None else "LLM-determined Price: N/A")
    hybrid_price = result3.get('hybrid_price')
    print(f"Hybrid Price: ${hybrid_price:.2f}" if hybrid_price is not None else "Hybrid Price: N/A")
    llm_confidence = result3.get('llm_confidence')
    print(f"LLM Confidence: {llm_confidence:.2f}" if llm_confidence is not None else "LLM Confidence: N/A")
    print(f"Key Factors: {', '.join(result3.get('llm_key_factors', []))}")
    print()
    
    print("=" * 50)
    print("💡 LLM Pricing Agent Features:")
    print("- Considers market context and trends")
    print("- Analyzes data quality factors")
    print("- Provides detailed reasoning")
    print("- Compares to historical benchmarks")
    print("- Combines with rule-based estimates")
    print("- Offers confidence scoring")


if __name__ == "__main__":
    try:
        demo_llm_pricing()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
