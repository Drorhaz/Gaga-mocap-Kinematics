# Data Flow Technical Assessment - Master Audit Log
**Date:** 2026-01-23  
**Audit Log:** Master_Audit_Log_20260123_151709.xlsx  
**Status:** ⚠️ CRITICAL - Schema Correct, Data Broken  

---

## Executive Summary

The Master Audit Log infrastructure has been correctly implemented with all structural elements in place. However, **the data pipeline is severely broken** between the processing notebooks (01-06) and the final audit report (notebook 07). While the "boxes" exist in the schema, the "data" is either:

1. **Missing entirely** (empty fields showing 'N/A')
2. **Zeroed out** (0.0 values where real metrics should exist)
3. **Not propagating** from JSON summaries to Excel tables

This is a **data flow bottleneck issue**, not a schema design issue.

---

## Root Cause Analysis

### 1. **Kinematics Summary JSON Generation Gap** (CRITICAL)

**Location:** `notebooks/06_rotvec_omega.ipynb`

**Problem:** Notebook 06 is computing kinematics but **NOT generating the complete summary JSON** required by the Master Audit.

**Evidence from batch log:**
```json
{
  "run_id": "505_T2_P1_R1_Take 2025-11-17 05.24.24 PM",
  "overall_status": "FAIL",
  "metrics": {
    "angular_velocity": {"max": 1992.0, "limit": 1500.0, "status": false},
    "angular_accel": {"max": 79610.22, "limit": 50000.0, "status": false}
  },
  "joint_statistics": {}  // ⚠️ EMPTY - Should contain per-joint ROM data
}
```

**Missing Fields:**
- `joint_statistics` - Empty dictionary (should contain per-joint data)
- `step_06_burst_analysis` - Not present (Gate 5 metrics)
- `step_06_burst_decision` - Not present (classification decision)
- `clean_statistics` - Not present (artifact-excluded metrics)
- `step_06_isb_compliant` - Not present (Gate 4 validation)
- `step_06_math_status` - Not present

**Impact:** ~40% of Master Audit columns show 'N/A' or 0 values because the source JSON doesn't contain the data.

---

### 2. **Preprocessing Summary Incomplete** (HIGH)

**Location:** `notebooks/02_preprocess.ipynb`

**Problem:** Missing **Gate 2** temporal quality metrics in the output JSON.

**Required Fields (per schema):**
```json
{
  "step_02_sample_time_jitter_ms": 0.0,      // ⚠️ Missing
  "step_02_jitter_status": "N/A",            // ⚠️ Missing
  "step_02_fallback_count": 0,               // ⚠️ Missing
  "step_02_fallback_rate_percent": 0.0,      // ⚠️ Missing
  "step_02_max_gap_frames": 0,               // ⚠️ Missing
  "step_02_interpolation_status": "N/A"      // ⚠️ Missing
}
```

**Current Output:** Basic preprocessing summary with bone QC, but **no temporal jitter analysis**.

**Impact:** Temporal Quality Score cannot be accurately computed (Gate 2 validation broken).

---

### 3. **Filtering Summary Missing Region-Specific Data** (MEDIUM)

**Location:** `notebooks/04_filtering.ipynb`

**Problem:** Per-region filtering is enabled, but the summary JSON doesn't export region-specific cutoffs.

**Expected Structure (from schema):**
```json
{
  "filter_params": {
    "filtering_mode": "per_region",
    "filter_cutoff_hz": 8.5,  // Weighted average
    "region_cutoffs": {       // ⚠️ MISSING - Individual region cutoffs
      "upper_body": 6.0,
      "lower_body": 9.0,
      "distal": 12.0
    }
  }
}
```

**Impact:** Per-region filtering transparency lost in audit trail.

---

### 4. **Reference Detection Missing Height Estimation** (MEDIUM)

**Location:** `notebooks/05_reference_detection.ipynb`

**Problem:** Missing subject context fields.

**Required Fields:**
```json
{
  "subject_context": {
    "height_cm": 170.0,           // ⚠️ Missing
    "scaling_factor": 1.02        // ⚠️ Missing
  }
}
```

**Impact:** Cannot validate anthropometric scaling or height estimates in audit.

---

### 5. **Master Report Parameter Extraction Logic** (MEDIUM)

**Location:** `src/utils_nb07.py` → `extract_parameters_flat()`

