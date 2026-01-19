"""
Simple validation script for coordinate systems module.
Tests basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, 'src')

import numpy as np
from scipy.spatial.transform import Rotation as R

from coordinate_systems import (
    COORDINATE_FRAMES,
    ISB_EULER_SEQUENCES,
    optitrack_to_isb_position,
    validate_coordinate_frame,
    validate_quaternion_frame,
    get_joint_euler_sequence,
    generate_coordinate_system_report
)


def test_frame_definitions():
    """Test that frame definitions are complete."""
    print("\n=== Test 1: Frame Definitions ===")
    
    required_fields = ['name', 'x_axis', 'y_axis', 'z_axis', 'handedness']
    
    all_complete = True
    for frame_id, frame_info in COORDINATE_FRAMES.items():
        for field in required_fields:
            if field not in frame_info:
                print(f"  [FAIL] Frame {frame_id} missing {field}")
                all_complete = False
    
    if all_complete:
        print(f"  All {len(COORDINATE_FRAMES)} frames have complete definitions")
        print("[PASS] Frame definitions complete")
        return True
    else:
        print("[FAIL] Some frames incomplete")
        return False


def test_position_transformation():
    """Test OptiTrack to ISB position transformation."""
    print("\n=== Test 2: Position Transformation ===")
    
    # OptiTrack: [X_right=1000, Y_up=2000, Z_forward=3000] mm
    pos_ot = np.array([[1000, 2000, 3000]])
    pos_isb = optitrack_to_isb_position(pos_ot)
    
    # ISB should be: [X_forward, Y_up, Z_right] = [3.0, 2.0, 1.0] m
    expected = np.array([[3.0, 2.0, 1.0]])
    
    print(f"  OptiTrack (mm): {pos_ot[0]}")
    print(f"  ISB (m): {pos_isb[0]}")
    print(f"  Expected: {expected[0]}")
    
    if np.allclose(pos_isb, expected):
        print("[PASS] Axes correctly reordered and units converted")
        return True
    else:
        print("[FAIL] Transformation incorrect")
        return False


def test_frame_validation():
    """Test coordinate frame validation."""
    print("\n=== Test 3: Frame Validation ===")
    
    # OptiTrack data (mm scale)
    pos_ot = np.random.randn(100, 3) * 500 + 1000
    result_ot = validate_coordinate_frame(pos_ot, 'optitrack_world')
    
    # ISB data (meter scale)
    pos_isb = np.random.randn(100, 3) * 0.5 + 1.0
    result_isb = validate_coordinate_frame(pos_isb, 'isb_anatomical')
    
    print(f"  OptiTrack validation: {result_ot['unit_check']}")
    print(f"  ISB validation: {result_isb['unit_check']}")
    
    if result_ot['unit_check'] == 'PASS' and result_isb['unit_check'] == 'PASS':
        print("[PASS] Frame validation detects correct units")
        return True
    else:
        print("[FAIL] Frame validation incorrect")
        return False


def test_quaternion_validation():
    """Test quaternion validation."""
    print("\n=== Test 4: Quaternion Validation ===")
    
    # Good quaternions (normalized)
    q_good = np.array([R.identity().as_quat() for _ in range(100)])
    result_good = validate_quaternion_frame(q_good)
    
    # Bad quaternions (not normalized)
    q_bad = np.random.randn(100, 4) * 2
    result_bad = validate_quaternion_frame(q_bad)
    
    print(f"  Normalized quats: {result_good['norm_status']}")
    print(f"  Random quats: {result_bad['norm_status']}")
    
    if result_good['norm_status'] == 'PASS' and result_bad['norm_status'] in ['WARN', 'FAIL']:
        print("[PASS] Quaternion validation working")
        return True
    else:
        print("[FAIL] Quaternion validation incorrect")
        return False


def test_euler_sequences():
    """Test ISB Euler sequence mapping."""
    print("\n=== Test 5: ISB Euler Sequences ===")
    
    # Test known joints
    shoulder = get_joint_euler_sequence('shoulder')
    knee = get_joint_euler_sequence('knee')
    unknown = get_joint_euler_sequence('random_joint')
    
    print(f"  Shoulder: {shoulder['sequence']}")
    print(f"  Knee: {knee['sequence']}")
    print(f"  Unknown: {unknown['sequence']}")
    
    if (shoulder['sequence'] == 'YXY' and 
        knee['sequence'] == 'ZXY' and 
        unknown['sequence'] == 'ZXY'):
        print("[PASS] Euler sequences correctly mapped")
        return True
    else:
        print("[FAIL] Euler sequence mapping incorrect")
        return False


def test_documentation_report():
    """Test documentation report generation."""
    print("\n=== Test 6: Documentation Report ===")
    
    report = generate_coordinate_system_report()
    
    # Check that report contains key sections
    has_frames = 'COORDINATE FRAMES' in report
    has_euler = 'EULER SEQUENCES' in report
    has_flow = 'PIPELINE FRAME FLOW' in report
    
    print(f"  Has frames section: {has_frames}")
    print(f"  Has Euler section: {has_euler}")
    print(f"  Has flow diagram: {has_flow}")
    
    if has_frames and has_euler and has_flow:
        print("[PASS] Documentation report complete")
        return True
    else:
        print("[FAIL] Documentation report incomplete")
        return False


def main():
    """Run all validation tests."""
    print("="*60)
    print("Coordinate Systems Module - Validation Tests")
    print("="*60)
    
    results = []
    results.append(test_frame_definitions())
    results.append(test_position_transformation())
    results.append(test_frame_validation())
    results.append(test_quaternion_validation())
    results.append(test_euler_sequences())
    results.append(test_documentation_report())
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    if all(results):
        print("\n[SUCCESS] ALL TESTS PASSED - Module validation successful!")
        
        # Print documentation report
        print("\n\nGENERATED DOCUMENTATION:")
        print("-"*60)
        from coordinate_systems import generate_coordinate_system_report
        print(generate_coordinate_system_report())
        
        return 0
    else:
        print("\n[WARN] SOME TESTS FAILED - Check implementation")
        return 1


if __name__ == '__main__':
    sys.exit(main())
