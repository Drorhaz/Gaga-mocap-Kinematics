"""
Check RAW Y-values in filtered parquet to understand units
"""

import pandas as pd
from pathlib import Path

# Load filtered parquet
deriv_path = Path("derivatives/step_04_filtering")
parquet_files = list(deriv_path.glob("*734*filtered.parquet"))

if parquet_files:
    file_path = parquet_files[0]
    print(f"Loading: {file_path.name}\n")
    
    df = pd.read_parquet(file_path)
    
    # Get head and foot Y columns
    head_y_col = [c for c in df.columns if 'Head__py' in c]
    foot_y_cols = [c for c in df.columns if any(m in c for m in 
                   ['LeftToeBase__py', 'RightToeBase__py', 'LeftFoot__py', 'RightFoot__py'])]
    all_y_cols = [c for c in df.columns if '__py' in c]
    
    # Reference window
    ref_start = 288
    ref_end = 408
    ref_df = df.iloc[ref_start:ref_end]
    
    print("="*80)
    print("RAW VALUES ANALYSIS (Filtered Parquet)")
    print("="*80)
    
    if head_y_col:
        head_max = ref_df[head_y_col].max().values[0]
        print(f"\nHead maximum (RAW): {head_max:.6f}")
    
    if foot_y_cols:
        foot_min = ref_df[foot_y_cols].min().min()
        print(f"Foot minimum (RAW): {foot_min:.6f}")
    
    if all_y_cols:
        global_min = ref_df[all_y_cols].min().min()
        print(f"Global minimum (RAW): {global_min:.6f}")
    
    print("\n" + "="*80)
    print("HEIGHT CALCULATIONS")
    print("="*80)
    
    if head_y_col and foot_y_cols:
        height_from_feet = head_max - foot_min
        print(f"\n[Using Foot Markers]")
        print(f"  Raw height: {height_from_feet:.6f}")
        print(f"  If units are METERS -> Height = {height_from_feet * 100:.2f} cm")
        print(f"  If units are CM already -> Height = {height_from_feet:.2f} cm")
    
    if head_y_col:
        height_from_zero = head_max - 0
        print(f"\n[Assuming Floor at Y=0]")
        print(f"  Raw head height: {head_max:.6f}")
        print(f"  If units are METERS -> Height = {height_max * 100:.2f} cm")
        print(f"  If units are CM already -> Height = {head_max:.2f} cm")
    
    print("\n" + "="*80)
    print("SAMPLE Y-VALUES (first frame in reference window)")
    print("="*80)
    
    print(f"\nFrame {ref_start}:")
    for col in sorted(all_y_cols)[:10]:  # Show first 10 markers
        val = ref_df[col].iloc[0]
        marker_name = col.replace('__py', '')
        print(f"  {marker_name:30s} Y = {val:10.4f}")
    
else:
    print("No filtered parquet found!")
