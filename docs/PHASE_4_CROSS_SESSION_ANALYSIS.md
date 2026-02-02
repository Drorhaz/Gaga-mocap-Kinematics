# Phase 4: Cross-Session Analysis Implementation

## Status: ✅ COMPLETE

**Date:** January 29, 2026

---

## What is Phase 4?

**Cross-Session Analysis** enables longitudinal studies by comparing multiple sessions and identifying patterns across time.

### Key Capabilities

1. **Subject-Level Aggregation** - Combine metrics across all sessions per subject
2. **Session Comparison** - Identify trends, improvements, or regressions
3. **Anomaly Detection** - Flag sessions that deviate significantly from baseline
4. **Movement Pattern Analysis** - Identify consistent vs variable characteristics
5. **Consistency Assessment** - Quantify reliability of measurements

---

## What Was Implemented

### 1. Cross-Session Analysis (Notebook 08, Section 12)

**For each subject with multiple sessions:**

#### A. Subject-Level Summary
- Number of sessions
- List of all session IDs
- Key metrics with mean ± std, range, and CV%

#### B. Key Metrics Tracked
- `Path_Length_Total_m` - Total movement
- `Intensity_Mean_m_per_s` - Movement intensity
- `Bilateral_Symmetry_Mean` - Left/Right balance
- `Raw_Missing_Data_Percent` - Data quality
- `Bone_Length_CV_Percent` - Structural consistency

#### C. Variability Flagging
- **CV% < 10%:** Very consistent
- **CV% 10-25%:** Consistent
- **CV% 25-50%:** Variable
- **CV% > 50%:** Highly variable (⚠️ flagged)

#### D. Movement Patterns
Compares intensity across anatomical regions:
- Wrists, Elbows, Shoulders
- Knees, Ankles, Hips
- Identifies subject's movement "signature"

### 2. Anomaly Detection

**Z-Score Method:**
- Computes mean and std for each metric across sessions
- Flags sessions with |Z| > 2 (beyond 2 standard deviations)
- Identifies outlier sessions that deviate from subject's baseline

**Example Output:**
```
Subject 734:
  ⚠️ Path_Length_Total_m:
      T3: 45.2m (Z=2.34, above baseline)
  ⚠️ Raw_Missing_Data_Percent:
      T1: 8.5% (Z=-2.1, below baseline)
```

### 3. Trend Analysis

**For subjects with ≥3 sessions:**
- Computes correlation between session order and metric values
- Identifies trends:
  - 📈 INCREASING (r > 0.5)
  - 📉 DECREASING (r < -0.5)
  - ➡️ STABLE (|r| ≤ 0.5)

**Example:**
```
Subject 734:
  Total Movement        : 📈 INCREASING (r=0.78)
  Movement Intensity    : ➡️ STABLE (r=0.12)
  Symmetry              : 📉 DECREASING (r=-0.65)
```

### 4. Subject Profiles Export (Section 13)

**Generates JSON file with aggregated subject data:**

```json
{
  "subject_id": "734",
  "n_sessions": 5,
  "session_ids": ["T1", "T2", "T3", "T4", "T5"],
  
  "Path_Length_Total_m_mean": 42.5,
  "Path_Length_Total_m_std": 3.2,
  "Path_Length_Total_m_min": 38.1,
  "Path_Length_Total_m_max": 47.3,
  "Path_Length_Total_m_cv_pct": 7.5,
  
  "movement_signature": {
    "Wrists": {"mean": 0.38, "std": 0.04},
    "Elbows": {"mean": 0.35, "std": 0.03},
    ...
  },
  
  "consistency_assessment": {
    "Path_Length_Total_m": "VERY_CONSISTENT",
    "Intensity_Mean_m_per_s": "CONSISTENT",
    "Bilateral_Symmetry_Mean": "VARIABLE"
  }
}
```

**Saved as:** `QC_Reports/Subject_Profiles_{timestamp}.json`

---

## Use Cases

### 1. Longitudinal Studies
**Question:** "Is the patient's movement improving over time?"

**Answer:** Check trend analysis
- 📈 Increasing path length/intensity = improvement
- ➡️ Stable = maintenance
- 📉 Decreasing = decline

### 2. Intervention Assessment
**Question:** "Did the therapy affect movement patterns?"

**Answer:** Compare sessions before/after intervention
- Look for anomalies (Z-score) right after intervention
- Check trend direction change

### 3. Quality Control
**Question:** "Are our measurements reliable?"

**Answer:** Check consistency assessment
- CV% < 10% = Excellent reliability
- CV% > 25% = Poor reliability (investigate)

### 4. Subject Baseline
**Question:** "What's normal for this subject?"

**Answer:** Use subject profile
- Mean ± std defines subject's baseline
- Deviations flag unusual sessions

---

## Example Output

### Multi-Session Subject

