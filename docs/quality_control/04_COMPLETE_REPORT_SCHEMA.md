# 📊 COMPLETE MASTER QUALITY REPORT SCHEMA v2.0

## Updated Field Count: **22 → 108 Fields**

This document provides the **complete, final schema** for the enhanced Master Quality Report with full joint identification tracking.

---

## 📋 COMPLETE FIELD LIST (75 Fields)

### **SECTION 1: IDENTITY & PROVENANCE (8 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Run_ID` | str | filename | Unique recording identifier |
| `Subject_ID` | str | parsed | Subject number (e.g., "734") |
| `Session_ID` | str | parsed | Timepoint (e.g., "T1", "T2") |
| `Recording_ID` | str | parsed | Protocol/repetition (e.g., "P1_R1") |
| `Recording_Date` | str | step_01 | Original capture date |
| `Processing_Date` | str | step_01 | Pipeline execution date |
| `Duration_Sec` | float | step_01 | Total recording length |
| `Pipeline_Version` | str | step_04 | Processing version (reproducibility) |

---

### **SECTION 2: RAW DATA QUALITY (9 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `OptiTrack_Error_mm` | float | step_01 | System mean error |
| `Total_Frames` | int | step_01 | Frame count |
| `Actual_FPS` | float | step_03/01 | Measured sampling rate |
| `Dropped_Frames` | int | step_01 | Missing frame indices |
| `Missing_Raw_%` | float | step_02 | Initial NaN percentage |
| `Total_Joints_Expected` | int | step_01 | Expected skeleton size (51) |
| `Total_Joints_Found` | int | step_01 | Detected joints |
| `Missing_Joints` | str | step_01 | Comma-separated list |
| `Joint_Coverage_%` | float | computed | (found/expected) × 100 |

---

### **SECTION 3: PREPROCESSING METRICS (18 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Artifact_Percent` | float | step_02 | % of data masked |
| `Artifact_Worst_Joint` | str | step_02 | Joint with most artifacts |
| `Num_Gaps_Filled` | int | step_02 | Count of interpolated gaps |
| `Max_Gap_Frames` | int | step_02 | Largest gap in frames |
| `Max_Gap_MS` | float | step_02 | Largest gap in milliseconds |
| `Max_Gap_Exceeded` | bool | computed | True if > 200ms |
| `Max_Gap_Joint` | str | step_02 | Joint with largest gap |
| `Gap_Fill_Method` | str | step_02 | "cubic_spline" / "linear" |
| `Bone_Stability_CV` | float | step_02 | Mean bone length CV |
| `Skeletal_Alerts` | int | step_02 | Number of bone alerts |
| `Worst_Bone` | str | step_02 | Bone with highest CV |
| `Worst_Bone_CV` | float | step_02 | CV value of worst bone |
| `Bone_QC_Grade` | str | step_02 | GOLD/SILVER/BRONZE/FAIL |
| `Artifact_MAD_Multiplier` | float | step_02 | MAD threshold used (default: 6.0) |
| `Artifact_MAD_Validated` | bool | step_02 | Threshold empirically validated |
| `Artifact_Detection_F1_Score` | float | step_02 | Validation F1 score |
| `Artifact_False_Positive_Rate` | float | step_02 | FPR from noise robustness |
| `Artifact_Optimal_Multiplier` | float | step_02 | Recommended multiplier from validation |

**Artifact Detection Validation (Research Phase 2 - Item 6):**
- Empirical validation of MAD multiplier (typically 3-8x)
- ROC analysis with synthetic artifacts
- Noise robustness testing (false positive rates)
- Method comparison (MAD vs. Z-score vs. fixed threshold)
- Current 6x multiplier validated as balanced choice
- References: Skurowski et al. (2015), Leys et al. (2013), Feng et al. (2019)

---

### **SECTION 4: TEMPORAL VALIDATION (3 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Time_Grid_Std_DT` | float | step_03 | std(dt) - regularity |
| `Temporal_Status` | str | step_03 | PERFECT/GOOD/POOR |
| `Resample_Method` | str | step_03 | CubicSpline/Linear |

---

