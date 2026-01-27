"""
Gate Logic Verification Script (No pytest required)

Verifies all gate implementations according to the verification plan.
Run with: python verify_gates.py
"""

import sys
import os
import json
import traceback
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path - use package import style
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

# Track results
PASSED = []
FAILED = []

def test(name):
    """Decorator to track test results."""
    def decorator(func):
        def wrapper():
            try:
                func()
                PASSED.append(name)
                print(f"  ✅ PASS: {name}")
                return True
            except AssertionError as e:
                FAILED.append((name, str(e)))
                print(f"  ❌ FAIL: {name}")
                print(f"         {e}")
                return False
            except Exception as e:
                FAILED.append((name, f"ERROR: {e}"))
                print(f"  💥 ERROR: {name}")
                print(f"         {e}")
                traceback.print_exc()
                return False
        return wrapper
    return decorator


# =============================================================================
# 1. LOGIC & ALGORITHM VERIFICATION
# =============================================================================

print("\n" + "="*70)
print("1. LOGIC & ALGORITHM VERIFICATION")
print("="*70)

print("\n--- Gate 2: Temporal Quality ---")

@test("Gate 2: Jitter calculation with known value")
def test_jitter_known():
    from src.resampling import compute_sample_jitter
    
    np.random.seed(42)
    base_dt = 1/120
    n_samples = 1000
    time_s = np.cumsum(np.full(n_samples, base_dt))
    jitter_std_sec = 0.002  # 2ms
    time_s += np.random.normal(0, jitter_std_sec, n_samples)
    time_s = np.sort(time_s)
    
    result = compute_sample_jitter(time_s)
    
    assert 'step_02_sample_time_jitter_ms' in result, "Missing jitter field"
    assert result['step_02_jitter_status'] == 'REVIEW', f"Expected REVIEW, got {result['step_02_jitter_status']}"
    print(f"         Jitter: {result['step_02_sample_time_jitter_ms']:.4f} ms")

test_jitter_known()

@test("Gate 2: Low jitter returns PASS")
def test_jitter_pass():
    from src.resampling import compute_sample_jitter
    
    np.random.seed(42)
    time_s = np.arange(1000) / 120.0
    time_s += np.random.normal(0, 0.0005, 1000)  # 0.5ms jitter
    time_s = np.sort(time_s)
    
    result = compute_sample_jitter(time_s)
    assert result['step_02_jitter_status'] == 'PASS', f"Expected PASS, got {result['step_02_jitter_status']}"

test_jitter_pass()

@test("Gate 2: Jitter units are milliseconds")
def test_jitter_units():
    from src.resampling import compute_sample_jitter
    
    time_s = np.arange(1000) / 120.0
    result = compute_sample_jitter(time_s)
    
    # For perfect timing, jitter should be ~0, definitely < 100ms
    assert result['step_02_sample_time_jitter_ms'] < 100, "Jitter seems to be in wrong units"

test_jitter_units()


print("\n--- Gate 3: Filtering ---")

@test("Gate 3: Body regions have extended range")
def test_regions_range():
    from src.filtering import BODY_REGIONS
    
    for region, config in BODY_REGIONS.items():
        cutoff_range = config.get('cutoff_range', (0, 0))
        assert cutoff_range[1] >= 10, f"Region {region} has narrow range: {cutoff_range}"
        print(f"         {region}: {cutoff_range}")

test_regions_range()

@test("Gate 3: WINTER_FMAX is 16 Hz")
def test_fmax():
    from src.filtering import WINTER_FMAX
    assert WINTER_FMAX == 16, f"Expected 16, got {WINTER_FMAX}"

test_fmax()


print("\n--- Gate 4: ISB Compliance ---")

@test("Gate 4: Euler sequences for known joints")
def test_euler_known():
    from src.euler_isb import get_euler_sequences_audit
    
    joint_list = ['Hips', 'LeftUpLeg', 'LeftLeg', 'Spine', 'LeftArm']
    result = get_euler_sequences_audit(joint_list)
    
    assert result['step_06_isb_compliant'] == True, "Should be ISB compliant"
    assert 'step_06_euler_sequences_used' in result
    print(f"         Sequences: {result['step_06_euler_sequences_used']}")

