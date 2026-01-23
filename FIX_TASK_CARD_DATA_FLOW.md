# 🔧 FIX TASK CARD: Master Audit Data Flow
**Created:** 2026-01-23  
**Priority:** 🔴 CRITICAL (P0)  
**Estimated Effort:** 3-4 days  

---

## Problem Statement (One-Liner)
The Master Audit Log has correct schema but **notebooks are not exporting complete JSON summaries**, causing 40% of audit columns to show 'N/A' or zeroed data.

---

## Quick Context
- ✅ Schema design is correct (`utils_nb07.py`)
- ✅ Excel generation works
- ❌ **Notebooks 01-06 are not exporting all required fields to JSON**
- ❌ Data holes propagate as 'N/A' in final Excel report

---

## Critical Path: Fix Notebook 06 (START HERE)

### File: `notebooks/06_rotvec_omega.ipynb`

### Missing JSON Fields:
```python
# CURRENT OUTPUT (incomplete)
{
  "run_id": "...",
  "overall_status": "PASS/FAIL",
  "metrics": {...},
  "joint_statistics": {}  # ⚠️ EMPTY
}

# REQUIRED OUTPUT (complete)
{
  "run_id": "...",
  "overall_status": "PASS/FAIL",
  "metrics": {...},
  "joint_statistics": {  # ✅ Per-joint ROM data
    "Left_Shoulder": {"max_angle_deg": 120.5, ...},
    ...
  },
  "step_06_burst_analysis": {  # ✅ Gate 5 metrics
    "classification": {"artifact_count": 12, ...},
    "timing": {...}
  },
  "step_06_burst_decision": {  # ✅ Classification decision
    "overall_status": "ACCEPT/REVIEW/REJECT",
    "primary_reason": "..."
  },
  "clean_statistics": {  # ✅ Artifact-excluded metrics
    "clean_statistics": {"max_deg_s": 450.2, ...}
  },
  "step_06_isb_compliant": true,  # ✅ Gate 4
  "step_06_math_status": "ACCEPT"  # ✅ Math stability
}
```

### Code Fix Location:
**Find:** End of notebook 06, JSON export section  
**Add:** Complete summary dictionary with all fields above

### Test Command:
```bash
# 1. Run single file
python run_pipeline.py --single "data/505/T2/505_T2_P1_R1_Take 2025-11-17 05.24.24 PM.csv"

# 2. Verify JSON
python -c "
import json
with open('derivatives/step_06_kinematics/505_T2_P1_R1__kinematics_summary.json') as f:
    d = json.load(f)
    assert len(d.get('joint_statistics', {})) > 0, 'Missing joint_statistics'
    assert 'step_06_burst_analysis' in d, 'Missing burst_analysis'
    print('✅ PASS')
"

# 3. Re-run notebook 07 and check Excel
```

**Success Criteria:** 
- ✅ `joint_statistics` dictionary has >20 joints
- ✅ `burst_analysis` shows real event counts
- ✅ Excel columns show non-zero values

---

## Secondary Fixes (After NB06 Works)

### 2. Notebook 02: Add Gate 2 Temporal Metrics
**File:** `notebooks/02_preprocess.ipynb`

**Missing Fields:**
```python
{
  "step_02_sample_time_jitter_ms": 0.85,  # Calculate from time_s
  "step_02_jitter_status": "ACCEPT",
  "step_02_fallback_count": 12,
  "step_02_fallback_rate_percent": 0.45,
  "step_02_max_gap_frames": 8,
  "step_02_interpolation_status": "GOLD"
}
```

**Code Pattern:**
```python
# Calculate jitter
time_diffs = np.diff(df['time_s'])
expected_dt = 1.0 / CONFIG['FS_TARGET']
jitter_ms = np.std(time_diffs - expected_dt) * 1000

# Add to summary
preprocess_summary["step_02_sample_time_jitter_ms"] = round(jitter_ms, 4)
preprocess_summary["step_02_jitter_status"] = "ACCEPT" if jitter_ms < 1.0 else "REVIEW"
```

---

### 3. Notebook 04: Export Per-Region Cutoffs
**File:** `notebooks/04_filtering.ipynb`

**Missing Fields:**
```python
{
  "filter_params": {
    "filtering_mode": "per_region",
    "region_cutoffs": {  # ⚠️ ADD THIS
      "upper_body": 6.0,
      "lower_body": 9.0,
      "distal": 12.0
    }
  }
}
```

**Code Pattern:**
```python
if filtering_mode == "per_region":
    filter_summary["filter_params"]["region_cutoffs"] = {
        "upper_body": upper_cutoff,
        "lower_body": lower_cutoff,
        "distal": distal_cutoff
    }
```

---

### 4. Notebook 05: Add Height Estimation
**File:** `notebooks/05_reference_detection.ipynb`

**Missing Fields:**
```python
{
  "subject_context": {
    "height_cm": 170.5,
    "scaling_factor": 1.02
  }
}
```