### **SECTION 5: FILTERING VALIDATION (13 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Filter_Cutoff_Hz` | float | step_04 | Winter-selected cutoff |
| `Filter_Method` | str | step_04 | "Winter" / "Fixed" |
| `Filter_Strategy` | str | step_04 | "multi_signal" / "trunk_global" |
| `Trunk_Min_Cutoff_Hz` | float | step_04 | Biomechanical guardrail |
| `Distal_Min_Cutoff_Hz` | float | step_04 | Biomechanical guardrail |
| `Winter_Failed` | bool | step_04 | True if cutoff = fmax |
| `Num_Filtered_Cols` | int | step_04 | Positions filtered |
| `Num_Excluded_Cols` | int | step_04 | Columns with issues |
| `Filter_PSD_Dance_Preservation_Pct` | float | step_04 | % of dance band (1-10Hz) power preserved |
| `Filter_PSD_Noise_Attenuation_dB` | float | step_04 | Noise band (15-30Hz) attenuation in dB |
| `Filter_PSD_SNR_Improvement_dB` | float | step_04 | Signal-to-noise ratio improvement |
| `Filter_PSD_Quality_Status` | str | step_04 | "PASS" / "WARN" / "FAIL" based on PSD metrics |
| `Filter_Cutoff_Validity` | str | step_04 | "VALID" / "WARN_UNUSUAL" / "FAIL_WINTER_FMAX" |

**PSD Validation (Research Phase 1 - Item 1):**
- Dance preservation >90% = excellent filter performance
- Noise attenuation >10dB = effective noise removal
- SNR improvement >3dB = overall signal quality improved
- References: Winter (2009), Welch (1967), Wren et al. (2006)

---

### **SECTION 6: REFERENCE QUALITY (17 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Ref_Stability_mm` | float | step_05 | Reference window stability |
| `Ref_Status` | str | step_05 | PASS/WARN/FAIL |
| `Ref_Method` | str | step_05 | "criteria" / "fallback" |
| `Ref_Is_Fallback` | bool | step_05 | No quiet stance found |
| `Ref_Window_Start_Sec` | float | step_05 | When reference starts |
| `Ref_Window_Duration_Sec` | float | step_05 | Window length |
| `Ref_Mean_Motion` | float | step_05 | rad/s during reference |
| `Ref_Std_Motion` | float | step_05 | Motion variability |
| `Identity_Error_Med` | float | step_05 | Quaternion self-consistency |
| `Calibration_Grade` | str | step_05 | GOLD/SILVER/BRONZE/LOCKED |
| `Left_Arm_Offset_Deg` | float | step_05 | V-pose correction |
| `Right_Arm_Offset_Deg` | float | step_05 | V-pose correction |
| `Ref_Validation_Status` | str | step_05 | "PASS" / "WARN_SHORT" / "WARN_MOTION" / "FAIL" |
| `Ref_Validation_Mean_Motion_Rad_S` | float | step_05 | Validated motion in window (rad/s) |
| `Ref_Validation_Std_Motion_Rad_S` | float | step_05 | Validated motion variability |
| `Ref_Stability_Identity_Error_Rad` | float | step_05 | Internal consistency (rad) |
| `Ref_Stability_Max_Jump_Rad` | float | step_05 | Maximum discontinuity in window |
| `Ref_Is_Early_In_Recording` | bool | step_05 | Window found in first 10s |

**Reference Validation (Research Phase 1 - Item 2):**
- Window validation: Ensures static pose meets research criteria (Kok et al. 2017)
- Stability validation: Checks internal consistency and discontinuities
- Motion thresholds: Mean <0.3 rad/s (strict) or <0.5 rad/s (relaxed)
- Duration: Prefer >1.0 second windows
- References: Kok et al. (2017), Roetenberg et al. (2009), Sabatini (2006)

---

### **SECTION 7: COORDINATE SYSTEM DOCUMENTATION (5 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Coordinate_System_Documented` | bool | metadata | Always True for validated pipelines |
| `Input_Frame` | str | metadata | "OptiTrack World (X=Right, Y=Up, Z=Forward)" |
| `Processing_Frame` | str | metadata | Frame used during processing |
| `Angle_Frame` | str | metadata | "ISB Anatomical" for Euler angles |
| `Frame_Transformation_Explicit` | bool | metadata | Transformations explicitly documented |

**Coordinate System Documentation (Research Phase 1 - Item 3):**
- Explicit documentation of all coordinate frames used
- OptiTrack: X=Right, Y=Up, Z=Forward (right-handed, mm)
- ISB: X=Anterior, Y=Superior, Z=Right (right-handed, m)
- Euler sequences follow Wu et al. (2005) ISB recommendations
- All transformations explicitly defined and validated
- References: Wu et al. (2005), OptiTrack Documentation (2020)

---

