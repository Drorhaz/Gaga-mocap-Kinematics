"""
Quick test to verify utils_nb07.py can find your data.
"""

import sys
sys.path.insert(0, r"c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\src")

from utils_nb07 import load_all_runs, filter_complete_runs

DERIV_ROOT = r"c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\derivatives"

print("Testing data loading...")
print("="*80)

# Load all JSON files
all_runs = load_all_runs(DERIV_ROOT)
print(f"\nTotal runs found: {len(all_runs)}")

for run_id, steps in all_runs.items():
    print(f"\nRun ID: {run_id}")
    print(f"  Steps: {sorted(steps.keys())}")

# Filter to complete runs
runs_data = filter_complete_runs(all_runs, required_steps=["step_01", "step_06"])
print(f"\n{'='*80}")
print(f"Complete runs: {len(runs_data)}")

if len(runs_data) > 0:
    print("\nSUCCESS! Data loading works correctly.")
    print("You can now run notebook 08_engineering_physical_audit.ipynb")
else:
    print("\nFAILURE: No complete runs found.")
    print("Check that JSON files match expected naming patterns.")

print("="*80)
