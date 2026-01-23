# MASTER AUDIT LOG (XLSX) - DEEP REVIEW & MISSING PARAMETERS
**Date:** 2026-01-23  
**Reviewer:** Gaga Pipeline Analysis  
**File Analyzed:** `Master_Audit_Log_20260123_182319.xlsx`

---

## EXECUTIVE SUMMARY

**Status:** ⚠️ **SIGNIFICANT DATA GAPS DETECTED**

The Master Audit Log XLSX is missing **14 critical parameters** (100% NULL across all recordings), resulting in incomplete audit trail for Steps 01, 04, and 05.

### Key Findings:
- ✅ **72 total columns** extracted (good coverage)
- ❌ **14 columns with 100% NULL values** (19.4% missing data rate)
- ✅ Step 02 (Preprocessing): **Complete** (9/9 parameters)
- ❌ Step 01 (Loader): **Incomplete** (13/14 parameters missing)
- ❌ Step 04 (Filtering): **Incomplete** (8/18 parameters missing)
- ❌ Step 05 (Reference): **Incomplete** (1/14 parameters missing)
- ✅ Step 06 (Kinematics): **Complete** (15/15 parameters)

---

## DETAILED BREAKDOWN BY STEP

### STEP 01: Raw Data Loader (13/14 MISSING - 93% INCOMPLETE)

| Parameter | Status | Impact |
|-----------|--------|--------|
| `identity.run_id` | ❌ MISSING | **CRITICAL** - No unique identifier |
| `identity.processing_timestamp` | ❌ MISSING | **HIGH** - Cannot track when processed |
| `identity.pipeline_version` | ❌ MISSING | **HIGH** - Version control lost |
| `identity.csv_source` | ❌ MISSING | **MEDIUM** - Source traceability lost |
| `raw_data_quality.total_frames` | ❌ MISSING | **CRITICAL** - Core QC metric |
| `raw_data_quality.missing_data_percent` | ❌ MISSING | **CRITICAL** - Gap analysis impossible |
| `raw_data_quality.sampling_rate_actual` | ❌ MISSING | **CRITICAL** - Temporal validation broken |
| `raw_data_quality.optitrack_mean_error_mm` | ❌ MISSING | **CRITICAL** - Rácz calibration layer incomplete |
| `raw_data_quality.optitrack_version` | ❌ MISSING | **MEDIUM** - Software provenance lost |
| `calibration.pointer_tip_rms_error_mm` | ❌ MISSING (100% NULL) | **HIGH** - Anatomical landmark precision unknown |
| `calibration.wand_error_mm` | ❌ MISSING (100% NULL) | **HIGH** - Volume calibration quality unknown |
| `calibration.export_date` | ❌ MISSING (100% NULL) | **MEDIUM** - Data export timestamp lost |
| `skeleton_info.segments_found_count` | ❌ MISSING | **HIGH** - Skeleton completeness unknown |
| `skeleton_info.segments_missing_count` | ❌ MISSING | **HIGH** - Data quality assessment broken |
| `duration_sec` | ✅ **FOUND** | Duration available |

**Root Cause:** The extraction logic in `utils_nb07.py -> extract_parameters_flat()` uses dot-notation paths (e.g., `"identity.run_id"`) but the actual JSON structure likely uses underscores or different nesting.

---

### STEP 02: Preprocessing (9/9 COMPLETE - 100% ✅)

All parameters successfully extracted:
- ✅ `run_id`
- ✅ `raw_missing_percent`
- ✅ `post_missing_percent`
- ✅ `max_interpolation_gap`
- ✅ `bone_qc_mean_cv` (Mean: 0.39% - GOLD status)
- ✅ `bone_qc_status`
- ✅ `bone_qc_alerts`
- ✅ `worst_bone`
- ✅ `interpolation_method`

**Status:** ✅ **FULLY FUNCTIONAL**

---

### STEP 04: Filtering - Winter Residual Analysis (10/18 FOUND - 44% INCOMPLETE)

#### Found Parameters (10):
- ✅ `run_id`
- ✅ `identity.timestamp` → `step_04_identity_timestamp`
- ✅ `identity.pipeline_version` → `step_04_identity_pipeline_version`
- ✅ `raw_quality.total_frames`
- ✅ `raw_quality.sampling_rate_actual`
- ✅ `filter_params.filter_type`
- ✅ `filter_params.filter_method`
- ✅ `filter_params.filter_order` (Value: 2 for all recordings)
- ✅ `filter_params.filter_range_hz` (Available in Quality_Report sheet)
- ✅ `filter_params.region_cutoffs` (Available for per-region filtering)

