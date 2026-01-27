# 📊 MASTER QUALITY REPORT REVIEW & RECOMMENDATIONS

## Executive Summary

Your current master quality report (Notebook 07) provides a **solid foundation** for quality assurance but is **missing several critical biomechanical validation metrics** that are standard in motion capture research. This document provides a comprehensive review and actionable recommendations.

---

## ✅ CURRENT REPORT STRENGTHS

### Currently Tracked Metrics (22 fields):

#### **Identity & Provenance** ✅
- ✅ Run_ID
- ✅ Processing_Date

#### **Raw Data Quality** ✅
- ✅ OptiTrack_Error_mm
- ✅ Total_Frames
- ✅ Missing_Raw_%

#### **Preprocessing Metrics** ✅
- ✅ Max_Gap_Frames
- ✅ Max_Gap_MS
- ✅ Bone_Stability_CV
- ✅ Skeletal_Alerts
- ✅ Worst_Bone

#### **Reference Quality** ✅
- ✅ Ref_Stability_mm
- ✅ Ref_Status

#### **Signal Quality** ✅
- ✅ Signal_Noise_RMS
- ✅ Dom_Freq_Hz
- ✅ Quat_Norm_Error

#### **Kinematic Metrics** ✅
- ✅ Max_Ang_Vel
- ✅ Mean_Ang_Vel
- ✅ Max_Lin_Acc
- ✅ Outlier_Frames

#### **Effort Metrics** ✅
- ✅ Path_Length_M
- ✅ Intensity_Index

#### **Quality Scoring** ✅
- ✅ Quality_Score (heuristic_v1)
- ✅ Research_Decision (ACCEPT/REVIEW/REJECT)
- ✅ Pipeline_Status

---

## ⚠️ CRITICAL MISSING METRICS

### 1. **Temporal & Sampling Validation** (Stage 3)

#### Missing:
```python
"Actual_FPS": float               # Measured sampling rate
"Time_Grid_Quality": str          # "PERFECT" / "GOOD" / "POOR"
"Time_Grid_Std_DT": float         # std(dt) - regularity metric
"Dropped_Frames": int             # Missing frame indices
"Temporal_Status": str            # From step_03 summary
```

**Why Critical:**
- Sampling rate deviations affect filter design
- Irregular time grids violate FFT assumptions
- Dropped frames indicate capture issues

**Where to Extract:**
```python
# From step_03_resample summary:
s03 = steps.get('step_03', {})
row["Actual_FPS"] = safe_float(safe_get(s03, 'target_fs'), default=120.0)
row["Time_Grid_Std_DT"] = safe_float(safe_get(s03, 'time_grid_std_dt'))
row["Temporal_Status"] = safe_get(s03, 'temporal_status', default='UNKNOWN')
```

---

### 2. **Filtering Validation** (Stage 4)

#### Missing:
```python
"Filter_Cutoff_Hz": float         # Winter-selected cutoff
"Filter_Method": str              # "Winter" / "Fixed"
"Filter_Strategy": str            # "multi_signal" / "trunk_global"
"Trunk_Min_Cutoff_Hz": float      # Biomechanical guardrail
"Distal_Min_Cutoff_Hz": float     # Biomechanical guardrail
"Winter_Failed": bool             # True if cutoff = fmax
"Num_Filtered_Cols": int          # Position columns filtered
"Num_Excluded_Cols": int          # Columns with issues
```

**Why Critical:**
- Winter failure (cutoff=12Hz) indicates data quality issues
- Different cutoffs for trunk vs. distal affects interpretation
- Excluded columns may indicate systematic problems

**Where to Extract:**
```python
# From step_04_filtering summary:
s04 = steps.get('step_04', {})
row["Filter_Cutoff_Hz"] = safe_float(safe_get(s04, 'filter_params', 'filter_cutoff_hz'))
row["Filter_Method"] = safe_get(s04, 'filter_params', 'filter_method', default='Unknown')
row["Filter_Strategy"] = safe_get(s04, 'filter_params', 'biomechanical_guardrails', 'strategy')
row["Winter_Failed"] = safe_get(s04, 'filter_params', 'winter_analysis_failed', default=False)
row["Num_Filtered_Cols"] = len(safe_get(s04, 'filter_params', 'pos_cols_valid', default=[]))
row["Num_Excluded_Cols"] = len(safe_get(s04, 'filter_params', 'pos_cols_excluded', default=[]))
```

---

### 3. **Reference Detection Quality** (Stage 5)

#### Missing:
```python
"Ref_Method": str                 # "criteria" / "fallback_min_motion"
"Ref_Is_Fallback": bool           # True if no quiet stance found
"Ref_Window_Start_Sec": float     # Reference window timing
"Ref_Window_Duration_Sec": float  # Window length used
"Ref_Mean_Motion": float          # rad/s during reference
"Ref_Std_Motion": float           # Motion variability
"Identity_Error_Med": float       # Quaternion self-consistency
"Ref_Quality_Score": float        # Reference pose quality
```

**Why Critical:**
- Fallback references are less reliable (no true quiet stance)
- Motion during "static" window affects zero-reference accuracy
- Identity error indicates reference pose consistency

**Where to Extract:**
```python
# From step_05_reference summary:
s05 = steps.get('step_05', {})
row["Ref_Method"] = safe_get(s05, 'window_metadata', 'method', default='unknown')
row["Ref_Is_Fallback"] = safe_get(s05, 'window_metadata', 'ref_is_fallback', default=True)
row["Ref_Window_Start_Sec"] = safe_float(safe_get(s05, 'window_metadata', 'start_time_sec'))
row["Ref_Mean_Motion"] = safe_float(safe_get(s05, 'window_metadata', 'metrics', 'mean_motion'))
row["Ref_Std_Motion"] = safe_float(safe_get(s05, 'window_metadata', 'metrics', 'std_motion'))
row["Identity_Error_Med"] = safe_float(safe_get(s05, 'reference_qc', 'identity_error_ref_med'))
```

