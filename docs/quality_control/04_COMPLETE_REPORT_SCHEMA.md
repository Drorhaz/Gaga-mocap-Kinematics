# 📊 COMPLETE MASTER QUALITY REPORT SCHEMA v2.0

## Updated Field Count: **22 → 80+ Fields**

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

### **SECTION 3: PREPROCESSING METRICS (13 fields)**

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

### **SECTION 6: REFERENCE QUALITY (11 fields)**

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

---

### **SECTION 7: SIGNAL QUALITY (5 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Signal_Noise_RMS` | float | step_06 | Velocity residual RMS |
| `Dom_Freq_Hz` | float | step_06 | Dominant frequency |
| `Quat_Norm_Error` | float | step_06 | Max quaternion error |
| `Quat_Norm_Error_Joint` | str | step_06 | **Which joint has error** |
| `Quat_Norm_Error_Frame` | int | step_06 | **When error occurred** |

---

### **SECTION 8: KINEMATIC METRICS (14 fields)**

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

---

### **SECTION 9: PHYSIOLOGICAL VALIDATION (8 fields)**

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

### **SECTION 10: EFFORT METRICS (3 fields)**

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `Path_Length_M` | float | step_06 | Total movement path |
| `Intensity_Index` | float | step_06 | Normalized effort |
| `Outlier_Percent` | float | computed | (outliers / total) × 100 |

---

### **SECTION 11: QUALITY SCORING (3 fields)**

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
| Preprocessing | 5 | 13 | +8 |
| Temporal Validation | 0 | 3 | +3 |
| Filtering Validation | 0 | 13 | +13 |
| Reference Quality | 2 | 11 | +9 |
| Signal Quality | 3 | 5 | +2 |
| Kinematic Metrics | 4 | 14 | +10 |
| Physiological Validation | 0 | 8 | +8 |
| Effort Metrics | 2 | 3 | +1 |
| Quality Scoring | 3 | 3 | 0 |
| **TOTAL** | **22** | **80** | **+58** |

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
