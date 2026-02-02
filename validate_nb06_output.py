"""
Quick validation script to check that notebook 06 has all required features.
Run this after executing the notebook to verify completeness.
"""

import pandas as pd
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent
RUN_ID = "734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002"
PARQUET_PATH = PROJECT_ROOT / "derivatives" / "step_06_kinematics" / "ultimate" / f"{RUN_ID}__kinematics_master.parquet"

# Required features per joint
REQUIRED_JOINT_FEATURES = {
    'orientation': ['raw_rel_qx', 'raw_rel_qy', 'raw_rel_qz', 'raw_rel_qw',
                    'zeroed_rel_qx', 'zeroed_rel_qy', 'zeroed_rel_qz', 'zeroed_rel_qw',
                    'zeroed_rel_rotvec_x', 'zeroed_rel_rotvec_y', 'zeroed_rel_rotvec_z',
                    'zeroed_rel_rotmag'],
    'angular': ['zeroed_rel_omega_x', 'zeroed_rel_omega_y', 'zeroed_rel_omega_z', 'zeroed_rel_omega_mag',
                'zeroed_rel_alpha_x', 'zeroed_rel_alpha_y', 'zeroed_rel_alpha_z', 'zeroed_rel_alpha_mag']
}

# Required features per segment
REQUIRED_SEGMENT_FEATURES = {
    'linear': ['lin_rel_px', 'lin_rel_py', 'lin_rel_pz',
               'lin_vel_rel_x', 'lin_vel_rel_y', 'lin_vel_rel_z', 'lin_vel_rel_mag',
               'lin_acc_rel_x', 'lin_acc_rel_y', 'lin_acc_rel_z', 'lin_acc_rel_mag']
}

def validate_parquet():
    """Validate that the parquet file has all required features."""
    
    if not PARQUET_PATH.exists():
        print(f"❌ ERROR: Parquet file not found: {PARQUET_PATH}")
        return False
    
    # Load parquet
    df = pd.read_parquet(PARQUET_PATH)
    print(f"✓ Loaded parquet: {len(df)} frames, {len(df.columns)} columns")
    
    # Extract joint names
    joint_cols = [c for c in df.columns if '__zeroed_rel_qx' in c]
    joints = [c.split('__')[0] for c in joint_cols]
    print(f"✓ Found {len(joints)} joints: {joints[:3]}...")
    
    # Extract segment names
    segment_cols = [c for c in df.columns if '__lin_rel_px' in c]
    segments = [c.split('__')[0] for c in segment_cols]
    print(f"✓ Found {len(segments)} segments with positions: {segments[:3]}...")
    
    # Validate joint features
    all_joint_features_present = True
    sample_joint = joints[0] if joints else None
    
    if sample_joint:
        missing_features = []
        for category, features in REQUIRED_JOINT_FEATURES.items():
            for feat in features:
                col_name = f"{sample_joint}__{feat}"
                if col_name not in df.columns:
                    missing_features.append(col_name)
                    all_joint_features_present = False
        
        if missing_features:
            print(f"❌ Missing joint features for '{sample_joint}':")
            for feat in missing_features:
                print(f"   - {feat}")
        else:
            print(f"✓ All required joint features present for '{sample_joint}'")
    
    # Validate segment features
    all_segment_features_present = True
    sample_segment = segments[0] if segments else None
    
    if sample_segment:
        missing_features = []
        for category, features in REQUIRED_SEGMENT_FEATURES.items():
            for feat in features:
                col_name = f"{sample_segment}__{feat}"
                if col_name not in df.columns:
                    missing_features.append(col_name)
                    all_segment_features_present = False
        
        if missing_features:
            print(f"❌ Missing segment features for '{sample_segment}':")
            for feat in missing_features:
                print(f"   - {feat}")
        else:
            print(f"✓ All required segment features present for '{sample_segment}'")
    
    # Check for critical ML/HMM/RQA features
    print("\n=== Critical Feature Check (ML/HMM/RQA) ===")
    critical_patterns = ['rotvec', 'rotmag', 'omega_mag', 'alpha_mag', 'vel_mag', 'acc_mag']
    critical_found = {}
    
    for pattern in critical_patterns:
        matching_cols = [c for c in df.columns if pattern in c]
        critical_found[pattern] = len(matching_cols) > 0
        status = "✓" if critical_found[pattern] else "❌"
        print(f"{status} {pattern}: {len(matching_cols)} columns")
    
    # Overall validation
    print("\n=== Overall Validation ===")
    all_critical = all(critical_found.values())
    overall_pass = all_joint_features_present and all_segment_features_present and all_critical
    
    if overall_pass:
        print("✅ VALIDATION PASSED - All required features present")
        print(f"\nFeature Summary:")
        print(f"  - Joints: {len(joints)}")
        print(f"  - Segments: {len(segments)}")
        print(f"  - Total frames: {len(df)}")
        print(f"  - Total columns: {len(df.columns)}")
        print(f"  - File size: {PARQUET_PATH.stat().st_size / 1024 / 1024:.2f} MB")
        return True
    else:
        print("❌ VALIDATION FAILED - See errors above")
        return False

if __name__ == "__main__":
    import sys
    success = validate_parquet()
    sys.exit(0 if success else 1)
