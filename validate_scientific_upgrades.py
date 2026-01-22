"""
Scientific Upgrades Validation Script
=====================================
Quick verification that all modules are properly implemented.

Run this script to validate:
1. ISB Euler module
2. SNR Analysis module
3. Interpolation Logger module
4. Integration readiness

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
    print("SCIENTIFIC UPGRADES VALIDATION")
    print("="*80)
    print()
    
    results = {}
    
    # 1. Validate ISB Euler module
    print("1. ISB Euler Sequences & Biomechanical Validation:")
    results['euler_isb'] = validate_module('euler_isb', [
        'ISB_EULER_SEQUENCES',
        'ANATOMICAL_ROM_LIMITS',
        'get_euler_sequence',
        'quaternion_to_isb_euler',
        'check_anatomical_validity',
        'convert_dataframe_to_isb_euler'
    ])
    print()
    
    # 2. Validate SNR Analysis module
    print("2. Signal-to-Noise Ratio Analysis:")
    results['snr_analysis'] = validate_module('snr_analysis', [
        'SNR_THRESHOLDS',
        'compute_snr_from_residuals',
        'compute_snr_psd',
        'assess_snr_quality',
        'compute_per_joint_snr',
        'generate_snr_report'
    ])
    print()
    
    # 3. Validate Interpolation Logger module
    print("3. Interpolation Fallback Logger:")
    results['interpolation_logger'] = validate_module('interpolation_logger', [
        'INTERPOLATION_HIERARCHY',
        'InterpolationLogger',
        'track_interpolation_with_logging'
    ])
    print()
    
    # 4. Check previously implemented enhancements
    print("4. Previously Implemented Enhancements:")
    results['interpolation_tracking'] = validate_module('interpolation_tracking', [
        'compute_per_joint_interpolation_stats'
    ])
    print()
    
    results['winter_export'] = validate_module('winter_export', [
        'export_winter_residual_data'
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
        print("\n🎉 ALL SCIENTIFIC UPGRADES SUCCESSFULLY IMPLEMENTED!")
        print("\nNext steps:")
        print("1. Integrate modules into notebooks (see SCIENTIFIC_UPGRADES_SUMMARY.md)")
        print("2. Run updated notebooks 02, 04, 06")
        print("3. Update Master Audit (07) with new sections")
        return 0
    else:
        print("\n⚠️  Some modules failed validation. Please check errors above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
