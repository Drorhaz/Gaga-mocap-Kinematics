"""
Simple validation script for reference validation module.
Tests basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, 'src')

import numpy as np
from scipy.spatial.transform import Rotation as R

from reference_validation import (
    compute_motion_profile,
    validate_reference_window,
    validate_reference_stability,
    compare_reference_with_ground_truth
)


def create_static_quaternions(n_frames, n_joints):
    """Create static (no motion) quaternions."""
    q_local = np.zeros((n_frames, n_joints, 4))
    q_identity = R.identity().as_quat()
    
    for j in range(n_joints):
        for t in range(n_frames):
            q_local[t, j] = q_identity
    
    return q_local


def create_moving_quaternions(n_frames, n_joints, motion_mag=0.5):
    """Create moving quaternions."""
    np.random.seed(42)
    q_local = np.zeros((n_frames, n_joints, 4))
    
    for j in range(n_joints):
        for t in range(n_frames):
            rotvec = np.random.randn(3) * motion_mag
            q_local[t, j] = R.from_rotvec(rotvec).as_quat()
    
    return q_local


def test_motion_profile():
    """Test motion profile computation."""
    print("\n=== Test 1: Motion Profile Computation ===")
    
    fs = 120.0
    duration = 5.0
    n_frames = int(fs * duration)
    n_joints = 10
    
    time_s = np.arange(n_frames) / fs
    
    # Static case
    q_static = create_static_quaternions(n_frames, n_joints)
    joint_indices = list(range(n_joints))
    
    profile_static = compute_motion_profile(time_s, q_static, joint_indices, fs)
    static_motion = np.nanmean(profile_static['motion_smooth'])
    
    # Moving case
    q_moving = create_moving_quaternions(n_frames, n_joints, motion_mag=0.5)
    profile_moving = compute_motion_profile(time_s, q_moving, joint_indices, fs)
    moving_motion = np.nanmean(profile_moving['motion_smooth'])
    
    print(f"  Static motion: {static_motion:.4f} rad/s")
    print(f"  Moving motion: {moving_motion:.4f} rad/s")
    
    if static_motion < 0.01 and moving_motion > 0.1:
        print("[PASS] Motion profile detects static vs. moving")
        return True
    else:
        print("[FAIL] Motion profile detection issue")
        return False


def test_reference_window_validation():
    """Test reference window validation."""
    print("\n=== Test 2: Reference Window Validation ===")
    
    fs = 120.0
    duration = 10.0
    n_frames = int(fs * duration)
    n_joints = 10
    
    time_s = np.arange(n_frames) / fs
    q_local = create_static_quaternions(n_frames, n_joints)
    joint_indices = list(range(n_joints))
    
    # Good reference window (2 seconds of static)
    result = validate_reference_window(
        time_s, q_local, 1.0, 3.0, joint_indices, fs, strict_thresholds=True
    )
    
    print(f"  Status: {result['status']}")
    print(f"  Mean motion: {result['mean_motion_rad_s']:.4f} rad/s")
    print(f"  Duration: {result['duration_sec']:.2f} s")
    
    if result['status'] == 'PASS' and result['mean_motion_rad_s'] < 0.3:
        print("[PASS] Static window validated correctly")
        return True
    else:
        print("[FAIL] Validation status incorrect")
        return False


def test_poor_reference_detection():
    """Test that moving window is rejected."""
    print("\n=== Test 3: Poor Reference Detection ===")
    
    fs = 120.0
    duration = 10.0
    n_frames = int(fs * duration)
    n_joints = 10
    
    time_s = np.arange(n_frames) / fs
    q_local = create_moving_quaternions(n_frames, n_joints, motion_mag=1.0)
    joint_indices = list(range(n_joints))
    
    result = validate_reference_window(
        time_s, q_local, 1.0, 3.0, joint_indices, fs, strict_thresholds=True
    )
    
    print(f"  Status: {result['status']}")
    print(f"  Mean motion: {result['mean_motion_rad_s']:.4f} rad/s")
    
    if result['status'] in ['FAIL', 'WARN_MOTION'] and result['mean_motion_rad_s'] > 0.5:
        print("[PASS] Moving window correctly rejected")
        return True
    else:
        print("[FAIL] Should have rejected moving window")
        return False


def test_reference_stability():
    """Test reference stability metrics."""
    print("\n=== Test 4: Reference Stability ===")
    
    fs = 120.0
    n_frames = 600  # 5 seconds
    n_joints = 10
    
    time_s = np.arange(n_frames) / fs
    q_local = create_static_quaternions(n_frames, n_joints)
    
    # Create reference (identity)
    q_ref = np.zeros((n_joints, 4))
    q_identity = R.identity().as_quat()
    for j in range(n_joints):
        q_ref[j] = q_identity
    
    joint_indices = list(range(n_joints))
    
    result = validate_reference_stability(
        q_ref, q_local, 1.0, 3.0, time_s, joint_indices
    )
    
    print(f"  Identity error: {result['identity_error_mean_rad']:.6f} rad")
    print(f"  Reference std: {result['reference_std_mean_rad']:.6f} rad")
    print(f"  Joints validated: {result['n_joints_validated']}")
    
    if result['identity_error_mean_rad'] < 0.1 and result['n_joints_validated'] == n_joints:
        print("[PASS] Reference stability validated")
        return True
    else:
        print("[FAIL] Stability metrics incorrect")
        return False


def test_ground_truth_comparison():
    """Test ground truth comparison."""
    print("\n=== Test 5: Ground Truth Comparison ===")
    
    n_joints = 10
    
    # Create identical references
    q_ref = np.zeros((n_joints, 4))
    q_identity = R.identity().as_quat()
    for j in range(n_joints):
        q_ref[j] = q_identity
    
    q_ground_truth = q_ref.copy()
    joint_indices = list(range(n_joints))
    
    result = compare_reference_with_ground_truth(
        q_ref, q_ground_truth, joint_indices
    )
    
    print(f"  Status: {result['status']}")
    print(f"  Mean error: {result['mean_error_deg']:.4f} deg")
    
    if result['status'] == 'EXCELLENT' and result['mean_error_deg'] < 1.0:
        print("[PASS] Identical references correctly matched")
        return True
    else:
        print("[FAIL] Should show zero error")
        return False


def main():
    """Run all validation tests."""
    print("="*60)
    print("Reference Validation Module - Validation Tests")
    print("="*60)
    
    results = []
    results.append(test_motion_profile())
    results.append(test_reference_window_validation())
    results.append(test_poor_reference_detection())
    results.append(test_reference_stability())
    results.append(test_ground_truth_comparison())
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    if all(results):
        print("\n[SUCCESS] ALL TESTS PASSED - Module validation successful!")
        return 0
    else:
        print("\n[WARN] SOME TESTS FAILED - Check implementation")
        return 1


if __name__ == '__main__':
    sys.exit(main())