test_euler_known()

@test("Gate 4: Unknown joint flags non-compliant")
def test_euler_unknown():
    from src.euler_isb import get_euler_sequences_audit
    
    joint_list = ['Hips', 'UnknownJoint123', 'Spine']
    result = get_euler_sequences_audit(joint_list)
    
    assert result['step_06_isb_compliant'] == False, "Should NOT be ISB compliant"

test_euler_unknown()

@test("Gate 4: Quaternion health thresholds")
def test_quat_thresholds():
    from src.euler_isb import assess_quaternion_health
    
    result_pass = assess_quaternion_health(0.005)
    assert result_pass['step_06_math_status'] == 'PASS', f"0.005 should be PASS, got {result_pass['step_06_math_status']}"
    
    result_review = assess_quaternion_health(0.03)
    assert result_review['step_06_math_status'] == 'REVIEW', f"0.03 should be REVIEW, got {result_review['step_06_math_status']}"
    
    result_reject = assess_quaternion_health(0.08)
    assert result_reject['step_06_math_status'] == 'REJECT', f"0.08 should be REJECT, got {result_reject['step_06_math_status']}"

test_quat_thresholds()


print("\n--- Gate 5: Burst Classification ---")

@test("Gate 5: Velocity thresholds correct")
def test_velocity_thresholds():
    from src.burst_classification import VELOCITY_TRIGGER, VELOCITY_EXTREME
    
    assert VELOCITY_TRIGGER == 2000, f"TRIGGER should be 2000, got {VELOCITY_TRIGGER}"
    assert VELOCITY_EXTREME == 5000, f"EXTREME should be 5000, got {VELOCITY_EXTREME}"

test_velocity_thresholds()

@test("Gate 5: 3 frames = ARTIFACT")
def test_tier_artifact():
    from src.burst_classification import classify_burst_events
    
    vel = np.zeros((100, 1))
    vel[10:13, 0] = 2500  # Exactly 3 frames
    result = classify_burst_events(vel, fs=120.0)
    
    assert result['summary']['artifact_count'] >= 1, f"Expected artifact, got {result['summary']}"
    print(f"         Artifacts: {result['summary']['artifact_count']}")

test_tier_artifact()

@test("Gate 5: 4 frames = BURST")
def test_tier_burst_4():
    from src.burst_classification import classify_burst_events
    
    vel = np.zeros((100, 1))
    vel[10:14, 0] = 2500  # Exactly 4 frames
    result = classify_burst_events(vel, fs=120.0)
    
    assert result['summary']['burst_count'] >= 1, f"Expected burst, got {result['summary']}"
    print(f"         Bursts: {result['summary']['burst_count']}")

test_tier_burst_4()

@test("Gate 5: 8 frames = FLOW")
def test_tier_flow():
    from src.burst_classification import classify_burst_events
    
    vel = np.zeros((100, 1))
    vel[10:18, 0] = 2500  # Exactly 8 frames
    result = classify_burst_events(vel, fs=120.0)
    
    assert result['summary']['flow_count'] >= 1, f"Expected flow, got {result['summary']}"
    print(f"         Flows: {result['summary']['flow_count']}")

test_tier_flow()

@test("Gate 5: Clean stats exclude artifacts")
def test_clean_stats():
    from src.burst_classification import classify_burst_events, compute_clean_statistics
    
    velocity = np.ones((1000, 1)) * 500  # Normal 500 deg/s
    velocity[100:102, 0] = 5000  # 2-frame artifact spike
    
    result = classify_burst_events(velocity, fs=120.0)
    clean = compute_clean_statistics(velocity, result)
    
    raw_max = clean['raw_statistics']['max_deg_s']
    clean_max = clean['clean_statistics']['max_deg_s']
    
    assert raw_max > 4000, f"Raw max should be ~5000, got {raw_max}"
    assert clean_max < 1000, f"Clean max should be ~500, got {clean_max}"
    print(f"         Raw: {raw_max:.1f}, Clean: {clean_max:.1f}")

