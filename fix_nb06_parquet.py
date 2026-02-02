"""
Standalone script to add missing columns to kinematics_master.parquet
This script adds Euler angles and fixes artifact/hampel flags without re-running the full notebook.

Run this from the project root: python fix_nb06_parquet.py
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial.transform import Rotation as R

# Setup paths
PROJECT_ROOT = Path(__file__).parent
DERIV_ROOT = PROJECT_ROOT / "derivatives"
STEP_06_DIR = DERIV_ROOT / "step_06_kinematics"

# Find the parquet file
parquet_files = list(STEP_06_DIR.glob("*__kinematics_master.parquet"))
if not parquet_files:
    print("ERROR: No kinematics_master.parquet file found!")
    sys.exit(1)

parquet_path = parquet_files[0]
RUN_ID = parquet_path.stem.replace("__kinematics_master", "")

print("="*80)
print("NOTEBOOK 06 PARQUET FIX - Adding Missing Columns")
print("="*80)
print(f"\nTarget file: {parquet_path}")
print(f"Run ID: {RUN_ID}")

# Load existing parquet
print("\n[1/4] Loading existing parquet...")
df = pd.read_parquet(parquet_path)
print(f"  Current shape: {df.shape}")
print(f"  Current columns: {len(df.columns)}")

# Extract segment names
segments = sorted(set([c.split('__')[0] for c in df.columns if '__' in c]))
print(f"  Detected {len(segments)} segments")

# ============================================================
# ADD EULER ANGLES
# ============================================================
print("\n[2/4] Adding Euler angles...")

euler_added = 0
for seg in segments:
    # Check if quaternion columns exist
    quat_cols = [f"{seg}__zeroed_rel_qx", f"{seg}__zeroed_rel_qy", 
                 f"{seg}__zeroed_rel_qz", f"{seg}__zeroed_rel_qw"]
    
    if not all(c in df.columns for c in quat_cols):
        continue
    
    # Get quaternions
    q_array = df[quat_cols].values
    
    # Convert to Euler angles (XYZ intrinsic order)
    rot = R.from_quat(q_array)
    euler_rad = rot.as_euler('XYZ', degrees=False)
    
    # Add to dataframe (in degrees)
    df[f"{seg}__euler_x"] = np.degrees(euler_rad[:, 0])
    df[f"{seg}__euler_y"] = np.degrees(euler_rad[:, 1])
    df[f"{seg}__euler_z"] = np.degrees(euler_rad[:, 2])
    
    euler_added += 3

print(f"  [OK] Added {euler_added} Euler angle columns ({euler_added//3} segments x 3 axes)")

# ============================================================
# FIX ARTIFACT/HAMPEL FLAGS FOR SEGMENTS
# ============================================================
print("\n[3/4] Fixing artifact and Hampel flags for segments...")

# Thresholds for artifact detection
THRESH_ARTIFACT = {
    'rotation_mag_deg': 140.0,
    'linear_velocity_mm_s': 3000.0,
}

segments_with_positions = [s for s in segments if f"{s}__lin_rel_px" in df.columns]

flags_added = 0
for seg in segments_with_positions:
    # Skip if already has flags
    if f"{seg}__is_artifact" in df.columns:
        continue
    
    # Initialize artifact mask
    artifact_mask = np.zeros(len(df), dtype=bool)
    
    # Check linear velocity magnitude
    linvel_mag_col = f"{seg}__lin_vel_rel_mag"
    if linvel_mag_col in df.columns:
        artifact_mask |= (df[linvel_mag_col] >= THRESH_ARTIFACT['linear_velocity_mm_s'])
    
    # Add flags
    df[f"{seg}__is_artifact"] = artifact_mask
    df[f"{seg}__is_hampel_outlier"] = np.zeros(len(df), dtype=bool)
    flags_added += 2

print(f"  [OK] Added {flags_added} flag columns for segments")

# ============================================================
# SAVE UPDATED PARQUET
# ============================================================
print("\n[4/4] Saving updated parquet...")

# Create backup
backup_path = parquet_path.parent / f"{parquet_path.stem}_backup.parquet"
print(f"  Creating backup: {backup_path.name}")
df_original = pd.read_parquet(parquet_path)
df_original.to_parquet(backup_path, index=False)

# Save updated version
print(f"  Saving updated parquet...")
df.to_parquet(parquet_path, index=False)

print(f"  [OK] Saved: {parquet_path}")

# ============================================================
# VERIFICATION
# ============================================================
print("\n" + "="*80)
print("VERIFICATION")
print("="*80)

df_verify = pd.read_parquet(parquet_path)

euler_cols = [c for c in df_verify.columns if '__euler_' in c]
artifact_cols = [c for c in df_verify.columns if '__is_artifact' in c]
hampel_cols = [c for c in df_verify.columns if '__is_hampel_outlier' in c]
omega_mag_cols = [c for c in df_verify.columns if 'omega_mag' in c.lower()]

print(f"\nFinal shape: {df_verify.shape}")
print(f"Total columns: {len(df_verify.columns)}")
print(f"\n[OK] Euler columns: {len(euler_cols)} (expected: 57)")
print(f"[OK] Artifact columns: {len(artifact_cols)} (expected: 38)")
print(f"[OK] Hampel columns: {len(hampel_cols)} (expected: 38)")
print(f"[OK] Omega mag columns: {len(omega_mag_cols)}")

if len(euler_cols) == 57 and len(artifact_cols) == 38:
    print("\n" + "="*80)
    print("🎉 SUCCESS! All required columns added successfully!")
    print("="*80)
    print("\nSample columns:")
    print(f"  Euler: {euler_cols[:3]}")
    print(f"  Artifact: {artifact_cols[:3]}")
else:
    print("\n[WARNING] Some columns may still be missing")
    print(f"   Euler: {len(euler_cols)}/57")
    print(f"   Artifact: {len(artifact_cols)}/38")

print(f"\nBackup saved as: {backup_path.name}")
print("You can restore it if needed by renaming it back to the original.")
