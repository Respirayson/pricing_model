import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from pricing_agent.estimate.voi_pricing_agent import VoIPricingAgent
from pricing_agent.extract.llm_client import LLMClient


def generate_basic_consumer_profile() -> Dict[str, Any]:
    return {
        "subscriber_id": "sub_789456123",
        "account_tier": "basic",
        "name": "John Smith",
        "phone": "+1-555-0123",
        "email": "jsmith@email.com",
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "90210"
        },
        "billing_summary": {
            "monthly_charge": 45.99,
            "data_usage_gb": 3.2,
            "voice_minutes": 250
        },
        "last_updated": (datetime.now() - timedelta(days=2)).isoformat()
    }


def generate_vip_executive_profile() -> Dict[str, Any]:
    return {
        "subscriber_id": "sub_VIP_992847",
        "account_tier": "premium_corporate",
        "name": "Sarah Chen",
        "job_title": "Chief Financial Officer",
        "employer": "TechCorp International Inc.",
        "phone": "+1-415-555-8800",
        "email": "schen@techcorp.com",
        "verified_identity": True,
        "address": {
            "street": "456 Executive Plaza",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        },
        "device_info": {
            "imei": "352099001761481",
            "sim_iccid": "8901410393928400001",
            "device_model": "iPhone 14 Pro"
        },
        "location_history": [
            {
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "latitude": 37.7749,
                "longitude": -122.4194,
                "accuracy_meters": 15
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
                "latitude": 37.7899,
                "longitude": -122.3988,
                "accuracy_meters": 20
            }
        ],
        "call_history": [
            {
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "direction": "outgoing",
                "duration_seconds": 420,
                "contact_name": "Board Member - Legal"
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
                "direction": "incoming",
                "duration_seconds": 180,
                "contact_name": "Bank of America - Private Client"
            }
        ],
        "billing_summary": {
            "monthly_charge": 299.99,
            "data_usage_gb": 45.8,
            "international_calls": 12
        },
        "last_updated": (datetime.now() - timedelta(hours=0.5)).isoformat()
    }


def generate_minimal_api_response() -> Dict[str, Any]:
    return {
        "status": "partial_data",
        "subscriber_id": "sub_333222111",
        "phone": "+1-555-9999",
        "account_status": "active",
        "note": "Limited data due to privacy restrictions"
    }


def generate_bulk_dataset_response() -> Dict[str, Any]:
    base_time = datetime.now() - timedelta(days=5)
    
    records = []
    for i in range(50):
        records.append({
            "subscriber_id": f"sub_bulk_{10000 + i}",
            "name": f"User {i}",
            "phone": f"+1-555-{2000 + i:04d}",
            "email": f"user{i}@example.com",
            "account_tier": "standard",
            "monthly_charge": 35.99,
            "data_usage_gb": 2.5 + (i % 10)
        })
    
    return {
        "dataset_id": "bulk_export_20251029",
        "record_count": 50,
        "records": records,
        "exported_at": base_time.isoformat()
    }


def run_simulation():
    print("=" * 80)
    print("VoI Pricing Model Simulation")
    print("=" * 80)
    print()
    
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("ERROR: LLM_API_KEY environment variable not set.")
        print("Please set it to your OpenAI API key:")
        print("  export LLM_API_KEY='your-api-key-here'")
        return
    else:
        llm_client = LLMClient(api_key=api_key)
    
    agent = VoIPricingAgent(llm_client=llm_client, model_params={"n_simulations": 1000})
    
    test_cases = [
        {
            "name": "Basic Consumer Profile",
            "description": "Low-value target with minimal sensitive data",
            "api_response": generate_basic_consumer_profile(),
            "metadata": {
                "data_type": "telecom_profile",
                "region": "US",
                "freshness_days": 2.0
            }
        },
        {
            "name": "VIP Executive Profile with Tracking",
            "description": "High-value target with real-time location and call history",
            "api_response": generate_vip_executive_profile(),
            "metadata": {
                "data_type": "telecom_profile",
                "region": "US",
                "freshness_days": 0.02  # ~30 minutes old
            }
        },
        {
            "name": "Minimal API Response",
            "description": "Failed or rate-limited query with minimal data",
            "api_response": generate_minimal_api_response(),
            "metadata": {
                "data_type": "telecom_subscription",
                "region": "US",
                "freshness_days": 0.0
            }
        },
        {
            "name": "Bulk Dataset (50 records)",
            "description": "Volume play - low per-record value but high count",
            "api_response": generate_bulk_dataset_response(),
            "metadata": {
                "data_type": "telecom_subscription",
                "region": "US",
                "freshness_days": 5.0
            }
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}/{len(test_cases)}: {test_case['name']}")
        print("-" * 80)
        print(f"Description: {test_case['description']}")
        print()
        
        # Estimate price
        result = agent.estimate_price(
            api_response=test_case['api_response'],
            query_id=f"sim_{i:03d}",
            metadata=test_case['metadata']
        )
        
        results.append({
            "test_case": test_case['name'],
            "result": result
        })
        
        # Print summary
        print_result_summary(result)
        print()
    
    print("\n" + "=" * 80)
    print("SIMULATION SUMMARY")
    print("=" * 80)
    print()
    
    for i, res in enumerate(results, 1):
        r = res['result']
        print(f"{i}. {res['test_case']}")
        print(f"   VoI:           ${r['V_ex_ante']:.2f} utility units")
        print(f"   USD Estimate:  ${r['USD_estimate']:.2f}")
        print(f"   Confidence:    {r['confidence']:.2%}")
        print(f"   Optimal Action: {r['optimal_action_ex_ante']} -> {r['optimal_action_ex_post']}")
        print()
    
    output_file = "voi_simulation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Detailed results saved to: {output_file}")
    print()
    

def print_result_summary(result: Dict[str, Any]):
    print("VoI ESTIMATION:")
    print(f"  V_ex_ante:       ${result['V_ex_ante']:.2f} utility units")
    print(f"  USD Estimate:    ${result['USD_estimate']:.2f}")
    print(f"  Confidence:      {result['confidence']:.1%}")
    print(f"  Freshness Factor: {result['freshness_factor']:.3f} (age: {result['freshness_days']:.1f} days)")
    print()
    
    print("DECISION ANALYSIS:")
    print(f"  Optimal Action (ex-ante):   {result['optimal_action_ex_ante']}")
    print(f"  Optimal Action (ex-post):   {result['optimal_action_ex_post']}")
    print()
    
    action_dist = result['simulation_stats']['action_distribution']
    sorted_actions = sorted(action_dist.items(), key=lambda x: x[1], reverse=True) # sort by frequency
    print("  Top Actions (frequency):")
    for action, freq in sorted_actions:
        print(f"    - {action:20s} {freq:.1%}")
    print()
    
    opt_action = result['optimal_action_ex_post']
    if opt_action in result['ex_post_params']['P_success']:
        print(f"  Ex-post Parameters for '{opt_action}':")
        print(f"    P(success):      {result['ex_post_params']['P_success'][opt_action]:.2%}")
        print(f"    E[Revenue]:      ${result['ex_post_params']['R_expected'][opt_action]:.2f}")
        print(f"    Cost:            ${result['ex_post_params']['C_cost'][opt_action]:.2f}")
        print(f"    Detection Risk:  {result['ex_post_params']['detection_risk'][opt_action]:.2%}")
        print()


if __name__ == "__main__":
    run_simulation()

