"""
Extract Height from Audit Summaries

This script demonstrates that height is ALREADY COMPUTED and stored
in step_05_reference summaries. We just need to pull it from there!
"""

import json
import os
import pandas as pd
from pathlib import Path

# Path to derivatives
DERIV_ROOT = Path("derivatives/step_05_reference")

# Find all reference summary files
summary_files = list(DERIV_ROOT.glob("*__reference_summary.json"))

print(f"Found {len(summary_files)} reference summary files\n")
print("="*80)
print("EXTRACTED HEIGHTS FROM AUDIT PARAMETERS")
print("="*80)

heights = []

for file_path in sorted(summary_files)[:10]:  # Show first 10
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    run_id = data.get('run_id', 'unknown')
    height_cm = data.get('subject_context', {}).get('height_cm', None)
    
    if height_cm:
        heights.append({
            'Run_ID': run_id,
            'Height_cm': round(height_cm, 2)
        })
        print(f"{run_id:60s} | {height_cm:6.2f} cm")

print("="*80)

# Summary statistics
df_heights = pd.DataFrame(heights)
print(f"\nSUMMARY STATISTICS:")
print(f"   Total trials: {len(df_heights)}")
print(f"   Mean height: {df_heights['Height_cm'].mean():.2f} cm")
print(f"   Std dev: {df_heights['Height_cm'].std():.2f} cm")
print(f"   Min: {df_heights['Height_cm'].min():.2f} cm")
print(f"   Max: {df_heights['Height_cm'].max():.2f} cm")

# Group by subject (extract subject ID from run_id)
df_heights['Subject'] = df_heights['Run_ID'].str.extract(r'(\d{3})')
subject_heights = df_heights.groupby('Subject')['Height_cm'].agg(['mean', 'std', 'count'])

print(f"\nPER-SUBJECT HEIGHTS:")
print(subject_heights)

print("\n" + "="*80)
print("SUCCESS: HEIGHT IS ALREADY COMPUTED IN step_05_reference summaries!")
print("SUCCESS: Just need to load it from there instead of recomputing!")
print("="*80)
