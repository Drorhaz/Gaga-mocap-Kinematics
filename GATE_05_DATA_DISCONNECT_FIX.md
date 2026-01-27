# Gate 5: Data Disconnect Fix Documentation

## The Problem

**Finding:** `Parameter_Audit` shows thousands of outliers (e.g., 2,013 in the full dataset), but the `Quality_Report` and `Executive_Summary` show **0 for all burst metrics** (`Burst_Artifact_Count`, `Burst_Count`, `Burst_Flow_Count`).

**Root Cause:** There is a **total decoupling** between Step 06 (Processing) and Step 07 (Audit). The burst classification data exists in the pipeline but is not being saved to the Step 06 JSON summary file, so Step 07 cannot pick it up.

## Data Flow Architecture

### Step 06: Data Generation (notebook `06_rotvec_omega.ipynb`)

The Gate 5 cell in notebook 06 does the following:

```python
# In Cell: "GATE 4 & 5 INTEGRATION"
from burst_classification import classify_burst_events, generate_burst_audit_fields

# 1. Run burst classification
burst_result = classify_burst_events(ang_vel_data, fs=fs, joint_names=vel_joint_names)

# Returns:
# {
#   'joint_status_mask': (N, J) int8 array with codes:
#     - 0 = NORMAL
#     - 1 = ARTIFACT (1-3 frames, <25ms) - EXCLUDE
#     - 2 = BURST (4-7 frames, 33-58ms) - REVIEW
#     - 3 = FLOW (8+ frames, >65ms) - ACCEPT
#   'events': List of event dictionaries
#   'summary': {
#       'artifact_count': int,
#       'burst_count': int,
#       'flow_count': int,
#       'total_events': int,
#       ...
#   }
#   'frames_to_exclude': [list of frame indices for Tier 1]
#   'frames_to_review': [list of frame indices for Tier 2/3]
# }

# 2. Generate audit fields
gate_5_fields = generate_burst_audit_fields(burst_result)

# Creates structure:
# {
#   "step_06_burst_analysis": {
#     "classification": {
#       "artifact_count": int,
#       "burst_count": int,
#       "flow_count": int,
#       "total_events": int
#     },
#     "frame_statistics": { ... },
#     "timing": { ... },
#     "density_assessment": { ... },
#     "events": [ ... ]
#   },
#   "step_06_burst_decision": { ... },
#   "step_06_frames_to_exclude": [ ... ],
#   "step_06_frames_to_review": [ ... ],
#   "step_06_data_validity": { ... }
# }

# 3. Save to JSON
updated_summary.update(gate_5_fields)
with open(summary_path, 'w') as f:
    json.dump(updated_summary, f, indent=4)
```

### Step 07: Data Consumption (`src/utils_nb07.py`)

The `build_quality_row()` function attempts to extract burst metrics:

```python
# Lines 864-867
"Burst_Artifact_Count": safe_int(safe_get_path(s06, "step_06_burst_analysis.classification.artifact_count")),
"Burst_Count": safe_int(safe_get_path(s06, "step_06_burst_analysis.classification.burst_count")),
"Burst_Flow_Count": safe_int(safe_get_path(s06, "step_06_burst_analysis.classification.flow_count")),
"Burst_Total_Events": safe_int(safe_get_path(s06, "step_06_burst_analysis.classification.total_events")),
```

## The Disconnect

The current Step 06 JSON files (e.g., `734_T1_P1_R1_Take 2025-12-01 02.18.27 PM__kinematics_summary.json`) **do NOT contain** the `step_06_burst_analysis` field because:

1. The Gate 4 & 5 Integration cell in notebook 06 was not executed, OR
2. The notebook was run before the Gate 5 implementation existed, OR  
3. The cell execution failed silently

## The Fix

### Required Action: Re-run Step 06 with Gate 5 Cell

For each recording, the user must:

1. **Open notebook:** `06_rotvec_omega.ipynb`
2. **Set RUN_ID** to the recording identifier
3. **Execute the Gate 4 & 5 Integration cell** (the cell that imports `burst_classification`)
4. **Verify output:** Check that the JSON summary contains `step_06_burst_analysis`

### Verification Script

```python
import json
import glob

# Check if Gate 5 data exists in Step 06 JSON files
deriv_root = "derivatives/step_06_kinematics"
json_files = glob.glob(f"{deriv_root}/*__kinematics_summary.json")

for json_path in json_files:
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    run_id = data.get('run_id', 'UNKNOWN')
    has_gate5 = 'step_06_burst_analysis' in data
    
    if has_gate5:
        burst_data = data['step_06_burst_analysis']['classification']
        print(f"✅ {run_id}: Gate 5 present")
        print(f"   Artifacts: {burst_data['artifact_count']}, Bursts: {burst_data['burst_count']}, Flows: {burst_data['flow_count']}")
    else:
        print(f"❌ {run_id}: Gate 5 MISSING - need to re-run notebook 06")
```

