"""
Standalone Test Script: Final Push Implementation
==================================================
Run without pytest: python test_final_push_standalone.py

Tests all 4 tasks with clear pass/fail output.
"""

def test_task1_height_validation():
    """Task 1: Height validation tests."""
    from src.subject_validation import validate_height, validate_mass, compute_normalized_intensity_index
    
    print("\n" + "="*70)
    print("TASK 1: SUBJECT CONTEXT & NORMALIZATION")
    print("="*70)
    
    # Test 1: Normal height
    status, reason = validate_height(170.0)
    assert status == 'PASS', f"Expected PASS, got {status}"
    print(f"[PASS] Height 170cm: {status} - {reason}")
    
    # Test 2: Zero height
    status, reason = validate_height(0.0)
    assert status == 'FAIL', f"Expected FAIL, got {status}"
    print(f"✅ Height 0cm: {status} - {reason}")
    
    # Test 3: Excessive height
    status, reason = validate_height(300.0)
    assert status == 'FAIL', f"Expected FAIL, got {status}"
    print(f"✅ Height 300cm: {status} - {reason}")
    
    # Test 4: Normal mass
    status, reason = validate_mass(70.0)
    assert status == 'PASS', f"Expected PASS, got {status}"
    print(f"✅ Mass 70kg: {status} - {reason}")
    
    # Test 5: Intensity normalization
    result = compute_normalized_intensity_index(1000.0, 70.0)
    assert result['intensity_normalized'] is not None
    assert abs(result['intensity_normalized'] - 14.286) < 0.01
    print(f"✅ Intensity normalization: 1000/70 = {result['intensity_normalized']:.3f}")
    
    print("\n✅ All Task 1 tests passed!")
    return True


def test_task2_outlier_thresholds():
    """Task 2: Outlier policy tests."""
    from src.burst_classification import EVENT_DENSITY_THRESHOLDS
    
    print("\n" + "="*70)
    print("TASK 2: OUTLIER POLICY IMPLEMENTATION")
    print("="*70)
    
    # Test 1: 5% outlier threshold exists
    assert 'outlier_rate_review' in EVENT_DENSITY_THRESHOLDS
    assert EVENT_DENSITY_THRESHOLDS['outlier_rate_review'] == 5.0
    print(f"✅ Outlier rate threshold: {EVENT_DENSITY_THRESHOLDS['outlier_rate_review']}% = REVIEW")
    
    # Test 2: 1% artifact reject threshold
    assert 'artifact_rate_reject' in EVENT_DENSITY_THRESHOLDS
    assert EVENT_DENSITY_THRESHOLDS['artifact_rate_reject'] == 1.0
    print(f"✅ Artifact rate threshold: {EVENT_DENSITY_THRESHOLDS['artifact_rate_reject']}% = REJECT (FAIL)")
    
    # Test 3: Frame classification thresholds
    from src.burst_classification import TIER_ARTIFACT_MAX, TIER_BURST_MAX
    assert TIER_ARTIFACT_MAX == 3
    assert TIER_BURST_MAX == 7
    print(f"✅ Consecutive frame classification: 1-{TIER_ARTIFACT_MAX}=Artifact, 4-{TIER_BURST_MAX}=Burst, 8+=Flow")
    
    print("\n✅ All Task 2 tests passed!")
    return True


def test_task3_filter_synergy():
    """Task 3: Filter synergy tests."""
    import numpy as np
    from src.filtering import winter_residual_analysis
    
    print("\n" + "="*70)
    print("TASK 3: RESIDUAL RMS & FILTER SYNERGY")
    print("="*70)
    
    # Create synthetic signal
    fs = 120.0
    t = np.linspace(0, 1, int(fs))
    signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
    
    # Test 1: Residual slope is returned
    result = winter_residual_analysis(signal, fs, return_details=True)
    assert 'residual_slope' in result
    assert isinstance(result['residual_slope'], float)
    print(f"✅ Residual slope returned: {result['residual_slope']:.6f}")
    
    # Test 2: Residual RMS is returned
    assert 'residual_rms_final' in result
    assert result['residual_rms_final'] >= 0
    print(f"✅ Residual RMS returned: {result['residual_rms_final']:.4f}")
    
    # Test 3: Cutoff is returned
    assert 'cutoff_hz' in result
    assert result['cutoff_hz'] > 0
    print(f"✅ Cutoff frequency: {result['cutoff_hz']:.1f} Hz")
    
    # Test 4: Knee point detection status
    assert 'knee_point_found' in result
    print(f"✅ Knee point found: {result['knee_point_found']}")
    
    print("\n✅ All Task 3 tests passed!")
    return True