### **SECTION 8: SIGNAL QUALITY (12 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Signal_Noise_RMS` | float | step_06 | Velocity residual RMS |
| `Dom_Freq_Hz` | float | step_06 | Dominant frequency |
| `Quat_Norm_Error` | float | step_06 | Max quaternion error |
| `Quat_Norm_Error_Joint` | str | step_06 | **Which joint has error** |
| `Quat_Norm_Error_Frame` | int | step_06 | **When error occurred** |
| `Quat_Max_Norm_Deviation` | float | step_02 | Maximum quaternion norm drift |
| `Quat_Mean_Norm_Deviation` | float | step_02 | Average quaternion norm drift |
| `Quat_Drift_Detected` | bool | step_02 | Significant drift detected (>0.01) |
| `Quat_Drift_Status` | str | step_02 | "EXCELLENT" / "GOOD" / "ACCEPTABLE" / "POOR" |
| `Quat_Drift_Percentage` | float | step_02 | % of frames with drift |
| `Quat_Continuity_Breaks` | int | step_02 | Number of hemisphere discontinuities |
| `Quat_Integrity_Status` | str | step_02 | Overall quaternion integrity status |

**Quaternion Normalization (Research Phase 1 - Item 4):**
- Frame-by-frame drift detection and correction
- Normalization: <0.001 = GOOD, <0.01 = ACCEPTABLE, >0.01 = POOR
- Continuity enforcement prevents double-cover jumps
- Drift accumulation detected over long sequences
- Critical for angular velocity and orientation accuracy
- References: Grassia (1998), Shoemake (1985), Diebel (2006)

---

### **SECTION 9: KINEMATIC METRICS (19 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Max_Ang_Vel` | float | step_06 | Peak angular velocity (deg/s) |
| `Max_Ang_Vel_Joint` | str | step_06 | **Which joint** |
| `Max_Ang_Vel_Frame` | int | step_06 | **When it occurred** |
| `Mean_Ang_Vel` | float | step_06 | Average angular velocity |
| `Max_Ang_Acc` | float | step_06 | Peak angular acceleration |
| `Max_Ang_Acc_Joint` | str | step_06 | **Which joint** |
| `Max_Ang_Acc_Frame` | int | step_06 | **When it occurred** |
| `Max_Lin_Acc` | float | step_06 | Peak linear acceleration (mm/s²) |
| `Max_Lin_Acc_Joint` | str | step_06 | **Which joint** |
| `Max_Lin_Acc_Frame` | int | step_06 | **When it occurred** |
| `Mean_Lin_Acc` | float | step_06 | Average linear acceleration |
| `Outlier_Frames` | int | step_06 | Total outlier count |
| `Outlier_Worst_Joint` | str | step_06 | **Joint with most outliers** |
| `Outlier_Joints_List` | str | step_06 | **All affected joints** |
| `Omega_Computation_Method` | str | step_06 | "quaternion_log" / "5point" / "central" |
| `Omega_Noise_Metric` | float | step_06 | Noise assessment (std of 2nd derivative) |
| `Omega_Method_Validated` | bool | step_06 | Method comparison performed |
| `Omega_Noise_Reduction_Factor` | float | step_06 | vs. central difference baseline |
| `Omega_Frame` | str | step_06 | "local" (body) or "global" (world) |

**Angular Velocity Enhancement (Research Phase 2 - Item 5):**
- Quaternion logarithm method: Respects SO(3) manifold structure
- 5-point stencil: 3.5x noise reduction vs. central difference
- Method comparison and automatic selection
- Robust to numerical issues with small rotations
- References: Müller et al. (2017), Diebel (2006), Sola (2017)

---

### **SECTION 10: PHYSIOLOGICAL VALIDATION (8 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Unphysiological_Accel` | bool | computed | True if max > 100 m/s² |
| `Unphysiological_Accel_Joint` | str | step_06 | **Which joint exceeded** |
| `Unphysiological_Accel_Value` | float | computed | **Actual value (m/s²)** |
| `Unphysiological_Accel_Frame` | int | step_06 | **When it occurred** |
| `Unphysiological_Ang_Vel` | bool | computed | True if max > 5000 deg/s |
| `Unphysiological_Ang_Vel_Joint` | str | step_06 | **Which joint exceeded** |
| `Unphysiological_Ang_Vel_Value` | float | computed | **Actual value (deg/s)** |
| `Unphysiological_Ang_Vel_Frame` | int | step_06 | **When it occurred** |

---