### Expected JSON Structure After Fix

The Step 06 JSON should contain:

```json
{
  "run_id": "...",
  "overall_status": "PASS",
  "metrics": { ... },
  
  "step_06_burst_analysis": {
    "classification": {
      "artifact_count": 234,
      "burst_count": 45,
      "flow_count": 12,
      "total_events": 291
    },
    "frame_statistics": {
      "total_frames": 30798,
      "artifact_frames": 567,
      "burst_frames": 234,
      "flow_frames": 189,
      "artifact_rate_percent": 1.84,
      "outlier_frames_total": 990,
      "outlier_rate_percent": 3.21
    },
    "timing": {
      "recording_duration_sec": 256.65,
      "burst_events_per_min": 6.81,
      "max_consecutive_frames": 23,
      "mean_event_duration_ms": 18.45,
      "max_event_duration_ms": 175.2
    },
    "density_assessment": {
      "status": "ACCEPTABLE",
      "reason": "Event density within normal range"
    },
    "events": [ ... ]
  },
  "step_06_burst_decision": {
    "overall_status": "ACCEPT_HIGH_INTENSITY",
    "primary_reason": "High-intensity movement confirmed: 12 sustained flow events"
  },
  "step_06_frames_to_exclude": [123, 124, 125, ...],
  "step_06_frames_to_review": [456, 457, 458, ...],
  "step_06_data_validity": {
    "usable": true,
    "excluded_frame_count": 567,
    "excluded_frame_percent": 1.84,
    "note": "567 artifact frames excluded; burst/flow frames preserved"
  }
}
```

## Testing the Fix

After re-running Step 06 for all recordings:

1. **Re-run notebook 07** (`07_master_quality_report.ipynb`)
2. **Check the Excel output:** `reports/Master_Audit_Log_*.xlsx`
3. **Verify columns:** `Burst_Artifact_Count`, `Burst_Count`, `Burst_Flow_Count` should now show non-zero values

### Expected Results in Quality Report

| Run_ID | Burst_Artifact_Count | Burst_Count | Burst_Flow_Count | Burst_Total_Events | Artifact_Rate_% |
|--------|---------------------|-------------|------------------|-------------------|----------------|
| 734_T1_P1 | 234 | 45 | 12 | 291 | 1.84 |
| 734_T1_P2 | 189 | 38 | 15 | 242 | 1.52 |
| 763_T2_P2 | 312 | 67 | 23 | 402 | 2.45 |

## Understanding the Mask Codes

The `joint_status_mask` is an (N_frames × N_joints) array where each element is:

- **0 (NORMAL)**: Frame is clean, no high-velocity event
- **1 (ARTIFACT)**: 1-3 frames (<25ms) - physically impossible spike, **EXCLUDE from statistics**
- **2 (BURST)**: 4-7 frames (33-58ms) - potential whip/shake, **REVIEW** required
- **3 (FLOW)**: 8+ frames (>65ms) - sustained intentional movement, **ACCEPT**

### How to Use the Mask

The mask can be loaded from the parquet file:

```python
import pandas as pd

# Load the status mask
df_status = pd.read_parquet(f"derivatives/step_06_kinematics/{run_id}__joint_status_mask.parquet")

# Columns:
# - frame_idx: Frame number
# - time_s: Timestamp
# - {Joint}__status: Status code (0-3)
# - {Joint}__velocity_deg_s: Angular velocity
# - any_outlier: True if any joint has status > 0
# - max_tier: Highest tier across all joints

# Example: Find all artifact frames
artifact_frames = df_status[df_status['max_tier'] == 1]['frame_idx'].tolist()

# Example: Count artifacts per joint
for joint in joint_names:
    artifact_count = (df_status[f'{joint}__status'] == 1).sum()
    print(f"{joint}: {artifact_count} artifact frames")
```

## Implementation Status

- ✅ **Gate 5 Module** (`src/burst_classification.py`): Complete
- ✅ **Notebook 06 Integration**: Cell ready for execution
- ✅ **Step 07 Reading Logic** (`src/utils_nb07.py`): Already implemented (lines 864-885)
- ❌ **Data Present in JSON Files**: **MISSING** - requires notebook 06 re-run
- ⏳ **Action Required**: User must execute Gate 5 cell for each recording

## Summary

The pipeline architecture is **correct** - Step 06 generates the data and Step 07 knows how to read it. The issue is that **the data hasn't been generated yet** for the existing recordings. Once the user re-runs the Gate 4 & 5 cell in notebook 06 for each recording, the burst metrics will automatically appear in the Master Quality Report.

---

**Version:** 2026-01-23  
**Status:** Documentation complete, awaiting user action to re-run notebook 06