#### Missing Parameters (8) - **100% NULL**:
| Parameter | Status | Impact |
|-----------|--------|--------|
| `subject_metadata.mass_kg` | ❌ NULL | **HIGH** - Biomechanics normalization impossible |
| `subject_metadata.height_cm` | ❌ NULL | **HIGH** - Anthropometric validation broken |
| `filter_params.filter_cutoff_hz` | ❌ NULL | **CRITICAL** - Cannot verify Winter cutoff selection |
| `filter_params.winter_analysis_failed` | ❌ NULL | **CRITICAL** - Cannot detect failed analysis |
| `filter_params.winter_failure_reason` | ❌ NULL | **HIGH** - Failure diagnostics missing |
| `filter_params.decision_reason` | ❌ NULL | **HIGH** - Cutoff rationale undocumented |
| `filter_params.residual_rms_mm` | ❌ NULL | **CRITICAL** - "Price of Smoothing" policy broken |
| `filter_params.residual_slope` | ❌ NULL | **MEDIUM** - Convergence quality unknown |
| `filter_params.biomechanical_guardrails.enabled` | ❌ NULL | **MEDIUM** - Safety validation status unknown |

**Root Cause:** The `filtering_summary.json` likely uses a different structure (e.g., `filter_cutoff_hz` instead of `filter_params.filter_cutoff_hz`). The extraction code expects nested `filter_params` object.

---

### STEP 05: Reference Detection (13/14 FOUND - 93% COMPLETE)

#### Found Parameters (13):
- ✅ `run_id`
- ✅ `subject_context.height_cm` (Range: 152.65-156.73 cm)
- ✅ `subject_context.scaling_factor` (Value: 1.0)
- ✅ `static_offset_audit.Left.measured_angle_deg` (Range: 9.09-10.13°)
- ✅ `static_offset_audit.Right.measured_angle_deg` (Range: 11.34-11.42°)
- ✅ `window_metadata.start_time_sec`
- ✅ `window_metadata.end_time_sec`
- ✅ `window_metadata.variance_score`
- ✅ `window_metadata.ref_quality_score` (Range: 0.81-0.82)
- ✅ `window_metadata.confidence_level`
- ✅ `window_metadata.detection_method`
- ✅ `metadata.grade`
- ✅ `metadata.status`

#### Missing Parameter (1):
| Parameter | Status | Impact |
|-----------|--------|--------|
| `subject_context.height_status` | ❌ NULL | **MEDIUM** - Height validation status (PASS/REVIEW/FAIL) missing |

**Status:** ⚠️ **MOSTLY FUNCTIONAL** (height validation status missing)

---

### STEP 06: Kinematics & Angular Velocities (15/15 COMPLETE - 100% ✅)

All core kinematics parameters successfully extracted:
- ✅ `run_id`
- ✅ `overall_status` (Pipeline completion indicator)
- ✅ `metrics.angular_velocity.max` (Range: 1027-1698 deg/s)
- ✅ `metrics.angular_velocity.limit` (1500 deg/s)
- ✅ `metrics.angular_accel.max` (Range: 42.5k-56.4k deg/s²)
- ✅ `metrics.linear_accel.max` (Range: 38.9k-45.9k mm/s²)
- ✅ `signal_quality.avg_residual_rms` (Range: 8.98-10.72 mm - GOLD status)
- ✅ `signal_quality.max_quat_norm_err` (0.0 - ISB compliant)
- ✅ `movement_metrics.path_length_mm`
- ✅ `movement_metrics.intensity_index`
- ✅ `outlier_analysis.counts.total_outliers`
- ✅ `outlier_analysis.percentages.total_outliers`
- ✅ `outlier_analysis.consecutive_runs.max_consecutive_any_outlier`
- ✅ `pipeline_params.sg_window_sec`
- ✅ `pipeline_params.fs_target`

**Status:** ✅ **FULLY FUNCTIONAL**

---

## ROOT CAUSE ANALYSIS

### Issue #1: JSON Path Mismatch (Step 01)
**Problem:** The extraction code uses dot-notation paths (e.g., `"identity.run_id"`) but the actual `__step01_loader_report.json` likely uses underscores or flat structure.

**Evidence:**
```python
# From utils_nb07.py line 35-49 (PARAMETER_SCHEMA):
"identity.run_id": {"type": "str", ...}
"identity.processing_timestamp": {"type": "str", ...}
"raw_data_quality.total_frames": {"type": "int", ...}
```