---

### 4. **V-Pose Calibration** (Stage 5)

#### Missing:
```python
"Calibration_Grade": str          # "GOLD" / "SILVER" / "BRONZE" / "LOCKED"
"Left_Arm_Offset_Deg": float      # Static offset correction
"Right_Arm_Offset_Deg": float     # Static offset correction
"Offset_Significant": bool        # True if > 5° correction applied
"Arm_Span_Ratio": float           # Anthropometric validation
```

**Why Critical:**
- Large offsets indicate poor calibration pose
- Anthropometric ratios validate scaling (if subject height provided)
- CAST technique standard for anatomical zero establishment

**Where to Extract:**
```python
# From step_05_reference summary:
s05 = steps.get('step_05', {})
row["Calibration_Grade"] = safe_get(s05, 'metadata', 'grade', default='UNKNOWN')
row["Left_Arm_Offset_Deg"] = safe_float(
    safe_get(s05, 'static_offset_audit', 'Left', 'measured_angle_deg')
)
row["Right_Arm_Offset_Deg"] = safe_float(
    safe_get(s05, 'static_offset_audit', 'Right', 'measured_angle_deg')
)
row["Offset_Significant"] = safe_get(
    s05, 'static_offset_audit', 'Left', 'is_significant', default=False
)
```

---

### 5. **Artifact Detection** (Stage 2)

#### Missing:
```python
"Artifact_Detection_Method": str  # "MAD_6.0" / etc.
"Artifact_Percent": float         # % of data masked as artifacts
"Num_Gaps_Filled": int            # Count of interpolated gaps
"Gap_Fill_Method": str            # "cubic_spline" / "linear"
"Max_Gap_Exceeded": bool          # True if gap > 200ms
```

**Why Critical:**
- High artifact percentage indicates capture quality issues
- Gap filling method affects data reliability
- Large gaps (>200ms) exceed interpolation validity

**Where to Extract:**
```python
# From step_02_preprocess summary:
s02 = steps.get('step_02', {})
row["Gap_Fill_Method"] = safe_get(s02, 'interpolation_method', default='unknown')
row["Artifact_Percent"] = safe_float(safe_get(s02, 'artifact_mask_percent'))
row["Num_Gaps_Filled"] = safe_get(s02, 'num_gaps_filled', default=0)
row["Max_Gap_Exceeded"] = safe_get(s02, 'max_gap_ms', default=0) > 200
```

---

### 6. **Physiological Validation** (Stage 6)

#### Missing:
```python
"Mean_Lin_Acc": float             # Mean acceleration (m/s²)
"Max_Ang_Acc": float              # Peak angular acceleration (deg/s²)
"Max_Ang_Acc_Joint": str          # Which joint has max angular accel (NEW)
"Max_Ang_Acc_Frame": int          # Frame number of max ang accel (NEW)
"Unphysiological_Accel": bool     # True if max_accel > 100 m/s²
"Unphysiological_Accel_Joint": str   # Which joint exceeded limit (NEW)
"Unphysiological_Accel_Value": float # Actual value in m/s² (NEW)
"Unphysiological_Ang_Vel": bool   # True if omega > 5000 deg/s
"Unphysiological_Ang_Vel_Joint": str # Which joint exceeded limit (NEW)
"Unphysiological_Ang_Vel_Value": float # Actual value in deg/s (NEW)
"Velocity_Range_Min": float       # Minimum velocity detected
"Velocity_Range_Max": float       # Maximum velocity detected
```

**Why Critical:**
- Unphysiological values indicate noise amplification or artifacts
- **Joint identification enables targeted debugging** (marker issue vs. systemic problem)
- Velocity ranges validate movement variety (not static)
- Flags for automatic rejection of corrupt data
- **Knowing which joint helps identify if it's expected** (e.g., rapid hand gesture vs. pelvis spike = artifact)

**Where to Extract:**
```python
# From step_06_kinematics summary:
s06 = steps.get('step_06', {})
row["Mean_Lin_Acc"] = safe_float(safe_get(s06, 'metrics', 'linear_accel', 'mean'))
row["Max_Ang_Acc"] = safe_float(safe_get(s06, 'metrics', 'angular_accel', 'max'))
row["Max_Ang_Acc_Joint"] = safe_get(s06, 'metrics', 'angular_accel', 'max_joint')  # NEW
row["Max_Ang_Acc_Frame"] = safe_get(s06, 'metrics', 'angular_accel', 'max_frame')  # NEW

# Unphysiological acceleration
max_acc = safe_float(row["Max_Lin_Acc"])
row["Unphysiological_Accel"] = max_acc > 100000  # mm/s²
if row["Unphysiological_Accel"]:
    row["Unphysiological_Accel_Joint"] = safe_get(s06, 'metrics', 'linear_accel', 'max_joint')
    row["Unphysiological_Accel_Value"] = round(max_acc / 1000, 2)  # Convert to m/s²
else:
    row["Unphysiological_Accel_Joint"] = "None"
    row["Unphysiological_Accel_Value"] = 0.0

# Unphysiological angular velocity
max_omega = safe_float(row["Max_Ang_Vel"])
row["Unphysiological_Ang_Vel"] = max_omega > 5000  # deg/s
if row["Unphysiological_Ang_Vel"]:
    row["Unphysiological_Ang_Vel_Joint"] = safe_get(s06, 'metrics', 'angular_velocity', 'max_joint')
    row["Unphysiological_Ang_Vel_Value"] = round(max_omega, 2)
else:
    row["Unphysiological_Ang_Vel_Joint"] = "None"
    row["Unphysiological_Ang_Vel_Value"] = 0.0
```