### **SECTION 11: EFFORT METRICS (3 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Path_Length_M` | float | step_06 | Total movement path |
| `Intensity_Index` | float | step_06 | Normalized effort |
| `Outlier_Percent` | float | computed | (outliers / total) × 100 |

---

### **SECTION 12: QUALITY SCORING (3 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Quality_Score` | float | computed | 0-100 score |
| `Quality_Score_Method` | str | computed | "heuristic_v2_biomechanical" |
| `Research_Decision` | str | computed | ACCEPT/REVIEW/REJECT |
| `Pipeline_Status` | str | step_06 | PASS/FAIL |

---

## 🎯 FIELD COUNT BREAKDOWN

| Section | Current | Enhanced | Added |
|---------|---------|----------|-------|
| Identity & Provenance | 2 | 8 | +6 |
| Raw Data Quality | 3 | 9 | +6 |
| Preprocessing | 5 | 18 | +13 |
| Temporal Validation | 0 | 3 | +3 |
| Filtering Validation | 0 | 13 | +13 |
| Reference Quality | 2 | 17 | +15 |
| Coordinate System Documentation | 0 | 5 | +5 |
| Signal Quality | 3 | 12 | +9 |
| Kinematic Metrics | 4 | 19 | +15 |
| Physiological Validation | 0 | 8 | +8 |
| Effort Metrics | 2 | 3 | +1 |
| Quality Scoring | 3 | 3 | 0 |
| **TOTAL** | **22** | **108** | **+86** |

---

## 🔍 JOINT IDENTIFICATION SUMMARY

### **Why Joint Tracking Matters**

**Example 1: Angular Velocity Context**
```python
# WITHOUT joint tracking:
"Max_Ang_Vel": 1026.98  # ⚠️ Is this normal or concerning?

# WITH joint tracking:
"Max_Ang_Vel": 1026.98,
"Max_Ang_Vel_Joint": "RightHand",  # ✅ Normal for hand gesture
"Max_Ang_Vel_Frame": 15234         # ✅ Can verify visually
```

**Example 2: Unphysiological Flag Context**
```python
# WITHOUT joint tracking:
"Unphysiological_Accel": True  # ❌ Automatic rejection?

# WITH joint tracking:
"Unphysiological_Accel": True,
"Unphysiological_Accel_Joint": "RightToeBase",  # ⚠️ Jump landing = Review
"Unphysiological_Accel_Value": 125.3,           # ⚠️ 125 m/s² borderline
"Unphysiological_Accel_Frame": 12045            # ✅ Navigate to frame

# vs.

"Unphysiological_Accel": True,
"Unphysiological_Accel_Joint": "Hips",          # ❌ Marker slip = Reject
"Unphysiological_Accel_Value": 256.8,           # ❌ 257 m/s² unphysiological
"Unphysiological_Accel_Frame": 8234
```

---

## 📊 COMPLETE EXAMPLE ROW