```
================================================================================
CROSS-SESSION ANALYSIS
================================================================================

Analyzing 5 sessions across 1 subject(s)

================================================================================
Subject: 734 (5 sessions)
================================================================================

Sessions:
  • T1: 120.5s, 14460 frames
  • T2: 135.2s, 16224 frames
  • T3: 142.8s, 17136 frames
  • T4: 128.3s, 15396 frames
  • T5: 131.7s, 15804 frames

--------------------------------------------------------------------------------
Key Metrics Across Sessions:
--------------------------------------------------------------------------------

Path_Length_Total_m:
  Mean ± Std: 42.3421 ± 3.1247
  Range: [38.1234, 47.3456]
  CV%: 7.38%

Intensity_Mean_m_per_s:
  Mean ± Std: 0.3156 ± 0.0245
  Range: [0.2891, 0.3512]
  CV%: 7.76%

Bilateral_Symmetry_Mean:
  Mean ± Std: 0.9523 ± 0.0387
  Range: [0.8912, 0.9845]
  CV%: 4.06%

--------------------------------------------------------------------------------
ANOMALY DETECTION
--------------------------------------------------------------------------------

734:
  ✅ No significant anomalies detected

--------------------------------------------------------------------------------
TREND ANALYSIS
--------------------------------------------------------------------------------

734:
  Total Movement        : 📈 INCREASING (r=0.78)
  Movement Intensity    : ➡️ STABLE (r=0.12)
  Symmetry              : ➡️ STABLE (r=0.34)
```

### Single Session

```
================================================================================
CROSS-SESSION ANALYSIS
================================================================================

⚠️ Only 1 session(s) available.
Cross-session analysis requires multiple sessions.

To enable:
  1. Process multiple sessions through the pipeline (notebooks 01-06)
  2. Re-run this notebook

Current session: 734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002
```

---

## Files Modified

1. **`notebooks/08_engineering_physical_audit.ipynb`**
   - Added Section 12: Cross-Session Analysis
   - Added Section 13: Subject Profiles Export
   - Added cells 15-18

2. **`src/utils_nb07.py`**
   - Added `build_subject_profile()` function

---

## Statistical Methods

### Coefficient of Variation (CV%)
```
CV% = (std / mean) × 100
```
Measures relative variability (standardized)

### Z-Score
```
Z = (value - mean) / std
```
Number of standard deviations from mean

### Correlation (Trend)
```
r = correlation(session_order, metric_values)
```
Pearson correlation coefficient

---

## Consistency Thresholds

| CV% Range | Assessment | Interpretation |
|-----------|------------|----------------|
| < 10% | VERY_CONSISTENT | Excellent reliability |
| 10-25% | CONSISTENT | Good reliability |
| 25-50% | VARIABLE | Acceptable for exploratory |
| > 50% | HIGHLY_VARIABLE | Poor reliability, investigate |

---

## Clinical Interpretation

### Trend Patterns

**Increasing Intensity + Stable Symmetry**
- ✅ Good: Improved movement capacity with maintained balance
- Suggests functional improvement

**Decreasing Intensity + Decreasing Symmetry**
- ⚠️ Concern: Decline in movement + emerging asymmetry
- May indicate disease progression or injury

**Stable Intensity + Increasing Symmetry**
- ✅ Good: Maintained activity with improved balance
- Suggests compensatory strategy refinement

**High Variability (CV% > 25%)**
- ⚠️ Investigate: Inconsistent performance
- May indicate:
  - Measurement error
  - Environmental changes
  - Fatigue effects
  - Disease fluctuations

---

## Future Enhancements

1. **Percentile Normalization** - Compare subject to population norms
2. **Change Point Detection** - Identify when significant changes occur
3. **Multi-Subject Comparison** - Group-level statistics
4. **Temporal Patterns** - Time-of-day, day-of-week effects
5. **Machine Learning** - Predict outcomes based on patterns

---

## Testing

### Test with Single Session
```
# Run notebook 08
# Expected: Message saying cross-session analysis needs multiple sessions
```

### Test with Multiple Sessions
```
# 1. Process 3+ sessions through notebooks 01-06
# 2. Run notebook 08
# 3. Check Section 12 for cross-session analysis
# 4. Check Section 13 for subject profiles JSON
# 5. Verify QC_Reports/Subject_Profiles_{timestamp}.json exists
```

---

## Documentation

- **This guide:** `docs/PHASE_4_CROSS_SESSION_ANALYSIS.md`
- **Phase 3:** `docs/PHASE_3_INTENSITY_INDEX.md`
- **Phase 2:** `docs/PHASE_2_IMPLEMENTATION_SUMMARY.md`
- **Phase 1:** `docs/PHASE_1_IMPLEMENTATION_SUMMARY.md`

---

## Summary

**Phase 4 Deliverables:**
- ✅ Cross-session comparison
- ✅ Subject-level aggregation
- ✅ Anomaly detection
- ✅ Trend analysis
- ✅ Consistency assessment
- ✅ Movement pattern signatures
- ✅ Subject profiles JSON export

**Impact:**
- Enables longitudinal studies
- Identifies intervention effects
- Flags data quality issues
- Quantifies measurement reliability
- Provides subject baselines

---

**Status:** Ready to test! Process multiple sessions and run notebook 08 to see Phase 4 in action. 🚀