---

### 7. **Data Provenance & Traceability**

#### Missing:
```python
"Subject_ID": str                 # Extracted from filename
"Session_ID": str                 # Timepoint (T1, T2, etc.)
"Recording_ID": str               # Protocol/repetition
"Take_Number": int                # Multiple takes per condition
"Recording_Date": str             # Original capture date
"Duration_Sec": float             # Total recording length
"Pipeline_Version": str           # Processing version
"Config_Checksum": str            # Configuration reproducibility
```

**Why Critical:**
- Essential for longitudinal studies (T1 vs T2 comparisons)
- Configuration changes affect reproducibility
- Duration affects intensity metrics normalization

**Where to Extract:**
```python
# Parse from Run_ID (e.g., "734_T1_P1_R1_Take 2025-12-01...")
import re
match = re.match(r"(\d+)_T(\d+)_P(\d+)_R(\d+)", run_id)
if match:
    row["Subject_ID"] = match.group(1)
    row["Session_ID"] = f"T{match.group(2)}"
    row["Recording_ID"] = f"P{match.group(3)}_R{match.group(4)}"

# From step_01:
row["Duration_Sec"] = safe_float(safe_get(s01, 'duration_sec'))
row["Pipeline_Version"] = safe_get(s04, 'identity', 'pipeline_version', default='unknown')
```

---

### 8. **Skeleton Completeness Tracking**

#### Missing:
```python
"Total_Joints_Expected": int      # 51 for full body
"Total_Joints_Found": int         # Detected in capture
"Missing_Joints": str             # Comma-separated list
"Critical_Joints_Missing": bool   # True if Hips/Hands/Feet missing
"Joint_Coverage_Percent": float   # (found / expected) × 100
```

**Why Critical:**
- Missing critical joints prevent kinematic chain computation
- Joint coverage affects movement analysis completeness
- Systematic missing joints indicate calibration issues

**Where to Extract:**
```python
# From step_01 loader report:
s01 = steps.get('step_01', {})
row["Total_Joints_Expected"] = safe_get(s01, 'segments_expected', default=51)
row["Total_Joints_Found"] = safe_get(s01, 'segments_found_count', default=0)
row["Missing_Joints"] = ', '.join(safe_get(s01, 'segments_missing_list', default=[]))
row["Joint_Coverage_Percent"] = (
    100.0 * row["Total_Joints_Found"] / row["Total_Joints_Expected"]
    if row["Total_Joints_Expected"] > 0 else 0.0
)
```

---

### 9. **Statistical Summary Metrics**

#### Missing:
```python
"Rotvec_Mag_P95": float           # 95th percentile joint excursion
"Rotvec_Mag_Median": float        # Typical joint displacement
"Omega_Mag_P95": float            # 95th percentile ang velocity
"Vel_Mag_P95": float              # 95th percentile lin velocity
"Dynamic_Range_Score": float      # Movement variety index
```

**Why Critical:**
- P95 metrics are robust to outliers (better than max)
- Median provides typical movement magnitude
- Dynamic range validates movement diversity (not static pose)

**Where to Extract:**
```python
# From step_06 kinematics summary (if available):
s06 = steps.get('step_06', {})
row["Rotvec_Mag_P95"] = safe_float(safe_get(s06, 'metrics', 'rotvec_mag', 'p95'))
row["Omega_Mag_P95"] = safe_float(safe_get(s06, 'metrics', 'omega_mag', 'p95'))
```

---

### 10. **Processing Efficiency Metrics**

#### Missing:
```python
"Processing_Time_Sec": float      # Total pipeline execution time
"Step_01_Time_Sec": float         # Parse time
"Step_04_Time_Sec": float         # Filtering time (most intensive)
"Step_06_Time_Sec": float         # Kinematics computation time
"File_Size_MB": float             # Original CSV size
"Derivative_Size_MB": float       # Total output size
```

**Why Critical:**
- Identifies computational bottlenecks
- Flags abnormally long processing (data issues)
- Resource planning for batch processing

---

## 📊 RECOMMENDED UPDATED REPORT SCHEMA

### Proposed Master Quality Report (60+ fields)