**Problem:** The parameter extraction functions correctly read the schema but:
- Do **not validate** that expected fields exist in source JSON
- Use `safe_get_path()` which returns 'N/A' for missing keys
- No warning/logging when critical fields are missing

**Example:**
```python
# This returns 'N/A' silently if key doesn't exist
value = safe_get_path(step_data, "step_06_burst_analysis.classification.artifact_count")
```

**Impact:** Silent failures - missing data propagates as 'N/A' instead of raising errors.

---

## Data Flow Diagram (Current vs. Expected)

```
┌─────────────────────┐
│ Notebook 01         │
│ (Load & Parse)      │
└──────┬──────────────┘
       │ ✅ __step01_loader_report.json
       ↓
┌─────────────────────┐
│ Notebook 02         │
│ (Preprocess)        │
└──────┬──────────────┘
       │ ⚠️ __preprocess_summary.json (INCOMPLETE)
       │    Missing: Gate 2 temporal metrics
       ↓
┌─────────────────────┐
│ Notebook 03         │
│ (Resample)          │
└──────┬──────────────┘
       │ ✅ (No summary - data only)
       ↓
┌─────────────────────┐
│ Notebook 04         │
│ (Filtering)         │
└──────┬──────────────┘
       │ ⚠️ __filtering_summary.json (INCOMPLETE)
       │    Missing: Per-region cutoffs
       ↓
┌─────────────────────┐
│ Notebook 05         │
│ (Reference)         │
└──────┬──────────────┘
       │ ⚠️ __reference_summary.json (INCOMPLETE)
       │    Missing: Height estimation
       ↓
┌─────────────────────┐
│ Notebook 06         │
│ (Kinematics)        │ ⚠️ CRITICAL BOTTLENECK
└──────┬──────────────┘
       │ ❌ __kinematics_summary.json (SEVERELY INCOMPLETE)
       │    Missing: 
       │    - joint_statistics (per-joint ROM)
       │    - burst_analysis (Gate 5)
       │    - burst_decision
       │    - clean_statistics (artifact-excluded)
       │    - isb_compliant (Gate 4)
       │    - math_status
       ↓
┌─────────────────────┐
│ Notebook 07         │
│ (Master Audit)      │
└──────┬──────────────┘
       │ ⚠️ Excel Output (DATA HOLES)
       │    40+ columns show 'N/A' or 0.0
       ↓
┌─────────────────────────────────────┐
│ Master_Audit_Log_20260123_151709    │
│ ✅ Schema correct                   │
│ ❌ Data missing/zeroed              │
└─────────────────────────────────────┘
```

---

## Prioritized Fix List

### 🔴 **CRITICAL (P0) - Blocks All Auditing**

1. **Fix Notebook 06 JSON Export**
   - **File:** `notebooks/06_rotvec_omega.ipynb`
   - **Action:** Add comprehensive JSON export at end of notebook:
     ```python
     summary = {
         "run_id": RUN_ID,
         "overall_status": "PASS/FAIL",
         "metrics": {...},  # Existing
         "joint_statistics": joint_rom_dict,  # ⚠️ ADD THIS
         "step_06_burst_analysis": burst_results,  # ⚠️ ADD THIS
         "step_06_burst_decision": decision_dict,  # ⚠️ ADD THIS
         "clean_statistics": clean_stats,  # ⚠️ ADD THIS
         "step_06_isb_compliant": True,  # ⚠️ ADD THIS
         "step_06_math_status": "ACCEPT/REVIEW/REJECT"  # ⚠️ ADD THIS
     }
     with open(f"{DERIV_KIN}/{RUN_ID}__kinematics_summary.json", 'w') as f:
         json.dump(summary, f, indent=2)
     ```
   - **Validation:** Re-run batch and verify non-zero values in audit log

---

### 🟠 **HIGH (P1) - Affects Quality Scoring**

2. **Add Gate 2 Metrics to Notebook 02**
   - **File:** `notebooks/02_preprocess.ipynb`
   - **Action:** Compute and export temporal jitter analysis:
     ```python
     # Calculate sample time jitter
     time_diffs = np.diff(df['time_s'])
     expected_dt = 1.0 / 120.0  # 120 Hz
     jitter_ms = np.std(time_diffs - expected_dt) * 1000
     
     preprocess_summary.update({
         "step_02_sample_time_jitter_ms": round(jitter_ms, 4),
         "step_02_jitter_status": "ACCEPT" if jitter_ms < 1.0 else "REVIEW",
         "step_02_fallback_count": fallback_count,
         "step_02_fallback_rate_percent": round(fallback_rate, 4),
         "step_02_max_gap_frames": max_gap,
         "step_02_interpolation_status": "GOLD/SILVER/BRONZE"
     })
     ```

