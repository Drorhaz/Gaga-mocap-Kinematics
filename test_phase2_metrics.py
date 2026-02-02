"""
Quick test to verify Phase 2 implementation (Path Length & Bilateral Symmetry).

Run this after executing notebook 06_ultimate_kinematics.ipynb to verify
that the new Phase 2 metrics are correctly exported to validation_report.json.
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = r"c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga"
DERIV_ROOT = os.path.join(PROJECT_ROOT, "derivatives")

# Find the most recent validation_report.json
validation_reports = list(Path(DERIV_ROOT).rglob("*__validation_report.json"))

if not validation_reports:
    print("❌ ERROR: No validation_report.json files found!")
    print(f"\nSearched in: {DERIV_ROOT}")
    print("\nPlease run notebook 06_ultimate_kinematics.ipynb first.")
    exit(1)

# Sort by modification time (most recent first)
validation_reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
latest_report = validation_reports[0]

print("="*80)
print("PHASE 2 VALIDATION TEST")
print("="*80)
print(f"\nTesting file: {latest_report.name}")
print(f"Modified: {latest_report.stat().st_mtime}")

# Load JSON
with open(latest_report, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\nRun ID: {data.get('run_id', 'N/A')}")
print(f"Total Frames: {data.get('total_frames', 0)}")

# Check Phase 2 fields
print("\n" + "="*80)
print("PHASE 2 FIELDS CHECK")
print("="*80)

# 1. Path Length
if "path_length_m" in data:
    path_lengths = data["path_length_m"]
    print(f"\n✅ path_length_m: FOUND ({len(path_lengths)} segments)")
    
    # Sort by value
    sorted_paths = sorted(path_lengths.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTop 5 most active segments:")
    for i, (seg, length) in enumerate(sorted_paths[:5], 1):
        print(f"  {i}. {seg:20s}: {length:8.2f} m")
    
    print(f"\nRange: {min(path_lengths.values()):.2f}m - {max(path_lengths.values()):.2f}m")
    print(f"Total distance traveled: {sum(path_lengths.values()):.2f}m")
else:
    print("\n❌ path_length_m: MISSING")
    print("   → Check notebook 06, cell 15 (path length computation)")

# 2. Bilateral Symmetry
if "bilateral_symmetry" in data:
    bilateral = data["bilateral_symmetry"]
    print(f"\n✅ bilateral_symmetry: FOUND ({len(bilateral)} metrics)")
    
    # Extract symmetry indices
    symmetry_data = []
    for key, value in bilateral.items():
        if isinstance(value, dict):
            symmetry_data.append((key, value["symmetry_index"], value.get("percent_diff", 0)))
    
    # Sort by symmetry (most asymmetric first)
    symmetry_data.sort(key=lambda x: x[1])
    
    print(f"\nTop 5 most asymmetric pairs:")
    for i, (metric, sym_idx, pct_diff) in enumerate(symmetry_data[:5], 1):
        print(f"  {i}. {metric:30s}: {sym_idx:.3f} ({pct_diff:.1f}% diff)")
    
    print(f"\nTop 5 most symmetric pairs:")
    for i, (metric, sym_idx, pct_diff) in enumerate(symmetry_data[-5:], 1):
        print(f"  {i}. {metric:30s}: {sym_idx:.3f} ({pct_diff:.1f}% diff)")
    
    # Overall statistics
    indices = [x[1] for x in symmetry_data]
    mean_sym = sum(indices) / len(indices) if indices else 0
    min_sym = min(indices) if indices else 0
    max_sym = max(indices) if indices else 0
    
    print(f"\nOverall symmetry statistics:")
    print(f"  Mean: {mean_sym:.3f}")
    print(f"  Min:  {min_sym:.3f} (most asymmetric)")
    print(f"  Max:  {max_sym:.3f} (most symmetric)")
else:
    print("\n❌ bilateral_symmetry: MISSING")
    print("   → Check notebook 06, cell 16 (bilateral symmetry computation)")

# 3. Overall Status
print("\n" + "="*80)
print("OVERALL STATUS")
print("="*80)

has_path_length = "path_length_m" in data
has_bilateral = "bilateral_symmetry" in data

if has_path_length and has_bilateral:
    print("\n✅ PHASE 2: COMPLETE")
    print("\nAll Phase 2 metrics are present and contain data.")
    print("You can now run notebook 08_engineering_physical_audit.ipynb")
    print("to see these metrics in the engineering DataFrame and Excel export.")
elif has_path_length or has_bilateral:
    print("\n⚠️ PHASE 2: INCOMPLETE")
    print("\nSome Phase 2 metrics are missing.")
    print("Re-run notebook 06_ultimate_kinematics.ipynb (cells 15-16).")
else:
    print("\n❌ PHASE 2: NOT FOUND")
    print("\nNo Phase 2 metrics detected in validation_report.json")
    print("\nTo fix:")
    print("  1. Open notebooks/06_ultimate_kinematics.ipynb")
    print("  2. Run all cells (especially 15-16 for Phase 2)")
    print("  3. Re-run this test")

print("\n" + "="*80)
print("END OF TEST")
print("="*80)
