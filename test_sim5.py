#!/usr/bin/env python3
"""Quick test of simulation 5 chain logic."""

from common.chains import FORKED_CHAIN_DEFINITIONS, get_next_service_name

# Verify test_scenario_5 is in forked definitions
assert "test_scenario_5" in FORKED_CHAIN_DEFINITIONS, "test_scenario_5 not found in FORKED_CHAIN_DEFINITIONS"

chain_def = FORKED_CHAIN_DEFINITIONS["test_scenario_5"]
print(f"✓ test_scenario_5 found")
print(f"  Entry: {chain_def['entry']}")
print(f"  Branches: {len(chain_def['branches'])}")
print(f"  Join: {chain_def['join']}")
print(f"  Dynamic: {chain_def.get('dynamic', False)}")

# Calculate total chain length
total_services = 1  # ABPT
for branch in chain_def['branches']:
    total_services += len(branch)
total_services += 1  # TDICE join
print(f"  Total services in chain: {total_services}")

# Verify minimum chain length requirement (12)
assert total_services >= 12, f"Chain too short: {total_services} < 12"
print(f"✓ Chain length requirement met (>= 12)")

# Verify branch count (3-4)
num_branches = len(chain_def['branches'])
assert 3 <= num_branches <= 4, f"Invalid branch count: {num_branches} (must be 3-4)"
print(f"✓ Branch count requirement met (3-4 branches: {num_branches})")

# Test randomized path selection
print("\nTesting randomized path selection (10 runs):")
for i in range(10):
    next_service = get_next_service_name("ABPT", "test_scenario_5")
    print(f"  Run {i+1}: ABPT -> {next_service}")

print("\n✓ All tests passed!")