```python
MASTER_QUALITY_REPORT_SCHEMA = {
    # === IDENTITY & PROVENANCE (8 fields) ===
    "Run_ID": str,
    "Subject_ID": str,                    # NEW
    "Session_ID": str,                    # NEW
    "Recording_ID": str,                  # NEW
    "Recording_Date": str,                # NEW
    "Processing_Date": str,
    "Duration_Sec": float,                # NEW
    "Pipeline_Version": str,              # NEW
    
    # === RAW DATA QUALITY (8 fields) ===
    "OptiTrack_Error_mm": float,
    "Total_Frames": int,
    "Actual_FPS": float,                  # NEW
    "Dropped_Frames": int,                # NEW
    "Missing_Raw_%": float,
    "Total_Joints_Expected": int,         # NEW
    "Total_Joints_Found": int,            # NEW
    "Joint_Coverage_%": float,            # NEW
    
    # === PREPROCESSING METRICS (12 fields) ===
    "Artifact_Percent": float,            # NEW
    "Artifact_Worst_Joint": str,          # NEW - Joint with most artifacts
    "Num_Gaps_Filled": int,               # NEW
    "Max_Gap_Frames": int,
    "Max_Gap_MS": float,
    "Max_Gap_Exceeded": bool,             # NEW
    "Max_Gap_Joint": str,                 # NEW - Which joint has largest gap
    "Gap_Fill_Method": str,               # NEW
    "Bone_Stability_CV": float,
    "Skeletal_Alerts": int,
    "Worst_Bone": str,
    "Worst_Bone_CV": float,               # NEW - Actual CV value of worst bone
    "Bone_QC_Grade": str,                 # NEW (GOLD/SILVER/BRONZE)
    
    # === TEMPORAL VALIDATION (3 fields) ===
    "Time_Grid_Std_DT": float,            # NEW
    "Temporal_Status": str,               # NEW
    "Resample_Method": str,               # NEW
    
    # === FILTERING VALIDATION (8 fields) ===
    "Filter_Cutoff_Hz": float,            # NEW
    "Filter_Method": str,                 # NEW
    "Filter_Strategy": str,               # NEW
    "Trunk_Min_Cutoff_Hz": float,         # NEW
    "Distal_Min_Cutoff_Hz": float,        # NEW
    "Winter_Failed": bool,                # NEW
    "Num_Filtered_Cols": int,             # NEW
    "Num_Excluded_Cols": int,             # NEW
    
    # === REFERENCE QUALITY (10 fields) ===
    "Ref_Stability_mm": float,
    "Ref_Status": str,
    "Ref_Method": str,                    # NEW
    "Ref_Is_Fallback": bool,              # NEW
    "Ref_Window_Start_Sec": float,        # NEW
    "Ref_Mean_Motion": float,             # NEW
    "Ref_Std_Motion": float,              # NEW
    "Identity_Error_Med": float,          # NEW
    "Calibration_Grade": str,             # NEW
    "Left_Arm_Offset_Deg": float,         # NEW
    "Right_Arm_Offset_Deg": float,        # NEW
    
    # === SIGNAL QUALITY (7 fields) ===
    "Signal_Noise_RMS": float,
    "Dom_Freq_Hz": float,
    "Quat_Norm_Error": float,
    "Quat_Norm_Error_Joint": str,         # NEW - Which joint has worst error
    "Quat_Norm_Error_Frame": int,         # NEW - When it occurred
    "Quat_Continuity_Flips": int,         # NEW
    "Signal_SNR_dB": float,               # NEW (if computable)
    
    # === KINEMATIC METRICS (18 fields) ===
    "Max_Ang_Vel": float,
    "Max_Ang_Vel_Joint": str,             # NEW - Which joint
    "Mean_Ang_Vel": float,
    "Omega_Mag_P95": float,               # NEW
    "Max_Ang_Acc": float,                 # NEW
    "Max_Ang_Acc_Joint": str,             # NEW - Which joint
    "Max_Ang_Acc_Frame": int,             # NEW - When it occurred
    "Max_Lin_Acc": float,
    "Max_Lin_Acc_Joint": str,             # NEW - Which joint
    "Mean_Lin_Acc": float,                # NEW
    "Vel_Mag_P95": float,                 # NEW
    "Rotvec_Mag_P95": float,              # NEW
    "Rotvec_Mag_Median": float,           # NEW
    "Dynamic_Range_Score": float,         # NEW
    "Outlier_Frames": int,
    "Outlier_Percent": float,             # NEW
    "Outlier_Joints_List": str,           # NEW - Comma-separated joints with outliers
    "Outlier_Worst_Joint": str,           # NEW - Joint with most outlier frames
    
    # === PHYSIOLOGICAL VALIDATION (8 fields) ===
    "Unphysiological_Accel": bool,        # NEW
    "Unphysiological_Accel_Joint": str,   # NEW - Which joint
    "Unphysiological_Accel_Value": float, # NEW - Actual value
    "Unphysiological_Accel_Frame": int,   # NEW - When it occurred
    "Unphysiological_Ang_Vel": bool,      # NEW
    "Unphysiological_Ang_Vel_Joint": str, # NEW - Which joint
    "Unphysiological_Ang_Vel_Value": float, # NEW - Actual value
    "Unphysiological_Ang_Vel_Frame": int, # NEW - When it occurred
    
    # === EFFORT METRICS (3 fields) ===
    "Path_Length_M": float,
    "Intensity_Index": float,
    "Movement_Efficiency": float,         # NEW (path / straight-line distance)
    
    # === QUALITY SCORING (4 fields) ===
    "Quality_Score": float,
    "Quality_Score_Method": str,
    "Research_Decision": str,
    "Pipeline_Status": str,
    
    # === METADATA (3 fields) ===
    "Processing_Time_Sec": float,         # NEW
    "File_Size_MB": float,                # NEW
    "Notes": str,                         # NEW (manual annotations)
}
```

---

## 🎯 PRIORITY IMPLEMENTATION ROADMAP

### **Phase 1: Critical Additions (Immediate - Next Sprint)**

1. **Temporal Validation** (3 fields)
   - `Actual_FPS`, `Time_Grid_Std_DT`, `Temporal_Status`
   - **Why**: Affects filter validity
   - **Effort**: 15 min (already in step_03 summary)

2. **Filtering Validation** (4 fields)
   - `Filter_Cutoff_Hz`, `Winter_Failed`, `Filter_Strategy`, `Num_Excluded_Cols`
   - **Why**: Critical for methodology reporting
   - **Effort**: 20 min (already in step_04 summary)

3. **Reference Method** (3 fields)
   - `Ref_Method`, `Ref_Is_Fallback`, `Ref_Mean_Motion`
   - **Why**: Distinguishes criteria-based vs. fallback references
   - **Effort**: 15 min (already in step_05 summary)

4. **Physiological Flags** (2 fields)
   - `Unphysiological_Accel`, `Unphysiological_Ang_Vel`
   - **Why**: Automatic rejection criteria
   - **Effort**: 10 min (computed from existing fields)

**Phase 1 Total**: ~60 min implementation, **12 new fields**

---

### **Phase 2: Enhanced QC Metrics (Week 2)**

5. **Provenance Parsing** (4 fields)
   - `Subject_ID`, `Session_ID`, `Recording_ID`, `Duration_Sec`
   - **Why**: Essential for longitudinal analysis
   - **Effort**: 30 min (regex parsing)