test_clean_stats()

@test("Gate 5: Clean max <= Raw max always")
def test_clean_lte_raw():
    from src.burst_classification import classify_burst_events, compute_clean_statistics
    
    for seed in range(5):
        np.random.seed(seed)
        velocity = np.random.randn(1000, 3) * 800
        velocity[np.random.randint(0, 1000, 5), :] = 3000
        
        result = classify_burst_events(velocity, fs=120.0)
        clean = compute_clean_statistics(velocity, result)
        
        assert clean['clean_statistics']['max_deg_s'] <= clean['raw_statistics']['max_deg_s'], \
            f"Clean ({clean['clean_statistics']['max_deg_s']}) > Raw ({clean['raw_statistics']['max_deg_s']})"

test_clean_lte_raw()


# =============================================================================
# 2. AUDIT LOGGING & TRANSPARENCY
# =============================================================================

print("\n" + "="*70)
print("2. AUDIT LOGGING & TRANSPARENCY")
print("="*70)

@test("Audit: Burst fields complete")
def test_audit_complete():
    from src.burst_classification import classify_burst_events, generate_burst_audit_fields
    
    velocity = np.random.randn(1000, 5) * 500
    velocity[100:103, 0] = 3000
    
    result = classify_burst_events(velocity, fs=120.0)
    audit = generate_burst_audit_fields(result)
    
    required = ['step_06_burst_analysis', 'step_06_burst_decision', 
                'step_06_frames_to_exclude', 'step_06_frames_to_review']
    
    for field in required:
        assert field in audit, f"Missing field: {field}"
    
    print(f"         All {len(required)} required fields present")

test_audit_complete()

@test("Audit: Decision reason is descriptive")
def test_decision_reason():
    from src.burst_classification import classify_burst_events, generate_burst_audit_fields
    
    velocity = np.random.randn(1000, 5) * 500
    velocity[100:103, 0] = 3000
    
    result = classify_burst_events(velocity, fs=120.0)
    audit = generate_burst_audit_fields(result)
    
    reason = audit['step_06_burst_decision'].get('primary_reason', '')
    assert len(reason) > 10, f"Reason too short: {reason}"
    assert reason != 'N/A', "Reason should not be N/A"
    
    print(f"         Reason: {reason[:60]}...")

test_decision_reason()


# =============================================================================
# 3. EDGE CASES
# =============================================================================

print("\n" + "="*70)
print("3. EDGE CASE HANDLING")
print("="*70)

@test("Edge: Extreme single frame = ARTIFACT")
def test_extreme_single():
    from src.burst_classification import classify_burst_events
    
    velocity = np.zeros((1000, 1))
    velocity[500, 0] = 10000  # Single extreme frame
    
    result = classify_burst_events(velocity, fs=120.0)
    
    assert result['summary']['artifact_count'] >= 1, "Should detect artifact"
    assert 500 in result['frames_to_exclude'], "Frame 500 should be excluded"

test_extreme_single()

@test("Edge: Extreme sustained = REVIEW/REJECT")
def test_extreme_sustained():
    from src.burst_classification import classify_burst_events
    
    velocity = np.zeros((1000, 1))
    velocity[500:520, 0] = 10000  # 20 frames extreme
    
    result = classify_burst_events(velocity, fs=120.0)
    
    assert result['decision']['overall_status'] in ['REVIEW', 'REJECT'], \
        f"Expected REVIEW/REJECT, got {result['decision']['overall_status']}"

test_extreme_sustained()

@test("Edge: Quaternion error >= 0.05 = REJECT")
def test_quat_reject():
    from src.euler_isb import assess_quaternion_health
    
    result = assess_quaternion_health(0.10)
    assert result['step_06_math_status'] == 'REJECT', f"Expected REJECT, got {result['step_06_math_status']}"

test_quat_reject()


# =============================================================================
# 4. DATA INTEGRITY
# =============================================================================

