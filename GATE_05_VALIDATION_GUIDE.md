# How to Validate the Gate 5 Fix

## Quick Validation (1 minute)

### Method 1: Run the Validation Script

```bash
python validate_gate5_fix.py
```

**What it checks:**
- ✅ All Step 06 JSON files have Gate 5 fields
- ✅ Event counts are populated (artifacts, bursts, flows)
- ✅ Decision status is valid
- ✅ Parquet mask files exist and load correctly
- ✅ Data structures are complete

**Expected output when fixed:**
```
====================================================================================================
GATE 5 FIX VALIDATION REPORT
====================================================================================================

Total Recordings: 33
  [OK] Valid: 33 (100.0%)
  [FAIL] Invalid: 0 (0.0%)

====================================================================================================
[OK] VALID RECORDINGS - GATE 5 DATA PRESENT
====================================================================================================

Aggregate Event Statistics:
  Total Artifacts (Tier 1): 7,234
  Total Bursts (Tier 2): 1,456
  Total Flows (Tier 3): 389
  Total Events: 9,079

[SUCCESS] All recordings have valid Gate 5 data!
```

---

## Detailed Validation (5 minutes)

### Method 2: Validate a Single Recording

```bash
python validate_gate5_fix.py "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM"
```

**Shows detailed checks for one recording:**
- JSON file structure
- All required fields present
- Event count consistency
- Decision reasoning
- Mask file validity

---

## Method 3: Manual Verification Steps

### Step 1: Check Step 06 JSON Files

```python
import json

# Pick any recording
RUN_ID = "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM"
json_path = f"derivatives/step_06_kinematics/{RUN_ID}__kinematics_summary.json"

with open(json_path, 'r') as f:
    data = json.load(f)

# Should all print True:
print('step_06_burst_analysis' in data)
print('step_06_burst_decision' in data)
print('step_06_frames_to_exclude' in data)

# Should show real counts (not zeros):
print(data['step_06_burst_analysis']['classification'])
# Expected: {'artifact_count': 234, 'burst_count': 45, 'flow_count': 12, 'total_events': 291}
```

### Step 2: Check Parquet Mask Files

```python
import pandas as pd
import os

mask_path = f"derivatives/step_06_kinematics/{RUN_ID}__joint_status_mask.parquet"

# Should be True:
print(os.path.exists(mask_path))

# Should load without errors:
df_mask = pd.read_parquet(mask_path)
print(df_mask.shape)  # Example: (30798, 47) - frames x columns

# Check columns exist:
required_cols = ['frame_idx', 'time_s', 'any_outlier', 'max_tier']
print(all(col in df_mask.columns for col in required_cols))  # Should be True

# Count events per tier:
print(f"Normal frames (0): {(df_mask['max_tier'] == 0).sum()}")
print(f"Artifact frames (1): {(df_mask['max_tier'] == 1).sum()}")
print(f"Burst frames (2): {(df_mask['max_tier'] == 2).sum()}")
print(f"Flow frames (3): {(df_mask['max_tier'] == 3).sum()}")
```

### Step 3: Check Master Quality Report (Step 07)

```python
import pandas as pd

# Load the latest Excel report
excel_path = "reports/Master_Audit_Log_20260123_020132.xlsx"  # Use latest timestamp

# Load Quality Report sheet
df_quality = pd.read_excel(excel_path, sheet_name='Quality_Report')

# Check burst columns - should have non-zero values:
burst_cols = ['Burst_Artifact_Count', 'Burst_Count', 'Burst_Flow_Count', 
              'Burst_Total_Events', 'Artifact_Rate_%']

print("\nBurst Metrics Summary:")
print(df_quality[burst_cols].describe())

# Should see non-zero means and maxes:
# Example:
#        Burst_Artifact_Count  Burst_Count  Burst_Flow_Count
# mean              219.2          44.1            11.8
# max               456.0          89.0            23.0
```

---

## Visual Validation Checklist

### Before Fix (BROKEN):
- [ ] `verify_gate5_data.py` shows 0/33 recordings
- [ ] Step 06 JSON missing `step_06_burst_analysis`
- [ ] Excel columns show all zeros
- [ ] No parquet mask files

### After Fix (WORKING):
- [x] `validate_gate5_fix.py` shows 33/33 valid
- [x] Step 06 JSON contains `step_06_burst_analysis` with event counts
- [x] Excel columns show real counts (hundreds of artifacts, tens of bursts/flows)
- [x] Parquet mask files exist for all recordings
- [x] Mask files have proper columns and tier distributions

