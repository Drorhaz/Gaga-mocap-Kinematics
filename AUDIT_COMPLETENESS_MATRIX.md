# AUDIT COMPLETENESS MATRIX

| Step | Parameter | Current Status | Impact | Fix Priority | Fix Location |
|------|-----------|----------------|--------|--------------|--------------|
| **STEP 01** | | **7% Complete (1/14)** | | | |
| 01 | identity.run_id | ❌ MISSING | CRITICAL | N/A | Schema path OK, but field shows as missing in audit |
| 01 | identity.processing_timestamp | ❌ MISSING | HIGH | N/A | Schema path OK |
| 01 | identity.pipeline_version | ❌ MISSING | HIGH | N/A | Schema path OK |
| 01 | identity.csv_source | ❌ MISSING | MEDIUM | N/A | Schema path OK |
| 01 | raw_data_quality.total_frames | ❌ MISSING | CRITICAL | N/A | Schema path OK |
| 01 | raw_data_quality.missing_data_percent | ❌ MISSING | CRITICAL | N/A | Schema path OK |
| 01 | raw_data_quality.sampling_rate_actual | ❌ MISSING | CRITICAL | N/A | Schema path OK |
| 01 | raw_data_quality.optitrack_mean_error_mm | ❌ MISSING | CRITICAL | N/A | Schema path OK |
| 01 | raw_data_quality.optitrack_version | ❌ MISSING | MEDIUM | N/A | Schema path OK |
| 01 | calibration.pointer_tip_rms_error_mm | 🔴 NULL (100%) | HIGH | P2 | `src/loader.py` - Add .mcal parsing |
| 01 | calibration.wand_error_mm | 🔴 NULL (100%) | HIGH | P2 | `src/loader.py` - Add .mcal parsing |
| 01 | calibration.export_date | 🔴 NULL (100%) | MEDIUM | P2 | `src/loader.py` - Add .mcal parsing |
| 01 | skeleton_info.segments_found_count | ❌ MISSING | HIGH | N/A | Schema path OK |
| 01 | skeleton_info.segments_missing_count | ❌ MISSING | HIGH | N/A | Schema path OK |
| 01 | duration_sec | ✅ FOUND | - | - | Working |
| **STEP 02** | | **100% Complete (9/9)** ✅ | | | |
| 02 | run_id | ✅ FOUND | - | - | Working |
| 02 | raw_missing_percent | ✅ FOUND | - | - | Working |
| 02 | post_missing_percent | ✅ FOUND | - | - | Working |
| 02 | max_interpolation_gap | ✅ FOUND | - | - | Working |
| 02 | bone_qc_mean_cv | ✅ FOUND | - | - | Working |
| 02 | bone_qc_status | ✅ FOUND | - | - | Working |
| 02 | bone_qc_alerts | ✅ FOUND | - | - | Working |
| 02 | worst_bone | ✅ FOUND | - | - | Working |
| 02 | interpolation_method | ✅ FOUND | - | - | Working |
| **STEP 04** | | **56% Complete (10/18)** | | | |
| 04 | run_id | ✅ FOUND | - | - | Working |
| 04 | identity.timestamp | ✅ FOUND | - | - | Working |
| 04 | identity.pipeline_version | ✅ FOUND | - | - | Working |
| 04 | subject_metadata.mass_kg | 🔴 NULL (100%) | HIGH | P1 | `src/filtering.py` - Load from config |
| 04 | subject_metadata.height_cm | 🔴 NULL (100%) | HIGH | P1 | `src/filtering.py` - Load from config |
| 04 | raw_quality.total_frames | ✅ FOUND | - | - | Working |
| 04 | raw_quality.sampling_rate_actual | ✅ FOUND | - | - | Working |
| 04 | filter_params.filter_type | ✅ FOUND | - | - | Working |
| 04 | filter_params.filter_method | ✅ FOUND | - | - | Working |
| 04 | filter_params.filter_cutoff_hz | 🔴 NULL (100%) | CRITICAL | P1 | `src/filtering.py` - Compute weighted avg |
| 04 | filter_params.filter_range_hz | ✅ FOUND | - | - | Working (exists as cutoff_range_hz) |
| 04 | filter_params.filter_order | ✅ FOUND | - | - | Working |
| 04 | filter_params.winter_analysis_failed | 🔴 NULL (100%) | CRITICAL | P1 | `src/filtering.py` - Add status flag |
| 04 | filter_params.winter_failure_reason | 🔴 NULL (100%) | HIGH | P1 | `src/filtering.py` - Add failure msg |
| 04 | filter_params.decision_reason | 🔴 NULL (100%) | HIGH | P1 | `src/filtering.py` - Add decision text |
| 04 | filter_params.residual_rms_mm | 🔴 NULL (100%) | CRITICAL | P1 | `src/filtering.py` - Export RMS metric |
| 04 | filter_params.residual_slope | 🔴 NULL (100%) | MEDIUM | P1 | `src/filtering.py` - Export slope metric |
| 04 | filter_params.biomechanical_guardrails.enabled | 🔴 NULL (100%) | MEDIUM | P1 | `src/filtering.py` - Add config flag |
| **STEP 05** | | **93% Complete (13/14)** | | | |
| 05 | run_id | ✅ FOUND | - | - | Working |
| 05 | subject_context.height_cm | ✅ FOUND | - | - | Working (152-157 cm) |
| 05 | subject_context.scaling_factor | ✅ FOUND | - | - | Working (1.0) |
| 05 | subject_context.height_status | 🔴 NULL (100%) | MEDIUM | P3 | `src/reference.py` - Add validation |
| 05 | static_offset_audit.Left.measured_angle_deg | ✅ FOUND | - | - | Working (9-10°) |
| 05 | static_offset_audit.Right.measured_angle_deg | ✅ FOUND | - | - | Working (11-11°) |
| 05 | window_metadata.start_time_sec | ✅ FOUND | - | - | Working |
| 05 | window_metadata.end_time_sec | ✅ FOUND | - | - | Working |
| 05 | window_metadata.variance_score | ✅ FOUND | - | - | Working |
| 05 | window_metadata.ref_quality_score | ✅ FOUND | - | - | Working (0.81-0.82) |
| 05 | window_metadata.confidence_level | ✅ FOUND | - | - | Working |
| 05 | window_metadata.detection_method | ✅ FOUND | - | - | Working |
| 05 | metadata.grade | ✅ FOUND | - | - | Working |
| 05 | metadata.status | ✅ FOUND | - | - | Working |
| **STEP 06** | | **100% Complete (15/15)** ✅ | | | |
| 06 | run_id | ✅ FOUND | - | - | Working |
| 06 | overall_status | ✅ FOUND | - | - | Working |
| 06 | metrics.angular_velocity.max | ✅ FOUND | - | - | Working (1027-1698 deg/s) |
| 06 | metrics.angular_velocity.limit | ✅ FOUND | - | - | Working (1500 deg/s) |
| 06 | metrics.angular_accel.max | ✅ FOUND | - | - | Working (42k-56k deg/s²) |
| 06 | metrics.linear_accel.max | ✅ FOUND | - | - | Working (39k-46k mm/s²) |
| 06 | signal_quality.avg_residual_rms | ✅ FOUND | - | - | Working (8.98-10.72 mm) |
| 06 | signal_quality.max_quat_norm_err | ✅ FOUND | - | - | Working (0.0) |
| 06 | movement_metrics.path_length_mm | ✅ FOUND | - | - | Working (25-26k mm) |
| 06 | movement_metrics.intensity_index | ✅ FOUND | - | - | Working (0.08-0.11) |
| 06 | outlier_analysis.counts.total_outliers | ✅ FOUND | - | - | Working (156-444 frames) |
| 06 | outlier_analysis.percentages.total_outliers | ✅ FOUND | - | - | Working (0.51-1.46%) |
| 06 | outlier_analysis.consecutive_runs.max_consecutive_any_outlier | ✅ FOUND | - | - | Working (9-27 frames) |
| 06 | pipeline_params.sg_window_sec | ✅ FOUND | - | - | Working (0.17 s) |
| 06 | pipeline_params.fs_target | ✅ FOUND | - | - | Working (120 Hz) |

