"""
Test script to verify biomechanics scoring with neutralization.

This script validates:
1. Clean statistics are present in step_06 JSON
2. Biomechanics scorecard is computed correctly
3. Component weights sum correctly
4. High Gaga velocities are not penalized when using clean data
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils_nb07 import (
    load_all_runs,
    discover_json_files,
    load_json_safe,
    compute_overall_score,
    score_biomechanics,
    safe_get_path,
    safe_float
)


def test_single_run(run_id: str):
    """Test biomechanics scoring for a single run."""
    print(f"\n{'='*80}")
    print(f"Testing Run: {run_id}")
    print(f"{'='*80}\n")
    
    # Load data
    deriv_dir = PROJECT_ROOT / "derivatives"
    
    # Load step_06 data
    s06_file = deriv_dir / "step_06_kinematics" / f"{run_id}__audit_metrics.json"
    if not s06_file.exists():
        print(f"[ERROR] Step 06 file not found: {s06_file}")
        return False
    
    s06 = load_json_safe(str(s06_file))
    if not s06:
        print(f"[ERROR] Failed to load step 06 JSON")
        return False
    
    # Load step_02 for skeleton data
    s02_file = deriv_dir / "step_02_preprocess" / f"{run_id}__preprocess_summary.json"
    s02 = load_json_safe(str(s02_file)) if s02_file.exists() else {}
    
    steps = {
        "step_06": s06,
        "step_02": s02
    }
    
    s06 = steps.get("step_06", {})
    
    # Check 1: Clean statistics present
    print("CHECK 1: Clean Statistics Presence")
    print("-" * 80)
    clean_max_vel = safe_float(safe_get_path(s06, "clean_statistics.clean_statistics.max_deg_s"))
    raw_max_vel = safe_float(safe_get_path(s06, "metrics.angular_velocity.max"))
    
    if clean_max_vel > 0:
        print(f"[OK] Clean statistics found")
        print(f"   Raw Max Velocity:   {raw_max_vel:.2f} deg/s")
        print(f"   Clean Max Velocity: {clean_max_vel:.2f} deg/s")
        reduction = 100 * (raw_max_vel - clean_max_vel) / raw_max_vel if raw_max_vel > 0 else 0
        print(f"   Reduction:          {reduction:.2f}%")
    else:
        print(f"[WARN] Clean statistics not found (may not have high velocity events)")
        print(f"   Raw Max Velocity:   {raw_max_vel:.2f} deg/s")
    
    # Check 2: Biomechanics scorecard
    print("\nCHECK 2: Biomechanics Scorecard")
    print("-" * 80)
    
    biomech_score, scorecard = score_biomechanics(steps)
    
    print(f"Overall Biomechanics Score: {biomech_score:.2f}")
    print(f"\nComponent Breakdown:")
    
    for comp_name, comp_data in scorecard['components'].items():
        print(f"\n  {comp_name.replace('_', ' ').title()}:")
        print(f"    Score:               {comp_data['score']:.2f}")
        print(f"    Weight:              {comp_data['weight']:.0%}")
        print(f"    Weighted Contrib:    {comp_data['weighted_contribution']:.2f}")
        print(f"    Details:")
        for key, val in comp_data['details'].items():
            print(f"      {key}: {val}")
    
    print(f"\n  Neutralization Applied:")
    for key, val in scorecard['neutralization_applied'].items():
        if key != 'rationale':
            print(f"    {key}: {val}")
    
    # Check 3: Weight validation
    print("\nCHECK 3: Weight Validation")
    print("-" * 80)
    
    calculated_score = sum(
        comp['weighted_contribution'] 
        for comp in scorecard['components'].values()
    )
    
    diff = abs(calculated_score - biomech_score)
    if diff < 0.1:
        print(f"[OK] Weights validated")
        print(f"   Calculated: {calculated_score:.2f}")
        print(f"   Reported:   {biomech_score:.2f}")
        print(f"   Difference: {diff:.4f}")
    else:
        print(f"[ERROR] Weight mismatch!")
        print(f"   Calculated: {calculated_score:.2f}")
        print(f"   Reported:   {biomech_score:.2f}")
        print(f"   Difference: {diff:.4f}")
        return False
    
    # Check 4: High velocity handling
    print("\nCHECK 4: High Velocity Handling")
    print("-" * 80)
    
    burst_decision = safe_get_path(s06, "step_06_burst_decision.overall_status")
    velocity_source = scorecard['components']['physiological_plausibility']['details'].get('velocity_source')
    velocity_assessment = scorecard['components']['physiological_plausibility']['details'].get('velocity_assessment')
    
    print(f"Burst Decision:        {burst_decision}")
    print(f"Velocity Source:       {velocity_source}")
    print(f"Velocity Assessment:   {velocity_assessment}")
    
    if burst_decision == "ACCEPT_HIGH_INTENSITY":
        if velocity_source == "clean":
            print(f"[OK] High Gaga movement correctly handled with clean data")
        else:
            print(f"[WARN] High intensity but not using clean data")
        
        if biomech_score > 70:
            print(f"[OK] Score not overly penalized ({biomech_score:.2f})")
        else:
            print(f"[WARN] Score may be too low for legitimate movement ({biomech_score:.2f})")
    
    # Overall test result
    print(f"\n{'='*80}")
    print(f"[OK] Test completed successfully for {run_id}")
    print(f"{'='*80}\n")
    
    return True


def test_multiple_runs():
    """Test multiple runs to verify consistency."""
    print("\n" + "="*80)
    print("BIOMECHANICS SCORING VALIDATION TEST SUITE")
    print("="*80)
    
    # Find available runs
    deriv_dir = PROJECT_ROOT / "derivatives" / "step_06_kinematics"
    
    if not deriv_dir.exists():
        print(f"[ERROR] Derivatives directory not found: {deriv_dir}")
        return
    
    json_files = list(deriv_dir.glob("*__audit_metrics.json"))
    
    if not json_files:
        print(f"[ERROR] No audit JSON files found in {deriv_dir}")
        return
    
    print(f"\nFound {len(json_files)} runs to test")
    
    # Test first 3 runs
    tested = 0
    passed = 0
    
    for json_file in json_files[:3]:
        run_id = json_file.stem.replace("__audit_metrics", "")
        
        try:
            success = test_single_run(run_id)
            tested += 1
            if success:
                passed += 1
        except Exception as e:
            print(f"\n[ERROR] Error testing {run_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Runs Tested:  {tested}")
    print(f"Runs Passed:  {passed}")
    print(f"Success Rate: {100*passed/tested:.1f}%" if tested > 0 else "N/A")
    
    if passed == tested:
        print("\n[OK] All tests passed!")
    else:
        print(f"\n[WARN] {tested - passed} test(s) failed")


if __name__ == "__main__":
    test_multiple_runs()