**Solution:** Check actual JSON structure:
```bash
# Inspect actual Step 01 JSON structure
cat derivatives/step_01_loader/*__step01_loader_report.json | head -50
```

### Issue #2: Nested Object Extraction (Step 04)
**Problem:** Step 04 parameters expect nested `filter_params` object but JSON may use flat structure or different nesting.

**Evidence:**
- `filter_params.filter_cutoff_hz` → Should be `filter_cutoff_hz` or `filtering.cutoff_hz`
- `subject_metadata.mass_kg` → Should be `mass_kg` or `metadata.mass_kg`

**Solution:** Verify `__filtering_summary.json` structure and update schema paths.

### Issue #3: Missing Calibration Data (Step 01)
**Problem:** `calibration.pointer_tip_rms_error_mm`, `calibration.wand_error_mm`, and `calibration.export_date` are 100% NULL.

**Evidence:** These fields exist in schema but may not be exported by Step 01 loader.

**Solution:** 
1. Check if `.mcal` files contain this data
2. Verify Step 01 loader (`src/loader.py`) actually extracts calibration metadata
3. If missing, add extraction logic to Step 01

---

## IMPACT ASSESSMENT

### Research Impact: 🔴 **HIGH**

| Area | Impact Level | Consequence |
|------|-------------|-------------|
| **Data Provenance** | 🔴 SEVERE | Cannot trace CSV source, version, processing time |
| **Rácz Calibration Layer** | 🔴 SEVERE | OptiTrack error, pointer/wand calibration missing |
| **Winter Residual Analysis** | 🔴 SEVERE | Cutoff decision, failure detection, RMS validation broken |
| **Biomechanics Scoring** | 🟡 MODERATE | Subject mass/height missing affects normalization |
| **Temporal Validation** | 🟡 MODERATE | Some Step 01 sampling metrics missing |

### Audit Trail Completeness: **56% COMPLETE**

- Step 01: 7% complete (1/14 parameters)
- Step 02: 100% complete (9/9 parameters) ✅
- Step 04: 56% complete (10/18 parameters)
- Step 05: 93% complete (13/14 parameters)
- Step 06: 100% complete (15/15 parameters) ✅

**Overall Parameter Extraction Rate: 48/65 (74%)**

---

## RECOMMENDED FIXES

### Priority 1: FIX STEP 01 JSON PATH MISMATCH (CRITICAL)

**Action:** Update `PARAMETER_SCHEMA` in `utils_nb07.py` to match actual JSON structure.

**Steps:**
1. Read actual Step 01 JSON:
   ```python
   import json
   with open('derivatives/step_01_loader/734_T1_P1_R1_Take 2025-12-01 02.18.27 PM__step01_loader_report.json') as f:
       data = json.load(f)
   print(json.dumps(data, indent=2)[:1000])
   ```

2. Update schema paths in `utils_nb07.py` lines 34-50 to match actual structure.

3. Likely fixes:
   ```python
   # OLD (dot notation):
   "identity.run_id" → "run_id" (flat)
   "raw_data_quality.total_frames" → "total_frames" (flat)
   
   # NEW (match actual JSON):
   Check if JSON uses underscores: "raw_data_quality_total_frames"
   ```

---

### Priority 2: FIX STEP 04 FILTERING PARAMETERS (CRITICAL)

**Action:** Update Step 04 schema paths to match `__filtering_summary.json` structure.

**Steps:**
1. Inspect filtering JSON:
   ```python
   with open('derivatives/step_04_filtering/*__filtering_summary.json') as f:
       data = json.load(f)
   print(json.dumps(data['filter_params'], indent=2) if 'filter_params' in data else 'NO filter_params KEY')
   ```

2. Update schema (likely fixes):
   ```python
   # If filter_params is nested:
   "filter_params.filter_cutoff_hz" → Keep as is
   
   # If flat structure:
   "filter_params.filter_cutoff_hz" → "filter_cutoff_hz"
   
   # If different nesting:
   "filter_params.filter_cutoff_hz" → "filtering.cutoff_hz"
   ```

3. Add subject metadata extraction:
   ```python
   # Check if mass/height are in Step 04 or should come from Step 05
   "subject_metadata.mass_kg" → Verify where this is stored
   ```

---

### Priority 3: ADD CALIBRATION DATA EXTRACTION (HIGH)

