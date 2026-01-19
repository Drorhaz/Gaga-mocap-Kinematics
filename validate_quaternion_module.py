"""
Simple validation script for quaternion normalization module.
Tests basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, 'src')

import numpy as np
from scipy.spatial.transform import Rotation as R

from quaternion_normalization import (
    normalize_quaternion_safe,
    detect_quaternion_drift,
    renormalize_quaternions_inplace,
    apply_hemispheric_continuity,
    validate_quaternion_integrity,
    correct_quaternion_sequence
)


def test_safe_normalization():
    """Test safe quaternion normalization."""
    print("\n=== Test 1: Safe Normalization ===")
    
    # Create denormalized quaternions
    q = np.array([[1, 2, 3, 4], [0.5, 0.5, 0.5, 0.5]]) / 2.0
    
    q_norm = normalize_quaternion_safe(q)
    norms = np.linalg.norm(q_norm, axis=1)
    
    print(f"  Norms before: {np.linalg.norm(q, axis=1)}")
    print(f"  Norms after: {norms}")
    
    if np.allclose(norms, 1.0):
        print("[PASS] Quaternions normalized to unit length")
        return True
    else:
        print("[FAIL] Normalization incorrect")
        return False


def test_drift_detection():
    """Test drift detection."""
    print("\n=== Test 2: Drift Detection ===")
    
    n_frames = 1000
    
    # Create quaternions with increasing drift
    q_good = np.array([R.identity().as_quat() for _ in range(n_frames)])
    q_drift = q_good.copy()
    for i in range(n_frames):
        q_drift[i] *= (1.0 + i * 0.00001)  # Gradual drift
    
    time_s = np.arange(n_frames) / 120.0
    
    drift_good = detect_quaternion_drift(q_good, time_s)
    drift_bad = detect_quaternion_drift(q_drift, time_s)
    
    print(f"  Good quats - Max error: {drift_good['max_norm_error']:.6f}, Status: {drift_good['drift_status']}")
    print(f"  Drift quats - Max error: {drift_bad['max_norm_error']:.6f}, Status: {drift_bad['drift_status']}")
    
    if drift_good['drift_status'] == 'EXCELLENT' and drift_bad['max_norm_error'] > drift_good['max_norm_error']:
        print("[PASS] Drift detection working")
        return True
    else:
        print("[FAIL] Drift detection incorrect")
        return False


def test_renormalization():
    """Test renormalization with statistics."""
    print("\n=== Test 3: Renormalization ===")
    
    # Create drifted quaternions
    q = np.random.randn(100, 4)
    for i in range(len(q)):
        q[i] = q[i] / np.linalg.norm(q[i]) * (1.0 + 0.05 * np.random.rand())  # 5% drift
    
    q_norm, stats = renormalize_quaternions_inplace(q.copy())
    
    print(f"  Drift before: {stats['drift_before_normalization']['max_norm_error']:.6f}")
    print(f"  Residual after: {stats['residual_error_after']:.6f}")
    print(f"  Frames corrected: {stats['frames_corrected']}")
    
    if stats['residual_error_after'] < 1e-6:
        print("[PASS] Renormalization successful")
        return True
    else:
        print("[FAIL] Renormalization incomplete")
        return False


def test_continuity_enforcement():
    """Test hemispheric continuity."""
    print("\n=== Test 4: Continuity Enforcement ===")
    
    # Create quaternions with hemisphere flips
    q = np.zeros((10, 4))
    for i in range(len(q)):
        q[i] = R.identity().as_quat()
        if i % 2 == 1:
            q[i] *= -1  # Flip hemisphere
    
    # Count discontinuities before
    dots_before = np.sum(q[:-1] * q[1:], axis=1)
    disc_before = np.sum(dots_before < 0)
    
    # Apply continuity
    q_cont = apply_hemispheric_continuity(q)
    
    # Count discontinuities after
    dots_after = np.sum(q_cont[:-1] * q_cont[1:], axis=1)
    disc_after = np.sum(dots_after < 0)
    
    print(f"  Discontinuities before: {disc_before}")
    print(f"  Discontinuities after: {disc_after}")
    
    if disc_after == 0:
        print("[PASS] Continuity enforced successfully")
        return True
    else:
        print("[FAIL] Continuity enforcement incomplete")
        return False


def test_integrity_validation():
    """Test comprehensive validation."""
    print("\n=== Test 5: Integrity Validation ===")
    
    # Good quaternions
    q_good = np.array([R.identity().as_quat() for _ in range(100)])
    time_s = np.arange(len(q_good)) / 120.0
    
    result = validate_quaternion_integrity(q_good, time_s, strict=True)
    
    print(f"  Status: {result['status']}")
    print(f"  Normalization OK: {result['normalization_ok']}")
    print(f"  Continuity OK: {result['continuity_ok']}")
    
    if result['status'] == 'PASS':
        print("[PASS] Integrity validation working")
        return True
    else:
        print("[FAIL] Should pass for good quaternions")
        return False


def test_full_correction():
    """Test full correction pipeline."""
    print("\n=== Test 6: Full Correction Pipeline ===")
    
    # Create problematic quaternions
    q = np.random.randn(100, 4) * 1.1  # Denormalized
    for i in range(1, len(q), 2):
        q[i] *= -1  # Add discontinuities
    
    time_s = np.arange(len(q)) / 120.0
    
    # Apply correction
    q_corrected, stats = correct_quaternion_sequence(q, time_s)
    
    print(f"  Before: {stats['validation_before']['status']}")
    print(f"  After: {stats['validation_after']['status']}")
    print(f"  Correction successful: {stats['correction_successful']}")
    
    if stats['correction_successful'] and stats['validation_after']['status'] in ['PASS', 'WARN']:
        print("[PASS] Full correction pipeline working")
        return True
    else:
        print("[FAIL] Correction pipeline issues")
        return False


def main():
    """Run all validation tests."""
    print("="*60)
    print("Quaternion Normalization Module - Validation Tests")
    print("="*60)
    
    results = []
    results.append(test_safe_normalization())
    results.append(test_drift_detection())
    results.append(test_renormalization())
    results.append(test_continuity_enforcement())
    results.append(test_integrity_validation())
    results.append(test_full_correction())
    
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