**Code Pattern:**
```python
# Use existing bone lengths to estimate height
height_cm = estimate_height_from_skeleton(bone_lengths)

reference_summary["subject_context"] = {
    "height_cm": round(height_cm, 1),
    "scaling_factor": round(scale_factor, 3)
}
```

---

## Validation Checklist

### After Each Fix:
- [ ] Run single CSV through pipeline
- [ ] Check JSON file exists and has required fields
- [ ] Verify non-'N/A' values in JSON
- [ ] Re-run notebook 07
- [ ] Check Excel for real data (not 'N/A' or 0)

### Final Validation (All Fixes Complete):
```bash
# Run full batch
python run_pipeline.py --json batch_configs/subject_505_all.json

# Execute notebook 07
# Check data completeness

python -c "
import pandas as pd
df = pd.read_excel('reports/Master_Audit_Log_*.xlsx', sheet_name='Quality_Report')
total_cells = df.size
na_cells = df.isna().sum().sum() + (df == 'N/A').sum().sum()
completeness = (1 - na_cells/total_cells) * 100
print(f'Data Completeness: {completeness:.1f}%')
assert completeness > 95, f'FAIL: Only {completeness:.1f}%'
print('✅ PASS: Data flow fixed')
"
```

**Target:** >95% data completeness (currently ~60%)

---

## Where to Find Things

### Key Files:
- Schema definition: `src/utils_nb07.py` → `PARAMETER_SCHEMA` dict
- Notebooks to fix: `notebooks/02_preprocess.ipynb`, `04_filtering.ipynb`, `05_reference_detection.ipynb`, **`06_rotvec_omega.ipynb`**
- Test runner: `run_pipeline.py`
- Batch configs: `batch_configs/subject_505_all.json`

### Example JSON Locations:
- Step 01: `derivatives/step_01_parse/*__step01_loader_report.json`
- Step 02: `derivatives/step_02_preprocess/*__preprocess_summary.json`
- Step 04: `derivatives/step_04_filtering/*__filtering_summary.json`
- Step 05: `derivatives/step_05_reference/*__reference_summary.json`
- Step 06: `derivatives/step_06_kinematics/*__kinematics_summary.json` ⚠️ **BROKEN**

### Sample Working JSON (Step 01):
```json
{
  "identity": {
    "run_id": "505_T2_P1_R1_Take 2025-11-17 05.24.24 PM",
    "processing_timestamp": "2026-01-23T14:28:30",
    "pipeline_version": "v2.0"
  },
  "raw_data_quality": {
    "total_frames": 31257,
    "sampling_rate_actual": 120.0,
    "optitrack_mean_error_mm": 0.45
  }
}
```

---

## Common Pitfalls

### ❌ DON'T:
- Copy-paste entire JSON - only add missing fields
- Change schema in `utils_nb07.py` - schema is correct
- Modify Excel generation - Excel logic is fine
- Add fields that aren't in schema

### ✅ DO:
- Start with Notebook 06 (biggest impact)
- Test each notebook individually before batch run
- Use existing variable names (they're already computed in notebooks)
- Validate JSON structure after each fix
- Check Excel after each notebook fix

---

## Help / Questions

**If stuck on:**
- "Where do I find X variable?" → Check earlier cells in same notebook, it's already computed
- "JSON export failing" → Check for `json.dump()` call at end of notebook
- "Excel still shows N/A" → Re-run notebook 07 after fixing source notebooks
- "How to test single file?" → Use `--single` flag with `run_pipeline.py`

**Documentation:**
- Full analysis: `DATA_FLOW_TECHNICAL_ASSESSMENT.md`
- Schema reference: `src/utils_nb07.py` lines 29-129
- Batch config examples: `batch_configs/README_BATCH_CONFIGS.md`

---

## Progress Tracker

### P0 (Critical - Must Fix):
- [ ] **Notebook 06:** Add complete JSON export (joint_statistics, burst_analysis, clean_stats, etc.)
- [ ] **Test:** Single run validation
- [ ] **Test:** Excel shows real data (not N/A)

### P1 (High - Fix This Week):
- [ ] **Notebook 02:** Add Gate 2 temporal metrics (jitter, fallback rate)
- [ ] **Notebook 04:** Add per-region cutoffs
- [ ] **Notebook 05:** Add height estimation
- [ ] **Test:** Full batch validation (>95% completeness)

### P2 (Medium - Nice to Have):
- [ ] Add validation warnings to Notebook 07
- [ ] Create JSON schema validator
- [ ] Add data flow health check script

---

**Remember:** The schema is CORRECT. The problem is notebooks not populating the schema. Fix the data export, not the schema design.

**Start Here:** Notebook 06 → Fix JSON export → Test → Move to next notebook

**End Goal:** Master Audit Excel with >95% real data (not 'N/A' or 0)

---

**Created:** 2026-01-23  
**Last Updated:** 2026-01-23  
**Status:** 🔴 ACTIVE - Needs immediate attention  
**Owner:** Development Team  
**Reviewer:** Pipeline Lead
