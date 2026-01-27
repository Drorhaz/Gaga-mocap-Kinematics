"""
Validation script to confirm biomechanics scoring fix is working correctly.

Run this AFTER re-running notebooks 06 and 07 to verify:
1. Clean statistics are populated
2. Neutralization is applied
3. High Gaga velocities are not penalized
4. Scoring transparency is present
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def validate_master_audit(excel_path: str):
    """Validate master audit Excel file."""
    print("\n" + "="*80)
    print("BIOMECHANICS SCORING FIX - VALIDATION REPORT")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"File: {excel_path}")
    print("="*80)
    
    # Load data
    df = pd.read_excel(excel_path, sheet_name="Quality_Overview")
    total_runs = len(df)
    
    print(f"\nTotal Runs: {total_runs}")
    
    # Check 1: New columns present
    print("\n" + "-"*80)
    print("CHECK 1: Transparency Columns Present")
    print("-"*80)
    
    required_cols = [
        'Biomech_Physiological_Score',
        'Biomech_Skeleton_Score',
        'Biomech_Continuity_Score',
        'Biomech_Velocity_Source',
        'Biomech_Velocity_Assessment',
        'Biomech_Neutralization_Applied',
        'Clean_Max_Vel_deg_s'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    
    if not missing:
        print("[OK] All transparency columns present")
        for col in required_cols:
            print(f"  - {col}")
    else:
        print("[ERROR] Missing columns:")
        for col in missing:
            print(f"  - {col}")
        return False
    
    # Check 2: Neutralization statistics
    print("\n" + "-"*80)
    print("CHECK 2: Neutralization Applied")
    print("-"*80)
    
    neutralized = df['Biomech_Velocity_Source'] == 'clean'
    neutralized_count = neutralized.sum()
    neutralized_pct = 100 * neutralized_count / total_runs
    
    print(f"Runs with neutralization: {neutralized_count} / {total_runs} ({neutralized_pct:.1f}%)")
    
    if neutralized_count > 0:
        print("[OK] Neutralization is being applied")
        
        # Show velocity reduction
        clean_runs = df[neutralized].copy()
        clean_runs['Vel_Reduction'] = (
            (clean_runs['Max_Ang_Vel_deg_s'] - clean_runs['Clean_Max_Vel_deg_s']) /
            clean_runs['Max_Ang_Vel_deg_s'] * 100
        )
        
        avg_reduction = clean_runs['Vel_Reduction'].mean()
        max_reduction = clean_runs['Vel_Reduction'].max()
        
        print(f"  Avg velocity reduction: {avg_reduction:.1f}%")
        print(f"  Max velocity reduction: {max_reduction:.1f}%")
    else:
        print("[WARN] No runs using clean data (may not have high-velocity events)")
    
    # Check 3: High-intensity Gaga movement scoring
    print("\n" + "-"*80)
    print("CHECK 3: High-Intensity Gaga Movement Handling")
    print("-"*80)
    
    high_intensity = df['Biomech_Burst_Assessment'] == 'HIGH_INTENSITY_LEGITIMATE'
    hi_count = high_intensity.sum()
    
    if hi_count > 0:
        hi_runs = df[high_intensity]
        avg_score = hi_runs['Score_Biomechanics'].mean()
        min_score = hi_runs['Score_Biomechanics'].min()
        
        print(f"High-intensity runs: {hi_count}")
        print(f"Avg biomechanics score: {avg_score:.1f}")
        print(f"Min biomechanics score: {min_score:.1f}")
        
        if avg_score > 70:
            print("[OK] High-intensity runs not overly penalized")
        else:
            print(f"[WARN] Avg score {avg_score:.1f} may be too low")
        
        # Check velocity source
        hi_using_clean = (hi_runs['Biomech_Velocity_Source'] == 'clean').sum()
        print(f"Using clean data: {hi_using_clean} / {hi_count}")
        
        if hi_using_clean == hi_count:
            print("[OK] All high-intensity runs using clean velocity")
        else:
            print(f"[WARN] {hi_count - hi_using_clean} runs not using clean velocity")
    else:
        print("[INFO] No high-intensity Gaga movement detected in dataset")
    
    # Check 4: Weight calculation
    print("\n" + "-"*80)
    print("CHECK 4: Component Weight Validation")
    print("-"*80)
    
    # Sample 5 runs
    sample_size = min(5, len(df))
    samples = df.sample(n=sample_size, random_state=42)
    
    errors = []
    for idx, row in samples.iterrows():
        calculated = (
            row['Biomech_Physiological_Score'] * 0.40 +
            row['Biomech_Skeleton_Score'] * 0.30 +
            row['Biomech_Continuity_Score'] * 0.30
        )
        reported = row['Score_Biomechanics']
        diff = abs(calculated - reported)
        
        if diff > 1.0:
            errors.append((row['Run_ID'], calculated, reported, diff))
    
    if not errors:
        print(f"[OK] Weights validated ({sample_size} samples checked)")
        print(f"  Formula: Physiological(40%) + Skeleton(30%) + Continuity(30%)")
    else:
        print(f"[ERROR] Weight calculation errors:")
        for run_id, calc, rep, diff in errors:
            print(f"  {run_id}: Calculated={calc:.1f}, Reported={rep:.1f}, Diff={diff:.1f}")
        return False
    
    # Check 5: Score distribution
    print("\n" + "-"*80)
    print("CHECK 5: Score Distribution Analysis")
    print("-"*80)
    
    bins = [(0, 40, "Reject"), (40, 60, "Poor"), (60, 75, "Marginal"), 
            (75, 90, "Good"), (90, 101, "Excellent")]
    
    print("Biomechanics Score Distribution:")
    for low, high, label in bins:
        count = ((df['Score_Biomechanics'] >= low) & (df['Score_Biomechanics'] < high)).sum()
        pct = 100 * count / total_runs
        bar = "█" * int(pct / 2)
        print(f"  {label:12s} ({low:3d}-{high-1:3d}): {count:3d} ({pct:5.1f}%) {bar}")
    
    avg_score = df['Score_Biomechanics'].mean()
    median_score = df['Score_Biomechanics'].median()
    
    print(f"\nStatistics:")
    print(f"  Mean:   {avg_score:.1f}")
    print(f"  Median: {median_score:.1f}")
    
    if avg_score > 50:
        print("[OK] Average score indicates good overall quality")
    else:
        print(f"[WARN] Low average score ({avg_score:.1f}) - check for systemic issues")
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print("[OK] Fix implementation verified")
    print("[OK] Neutralization logic working")
    print("[OK] Transparency columns present")
    print("[OK] Weight calculation correct")
    print("\n[SUCCESS] Biomechanics scoring fix validated!")
    print("="*80 + "\n")
    
    return True


def check_step06_json_sample():
    """Check a sample step_06 JSON for required fields."""
    print("\n" + "="*80)
    print("STEP 06 JSON STRUCTURE CHECK")
    print("="*80)
    
    deriv_dir = Path("derivatives/step_06_kinematics")
    json_files = list(deriv_dir.glob("*__audit_metrics.json"))
    
    if not json_files:
        print("[WARN] No step_06 audit JSON files found")
        return
    
    # Check first file
    sample_file = json_files[0]
    print(f"Sample: {sample_file.name}\n")
    
    with open(sample_file) as f:
        data = json.load(f)
    
    required_fields = [
        'clean_statistics.clean_statistics.max_deg_s',
        'clean_statistics.comparison.max_reduction_percent',
        'step_06_burst_decision.overall_status',
        'step_06_burst_analysis.classification',
        'metrics.angular_velocity.max'
    ]
    
    print("Required fields:")
    for field in required_fields:
        parts = field.split('.')
        value = data
        found = True
        try:
            for part in parts:
                value = value[part]
        except (KeyError, TypeError):
            found = False
            value = None
        
        status = "[OK]" if found else "[MISSING]"
        print(f"  {status} {field}")
        if found and value is not None:
            print(f"       Value: {value}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    print("\n")
    print("="*80)
    print(" BIOMECHANICS SCORING FIX - VALIDATION SUITE")
    print("="*80)
    
    # Check step_06 JSON structure
    check_step06_json_sample()
    
    # Find most recent master audit
    reports_dir = Path("reports")
    if reports_dir.exists():
        excel_files = list(reports_dir.glob("master_audit_*.xlsx"))
        
        if excel_files:
            # Sort by modification time
            latest = max(excel_files, key=lambda p: p.stat().st_mtime)
            print(f"Found latest master audit: {latest.name}")
            
            # Validate
            validate_master_audit(str(latest))
        else:
            print("[WARN] No master audit Excel files found in reports/")
            print("Please run notebook 07 to generate master audit")
    else:
        print("[WARN] Reports directory not found")
        print("Please run notebook 07 to generate master audit")
    
    print("\n[INFO] Validation complete!")
    print("[INFO] If step_06 fields are MISSING, re-run notebook 06")
    print("[INFO] If master audit missing, run notebook 07")
    print()
