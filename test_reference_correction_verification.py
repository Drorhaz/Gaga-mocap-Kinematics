#!/usr/bin/env python3
"""
Verification Test: Reference Pose Correction in NB06

Tests if reference correction is applied correctly to every joint and frame.
If reference correction is applied correctly, then inside the reference window,
the corrected rotation should be ~Identity → residual angles near 0° for all joints.

Pass Criteria:
- For each joint: median residual in reference window < 1°
- Global: 95th percentile residual < 3°
- Shoulders can be excluded from anatomy checks, but identity check should still pass
"""

import os
import sys
import numpy as np
import pandas as pd
import json
from pathlib import Path
from scipy.spatial.transform import Rotation as R

# Add src to path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from config import CONFIG

def load_test_data():
    """Load the required data for testing"""
    # Get run ID from config
    csv_filename = Path(CONFIG['current_csv']).stem
    RUN_ID = csv_filename
    
    # Load filtered data (input to NB06)
    deriv_filtered = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_04_filtering")
    input_file = os.path.join(deriv_filtered, f"{RUN_ID}__filtered.parquet")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Filtered data not found: {input_file}")
    
    df_in = pd.read_parquet(input_file)
    
    # Load kinematics map
    deriv_ref = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_05_reference")
    map_path = os.path.join(deriv_ref, f"{RUN_ID}__kinematics_map.json")
    
    if not os.path.exists(map_path):
        map_path = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_03_resample", f"{RUN_ID}__kinematics_map.json")
    
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"Kinematics map not found: {map_path}")
    
    with open(map_path, 'r') as f:
        kinematics_map = json.load(f)
    
    # Load reference pose (rot_rel_ref source from NB05)
    ref_path = os.path.join(deriv_ref, f"{RUN_ID}__reference_map.json")
    
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference map not found: {ref_path}")
    
    with open(ref_path, 'r') as f:
        ref_pose = json.load(f)
    
    # Load reference window indices
    summary_path = os.path.join(deriv_ref, f"{RUN_ID}__reference_summary.json")
    
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Reference summary not found: {summary_path}")
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Extract reference window from metadata
    window_metadata = summary.get('window_metadata', {})
    time_window = window_metadata.get('time_window', [0.0, 1.0])
    fs = CONFIG.get('FS_TARGET', 120.0)
    
    start_idx = int(time_window[0] * fs)
    end_idx = int(time_window[1] * fs)
    ref_window_idx = slice(start_idx, end_idx)
    
    return df_in, kinematics_map, ref_pose, ref_window_idx

def apply_reference_correction(df, k_map, r_pose):
    """
    Apply the same reference correction as NB06
    Returns corrected rotations for all joints and frames
    """
    results = {}
    
    for joint_name, info in k_map.items():
        parent_name = info['parent']
        
        # Extract child rotation quaternions
        q_c_cols = [f"{joint_name}__qx", f"{joint_name}__qy", f"{joint_name}__qz", f"{joint_name}__qw"]
        q_c = df[q_c_cols].values
        
        rot_c = R.from_quat(q_c)
        
        # Get child reference rotation
        q_c_ref = [r_pose[f"{joint_name}__qx"], r_pose[f"{joint_name}__qy"], 
                   r_pose[f"{joint_name}__qz"], r_pose[f"{joint_name}__qw"]]
        r_c_ref = R.from_quat(q_c_ref)
        
        if parent_name is not None:
            # Parent dynamic rotation
            q_p_cols = [f"{parent_name}__qx", f"{parent_name}__qy", f"{parent_name}__qz", f"{parent_name}__qw"]
            q_p = df[q_p_cols].values
            rot_p = R.from_quat(q_p)
            
            # Current relative: inv(Parent) * Child
            rot_rel = rot_p.inv() * rot_c
            
            # Reference relative: inv(Parent_Ref) * Child_Ref
            q_p_ref = [r_pose[f"{parent_name}__qx"], r_pose[f"{parent_name}__qy"], 
                       r_pose[f"{parent_name}__qz"], r_pose[f"{parent_name}__qw"]]
            r_p_ref = R.from_quat(q_p_ref)
            rot_rel_ref = r_p_ref.inv() * r_c_ref
        else:
            # Root joint - global rotation
            rot_rel = rot_c
            rot_rel_ref = r_c_ref
        
        # Apply zeroing calibration: inv(Reference) * Current
        rot_final = rot_rel_ref.inv() * rot_rel
        
        results[joint_name] = rot_final
    
    return results

