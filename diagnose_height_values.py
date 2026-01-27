"""
Diagnostic: Check Actual Y Values in Reference Window

This will show us EXACTLY what floor_y and head_y_max are,
and what the scale factor should be.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# Load one of the derivative CSVs to check actual position values
csv_path = Path("derivatives/step_06_kinematics")
csv_files = list(csv_path.glob("*763*kinematics.csv"))

if csv_files:
    file_path = csv_files[0]
    print(f"Loading: {file_path.name}\n")
    
    df = pd.read_csv(file_path)
    
    # Get Y-position columns
    y_cols = [c for c in df.columns if '__py' in c]
    head_y_col = [c for c in df.columns if 'Head__py' in c]
    foot_y_cols = [c for c in df.columns if any(m in c for m in ['LeftToeBase__py', 'RightToeBase__py', 'LeftFoot__py', 'RightFoot__py'])]
    
    print("="*80)
    print("Y-AXIS POSITION ANALYSIS")
    print("="*80)
    
    # Take reference window (e.g., frames 288-408 = 2.4-3.4 seconds at 120 Hz)
    ref_start = 288
    ref_end = 408
    ref_df = df.iloc[ref_start:ref_end]
    
    print(f"\nReference window: frames {ref_start}-{ref_end}")
    print(f"Duration: {(ref_end - ref_start) / 120:.2f} seconds\n")
    
    # Check all Y values
    if y_cols:
        floor_all_markers = ref_df[y_cols].min().min()
        print(f"Floor (ALL markers minimum): {floor_all_markers:.3f}")
    
    if foot_y_cols:
        floor_feet_only = ref_df[foot_y_cols].min().min()
        print(f"Floor (FOOT markers only):   {floor_feet_only:.3f}")
    
    if head_y_col:
        head_max = ref_df[head_y_col].max().values[0]
        print(f"Head maximum:                {head_max:.3f}")
    
    print("\n" + "="*80)
    print("HEIGHT CALCULATIONS")
    print("="*80)
    
    # Method 1: All markers (CURRENT BUGGY METHOD)
    if y_cols and head_y_col:
        height_raw_all = head_max - floor_all_markers
        print(f"\n[METHOD 1] Using ALL markers as floor:")
        print(f"   Raw: {height_raw_all:.3f}")
        print(f"   If millimeters -> {height_raw_all * 0.1:.2f} cm")
        print(f"   If meters      -> {height_raw_all * 100:.2f} cm")
    
    # Method 2: Foot markers only (CORRECT METHOD)
    if foot_y_cols and head_y_col:
        height_raw_feet = head_max - floor_feet_only
        print(f"\n[METHOD 2] Using FOOT markers as floor:")
        print(f"   Raw: {height_raw_feet:.3f}")
        print(f"   If millimeters -> {height_raw_feet * 0.1:.2f} cm")
        print(f"   If meters      -> {height_raw_feet * 100:.2f} cm")
    
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)
    
    # Check sample value for unit detection
    sample_val = abs(df[y_cols[0]].iloc[0])
    print(f"\nSample Y value: {sample_val:.3f}")
    print(f"Unit detection: {'METERS' if sample_val < 50 else 'MILLIMETERS'}")
    print(f"Scale factor:   {'100' if sample_val < 50 else '0.1'}")
    
    # Expected height range
    print(f"\nExpected height: 160-180 cm")
    print(f"Actual computed: {height_raw_all * 0.1:.2f} cm (current method)")
    print(f"Difference:      {160 - (height_raw_all * 0.1):.2f} cm too short")
    
else:
    print("ERROR: No CSV files found in derivatives!")
