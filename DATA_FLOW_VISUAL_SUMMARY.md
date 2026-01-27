# Master Audit Data Flow - Visual Summary

## 📊 Current State (Broken Data Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE EXECUTION                          │
│                     (run_pipeline.py)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 01: Parse CSV                                         │
│  ✅ Status: WORKING                                             │
│  Output: __step01_loader_report.json                           │
│  Data Completeness: 100%                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 02: Preprocessing                                     │
│  ⚠️  Status: INCOMPLETE                                         │
│  Output: __preprocess_summary.json                             │
│  Missing:                                                       │
│    - step_02_sample_time_jitter_ms        (Gate 2)            │
│    - step_02_jitter_status                (Gate 2)            │
│    - step_02_fallback_count               (Gate 2)            │
│    - step_02_fallback_rate_percent        (Gate 2)            │
│    - step_02_max_gap_frames               (Gate 2)            │
│  Data Completeness: ~75%                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 03: Resampling                                        │
│  ✅ Status: WORKING (No summary file required)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 04: Filtering                                         │
│  ⚠️  Status: INCOMPLETE                                         │
│  Output: __filtering_summary.json                              │
│  Missing:                                                       │
│    - filter_params.region_cutoffs         (Gate 3)            │
│      (Only global average exported, not individual regions)    │
│  Data Completeness: ~85%                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 05: Reference Detection                               │
│  ⚠️  Status: INCOMPLETE                                         │
│  Output: __reference_summary.json                              │
│  Missing:                                                       │
│    - subject_context.height_cm                                 │
│    - subject_context.scaling_factor                            │
│  Data Completeness: ~90%                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 06: Kinematics & Angular Velocity                    │
│  ❌ Status: CRITICALLY INCOMPLETE                               │
│  Output: __kinematics_summary.json                             │
│  Missing:                                                       │
│    - joint_statistics (ENTIRE DICT EMPTY)   (Core Data)       │
│    - step_06_burst_analysis                 (Gate 5)          │
│    - step_06_burst_decision                 (Gate 5)          │
│    - clean_statistics                       (Gate 5)          │
│    - step_06_isb_compliant                  (Gate 4)          │
│    - step_06_math_status                    (Gate 4)          │
│    - step_06_data_validity                  (Gate 5)          │
│  Data Completeness: ~40% ⚠️                                     │
│                                                                 │
│  ⚠️  THIS IS THE CRITICAL BOTTLENECK                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 07: Master Quality Report                            │
│  ✅ Status: WORKING (Schema & Logic Correct)                   │
│  Input: All JSON files from steps 01-06                       │
│  Output: Master_Audit_Log_*.xlsx                              │
│                                                                 │
│  Problem: Schema expects 150+ fields                           │
│           Only ~90 fields have real data                       │
│           ~60 fields show 'N/A' or 0.0                         │
│                                                                 │
│  Result: Excel has correct columns but missing data           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           MASTER AUDIT LOG EXCEL OUTPUT                         │
│                                                                 │
│  Sheet 1: Executive Summary        ✅ CORRECT                  │
│  Sheet 2: Quality Report           ⚠️  40% MISSING DATA        │
│  Sheet 3: Parameter Audit          ⚠️  40% MISSING DATA        │
│  Sheet 4: Parameter Schema         ✅ CORRECT                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Data Flow Breakdown by Column Category

### ✅ WORKING (Data Flowing Correctly)

```
Category: Identity & Provenance (S0)
Source: Step 01 JSON
Status: ✅ 100% Complete
Columns:
  - Run_ID
  - Subject_ID
  - Session_ID
  - Processing_Date
  - Pipeline_Version
  - OptiTrack_Version
```

```
Category: Basic Quality Metrics
Source: Step 01, 02, 04, 05 JSONs
Status: ✅ 80-90% Complete
Columns:
  - Total_Frames
  - Duration_Sec
  - Sampling_Rate_Hz
  - Raw_Missing_%
  - Bone_CV_%
  - Filter_Cutoff_Hz
  - Ref_Quality_Score
```