---

## Expected Values After Fix

### Typical Recording Stats (will vary per recording):

| Metric | Typical Range | What It Means |
|--------|---------------|---------------|
| **Artifact Count** | 50-500 | Short impossible spikes (1-3 frames) |
| **Burst Count** | 10-100 | Medium rapid movements (4-7 frames) |
| **Flow Count** | 5-30 | Long sustained movements (8+ frames) |
| **Total Events** | 100-600 | Sum of all high-velocity events |
| **Artifact Rate %** | 0.5-5.0% | Percentage of frames that are artifacts |

### Decision Distribution (across all recordings):

| Status | Expected % | Meaning |
|--------|-----------|---------|
| **ACCEPT_HIGH_INTENSITY** | 60-80% | Normal Gaga movement |
| **REVIEW** | 15-30% | Higher than usual events, check visually |
| **REJECT** | 0-10% | Too many artifacts, data quality issue |

---

## Troubleshooting Validation Failures

### Issue: "Missing Gate 5 fields"

**Cause:** Gate 5 cell wasn't run for this recording

**Fix:**
1. Open `notebooks/06_rotvec_omega.ipynb`
2. Set `RUN_ID` to the failing recording
3. Run "GATE 4 & 5 INTEGRATION" cell
4. Re-run validation

### Issue: "Classification counts missing"

**Cause:** Gate 5 cell crashed partway through

**Solution:**
```python
# Check for errors in the notebook cell output
# Look for Python tracebacks or "No angular velocity data available"
# If found, run the full notebook 06 from the beginning
```

### Issue: "Mask parquet not found"

**Cause:** Cell ran but didn't save the mask file

**Check:**
```python
# Manually save it:
from burst_classification import create_joint_status_dataframe
df_status = create_joint_status_dataframe(time_array, ang_vel_data, vel_joint_names, burst_result)
df_status.to_parquet(f"derivatives/step_06_kinematics/{RUN_ID}__joint_status_mask.parquet")
```

### Issue: "Total events mismatch"

**Cause:** Data inconsistency (very rare)

**Impact:** Low - counts are still valid

**Action:** Review the specific recording's burst_result if needed

---

## Final Validation: Master Quality Report Excel

### Open the Excel file:
`reports/Master_Audit_Log_YYYYMMDD_HHMMSS.xlsx`

### Check these sheets:

#### 1. Executive Summary
- Look for non-zero means in component scores
- Check "Biomechanics" score > 0

#### 2. Quality Report
- **Columns to verify:**
  - `Burst_Artifact_Count` → Should have values like 234, 189, 312
  - `Burst_Count` → Should have values like 45, 38, 67
  - `Burst_Flow_Count` → Should have values like 12, 15, 23
  - `Artifact_Rate_%` → Should have values like 1.84, 2.45, 0.92
  - `Burst_Decision` → Should show ACCEPT_HIGH_INTENSITY, REVIEW, etc.

- **All these should be non-zero for ALL recordings**

#### 3. Parameter Audit
- Search for columns starting with `step_06_burst_analysis`
- Should show extracted event counts
- Cross-reference with Quality Report to ensure consistency

---

## Success Criteria Summary

✅ **All checks pass:**

1. **Verification script:** `python validate_gate5_fix.py` exits with code 0
2. **File count:** 33 JSON files, 33 parquet mask files
3. **JSON structure:** All have `step_06_burst_analysis` field
4. **Event counts:** Non-zero artifacts/bursts/flows
5. **Excel report:** Burst columns populated with real data
6. **No errors:** Validation script shows no invalid recordings

✅ **When successful, you'll see:**
```
[SUCCESS] All recordings have valid Gate 5 data!
  - Step 06 JSON files contain complete burst analysis
  - Event counts are properly populated
  - Ready for Step 07 Master Quality Report

Next step: Run notebook 07_master_quality_report.ipynb
```

---

## Quick Reference Commands

```bash
# Check current status
python verify_gate5_data.py

# Validate the fix worked
python validate_gate5_fix.py

# Validate specific recording
python validate_gate5_fix.py "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM"

# Show expected data structure
python test_gate5_structure.py

# Re-generate Master Quality Report
# (Open notebook 07 and run all cells)
```

---

**Created:** 2026-01-23  
**Tools:** `validate_gate5_fix.py`, `verify_gate5_data.py`  
**Documentation:** See `GATE_05_README.md` for complete guide