3. **Add Per-Region Cutoffs to Notebook 04**
   - **File:** `notebooks/04_filtering.ipynb`
   - **Action:** Export individual region cutoffs (if per-region mode enabled):
     ```python
     if filtering_mode == "per_region":
         filter_summary["filter_params"]["region_cutoffs"] = {
             "upper_body": upper_cutoff,
             "lower_body": lower_cutoff,
             "distal": distal_cutoff
         }
     ```

---

### 🟡 **MEDIUM (P2) - Documentation & Transparency**

4. **Add Height Estimation to Notebook 05**
   - **File:** `notebooks/05_reference_detection.ipynb`
   - **Action:** Calculate estimated height from skeleton:
     ```python
     # Estimate height from bone lengths
     height_cm = estimate_height_from_skeleton(bone_lengths)
     
     reference_summary.update({
         "subject_context": {
             "height_cm": round(height_cm, 1),
             "scaling_factor": round(scale_factor, 3)
         }
     })
     ```

5. **Add Validation Warnings to Notebook 07**
   - **File:** `notebooks/07_master_quality_report.ipynb`
   - **Action:** Log warnings when critical fields are missing:
     ```python
     # After loading JSON files
     for run_id, steps in runs_data.items():
         s06 = steps.get("step_06", {})
         if not s06.get("joint_statistics"):
             print(f"⚠️ WARNING: {run_id} missing joint_statistics in step_06")
         if not s06.get("step_06_burst_analysis"):
             print(f"⚠️ WARNING: {run_id} missing burst_analysis in step_06")
     ```

---

### 🟢 **LOW (P3) - Nice-to-Have**

6. **Add JSON Schema Validation**
   - **File:** Create `src/json_schema_validator.py`
   - **Action:** Validate each JSON summary against expected schema before export
   - **Benefit:** Catch missing fields at generation time, not audit time

7. **Add Data Flow Health Check Script**
   - **File:** Create `verify_data_flow.py`
   - **Action:** Post-batch validation that checks all expected JSON files exist and contain non-empty values
   - **Usage:** `python verify_data_flow.py --batch-summary reports/batch_summary_latest.json`

---

## Testing & Validation Protocol

### Step 1: Fix Critical Path (Notebook 06)
```bash
# 1. Update Notebook 06 with comprehensive JSON export
# 2. Test on single run
python run_pipeline.py --single "data/505/T2/505_T2_P1_R1_Take 2025-11-17 05.24.24 PM.csv"

# 3. Verify JSON output
python -c "
import json
with open('derivatives/step_06_kinematics/505_T2_P1_R1__kinematics_summary.json') as f:
    data = json.load(f)
    assert 'joint_statistics' in data, 'Missing joint_statistics'
    assert len(data['joint_statistics']) > 0, 'Empty joint_statistics'
    assert 'step_06_burst_analysis' in data, 'Missing burst_analysis'
    print('✅ Kinematics JSON validation passed')
"

# 4. Re-run Master Audit
# Execute Notebook 07 and check Excel output

# 5. Verify non-zero values
python -c "
import pandas as pd
df = pd.read_excel('reports/Master_Audit_Log_*.xlsx', sheet_name='Quality_Report')
print(f'Burst_Artifact_Count non-zero: {(df[\"Burst_Artifact_Count\"] > 0).sum()}')
print(f'Clean_Max_Vel non-zero: {(df[\"Clean_Max_Vel_deg_s\"] > 0).sum()}')
"
```

### Step 2: Validate P1 Fixes
```bash
# Run full batch
python run_pipeline.py --json batch_configs/subject_505_all.json

# Check for temporal metrics
python -c "
import json, glob
files = glob.glob('derivatives/step_02_preprocess/*__preprocess_summary.json')
for f in files[:3]:
    with open(f) as fp:
        data = json.load(fp)
        jitter = data.get('step_02_sample_time_jitter_ms', 'MISSING')
        print(f'{f}: jitter = {jitter}')
"
```