```python
{
    # === IDENTITY & PROVENANCE ===
    "Run_ID": "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM",
    "Subject_ID": "734",
    "Session_ID": "T1",
    "Recording_ID": "P1_R1",
    "Recording_Date": "2025-12-01",
    "Processing_Date": "2026-01-18 17:05",
    "Duration_Sec": 256.64,
    "Pipeline_Version": "v2.6_biomechanical_guardrails",
    
    # === RAW DATA QUALITY ===
    "OptiTrack_Error_mm": 0.0,
    "Total_Frames": 30798,
    "Actual_FPS": 120.0,
    "Dropped_Frames": 0,
    "Missing_Raw_%": 0.0,
    "Total_Joints_Expected": 51,
    "Total_Joints_Found": 51,
    "Missing_Joints": "",
    "Joint_Coverage_%": 100.0,
    
    # === PREPROCESSING METRICS ===
    "Artifact_Percent": 0.5,
    "Artifact_Worst_Joint": "RightHandPinky3",
    "Num_Gaps_Filled": 12,
    "Max_Gap_Frames": 10,
    "Max_Gap_MS": 83.3,
    "Max_Gap_Exceeded": False,
    "Max_Gap_Joint": "RightHandPinky3",
    "Gap_Fill_Method": "cubic_spline",
    "Bone_Stability_CV": 0.408,
    "Skeletal_Alerts": 2,
    "Worst_Bone": "Hips->Spine",
    "Worst_Bone_CV": 0.82,
    "Bone_QC_Grade": "GOLD",
    
    # === TEMPORAL VALIDATION ===
    "Time_Grid_Std_DT": 0.0,
    "Temporal_Status": "PERFECT",
    "Resample_Method": "CubicSpline",
    
    # === FILTERING VALIDATION ===
    "Filter_Cutoff_Hz": 8.0,
    "Filter_Method": "Winter Dynamic Cutoff Selection",
    "Filter_Strategy": "multi_signal_with_guardrails",
    "Trunk_Min_Cutoff_Hz": 6.0,
    "Distal_Min_Cutoff_Hz": 8.0,
    "Winter_Failed": False,
    "Num_Filtered_Cols": 153,
    "Num_Excluded_Cols": 0,
    
    # === REFERENCE QUALITY ===
    "Ref_Stability_mm": 35.99,
    "Ref_Status": "MEDIUM",
    "Ref_Method": "criteria",
    "Ref_Is_Fallback": False,
    "Ref_Window_Start_Sec": 0.0,
    "Ref_Window_Duration_Sec": 1.0,
    "Ref_Mean_Motion": 0.08,
    "Ref_Std_Motion": 0.03,
    "Identity_Error_Med": 0.05,
    "Calibration_Grade": "LOCKED",
    "Left_Arm_Offset_Deg": 10.13,
    "Right_Arm_Offset_Deg": 11.34,
    
    # === SIGNAL QUALITY ===
    "Signal_Noise_RMS": 10.72,
    "Dom_Freq_Hz": 0.0,
    "Quat_Norm_Error": 0.0,
    "Quat_Norm_Error_Joint": "None",
    "Quat_Norm_Error_Frame": -1,
    
    # === KINEMATIC METRICS ===
    "Max_Ang_Vel": 1026.98,
    "Max_Ang_Vel_Joint": "RightHand",
    "Max_Ang_Vel_Frame": 15234,
    "Mean_Ang_Vel": 31.98,
    "Max_Ang_Acc": 42172.89,
    "Max_Ang_Acc_Joint": "LeftHandIndex3",
    "Max_Ang_Acc_Frame": 8967,
    "Max_Lin_Acc": 38536.2,
    "Max_Lin_Acc_Joint": "RightToeBase",
    "Max_Lin_Acc_Frame": 12045,
    "Mean_Lin_Acc": 814.07,
    "Outlier_Frames": 0,
    "Outlier_Worst_Joint": "None",
    "Outlier_Joints_List": "None",
    
    # === PHYSIOLOGICAL VALIDATION ===
    "Unphysiological_Accel": False,
    "Unphysiological_Accel_Joint": "None",
    "Unphysiological_Accel_Value": 0.0,
    "Unphysiological_Accel_Frame": -1,
    "Unphysiological_Ang_Vel": False,
    "Unphysiological_Ang_Vel_Joint": "None",
    "Unphysiological_Ang_Vel_Value": 0.0,
    "Unphysiological_Ang_Vel_Frame": -1,
    
    # === EFFORT METRICS ===
    "Path_Length_M": 25.67,
    "Intensity_Index": 0.084,
    "Outlier_Percent": 0.0,
    
    # === QUALITY SCORING ===
    "Quality_Score": 87.5,
    "Quality_Score_Method": "heuristic_v2_biomechanical",
    "Research_Decision": "ACCEPT",
    "Pipeline_Status": "PASS"
}
```

---

## 🛠️ IMPLEMENTATION PHASES

### **Phase 1: Core Enhancements (2-3 hours)**
- [ ] Add 12 critical validation fields
- [ ] Add 8 joint identification fields (high priority)
- [ ] Update quality score v2.0
- **Result**: 42 fields total

### **Phase 2: Complete Joint Tracking (2-3 hours)**
- [ ] Add remaining 8 joint identification fields
- [ ] Update step_06 to track maxima
- [ ] Add frame number tracking
- **Result**: 58 fields total

### **Phase 3: Full Enhancement (3-4 hours)**
- [ ] Add all remaining fields
- [ ] Implement percentile metrics
- [ ] Create multi-sheet Excel export
- **Result**: 75+ fields total

---

## 📚 DOCUMENTATION ALIGNMENT

All three documents now aligned:
1. ✅ **RECORDING_AUDIT_CHECKLIST.md** - Audit protocol
2. ✅ **MASTER_QUALITY_REPORT_REVIEW.md** - Gap analysis & recommendations
3. ✅ **JOINT_LEVEL_TRACKING.md** - Joint identification rationale
4. ✅ **COMPLETE_REPORT_SCHEMA.md** - Final schema (this document)

---

**VERSION**: 2.0  
**DATE**: January 2026  
**STATUS**: Production-Ready Schema