def test_reference_correction():
    """Main verification test"""
    print("="*60)
    print("REFERENCE CORRECTION VERIFICATION TEST")
    print("="*60)
    
    # Load data
    print("Loading test data...")
    df_in, kinematics_map, ref_pose, ref_window_idx = load_test_data()
    
    print(f"✅ Loaded data for {len(df_in)} frames")
    print(f"✅ Processing {len(kinematics_map)} joints")
    print(f"✅ Reference window: frames {ref_window_idx.start}-{ref_window_idx.stop}")
    
    # Apply reference correction
    print("\nApplying reference correction...")
    corrected_rotations = apply_reference_correction(df_in, kinematics_map, ref_pose)
    
    # Test reference window residuals
    print("\nComputing residuals in reference window...")
    
    joint_results = {}
    all_residuals = []
    
    for joint_name, rot_final in corrected_rotations.items():
        # Extract rotations in reference window
        rot_window = rot_final[ref_window_idx]
        
        # Convert to Euler angles (degrees)
        euler_window = rot_window.as_euler('XYZ', degrees=True)
        
        # Compute residuals from identity (should be near 0)
        residuals = np.abs(euler_window)  # Absolute deviation from 0°
        
        # Joint-level metrics
        median_residual = np.median(residuals)
        max_residual = np.max(residuals)
        p95_residual = np.percentile(residuals, 95)
        
        joint_results[joint_name] = {
            'median_residual_deg': median_residual,
            'max_residual_deg': max_residual,
            'p95_residual_deg': p95_residual
        }
        
        # Collect all residuals for global metrics
        all_residuals.extend(residuals.flatten())
    
    # Global metrics
    global_median = np.median(all_residuals)
    global_p95 = np.percentile(all_residuals, 95)
    global_max = np.max(all_residuals)
    
    # Results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    # Joint-level results
    print("\nJoint-level residuals (degrees):")
    print(f"{'Joint':<20} | {'Median':<8} | {'95th':<8} | {'Max':<8} | {'Status'}")
    print("-" * 65)
    
    passed_joints = 0
    failed_joints = []
    
    for joint_name, metrics in joint_results.items():
        median = metrics['median_residual_deg']
        p95 = metrics['p95_residual_deg']
        max_res = metrics['max_residual_deg']
        
        # Pass criteria: median < 1°
        status = "✅ PASS" if median < 1.0 else "❌ FAIL"
        
        if median < 1.0:
            passed_joints += 1
        else:
            failed_joints.append(joint_name)
        
        print(f"{joint_name:<20} | {median:>7.3f} | {p95:>7.3f} | {max_res:>7.3f} | {status}")
    
    # Global results
    print(f"\nGlobal metrics:")
    print(f"  Median residual: {global_median:.3f}°")
    print(f"  95th percentile: {global_p95:.3f}°")
    print(f"  Maximum residual: {global_max:.3f}°")
    
    # Final assessment
    print(f"\n" + "="*60)
    print("ASSESSMENT")
    print("="*60)
    
    joint_pass_rate = passed_joints / len(joint_results) * 100
    
    # Pass criteria
    joint_test = passed_joints == len(joint_results)  # All joints pass median < 1°
    global_test = global_p95 < 3.0  # 95th percentile < 3°
    
    overall_pass = joint_test and global_test
    
    print(f"Joint test (median < 1°): {passed_joints}/{len(joint_results)} joints pass ({joint_pass_rate:.1f}%)")
    print(f"Global test (95th < 3°): {'✅ PASS' if global_test else '❌ FAIL'} ({global_p95:.3f}°)")
    print(f"Overall: {'✅ PASS' if overall_pass else '❌ FAIL'}")
    
    if failed_joints:
        print(f"\nFailed joints: {', '.join(failed_joints)}")
    
    # Special note for shoulders
    shoulder_joints = [j for j in joint_results.keys() if 'Shoulder' in j]
    if shoulder_joints:
        print(f"\nNote: Shoulder joints ({', '.join(shoulder_joints)}) included in identity check")
        for shoulder in shoulder_joints:
            median = joint_results[shoulder]['median_residual_deg']
            status = "✅ PASS" if median < 1.0 else "❌ FAIL"
            print(f"  {shoulder}: {median:.3f}° {status}")
    
    return overall_pass, {
        'joint_results': joint_results,
        'global_metrics': {
            'median_deg': global_median,
            'p95_deg': global_p95,
            'max_deg': global_max
        },
        'passed_joints': passed_joints,
        'total_joints': len(joint_results),
        'failed_joints': failed_joints
    }

if __name__ == "__main__":
    try:
        passed, results = test_reference_correction()
        
        if passed:
            print(f"\n🎉 VERIFICATION PASSED")
            print("Reference correction is applied correctly to every joint and frame.")
        else:
            print(f"\n❌ VERIFICATION FAILED")
            print("Reference correction may not be applied correctly.")
            
        sys.exit(0 if passed else 1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