**Action:** Ensure Step 01 loader extracts calibration metadata from `.mcal` files.

**Steps:**
1. Check if `src/calibration.py` has `parse_mcal_calibration()` function.

2. If missing, add to Step 01 loader:
   ```python
   # In src/loader.py -> load_raw_data():
   from .calibration import parse_mcal_calibration
   
   mcal_path = csv_path.replace('.csv', '.mcal')
   if os.path.exists(mcal_path):
       cal_data = parse_mcal_calibration(mcal_path)
       report['calibration'] = {
           'pointer_tip_rms_error_mm': cal_data.get('pointer_tip_error'),
           'wand_error_mm': cal_data.get('wand_error'),
           'export_date': cal_data.get('export_date')
       }
   ```

3. Update test to verify calibration extraction.

---

### Priority 4: FIX STEP 05 HEIGHT STATUS (MEDIUM)

**Action:** Ensure `subject_context.height_status` is exported in `__reference_summary.json`.

**Steps:**
1. Check `src/reference.py -> detect_static_reference()` function.

2. Add height status to output:
   ```python
   # In reference detection:
   height_status = "PASS" if 150 < height_cm < 200 else "REVIEW" if height_cm > 0 else "FAIL"
   
   summary['subject_context']['height_status'] = height_status
   ```

---

## VALIDATION CHECKLIST

After implementing fixes, verify:

- [ ] Step 01: All 14 parameters extracted (0% NULL rate)
- [ ] Step 04: All 18 parameters extracted (0% NULL rate)
- [ ] Step 05: `height_status` populated
- [ ] Calibration data (`pointer_tip_rms_error_mm`, `wand_error_mm`, `export_date`) present
- [ ] Run analysis script again to confirm 100% parameter coverage
- [ ] Regenerate XLSX audit log
- [ ] Verify Research Decision logic still works correctly
- [ ] Check that Quality Scores are calculated with complete data

---

## ADDITIONAL OBSERVATIONS

### Good News: Quality Report Sheet is More Complete

The `Quality_Report` sheet (Sheet 2) in the XLSX contains **MORE data** than the `Parameter_Audit` sheet:

**Quality_Report includes:**
- ✅ `Filter_Cutoff_Hz` (values: present, not NULL)
- ✅ `Filter_Method`
- ✅ `Subject_Mass_kg`
- ✅ `Subject_Height_cm`
- ✅ `Residual_RMS_mm`
- ✅ All Gate 2/3/4/5 metrics
- ✅ Biomechanics scorecard components

**This suggests:** The `build_quality_row()` function (line 938-1089) successfully extracts these parameters, but `extract_parameters_flat()` (line 402-426) fails due to schema path mismatches.

**Implication:** The core extraction logic **works**, just needs schema alignment.

---

## CONCLUSION

The Master Audit Log XLSX has **good architecture** but **incomplete parameter extraction** due to:

1. **JSON path mismatches** between schema and actual file structure
2. **Missing calibration data extraction** in Step 01
3. **Nested object path confusion** in Step 04

**Fix Effort Estimate:** 2-4 hours
- 1 hour: Inspect actual JSON structures
- 1 hour: Update schema paths in `utils_nb07.py`
- 1 hour: Add calibration extraction to Step 01 loader
- 1 hour: Test and validate

**Expected Outcome:** 100% parameter coverage, complete audit trail, full traceability from raw CSV to final kinematics.

---

## NEXT STEPS

1. **Inspect JSON Files:**
   ```bash
   # Check Step 01 structure
   python -c "import json; print(json.dumps(json.load(open('derivatives/step_01_loader/<first_file>__step01_loader_report.json')), indent=2)[:2000])"
   
   # Check Step 04 structure  
   python -c "import json; print(json.dumps(json.load(open('derivatives/step_04_filtering/<first_file>__filtering_summary.json')), indent=2)[:2000])"
   ```

2. **Create Fix Script:** Generate `fix_audit_extraction.py` with corrected schema paths.

3. **Test on Sample:** Run on 2-3 recordings to verify extraction.

4. **Regenerate Full Audit:** Re-run Notebook 07 with fixed extraction.

5. **Document Changes:** Update `MASTER_AUDIT_EXECUTIVE_SUMMARY.md` with new coverage metrics.

---

**Report Generated:** 2026-01-23  
**Analysis Tool:** `analyze_audit.py`  
**Files Analyzed:** `Master_Audit_Log_20260123_182319.xlsx` (2 recordings)
