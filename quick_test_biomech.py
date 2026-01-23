"""Quick check for specific run with velocity data."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils_nb07 import score_biomechanics, load_json_safe

# Check specific run
run_id = "763_T2_P2_R2_Take_2025-12-25 10.51.23 AM_005"
s06_file = Path(f"derivatives/step_06_kinematics/{run_id}__audit_metrics.json")
s02_file = Path(f"derivatives/step_02_preprocess/{run_id}__preprocess_summary.json")

print(f"Testing Run: {run_id}")
print("=" * 80)

s06 = load_json_safe(str(s06_file))
s02 = load_json_safe(str(s02_file)) if s02_file.exists() else {}

if s06:
    # Check raw data
    raw_vel = s06.get('metrics', {}).get('angular_velocity', {}).get('max', 0)
    clean_vel = s06.get('clean_statistics', {}).get('clean_statistics', {}).get('max_deg_s', 0)
    burst_dec = s06.get('step_06_burst_decision', {}).get('overall_status', 'N/A')
    
    print(f"\nRaw Data:")
    print(f"  Raw Max Velocity:    {raw_vel:.2f} deg/s")
    print(f"  Clean Max Velocity:  {clean_vel:.2f} deg/s")
    print(f"  Burst Decision:      {burst_dec}")
    
    # Test scoring
    steps = {"step_06": s06, "step_02": s02}
    score, scorecard = score_biomechanics(steps)
    
    print(f"\nBiomechanics Score: {score:.2f}")
    print(f"\nComponent Scores:")
    for comp_name, comp_data in scorecard['components'].items():
        print(f"  {comp_name}: {comp_data['score']:.2f}")
        print(f"    Source: {comp_data['details'].get('velocity_source', 'N/A')}")
        print(f"    Assessment: {comp_data['details'].get('velocity_assessment', comp_data['details'].get('bone_stability', comp_data['details'].get('burst_assessment', 'N/A')))}")
    
    print(f"\nNeutralization: {scorecard['neutralization_applied']['tier_1_artifacts_excluded']}")
    print(f"\nResult: {'[OK] Clean data used!' if scorecard['neutralization_applied']['tier_1_artifacts_excluded'] else '[INFO] No artifacts to exclude'}")
else:
    print("[ERROR] Could not load file")
