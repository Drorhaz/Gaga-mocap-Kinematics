# Parameter Schema - Master Quality Report (NB07)

This document describes all JSON parameters extracted by the Master Quality Report.

**Generated:** 2026-01-23 15:17:10

---

## Section Overview

| Section | Name | Description |
|---------|------|-------------|
| S0 | Data Lineage & Provenance | Report section |
| S1 | Rácz Calibration Layer | Report section |
| S2 | Temporal Quality & Sampling | Report section |
| S3 | Gap & Interpolation Transparency | Report section |
| S4 | Winter's Residual Validation | Report section |
| S5 | Reference Detection & Stability | Report section |
| S6 | Biomechanics & Outlier Analysis | Report section |
| S7 | Signal-to-Noise Quantification | Report section |
| S8 | Decision Matrix | Report section |

---

## step_01: Raw data loader report - initial parsing results

**File Suffix:** `__step01_loader_report.json`

| Parameter Path | Type | Section | Description |
|----------------|------|---------|-------------|
| `identity.run_id` | str | S0 | Unique recording identifier |
| `identity.processing_timestamp` | str | S0 | When pipeline ran |
| `identity.pipeline_version` | str | S0 | Pipeline version string |
| `identity.csv_source` | str | S0 | Path to raw CSV file |
| `raw_data_quality.total_frames` | int | S2 | Total frames in recording |
| `raw_data_quality.missing_data_percent` | str | S3 | Percentage of missing data |
| `raw_data_quality.sampling_rate_actual` | float | S2 | Actual sampling rate (Hz) |
| `raw_data_quality.optitrack_mean_error_mm` | float | S1 | OptiTrack calibration error (mm) |
| `raw_data_quality.optitrack_version` | str | S0 | OptiTrack software version |
| `calibration.pointer_tip_rms_error_mm` | float | S1 | Pointer tip RMS error (mm) |
| `calibration.wand_error_mm` | float | S1 | Wand calibration error (mm) |
| `calibration.export_date` | str | S0 | Data export date |
| `skeleton_info.segments_found_count` | int | S1 | Number of skeleton segments found |
| `skeleton_info.segments_missing_count` | int | S1 | Number of missing segments |
| `duration_sec` | float | S2 | Recording duration in seconds |

---

## step_02: Preprocessing summary - gap filling and bone stability

**File Suffix:** `__preprocess_summary.json`

| Parameter Path | Type | Section | Description |
|----------------|------|---------|-------------|
| `run_id` | str | S0 | Recording identifier |
| `raw_missing_percent` | float | S3 | Raw missing data percentage |
| `post_missing_percent` | float | S3 | Missing data after interpolation |
| `max_interpolation_gap` | int | S3 | Maximum gap frames allowed for interpolation |
| `bone_qc_mean_cv` | float | S1 | Mean coefficient of variation for bone lengths |
| `bone_qc_status` | str | S1 | Bone QC status (GOLD/SILVER/BRONZE/FAIL) |
| `bone_qc_alerts` | list | S1 | List of bones with alerts |
| `worst_bone` | str | S1 | Bone with highest CV |
| `interpolation_method` | str | S3 | Global interpolation method used |

---

## step_04: Filtering summary - Winter residual analysis

**File Suffix:** `__filtering_summary.json`

| Parameter Path | Type | Section | Description |
|----------------|------|---------|-------------|
| `run_id` | str | S0 | Recording identifier |
| `identity.timestamp` | str | S0 | Filtering timestamp |
| `identity.pipeline_version` | str | S0 | Pipeline version |
| `subject_metadata.mass_kg` | float | S0 | Subject mass (kg) |
| `subject_metadata.height_cm` | float | S0 | Subject height (cm) |
| `raw_quality.total_frames` | int | S2 | Total frames |
| `raw_quality.sampling_rate_actual` | float | S2 | Sampling rate (Hz) |
| `filter_params.filter_type` | str | S4 | Filter type description |
| `filter_params.filter_method` | str | S4 | Filter method name |
| `filter_params.filter_cutoff_hz` | float | S4 | Cutoff frequency (Hz) |
| `filter_params.filter_range_hz` | list | S4 | Filter range [min, max] Hz |
| `filter_params.filter_order` | int | S4 | Butterworth filter order |
| `filter_params.winter_analysis_failed` | bool | S4 | Whether Winter analysis failed |
| `filter_params.winter_failure_reason` | str | S4 | Reason for Winter analysis failure (if any) |
| `filter_params.decision_reason` | str | S4 | Decision rationale for filter cutoff selection |
| `filter_params.biomechanical_guardrails.enabled` | bool | S4 | Guardrails enabled |

---

## step_05: Reference detection - static pose alignment

**File Suffix:** `__reference_summary.json`

| Parameter Path | Type | Section | Description |
|----------------|------|---------|-------------|
| `run_id` | str | S0 | Recording identifier |
| `subject_context.height_cm` | float | S0 | Estimated height (cm) |
| `subject_context.scaling_factor` | float | S0 | Scaling factor applied |
| `static_offset_audit.Left.measured_angle_deg` | float | S1 | Left shoulder offset (deg) |
| `static_offset_audit.Right.measured_angle_deg` | float | S1 | Right shoulder offset (deg) |
| `window_metadata.start_time_sec` | float | S5 | Reference window start (sec) |
| `window_metadata.end_time_sec` | float | S5 | Reference window end (sec) |
| `window_metadata.variance_score` | float | S5 | Window stability score |
| `window_metadata.ref_quality_score` | float | S5 | Reference quality score |
| `window_metadata.confidence_level` | str | S5 | Confidence level (HIGH/MEDIUM/LOW) |
| `window_metadata.detection_method` | str | S5 | Detection method used |
| `metadata.grade` | str | S5 | Reference grade |
| `metadata.status` | str | S5 | Reference status (LOCKED/PROVISIONAL) |

---

## step_06: Kinematics summary - angular velocities and outliers

**File Suffix:** `__kinematics_summary.json`

| Parameter Path | Type | Section | Description |
|----------------|------|---------|-------------|
| `run_id` | str | S0 | Recording identifier |
| `overall_status` | str | S8 | Overall pipeline status (PASS/FAIL) |
| `metrics.angular_velocity.max` | float | S6 | Max angular velocity (deg/s) |
| `metrics.angular_velocity.limit` | float | S6 | Angular velocity limit |
| `metrics.angular_accel.max` | float | S6 | Max angular acceleration (deg/s²) |
| `metrics.linear_accel.max` | float | S6 | Max linear acceleration (mm/s²) |
| `signal_quality.avg_residual_rms` | float | S7 | Average residual RMS |
| `signal_quality.max_quat_norm_err` | float | S2 | Max quaternion normalization error |
| `movement_metrics.path_length_mm` | float | S6 | Total path length (mm) |
| `movement_metrics.intensity_index` | float | S6 | Movement intensity index |
| `outlier_analysis.counts.total_outliers` | int | S6 | Total outlier frames |
| `outlier_analysis.percentages.total_outliers` | float | S6 | Outlier percentage |
| `outlier_analysis.consecutive_runs.max_consecutive_any_outlier` | int | S6 | Max consecutive outliers |
| `pipeline_params.sg_window_sec` | float | S6 | Savitzky-Golay window (sec) |
| `pipeline_params.fs_target` | float | S2 | Target sampling rate |

---
