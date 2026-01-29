"""
Diagnostic script to check pipeline completeness.

This script helps identify which pipeline steps are missing for each recording.
Run this before notebook 08 to understand what data is available.
"""

import os
import glob
from collections import defaultdict

# Adjust this path to your project root
PROJECT_ROOT = r"c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga"
DERIV_ROOT = os.path.join(PROJECT_ROOT, "derivatives")

print("="*80)
print("PIPELINE COMPLETENESS DIAGNOSTIC")
print("="*80)
print(f"\nSearching in: {DERIV_ROOT}\n")

# Expected file patterns
EXPECTED_FILES = {
    "step_01": "__step01_loader_report.json",
    "step_02": "__preprocess_summary.json",
    "step_03": "__resample_summary.json",
    "step_04": "__filtering_summary.json",
    "step_05": "__reference_summary.json",
    "step_06": "__outlier_validation.json"
}

# Search for JSON files in each step folder
all_files = defaultdict(list)

for step_name, suffix in EXPECTED_FILES.items():
    step_folder = os.path.join(DERIV_ROOT, f"{step_name}_*")
    matching_folders = glob.glob(step_folder)
    
    for folder in matching_folders:
        # Special handling for step_06 which has ultimate/ subfolder
        if step_name == "step_06":
            search_path = os.path.join(folder, "ultimate", f"*{suffix}")
        else:
            search_path = os.path.join(folder, f"*{suffix}")
        
        files = glob.glob(search_path)
        all_files[step_name].extend(files)

# Extract run IDs from filenames
runs = defaultdict(lambda: defaultdict(bool))

for step_name, files in all_files.items():
    print(f"{step_name}: Found {len(files)} files")
    for filepath in files:
        filename = os.path.basename(filepath)
        # Extract run_id by removing the suffix
        run_id = filename.replace(EXPECTED_FILES[step_name], "")
        runs[run_id][step_name] = True

print(f"\n{'='*80}")
print(f"SUMMARY: {len(runs)} unique run IDs found")
print("="*80)

# Analyze completeness
complete_runs = []
incomplete_runs = []

for run_id, steps in sorted(runs.items()):
    steps_present = [s for s in ['step_01', 'step_02', 'step_03', 'step_04', 'step_05', 'step_06'] if steps.get(s)]
    steps_missing = [s for s in ['step_01', 'step_02', 'step_03', 'step_04', 'step_05', 'step_06'] if not steps.get(s)]
    
    # Check if complete (has step_01 AND step_06 at minimum)
    is_complete = steps.get('step_01', False) and steps.get('step_06', False)
    
    if is_complete:
        complete_runs.append(run_id)
    else:
        incomplete_runs.append((run_id, steps_missing))

print(f"\n[OK] COMPLETE RUNS: {len(complete_runs)}")
print("   (Has step_01 AND step_06 - minimum required for notebook 08)")
if complete_runs:
    for run_id in complete_runs[:5]:  # Show first 5
        print(f"   - {run_id[:70]}")
    if len(complete_runs) > 5:
        print(f"   ... and {len(complete_runs) - 5} more")

print(f"\n[!] INCOMPLETE RUNS: {len(incomplete_runs)}")
print("   (Missing step_01 or step_06 - will be skipped)")
if incomplete_runs:
    for run_id, missing in incomplete_runs[:5]:  # Show first 5
        print(f"   - {run_id[:70]}")
        print(f"     Missing: {missing}")
    if len(incomplete_runs) > 5:
        print(f"   ... and {len(incomplete_runs) - 5} more")

# Recommendations
print(f"\n{'='*80}")
print("RECOMMENDATIONS")
print("="*80)

if len(complete_runs) == 0:
    print("\n[!] NO COMPLETE RUNS FOUND!")
    print("\nYou need to run the full pipeline (notebooks 01-06) on at least one recording.")
    print("\nTo process a recording:")
    print("  1. Place CSV file in data/{subject_id}/{session_id}/")
    print("  2. Run notebook 01_parse_csv.ipynb")
    print("  3. Run notebook 02_preprocess.ipynb")
    print("  4. Run notebook 03_resample.ipynb")
    print("  5. Run notebook 04_filtering.ipynb")
    print("  6. Run notebook 05_reference.ipynb")
    print("  7. Run notebook 06_rotvec_omega.ipynb")
    print("  8. Then run notebook 08_engineering_physical_audit.ipynb")
elif len(incomplete_runs) > 0:
    print(f"\n[OK] You have {len(complete_runs)} complete run(s) ready for notebook 08.")
    print(f"[!] You have {len(incomplete_runs)} incomplete run(s) that will be skipped.")
    print("\nTo complete the incomplete runs:")
    print("  - Identify which steps are missing (see list above)")
    print("  - Re-run those specific notebooks for the affected recordings")
else:
    print(f"\n[OK] All {len(complete_runs)} runs are complete!")
    print("   You can run notebook 08_engineering_physical_audit.ipynb now.")

print(f"\n{'='*80}")
print("END OF DIAGNOSTIC")
print("="*80)