### ⚠️ PARTIALLY WORKING (Some Data Missing)

```
Category: Gate 2 - Temporal Quality
Source: Step 02 JSON
Status: ⚠️  0% Complete (Fields Not Exported)
Columns:
  - Sample_Jitter_ms                    → 'N/A'
  - Jitter_Status                       → 'N/A'
  - Fallback_Count                      → 0
  - Fallback_Rate_%                     → 0.0
  - Max_Gap_Frames                      → 0
  - Interpolation_Status                → 'N/A'
```

```
Category: Gate 3 - Per-Region Filtering
Source: Step 04 JSON
Status: ⚠️  50% Complete (Missing Region Details)
Columns:
  - Filter_Cutoff_Hz                    → ✅ Working
  - Filter_Method                       → ✅ Working
  - Region_Cutoffs                      → 'N/A' (missing)
```

### ❌ BROKEN (Critical Data Missing)

```
Category: Gate 4 - ISB Compliance & Math Stability
Source: Step 06 JSON
Status: ❌ 0% Complete (Fields Not Exported)
Columns:
  - ISB_Compliant                       → 'N/A'
  - Math_Status                         → 'N/A'
  - Math_Decision_Reason                → 'N/A'
```

```
Category: Gate 5 - Burst Classification & Artifact Analysis
Source: Step 06 JSON
Status: ❌ 0% Complete (Fields Not Exported)
Columns:
  - Burst_Artifact_Count                → 0
  - Burst_Count                         → 0
  - Burst_Flow_Count                    → 0
  - Burst_Total_Events                  → 0
  - Artifact_Rate_%                     → 0.0
  - Max_Consecutive_Frames              → 0
  - Mean_Event_Duration_ms              → 0.0
  - Burst_Decision                      → 'N/A'
  - Burst_Decision_Reason               → 'N/A'
  - Data_Usable                         → 'N/A'
  - Excluded_Frames                     → 0
  - Artifact_Frame_Ranges               → 'N/A'
  - Burst_Frame_Ranges                  → 'N/A'
```

```
Category: Clean Statistics (Artifact-Excluded Metrics)
Source: Step 06 JSON
Status: ❌ 0% Complete (Fields Not Exported)
Columns:
  - Clean_Max_Vel_deg_s                 → 0.0
  - Clean_Mean_Vel_deg_s                → 0.0
  - Max_Vel_Reduction_%                 → 0.0
  - Data_Retained_%                     → 0.0
```

```
Category: Biomechanics Scorecard
Source: Step 06 JSON
Status: ❌ 0% Complete (Fields Not Exported)
Columns:
  - Biomech_Physiological_Score         → 0
  - Biomech_Skeleton_Score              → 0
  - Biomech_Continuity_Score            → 0
  - Biomech_Velocity_Source             → 'N/A'
  - Biomech_Velocity_Assessment         → 'N/A'
  - Biomech_Accel_Assessment            → 'N/A'
  - Biomech_Bone_Stability              → 'N/A'
  - Biomech_Burst_Assessment            → 'N/A'
  - Biomech_Artifact_Assessment         → 'N/A'
  - Biomech_Neutralization_Applied      → False
```

---

## 📈 Data Completeness Metrics

