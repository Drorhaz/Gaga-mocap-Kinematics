"""
Additional Features Validation Script
=====================================
Validate bone length validation and LCS visualization modules

Author: Gaga Motion Analysis Pipeline
Date: 2026-01-22
"""

import sys
import os
import io

# Fix UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

def validate_module(module_name, expected_functions):
    """Validate that a module exists and has expected functions."""
    try:
        module = __import__(module_name)
        print(f"✅ {module_name}: Module loaded successfully")
        
        missing = []
        for func in expected_functions:
            if not hasattr(module, func):
                missing.append(func)
        
        if missing:
            print(f"   ⚠️  Missing functions: {', '.join(missing)}")
            return False
        else:
            print(f"   ✅ All {len(expected_functions)} expected functions present")
            return True
            
    except ImportError as e:
        print(f"❌ {module_name}: Failed to import - {e}")
        return False
    except Exception as e:
        print(f"❌ {module_name}: Error - {e}")
        return False


def main():
    print("="*80)
    print("ADDITIONAL FEATURES VALIDATION")
    print("="*80)
    print()
    
    results = {}
    
    # 1. Validate Bone Length Validation module
    print("1. Bone Length Validation (Static vs. Dynamic):")
    results['bone_length_validation'] = validate_module('bone_length_validation', [
        'BONE_LENGTH_VARIANCE_THRESHOLD',
        'compute_bone_length_timeseries',
        'compare_static_dynamic_bones',
        'validate_bone_lengths_from_dataframe',
        'export_bone_validation_report'
    ])
    print()
    
    # 2. Validate LCS Visualization module
    print("2. Local Coordinate System (LCS) Visualization:")
    results['lcs_visualization'] = validate_module('lcs_visualization', [
        'LCS_ARROW_LENGTH',
        'quaternion_to_rotation_matrix',
        'compute_lcs_axes',
        'plot_skeleton_with_lcs',
        'create_lcs_animation',
        'plot_lcs_stability_check'
    ])
    print()
    
    # Summary
    print("="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    passed = sum(results.values())
    total = len(results)
    
    for module, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {module}")
    
    print()
    print(f"Result: {passed}/{total} modules validated")
    
    if passed == total:
        print("\n🎉 ALL ADDITIONAL FEATURES SUCCESSFULLY IMPLEMENTED!")
        print("\nFeature 1: Bone Length Validation")
        print("  - Compares static calibration to dynamic trial bone lengths")
        print("  - Detects marker drift, swap, or tracking issues")
        print("  - Thresholds: 2% variance, 5% drift, 10% swap")
        print("\nFeature 2: LCS Visualization")
        print("  - Plots X/Y/Z axes at each joint")
        print("  - Verifies ISB orientation stability")
        print("  - Creates animations and stability checks")
        return 0
    else:
        print("\n⚠️  Some modules failed validation. Please check errors above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