---

## SUMMARY STATISTICS

| Metric | Value |
|--------|-------|
| **Total Parameters** | 65 |
| **Found & Populated** | 48 (74%) |
| **NULL in JSON** | 14 (22%) |
| **Schema Mismatch** | 3 (4%) |
| **Overall Completeness** | **74%** |

---

## FIX PRIORITY BREAKDOWN

| Priority | Fields to Fix | Estimated Effort |
|----------|---------------|------------------|
| **P1 (Critical)** | 8 fields (Step 04) | 1-2 hours |
| **P2 (High)** | 3 fields (Step 01) | 2-3 hours |
| **P3 (Medium)** | 1 field (Step 05) | 30 minutes |
| **Schema Fix** | 3 fields (Step 01) | 1 hour investigation |
| **TOTAL** | 15 fields | **4-6 hours** |

---

## CRITICAL OBSERVATION

**Step 01 Issue:** The schema shows 13 fields as "MISSING" even though the JSON contains them correctly nested. This needs investigation - likely an issue with the `discover_json_files()` function not finding the files in `step_01_parse/` folder (expected `step_01_loader/`).

**Quick Fix for Step 01:**
```python
# In utils_nb07.py -> discover_json_files():
# Change folder pattern to match actual folder names:
"step_01": "step_01_parse",  # Not "step_01_loader"
```

---

**Generated:** 2026-01-23  
**Source:** Analysis of `Master_Audit_Log_20260123_182319.xlsx` + JSON inspection