### Step 3: Full Audit Validation
```bash
# Generate final audit log
# Execute Notebook 07

# Validate completeness
python -c "
import pandas as pd
df = pd.read_excel('reports/Master_Audit_Log_*.xlsx', sheet_name='Quality_Report')
total_cells = df.size
na_cells = df.isna().sum().sum() + (df == 'N/A').sum().sum()
completeness = (1 - na_cells/total_cells) * 100
print(f'Data Completeness: {completeness:.1f}%')
print(f'Target: >95%')
assert completeness > 95, f'Data completeness too low: {completeness:.1f}%'
print('✅ Master Audit validation passed')
"
```

---

## Expected Outcomes After Fixes

### Before (Current State)
```
Master_Audit_Log_20260123_151709.xlsx
├── Quality_Report (Sheet 2)
│   ├── Burst_Artifact_Count:     100% 'N/A'
│   ├── Burst_Decision:           100% 'N/A'
│   ├── Clean_Max_Vel_deg_s:      100% 0.0
│   ├── Sample_Jitter_ms:         100% 0.0
│   ├── ISB_Compliant:            100% 'N/A'
│   └── Data Completeness:        ~60%
```

### After (Target State)
```
Master_Audit_Log_20260123_152000.xlsx
├── Quality_Report (Sheet 2)
│   ├── Burst_Artifact_Count:     Real counts (e.g., 5-50)
│   ├── Burst_Decision:           ACCEPT/REVIEW/REJECT
│   ├── Clean_Max_Vel_deg_s:      Real velocities (e.g., 400-1200 deg/s)
│   ├── Sample_Jitter_ms:         Real jitter (e.g., 0.2-2.0 ms)
│   ├── ISB_Compliant:            True/False
│   └── Data Completeness:        >95%
```

---

## Long-Term Recommendations

1. **Schema-Driven Development**
   - Maintain `PARAMETER_SCHEMA` in `utils_nb07.py` as source of truth
   - Generate JSON templates automatically from schema
   - Validate all JSON outputs against schema at generation time

2. **Data Flow Health Monitoring**
   - Add `--verify` flag to `run_pipeline.py` that checks JSON completeness
   - Fail pipeline early if JSON export is incomplete (don't wait for audit)

3. **JSON Export Standardization**
   - Create `src/json_exporter.py` module with standard export patterns
   - All notebooks import and use standardized export functions
   - Reduces copy-paste errors and ensures consistency

4. **Unit Tests for JSON Exports**
   - Add tests that validate JSON structure for each notebook
   - Example: `tests/test_nb06_json_export.py`
   - Catch schema drift during development

---

## Files Requiring Changes

### Critical (Must Fix Now)
1. `notebooks/06_rotvec_omega.ipynb` - Add complete JSON export
2. `notebooks/07_master_quality_report.ipynb` - Add validation warnings

### High Priority (Fix This Sprint)
3. `notebooks/02_preprocess.ipynb` - Add Gate 2 metrics
4. `notebooks/04_filtering.ipynb` - Add per-region cutoffs
5. `notebooks/05_reference_detection.ipynb` - Add height estimation

### Infrastructure (Nice-to-Have)
6. `src/json_schema_validator.py` - New file
7. `verify_data_flow.py` - New file
8. `tests/test_json_exports.py` - New file

---

## Summary

**The Good:**
- ✅ Schema design is correct and comprehensive
- ✅ Excel generation logic works properly
- ✅ Quality scoring functions are well-structured
- ✅ Parameter extraction framework is robust

**The Bad:**
- ❌ Notebooks 02, 04, 05, 06 are not exporting complete JSON summaries
- ❌ ~40% of audit columns show 'N/A' or zeroed data
- ❌ No validation to catch missing data at generation time

**The Fix:**
- 🔧 Update 4 notebooks to export complete JSON (1-2 days of work)
- 🔧 Add validation to catch incomplete exports (1 day)
- 🔧 Re-run batch and verify >95% data completeness (1 day)

**Estimated Effort:** 3-4 days for complete fix + validation

---

**Assessment Date:** 2026-01-23  
**Assessed By:** Technical Analysis  
**Priority:** CRITICAL (P0)  
**Next Action:** Fix Notebook 06 JSON export (start with single run test)
