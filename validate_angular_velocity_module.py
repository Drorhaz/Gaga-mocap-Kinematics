"""
Simple validation script for angular velocity module.
Tests basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, 'src')

import numpy as np
from scipy.spatial.transform import Rotation as R

from angular_velocity import (
    quaternion_log_angular_velocity,
    finite_difference_5point,
    central_difference_angular_velocity,
    compare_angular_velocity_methods,
    compute_angular_velocity_enhanced
)


def create_constant_rotation_quaternions(n_frames, omega_true, fs):
    """Create quaternions with known constant angular velocity."""
    dt = 1.0 / fs
    q = np.zeros((n_frames, 4))
    
    # Start at identity
    R_current = R.identity()
    q[0] = R_current.as_quat()
    
    # Apply constant rotation each frame
    for t in range(1, n_frames):
        rotvec = omega_true * dt
        R_delta = R.from_rotvec(rotvec)
        R_current = R_current * R_delta
        q[t] = R_current.as_quat()
    
    return q


def test_quaternion_log_method():
    """Test quaternion logarithm method."""
    print("\n=== Test 1: Quaternion Logarithm Method ===")
    
    fs = 120.0
    n_frames = 1000
    omega_true = np.array([0.5, 0.0, 0.0])  # 0.5 rad/s around X
    
    q = create_constant_rotation_quaternions(n_frames, omega_true, fs)
    omega_computed = quaternion_log_angular_velocity(q, fs, frame='local')
    
    # Check X-axis (should be ~0.5 rad/s)
    mean_omega_x = np.mean(omega_computed[:-1, 0])  # Exclude last frame
    error = abs(mean_omega_x - omega_true[0])
    
    print(f"  True omega_x: {omega_true[0]:.4f} rad/s")
    print(f"  Computed omega_x: {mean_omega_x:.4f} rad/s")
    print(f"  Error: {error:.6f} rad/s")
    
    if error < 0.001:  # <0.1% error
        print("[PASS] Quaternion log method accurate")
        return True
    else:
        print("[FAIL] Quaternion log method inaccurate")
        return False


def test_5point_stencil():
    """Test 5-point finite difference stencil."""
    print("\n=== Test 2: 5-Point Stencil Method ===")
    
    fs = 120.0
    n_frames = 1000
    omega_true = np.array([0.0, 1.0, 0.0])  # 1.0 rad/s around Y
    
    q = create_constant_rotation_quaternions(n_frames, omega_true, fs)
    omega_computed = finite_difference_5point(q, fs, frame='local')
    
    # Check Y-axis (should be ~1.0 rad/s)
    mean_omega_y = np.mean(omega_computed[2:-2, 1])  # Exclude boundaries
    error = abs(mean_omega_y - omega_true[1])
    
    print(f"  True omega_y: {omega_true[1]:.4f} rad/s")
    print(f"  Computed omega_y: {mean_omega_y:.4f} rad/s")
    print(f"  Error: {error:.6f} rad/s")
    
    if error < 0.01:  # <1% error
        print("[PASS] 5-point stencil accurate")
        return True
    else:
        print("[FAIL] 5-point stencil inaccurate")
        return False


def test_noise_resistance():
    """Test that advanced methods are less noisy than central diff."""
    print("\n=== Test 3: Noise Resistance ===")
    
    fs = 120.0
    n_frames = 500
    omega_true = np.array([0.3, 0.3, 0.3])  # Multi-axis rotation
    
    # Create clean quaternions
    q_clean = create_constant_rotation_quaternions(n_frames, omega_true, fs)
    
    # Add small noise to quaternions
    np.random.seed(42)
    noise_level = 0.01
    q_noisy = q_clean + np.random.randn(*q_clean.shape) * noise_level
    
    # Renormalize
    for t in range(n_frames):
        q_noisy[t] = q_noisy[t] / np.linalg.norm(q_noisy[t])
    
    # Compute with all methods
    omega_qlog = quaternion_log_angular_velocity(q_noisy, fs)
    omega_5pt = finite_difference_5point(q_noisy, fs)
    omega_central = central_difference_angular_velocity(q_noisy, fs)
    
    # Measure noise (std of second derivative of magnitude)
    mag_qlog = np.linalg.norm(omega_qlog, axis=1)
    mag_5pt = np.linalg.norm(omega_5pt, axis=1)
    mag_central = np.linalg.norm(omega_central, axis=1)
    
    noise_qlog = np.std(np.diff(mag_qlog, n=2))
    noise_5pt = np.std(np.diff(mag_5pt, n=2))
    noise_central = np.std(np.diff(mag_central, n=2))
    
    print(f"  Noise (quat log): {noise_qlog:.6f}")
    print(f"  Noise (5-point): {noise_5pt:.6f}")
    print(f"  Noise (central diff): {noise_central:.6f}")
    print(f"  Noise reduction (qlog vs central): {noise_central/noise_qlog:.2f}x")
    print(f"  Noise reduction (5pt vs central): {noise_central/noise_5pt:.2f}x")
    
    # At least one method should reduce noise significantly
    if noise_5pt < noise_central * 0.5 or noise_qlog < noise_central * 0.5:
        print("[PASS] At least one advanced method significantly reduces noise")
        return True
    else:
        print("[FAIL] Noise reduction not achieved")
        return False


def test_method_comparison():
    """Test method comparison function."""
    print("\n=== Test 4: Method Comparison ===")
    
    fs = 120.0
    n_frames = 500
    omega_true = np.array([0.5, 0.5, 0.0])
    
    q = create_constant_rotation_quaternions(n_frames, omega_true, fs)
    
    result = compare_angular_velocity_methods(q, fs, frame='local')
    
    print(f"  Methods compared: qlog, 5pt, central")
    print(f"  Mean magnitude (qlog): {result['statistics']['mean_magnitude_qlog']:.4f} rad/s")
    print(f"  Mean magnitude (5pt): {result['statistics']['mean_magnitude_5pt']:.4f} rad/s")
    print(f"  Recommendation: {result['method_recommendation']}")
    
    if 'omega_qlog' in result and 'statistics' in result:
        print("[PASS] Method comparison working")
        return True
    else:
        print("[FAIL] Method comparison incomplete")
        return False


def test_multi_joint():
    """Test angular velocity for multiple joints."""
    print("\n=== Test 5: Multi-Joint Computation ===")
    
    fs = 120.0
    n_frames = 200
    n_joints = 10
    
    # Create quaternions for multiple joints
    q = np.zeros((n_frames, n_joints, 4))
    for j in range(n_joints):
        omega_true = np.array([0.1 * (j+1), 0.0, 0.0])  # Different omega per joint
        q[:, j, :] = create_constant_rotation_quaternions(n_frames, omega_true, fs)
    
    omega, metadata = compute_angular_velocity_enhanced(
        q, fs, method='quaternion_log', frame='local'
    )
    
    print(f"  Joints processed: {metadata['n_joints']}")
    print(f"  Mean magnitude: {metadata['mean_magnitude_rad_s']:.4f} rad/s")
    print(f"  Max magnitude: {metadata['max_magnitude_rad_s']:.4f} rad/s")
    
    if omega.shape == (n_frames, n_joints, 3) and metadata['n_joints'] == n_joints:
        print("[PASS] Multi-joint computation working")
        return True
    else:
        print("[FAIL] Multi-joint computation issues")
        return False


def test_enhanced_api():
    """Test main API function."""
    print("\n=== Test 6: Enhanced API ===")
    
    fs = 120.0
    n_frames = 300
    omega_true = np.array([1.0, 0.5, 0.2])
    
    q = create_constant_rotation_quaternions(n_frames, omega_true, fs)
    
    # Test all methods
    methods_tested = []
    for method in ['quaternion_log', '5point', 'central']:
        omega, metadata = compute_angular_velocity_enhanced(q, fs, method=method)
        methods_tested.append(metadata['method'] == method)
    
    if all(methods_tested):
        print(f"  All methods accessible: {['quaternion_log', '5point', 'central']}")
        print("[PASS] Enhanced API working")
        return True
    else:
        print("[FAIL] Some methods not accessible")
        return False


def main():
    """Run all validation tests."""
    print("="*60)
    print("Angular Velocity Module - Validation Tests")
    print("="*60)
    
    results = []
    results.append(test_quaternion_log_method())
    results.append(test_5point_stencil())
    results.append(test_noise_resistance())
    results.append(test_method_comparison())
    results.append(test_multi_joint())
    results.append(test_enhanced_api())
    
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