print("\n" + "="*70)
print("4. DATA INTEGRITY")
print("="*70)

@test("Integrity: More artifacts = lower retained %")
def test_artifact_correlation():
    from src.burst_classification import classify_burst_events, compute_clean_statistics
    
    # Many artifacts
    vel_many = np.ones((1000, 1)) * 500
    for i in range(0, 1000, 50):
        vel_many[i:i+2, 0] = 3000
    
    # Few artifacts
    vel_few = np.ones((1000, 1)) * 500
    vel_few[100:102, 0] = 3000
    
    result_many = classify_burst_events(vel_many, fs=120.0)
    result_few = classify_burst_events(vel_few, fs=120.0)
    
    clean_many = compute_clean_statistics(vel_many, result_many)
    clean_few = compute_clean_statistics(vel_few, result_few)
    
    retained_many = clean_many['comparison']['data_retained_percent']
    retained_few = clean_few['comparison']['data_retained_percent']
    
    assert retained_many < retained_few, f"Many: {retained_many}%, Few: {retained_few}%"
    print(f"         Many artifacts: {retained_many:.2f}% retained")
    print(f"         Few artifacts: {retained_few:.2f}% retained")

test_artifact_correlation()

@test("Integrity: Frame indices within range")
def test_frame_range():
    from src.burst_classification import classify_burst_events
    
    n_frames = 500
    velocity = np.random.randn(n_frames, 3) * 800
    velocity[100:102, 0] = 3000
    
    result = classify_burst_events(velocity, fs=120.0)
    
    for idx in result['frames_to_exclude']:
        assert 0 <= idx < n_frames, f"Index {idx} out of range [0, {n_frames})"

test_frame_range()


# =============================================================================
# 5. INTEGRATION TEST
# =============================================================================

print("\n" + "="*70)
print("5. INTEGRATION TEST")
print("="*70)

@test("Integration: Full Gate 5 pipeline")
def test_integration():
    from src.burst_classification import classify_burst_events, generate_burst_audit_fields, compute_clean_statistics
    
    np.random.seed(42)
    n_frames = 3000
    n_joints = 10
    velocity = np.random.randn(n_frames, n_joints) * 600
    
    # Add events
    velocity[100:102, 0] = 2800   # Artifact
    velocity[500:505, 1] = 2500   # Burst
    velocity[1000:1020, 2] = 2200 # Flow
    velocity[2000:2001, 3] = 8000 # Extreme artifact
    
    joint_names = [f"Joint_{i}" for i in range(n_joints)]
    
    result = classify_burst_events(velocity, fs=120.0, joint_names=joint_names)
    audit = generate_burst_audit_fields(result)
    clean = compute_clean_statistics(velocity, result, joint_names)
    
    assert result['summary']['artifact_count'] >= 2
    assert result['summary']['burst_count'] >= 1
    assert result['summary']['flow_count'] >= 1
    assert clean['clean_statistics']['max_deg_s'] < clean['raw_statistics']['max_deg_s']
    
    print(f"         Artifacts: {result['summary']['artifact_count']}")
    print(f"         Bursts: {result['summary']['burst_count']}")
    print(f"         Flows: {result['summary']['flow_count']}")
    print(f"         Raw max: {clean['raw_statistics']['max_deg_s']:.1f} deg/s")
    print(f"         Clean max: {clean['clean_statistics']['max_deg_s']:.1f} deg/s")
    print(f"         Decision: {audit['step_06_burst_decision']['overall_status']}")

test_integration()


# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70)

print(f"\n✅ PASSED: {len(PASSED)}")
print(f"❌ FAILED: {len(FAILED)}")

if FAILED:
    print("\nFailed tests:")
    for name, reason in FAILED:
        print(f"  - {name}: {reason}")

print("\n" + "="*70)

if len(FAILED) == 0:
    print("🎉 ALL VERIFICATION TESTS PASSED!")
    sys.exit(0)
else:
    print(f"⚠️  {len(FAILED)} test(s) failed - review required")
    sys.exit(1)
