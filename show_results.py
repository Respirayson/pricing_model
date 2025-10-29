import json

with open('voi_simulation_results.json') as f:
    results = json.load(f)

print("=" * 80)
print("VoI SIMULATION RESULTS SUMMARY")
print("=" * 80)
print()

for i, item in enumerate(results, 1):
    r = item['result']
    print(f"{i}. {item['test_case']}")
    print(f"   VoI:           ${r['V_ex_ante']:.2f} utility units")
    print(f"   USD Estimate:  ${r['USD_estimate']:.2f}")
    print(f"   95% CI:        [${r['price_low_usd']:.2f}, ${r['price_high_usd']:.2f}]")
    print(f"   Confidence:    {r['confidence']:.1%}")
    print(f"   Action:        {r['optimal_action_ex_ante']} -> {r['optimal_action_ex_post']}")
    if r['flags']:
        print(f"   Flags:         {', '.join(r['flags'][:2])}")
    print()