6. **Calibration Details** (3 fields)
   - `Calibration_Grade`, `Left_Arm_Offset_Deg`, `Right_Arm_Offset_Deg`
   - **Why**: V-pose correction transparency
   - **Effort**: 20 min (already in step_05 summary)

7. **Skeleton Completeness** (4 fields)
   - `Total_Joints_Found`, `Missing_Joints`, `Joint_Coverage_%`
   - **Why**: Identifies systematic capture issues
   - **Effort**: 20 min (already in step_01 summary)

8. **Artifact Tracking** (3 fields)
   - `Artifact_Percent`, `Num_Gaps_Filled`, `Max_Gap_Exceeded`
   - **Why**: Gap filling reliability assessment
   - **Effort**: 15 min (requires step_02 updates)

**Phase 2 Total**: ~85 min implementation, **14 new fields**

---

### **Phase 3: Statistical Robustness (Week 3)**

9. **Percentile Metrics** (4 fields)
   - `Omega_Mag_P95`, `Vel_Mag_P95`, `Rotvec_Mag_P95`, `Rotvec_Mag_Median`
   - **Why**: Robust to outliers, better than max
   - **Effort**: 45 min (requires step_06 updates to compute)

10. **Movement Characterization** (2 fields)
    - `Dynamic_Range_Score`, `Movement_Efficiency`
    - **Why**: Validates movement diversity
    - **Effort**: 30 min (algorithmic development)

**Phase 3 Total**: ~75 min implementation, **6 new fields**

---

### **Phase 4: Advanced Features (Future)**

11. **Processing Performance** (3 fields)
    - `Processing_Time_Sec`, `File_Size_MB`, `Derivative_Size_MB`
    - **Why**: Batch processing optimization
    - **Effort**: 60 min (pipeline instrumentation)

12. **Manual Annotations** (1 field)
    - `Notes` - Free text for researcher comments
    - **Why**: Contextual information
    - **Effort**: 5 min (database schema)

**Phase 4 Total**: ~65 min implementation, **4 new fields**

---

## 📈 UPDATED QUALITY SCORE ALGORITHM

### Proposed Quality Score v2.0

```python
def compute_quality_score_v2(row, cfg):
    """
    Enhanced quality score with biomechanical validation.
    
    Score range: 0-100
    Components: Data Quality (40), Processing (30), Biomechanics (30)
    """
    score = 100.0
    
    # === DATA QUALITY COMPONENT (40 points) ===
    # Capture system performance (10 pts)
    opti_error = safe_float(row["OptiTrack_Error_mm"])
    if opti_error >= 2.0:
        score -= 10
    elif opti_error >= 1.0:
        score -= 5
    elif opti_error >= 0.5:
        score -= 2
    
    # Missing data (10 pts)
    score -= safe_float(row["Missing_Raw_%"]) * 2  # -2 pts per %
    
    # Gap filling quality (10 pts)
    if row.get("Max_Gap_Exceeded", False):
        score -= 10  # Gap > 200ms is critical
    else:
        score -= safe_float(row["Max_Gap_MS"]) / 20  # -0.5 pt per 10ms
    
    # Joint coverage (10 pts)
    coverage = safe_float(row.get("Joint_Coverage_%", 100))
    score -= (100 - coverage) / 2  # -5 pts for 90% coverage
    
    # === PROCESSING COMPONENT (30 points) ===
    # Bone stability (10 pts)
    bone_cv = safe_float(row["Bone_Stability_CV"])
    if bone_cv >= 2.5:
        score -= 10
    elif bone_cv >= 1.5:
        score -= 5
    else:
        score -= bone_cv * 3  # Linear penalty
    
    # Reference quality (10 pts)
    if row.get("Ref_Is_Fallback", False):
        score -= 5  # No true quiet stance
    ref_stab = safe_float(row["Ref_Stability_mm"])
    if ref_stab >= 6.0:
        score -= 10
    elif ref_stab >= 4.0:
        score -= 5
    elif ref_stab >= 2.0:
        score -= 2
    
    # Filtering validity (10 pts)
    if row.get("Winter_Failed", False):
        score -= 10  # Critical: pre-smoothed data
    if safe_float(row.get("Num_Excluded_Cols", 0)) > 5:
        score -= 5  # Many columns with issues
    
    # === BIOMECHANICAL COMPONENT (30 points) ===
    # Physiological plausibility (15 pts)
    if row.get("Unphysiological_Accel", False):
        score -= 10
    if row.get("Unphysiological_Ang_Vel", False):
        score -= 10
    
    # Signal quality (10 pts)
    quat_error = safe_float(row["Quat_Norm_Error"])
    if quat_error >= 0.1:
        score -= 10
    elif quat_error >= 0.05:
        score -= 5
    
    # Artifact burden (5 pts)
    artifact_pct = safe_float(row.get("Artifact_Percent", 0))
    score -= min(artifact_pct, 5)  # Cap at -5 pts
    
    return max(0, min(100, round(score, 2)))
```

### Quality Score Interpretation

```
90-100: EXCELLENT - Publication quality
75-89:  GOOD      - Research acceptable
50-74:  FAIR      - Review recommended
0-49:   POOR      - Reject or re-capture
```

---

## 🛠️ IMPLEMENTATION CODE

### Updated Notebook 07 Cell Structure