def test_task4_schema_documentation():
    """Task 4: Schema documentation tests."""
    from src.utils_nb07 import PARAMETER_SCHEMA
    
    print("\n" + "="*70)
    print("TASK 4: PARAMETER SCHEMA DOCUMENTATION")
    print("="*70)
    
    # Test 1: Height parameter has formula
    height_param = PARAMETER_SCHEMA['step_05']['parameters']['subject_context.height_cm']
    desc = height_param['description']
    assert '$' in desc or 'Formula:' in desc
    assert '250' in desc  # Sanity check threshold
    print(f"✅ Height parameter has LaTeX formula and threshold")
    print(f"   Description preview: {desc[:100]}...")
    
    # Test 2: Intensity index has normalization formula
    intensity_param = PARAMETER_SCHEMA['step_06']['parameters']['movement_metrics.intensity_index']
    desc = intensity_param['description']
    assert '$I_{norm}' in desc or 'I / m' in desc.replace('_', ' ')
    print(f"✅ Intensity index has normalization formula")
    print(f"   Description preview: {desc[:100]}...")
    
    # Test 3: Residual RMS has thresholds
    rms_param = PARAMETER_SCHEMA['step_06']['parameters']['signal_quality.avg_residual_rms']
    desc = rms_param['description']
    assert '15' in desc and '30' in desc  # GOLD<15, SILVER 15-30
    print(f"✅ Residual RMS has quality thresholds (GOLD<15mm, SILVER 15-30mm)")
    
    # Test 4: Filter cutoff has code reference
    cutoff_param = PARAMETER_SCHEMA['step_04']['parameters']['filter_params.filter_cutoff_hz']
    desc = cutoff_param['description']
    assert 'filtering.py' in desc
    print(f"✅ Filter cutoff has code reference (src/filtering.py)")
    
    # Test 5: Outlier parameters have explicit thresholds
    outlier_param = PARAMETER_SCHEMA['step_06']['parameters']['outlier_analysis.percentages.total_outliers']
    desc = outlier_param['description']
    assert '5' in desc  # >5% threshold
    print(f"✅ Outlier percentage has explicit threshold (>5% = REVIEW)")
    
    print("\n✅ All Task 4 tests passed!")
    return True


def test_integration():
    """Integration tests across tasks."""
    from src.subject_validation import validate_subject_context, compute_normalized_intensity_index
    
    print("\n" + "="*70)
    print("INTEGRATION TESTS")
    print("="*70)
    
    # Test 1: Complete subject validation workflow
    validation = validate_subject_context(height_cm=170.0, mass_kg=70.0)
    assert validation['overall_status'] == 'PASS'
    print(f"✅ Subject validation: {validation['overall_status']}")
    
    # Test 2: Normalize intensity with validated subject
    intensity = compute_normalized_intensity_index(1000.0, 70.0)
    assert intensity['intensity_normalized'] is not None
    assert intensity['mass_kg'] == validation['mass']['value_kg']
    print(f"✅ Intensity normalization with validated subject: {intensity['intensity_normalized']:.3f}")
    
    # Test 3: Invalid subject prevents normalization
    validation_fail = validate_subject_context(height_cm=0.0, mass_kg=0.0)
    assert validation_fail['overall_status'] == 'FAIL'
    print(f"✅ Invalid subject detected: {validation_fail['overall_status']}")
    
    print("\n✅ All integration tests passed!")
    return True


def main():
    """Run all tests."""
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  FINAL PUSH IMPLEMENTATION - STANDALONE TEST SUITE".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    results = []
    
    try:
        results.append(("Task 1: Subject Validation", test_task1_height_validation()))
    except Exception as e:
        print(f"\n❌ Task 1 FAILED: {e}")
        results.append(("Task 1: Subject Validation", False))
    
    try:
        results.append(("Task 2: Outlier Policy", test_task2_outlier_thresholds()))
    except Exception as e:
        print(f"\n❌ Task 2 FAILED: {e}")
        results.append(("Task 2: Outlier Policy", False))
    
    try:
        results.append(("Task 3: Filter Synergy", test_task3_filter_synergy()))
    except Exception as e:
        print(f"\n❌ Task 3 FAILED: {e}")
        results.append(("Task 3: Filter Synergy", False))
    
    try:
        results.append(("Task 4: Schema Documentation", test_task4_schema_documentation()))
    except Exception as e:
        print(f"\n❌ Task 4 FAILED: {e}")
        results.append(("Task 4: Schema Documentation", False))
    
    try:
        results.append(("Integration Tests", test_integration()))
    except Exception as e:
        print(f"\n❌ Integration tests FAILED: {e}")
        results.append(("Integration Tests", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print("\n" + "="*70)
    if passed_count == total:
        print(f"🎉 ALL TESTS PASSED: {passed_count}/{total}")
        print("="*70)
        print("\n✅ Implementation is ready for deployment!")
        return 0
    else:
        print(f"⚠️  SOME TESTS FAILED: {passed_count}/{total} passed")
        print("="*70)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