```
┌─────────────────────────────────────────────────────────────┐
│  Master Audit Log - Data Completeness Analysis             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Total Columns in Schema:        150                       │
│  Columns with Real Data:         ~90  (60%)               │
│  Columns with Missing Data:      ~60  (40%)               │
│                                                             │
│  Missing Data Breakdown:                                    │
│    - Gate 2 (Temporal):          6 columns  (100% missing) │
│    - Gate 3 (Filtering):         1 column   (100% missing) │
│    - Gate 4 (ISB/Math):          3 columns  (100% missing) │
│    - Gate 5 (Burst/Artifact):    40 columns (100% missing) │
│    - Height Estimation:          2 columns  (100% missing) │
│                                                             │
│  ⚠️  CRITICAL: 50+ columns depend on Notebook 06 fix      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Fix Impact Analysis

### Priority 0: Fix Notebook 06 (CRITICAL)
```
Before:  60 columns with 'N/A' or 0
After:   15 columns with 'N/A' or 0
Impact:  +30% data completeness (60% → 90%)
Time:    2 days
```

### Priority 1: Fix Notebooks 02, 04, 05 (HIGH)
```
Before:  15 columns with 'N/A' or 0
After:   <10 columns with 'N/A' or 0
Impact:  +5% data completeness (90% → 95%+)
Time:    1-2 days
```

### Total Impact
```
Current State:     60% data completeness
After All Fixes:   95%+ data completeness
                   
Quality Score Calculation:  Currently unreliable
After Fixes:                Accurate & trustworthy
```

---

## 🔧 Quick Fix Checklist

### Notebook 06 (Start Here)
- [ ] Find JSON export section at end of notebook
- [ ] Add `joint_statistics` dictionary (per-joint ROM)
- [ ] Add `step_06_burst_analysis` dictionary (Gate 5)
- [ ] Add `step_06_burst_decision` dictionary
- [ ] Add `clean_statistics` dictionary
- [ ] Add `step_06_isb_compliant` boolean (Gate 4)
- [ ] Add `step_06_math_status` string
- [ ] Test with single run
- [ ] Verify Excel shows non-zero values

### Notebook 02
- [ ] Calculate sample time jitter
- [ ] Add Gate 2 fields to summary JSON
- [ ] Test temporal quality scoring

### Notebook 04
- [ ] Export per-region cutoffs if per-region mode enabled
- [ ] Test filtering transparency

### Notebook 05
- [ ] Calculate estimated height from skeleton
- [ ] Add subject context to summary JSON
- [ ] Test anthropometric validation

---

## 📋 Validation Commands

### Quick Test (Single File)
```bash
python run_pipeline.py --single "data/505/T2/505_T2_P1_R1_Take 2025-11-17 05.24.24 PM.csv"
```

### Verify JSON Output
```bash
python -c "
import json, glob
json_file = glob.glob('derivatives/step_06_kinematics/*__kinematics_summary.json')[0]
with open(json_file) as f:
    d = json.load(f)
    print(f'joint_statistics: {len(d.get(\"joint_statistics\", {}))} joints')
    print(f'burst_analysis: {\"step_06_burst_analysis\" in d}')
    print(f'clean_statistics: {\"clean_statistics\" in d}')
"
```

### Check Excel Completeness
```bash
python -c "
import pandas as pd
df = pd.read_excel('reports/Master_Audit_Log_*.xlsx', sheet_name='Quality_Report')
na_count = df.isna().sum().sum() + (df == 'N/A').sum().sum()
completeness = (1 - na_count/df.size) * 100
print(f'Data Completeness: {completeness:.1f}%')
print('✅ PASS' if completeness > 95 else '❌ FAIL')
"
```

---

## 🚀 Expected Timeline

```
Day 1:  Fix Notebook 06 JSON export
        Test single run
        Verify data in Excel
        
Day 2:  Continue Notebook 06 edge cases
        Add validation warnings to NB07
        Full batch test
        
Day 3:  Fix Notebooks 02, 04, 05
        Test each individually
        
Day 4:  Final validation
        Full batch run
        Data completeness >95%
        Quality report ready for use
```

---

**Created:** 2026-01-23  
**Purpose:** Visual summary of data flow issue for development team  
**Next Action:** Fix Notebook 06 (see FIX_TASK_CARD_DATA_FLOW.md)  
**Success Criteria:** Master Audit Log with >95% data completeness