```python
# Cell 1: Enhanced Data Extraction
all_summaries = []

for run_id, steps in complete_runs.items():
    s01 = steps.get('step_01', {})
    s02 = steps.get('step_02', {})
    s03 = steps.get('step_03', {})  # NEW
    s04 = steps.get('step_04', {})
    s05 = steps.get('step_05', {})
    s06 = steps.get('step_06', {})
    
    # === PARSE PROVENANCE ===
    import re
    match = re.match(r"(\d+)_T(\d+)_P(\d+)_R(\d+)", run_id)
    subject_id = match.group(1) if match else "Unknown"
    session_id = f"T{match.group(2)}" if match else "Unknown"
    recording_id = f"P{match.group(3)}_R{match.group(4)}" if match else "Unknown"
    
    row = {
        # === IDENTITY & PROVENANCE ===
        "Run_ID": run_id,
        "Subject_ID": subject_id,                              # NEW
        "Session_ID": session_id,                              # NEW
        "Recording_ID": recording_id,                          # NEW
        "Recording_Date": safe_get(s01, 'identity', 'capture_date'),  # NEW
        "Processing_Date": safe_get(s01, 'identity', 'processing_timestamp'),
        "Duration_Sec": safe_float(safe_get(s01, 'duration_sec')),    # NEW
        "Pipeline_Version": safe_get(s04, 'identity', 'pipeline_version'),  # NEW
        
        # === RAW DATA QUALITY ===
        "OptiTrack_Error_mm": safe_float(safe_get(s01, 'raw_data_quality', 'optitrack_mean_error_mm')),
        "Total_Frames": safe_get(s01, 'raw_data_quality', 'total_frames', default=0),
        "Actual_FPS": safe_float(safe_get(s03, 'target_fs', safe_get(s01, 'fps_estimated'))),  # NEW
        "Missing_Raw_%": safe_float(safe_get(s02, 'raw_missing_percent')),
        "Total_Joints_Expected": safe_get(s01, 'segments_expected', default=51),  # NEW
        "Total_Joints_Found": safe_get(s01, 'segments_found_count', default=0),   # NEW
        "Joint_Coverage_%": round(100.0 * safe_get(s01, 'segments_found_count', default=0) / max(1, safe_get(s01, 'segments_expected', default=51)), 1),  # NEW
        
        # === PREPROCESSING METRICS ===
        "Max_Gap_Frames": safe_get(s02, 'max_interpolation_gap', default=0),
        "Max_Gap_MS": safe_float(safe_get(s02, 'max_gap_ms')),
        "Max_Gap_Exceeded": safe_float(safe_get(s02, 'max_gap_ms')) > 200,  # NEW
        "Max_Gap_Joint": safe_get(s02, 'max_gap_joint', default='Unknown'),  # NEW
        "Gap_Fill_Method": safe_get(s02, 'interpolation_method'),           # NEW
        "Bone_Stability_CV": safe_float(safe_get(s02, 'bone_qc_mean_cv')),
        "Skeletal_Alerts": safe_get(s02, 'bone_qc_alerts', default=0),
        "Worst_Bone": safe_get(s02, 'worst_bone'),
        "Worst_Bone_CV": safe_float(safe_get(s02, 'worst_bone_cv')),       # NEW
        "Bone_QC_Grade": safe_get(s02, 'bone_qc_status', default='UNKNOWN'),  # NEW
        "Artifact_Percent": safe_float(safe_get(s02, 'artifact_mask_percent')),  # NEW
        "Artifact_Worst_Joint": safe_get(s02, 'artifact_worst_joint', default='Unknown'),  # NEW
        
        # === TEMPORAL VALIDATION ===
        "Time_Grid_Std_DT": safe_float(safe_get(s03, 'time_grid_std_dt')),  # NEW
        "Temporal_Status": safe_get(s03, 'temporal_status'),                # NEW
        "Resample_Method": safe_get(s03, 'interpolation_methods', 'positions'),  # NEW
        
        # === FILTERING VALIDATION ===
        "Filter_Cutoff_Hz": safe_float(safe_get(s04, 'filter_params', 'filter_cutoff_hz')),  # NEW
        "Filter_Method": safe_get(s04, 'filter_params', 'filter_method'),                    # NEW
        "Filter_Strategy": safe_get(s04, 'filter_params', 'biomechanical_guardrails', 'strategy'),  # NEW
        "Winter_Failed": safe_get(s04, 'filter_params', 'winter_analysis_failed', default=False),   # NEW
        "Num_Filtered_Cols": len(safe_get(s04, 'filter_params', 'pos_cols_valid', default=[])),     # NEW
        "Num_Excluded_Cols": len(safe_get(s04, 'filter_params', 'pos_cols_excluded', default=[])),  # NEW
        
        # === REFERENCE QUALITY ===
        "Ref_Stability_mm": safe_float(safe_get(s05, 'reference_metrics', 'ref_stability_mm')),
        "Ref_Status": str(safe_get(s05, 'reference_metrics', 'ref_quality_status', default='MISSING')).upper(),
        "Ref_Method": safe_get(s05, 'window_metadata', 'method'),                    # NEW
        "Ref_Is_Fallback": safe_get(s05, 'window_metadata', 'ref_is_fallback', default=True),  # NEW
        "Ref_Window_Start_Sec": safe_float(safe_get(s05, 'window_metadata', 'start_time_sec')),  # NEW
        "Ref_Mean_Motion": safe_float(safe_get(s05, 'window_metadata', 'metrics', 'mean_motion')),  # NEW
        "Calibration_Grade": safe_get(s05, 'metadata', 'grade'),                    # NEW
        "Left_Arm_Offset_Deg": safe_float(safe_get(s05, 'static_offset_audit', 'Left', 'measured_angle_deg')),  # NEW
        "Right_Arm_Offset_Deg": safe_float(safe_get(s05, 'static_offset_audit', 'Right', 'measured_angle_deg')),  # NEW
        
        # === SIGNAL QUALITY ===
        "Signal_Noise_RMS": safe_float(safe_get(s06, 'signal_quality', 'avg_vel_residual_rms')),
        "Dom_Freq_Hz": safe_float(safe_get(s06, 'signal_quality', 'avg_dominant_freq_hz')),
        "Quat_Norm_Error": safe_float(safe_get(s06, 'signal_quality', 'max_quat_norm_error')),
        "Quat_Norm_Error_Joint": safe_get(s06, 'signal_quality', 'max_quat_norm_error_joint', default='Unknown'),  # NEW
        "Quat_Norm_Error_Frame": safe_get(s06, 'signal_quality', 'max_quat_norm_error_frame', default=-1),         # NEW
        
        # === KINEMATIC METRICS ===
        "Max_Ang_Vel": safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'max')),
        "Max_Ang_Vel_Joint": safe_get(s06, 'metrics', 'angular_velocity', 'max_joint', default='Unknown'),  # NEW
        "Mean_Ang_Vel": safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'mean')),
        "Max_Ang_Acc": safe_float(safe_get(s06, 'metrics', 'angular_accel', 'max')),    # NEW
        "Max_Ang_Acc_Joint": safe_get(s06, 'metrics', 'angular_accel', 'max_joint', default='Unknown'),    # NEW
        "Max_Ang_Acc_Frame": safe_get(s06, 'metrics', 'angular_accel', 'max_frame', default=-1),           # NEW
        "Max_Lin_Acc": safe_float(safe_get(s06, 'metrics', 'linear_accel', 'max')),
        "Max_Lin_Acc_Joint": safe_get(s06, 'metrics', 'linear_accel', 'max_joint', default='Unknown'),     # NEW
        "Mean_Lin_Acc": safe_float(safe_get(s06, 'metrics', 'linear_accel', 'mean')),   # NEW
        "Outlier_Frames": safe_get(s06, 'effort_metrics', 'outlier_frame_count', default=0),
        "Outlier_Percent": round(100.0 * safe_float(safe_get(s06, 'effort_metrics', 'outlier_frame_count', default=0)) / max(1, safe_get(s01, 'raw_data_quality', 'total_frames', default=1)), 2),  # NEW
        "Outlier_Joints_List": safe_get(s06, 'effort_metrics', 'outlier_joints_list', default='None'),     # NEW
        "Outlier_Worst_Joint": safe_get(s06, 'effort_metrics', 'outlier_worst_joint', default='None'),     # NEW
        
        # === PHYSIOLOGICAL VALIDATION ===
        "Unphysiological_Accel": safe_float(safe_get(s06, 'metrics', 'linear_accel', 'max')) > 100000,  # NEW (>100 m/s² in mm/s²)
        "Unphysiological_Accel_Joint": safe_get(s06, 'metrics', 'linear_accel', 'max_joint') if safe_float(safe_get(s06, 'metrics', 'linear_accel', 'max')) > 100000 else 'None',  # NEW
        "Unphysiological_Accel_Value": round(safe_float(safe_get(s06, 'metrics', 'linear_accel', 'max')) / 1000, 2) if safe_float(safe_get(s06, 'metrics', 'linear_accel', 'max')) > 100000 else 0.0,  # NEW (convert to m/s²)
        "Unphysiological_Accel_Frame": safe_get(s06, 'metrics', 'linear_accel', 'max_frame', default=-1) if safe_float(safe_get(s06, 'metrics', 'linear_accel', 'max')) > 100000 else -1,  # NEW
        "Unphysiological_Ang_Vel": safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'max')) > 5000,  # NEW (>5000 deg/s)
        "Unphysiological_Ang_Vel_Joint": safe_get(s06, 'metrics', 'angular_velocity', 'max_joint') if safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'max')) > 5000 else 'None',  # NEW
        "Unphysiological_Ang_Vel_Value": round(safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'max')), 2) if safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'max')) > 5000 else 0.0,  # NEW
        "Unphysiological_Ang_Vel_Frame": safe_get(s06, 'metrics', 'angular_velocity', 'max_frame', default=-1) if safe_float(safe_get(s06, 'metrics', 'angular_velocity', 'max')) > 5000 else -1,  # NEW
        
        # === EFFORT METRICS ===
        "Path_Length_M": round(safe_float(safe_get(s06, 'effort_metrics', 'total_path_length_mm')) / 1000, 2),
        "Intensity_Index": safe_float(safe_get(s06, 'effort_metrics', 'intensity_index')),
        
        # === OVERALL STATUS ===
        "Pipeline_Status": safe_get(s06, 'overall_status'),
    }
    
    # === COMPUTE ENHANCED QUALITY SCORE ===
    row["Quality_Score"] = compute_quality_score_v2(row, CONFIG)
    row["Quality_Score_Method"] = "heuristic_v2_biomechanical"
    
    # === RESEARCH DECISION (ENHANCED) ===
    # Note: Pipeline_Status is now a processing indicator (e.g., "COMPLETED_STEP_06")
    # Quality assessment is based on actual metrics, not status string
    if (row["Quality_Score"] >= 75 and 
        row["Ref_Status"] == "PASS" and 
        safe_float(row["Bone_Stability_CV"]) < 1.5 and
        not row["Winter_Failed"] and                          # NEW
        not row["Unphysiological_Accel"] and                  # NEW
        not row["Unphysiological_Ang_Vel"]):                  # NEW
        row["Research_Decision"] = "ACCEPT"
    elif (row["Quality_Score"] >= 50 and
          not row["Unphysiological_Accel"] and
          not row["Unphysiological_Ang_Vel"]):
        row["Research_Decision"] = "REVIEW"
    else:
        row["Research_Decision"] = "REJECT"
    
    all_summaries.append(row)
```

---

## 📋 EXCEL REPORT ENHANCEMENTS

### Recommended Additional Sheets

1. **Sheet 1: Audit_Log** (Main summary - 60 fields)
2. **Sheet 2: Bone_Stability_Details** (Per-bone CV tracking)
3. **Sheet 3: Gap_Distribution** (Gap sizes histogram)
4. **Sheet 4: Reference_Windows** (Time windows used per run)
5. **Sheet 5: Filter_Cutoffs** (Cutoff distribution analysis)
6. **Sheet 6: Rejection_Reasons** (Why runs were rejected)
7. **Sheet 7: Longitudinal_Comparison** (Subject T1 vs T2)

### Enhanced Conditional Formatting

```python
# Add to Excel writer:
# 1. Color scale for Quality_Score (red → yellow → green)
# 2. Icons for boolean flags (✓/✗)
# 3. Highlight unphysiological values (red background)
# 4. Warning icons for fallback references
# 5. Data bars for continuous metrics
```

---

## 🎯 SUMMARY OF RECOMMENDATIONS

### **Complete Metrics Requiring Joint Identification**

| Metric | Joint Field | Value Field | Frame Field | Priority |
|--------|------------|-------------|-------------|----------|
| Max Angular Velocity | `Max_Ang_Vel_Joint` | `Max_Ang_Vel` (existing) | `Max_Ang_Vel_Frame` | ⭐⭐⭐ HIGH |
| Max Angular Acceleration | `Max_Ang_Acc_Joint` | `Max_Ang_Acc` | `Max_Ang_Acc_Frame` | ⭐⭐⭐ HIGH |
| Max Linear Acceleration | `Max_Lin_Acc_Joint` | `Max_Lin_Acc` (existing) | `Max_Lin_Acc_Frame` | ⭐⭐⭐ HIGH |
| Unphysiological Accel | `Unphysiological_Accel_Joint` | `Unphysiological_Accel_Value` | `Unphysiological_Accel_Frame` | ⭐⭐⭐ HIGH |
| Unphysiological Ang Vel | `Unphysiological_Ang_Vel_Joint` | `Unphysiological_Ang_Vel_Value` | `Unphysiological_Ang_Vel_Frame` | ⭐⭐⭐ HIGH |
| Quaternion Norm Error | `Quat_Norm_Error_Joint` | `Quat_Norm_Error` (existing) | `Quat_Norm_Error_Frame` | ⭐⭐⭐ HIGH |
| Maximum Gap | `Max_Gap_Joint` | `Max_Gap_MS` (existing) | `Max_Gap_Start_Frame`, `Max_Gap_End_Frame` | ⭐⭐ MEDIUM |
| Worst Bone | `Worst_Bone` (existing) | `Worst_Bone_CV` | `Worst_Bone_Frame` | ⭐⭐ MEDIUM |
| Outliers | `Outlier_Worst_Joint`, `Outlier_Joints_List` | `Outlier_Frames` (existing) | - | ⭐⭐ MEDIUM |
| Artifacts | `Artifact_Worst_Joint` | `Artifact_Percent` | - | ⭐ LOW |

**Total New Fields Added: 26** (across all priorities)

**Why This Matters:**
- 🎯 **Targeted Debugging**: "RightHand @ 1000°/s" (normal) vs "Hips @ 1000°/s" (artifact)
- 🎯 **Frame Navigation**: Jump directly to problematic frames for visual inspection
- 🎯 **Pattern Recognition**: Same joint problematic across multiple recordings = systematic issue
- 🎯 **Physiological Context**: Different joints have different acceptable ranges

### **Immediate Actions (This Week)**

1. ✅ **Add 12 critical fields** (Phase 1)
   - Temporal, filtering, reference validation
   - Physiological plausibility flags
   
2. ✅ **Add 16 joint identification fields** (NEW - Phase 1.5)
   - Joint + Frame tracking for all kinematic extremes
   - Enables targeted debugging
   - **Implementation time: ~90 min** (requires step_06 updates)

3. ✅ **Update quality score algorithm** (v2.0)
   - Include new biomechanical validation
   - Enhanced rejection criteria

3. ✅ **Document methodology changes**
   - Update README with new fields
   - Version quality score method

### **Short-Term (Next 2 Weeks)**

4. ✅ **Add 14 enhanced QC fields** (Phase 2)
   - Provenance, calibration, skeleton completeness
   
5. ✅ **Create multi-sheet Excel report**
   - Bone details, gaps, reference windows
   
6. ✅ **Implement automated flagging**
   - Unphysiological values auto-reject

### **Medium-Term (Month 2)**

7. ✅ **Add statistical robustness** (Phase 3)
   - Percentile metrics (P95)
   - Dynamic range scoring
   
8. ✅ **Longitudinal comparison tools**
   - Subject T1 vs T2 analysis
   - Session-to-session stability

### **Future Enhancements**

9. ⏳ **Performance monitoring** (Phase 4)
10. ⏳ **Interactive dashboard** (Plotly/Dash)
11. ⏳ **Automated report generation** (LaTeX/PDF)

---

## 📚 JUSTIFICATION SUMMARY

**Current Report**: Good foundation (22 fields)

**Recommended Report**: Comprehensive audit trail (60+ fields)

**Added Value**:
- ✅ **Traceability**: Full provenance tracking
- ✅ **Biomechanical Validity**: Physiological plausibility checks
- ✅ **Methodological Transparency**: Filter/reference decisions logged
- ✅ **Statistical Robustness**: Percentile metrics (outlier-resistant)
- ✅ **Automated QC**: Clear rejection criteria
- ✅ **Publication-Ready**: All metrics for methods section

**Alignment with Standards**:
- Wu et al. (2005) - ISB recommendations
- Winter (2009) - Filtering methodology
- Skurowski et al. - Artifact detection
- Rácz et al. (2025) - CAST calibration

---

**VERSION**: 1.0  
**AUTHOR**: Biomechanical Pipeline Audit  
**DATE**: January 2026  
**STATUS**: Ready for Implementation
