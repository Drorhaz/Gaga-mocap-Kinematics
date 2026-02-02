# Phase 3: Intensity Index Implementation

## Status: ✅ COMPLETE (Part 1 of Phase 3)

**Date:** January 29, 2026

---

## What is Intensity Index?

**Definition:** Movement activity normalized by duration

**Formula:** `Intensity Index = Path Length / Duration`

**Units:** meters per second (m/s)

**Purpose:**
- Raw path length is biased by session duration
- Longer sessions → longer paths (even with same activity level)
- Intensity Index = "How much movement per second?"
- Enables fair comparison between sessions of different lengths

---

## Example

### Without Intensity Normalization (Biased)
```
Session A: 60 seconds, Path = 30m → Appears "less active"
Session B: 120 seconds, Path = 40m → Appears "more active"
```

### With Intensity Normalization (Fair)
```
Session A: 30m / 60s = 0.50 m/s
Session B: 40m / 120s = 0.33 m/s
```
**Result:** Session A is actually MORE intense (0.50 vs 0.33)!

---

## What Was Implemented

### 1. Notebook 06 (`06_ultimate_kinematics.ipynb`)

**Added computation** (in Cell 13, after path length):
```python
duration_sec = n_frames / FS
intensity_index = {}
for segment, path_m in path_lengths.items():
    if duration_sec > 0:
        intensity_index[segment] = path_m / duration_sec  # m/s
    else:
        intensity_index[segment] = 0.0
```

**Added to JSON export:**
```json
{
  "intensity_index_m_per_s": {
    "LeftHand": 0.3542,
    "RightHand": 0.3421,
    ...
  }
}
```

### 2. `src/utils_nb07.py`

**Updated `extract_phase2_metrics()`:**
- Extracts intensity_index from validation_report.json
- Computes max, mean intensity
- Identifies top 3 most intense segments
- Aggregates by anatomical region

**Added 19 new columns to engineering profile:**
1. `Intensity_Max_m_per_s`
2. `Intensity_Mean_m_per_s`
3. `Most_Intense_Segments`
4. `Intensity_Neck_m_per_s`
5. `Intensity_Shoulders_m_per_s`
6. `Intensity_Elbows_m_per_s`
7. `Intensity_Wrists_m_per_s`
8. `Intensity_Spine_m_per_s`
9. `Intensity_Hips_m_per_s`
10. `Intensity_Knees_m_per_s`
11. `Intensity_Ankles_m_per_s`
... (8 anatomical regions total)

### 3. Notebook 08 (`08_engineering_physical_audit.ipynb`)

**Added Section 11.6:**
- Displays intensity by anatomical region
- Summary statistics (mean, min, max)
- Ranking of most intense regions
- Interpretation guide

**Output Example:**
```
================================================================================
INTENSITY INDEX (meters per second)
================================================================================

Intensity by Anatomical Region (m/s):

Run_ID                                Duration_sec  Neck  Shoulders  Elbows  Wrists  ...
734_T3_P2_R1_Take 2025-12-30...       137.53       0.09    0.33      0.35    0.38   ...

================================================================================
MOST INTENSE REGIONS (ranked by average intensity)
================================================================================
  1. Wrists      : 0.3804 m/s
  2. Elbows      : 0.3541 m/s
  3. Shoulders   : 0.3289 m/s
  ...

INTERPRETATION GUIDE:
  • 0.10 - 0.30 m/s : Slow, controlled movements
  • 0.30 - 0.60 m/s : Moderate movement speed
  • 0.60 - 1.00 m/s : Fast, dynamic movements
  • >1.00 m/s       : Very fast movements
```

---

## Column Count Update

**Before Phase 3:** 77 columns  
**After Phase 3:** **96 columns** (+19)

Breakdown:
- 3 global intensity metrics
- 8 anatomical region intensity values (× 2 for path + intensity = 16 total region columns)

---

## Testing Instructions

### Step 1: Run Notebook 06
```
1. Open notebooks/06_ultimate_kinematics.ipynb
2. Restart kernel
3. Run all cells
4. Look for output: "✓ Intensity Index computed"
```

### Step 2: Verify JSON Output
```bash
python -c "import json; v = json.load(open('derivatives/step_06_kinematics/ultimate/{RUN_ID}__validation_report.json')); print('intensity_index_m_per_s' in v)"
```
**Expected:** `True`

### Step 3: Run Notebook 08
```
1. Open notebooks/08_engineering_physical_audit.ipynb
2. Run all cells
3. Check Section 11.6 for Intensity Index display
4. Verify new columns in DataFrame
```

### Step 4: Check Excel Export
```
File: QC_Reports/Engineering_Audit_{timestamp}.xlsx
Verify columns: Intensity_Max_m_per_s, Intensity_Neck_m_per_s, etc.
```

---

## Interpretation Guide

### What is "Normal" Intensity?

| Activity Type | Typical Intensity (m/s) |
|---------------|------------------------|
| **Resting/Static** | 0.01 - 0.10 |
| **Slow, controlled movements** | 0.10 - 0.30 |
| **Moderate daily activities** | 0.30 - 0.60 |
| **Fast movements (reaching, walking)** | 0.60 - 1.00 |
| **Very fast (sports, rapid tasks)** | > 1.00 |

### Clinical Relevance

**High Intensity:**
- ✅ Good: Indicates active movement, functional task performance
- ⚠️ Caution: May indicate tremor, hyperkinesia, or compensatory strategies

**Low Intensity:**
- ✅ Good: Smooth, controlled movements
- ⚠️ Caution: May indicate bradykinesia, fatigue, or limited range of motion

**Context matters!** Interpret in relation to task requirements.

---

## Advantages Over Raw Path Length

| Metric | Raw Path Length | Intensity Index |
|--------|----------------|-----------------|
| **Units** | meters | meters/second |
| **Bias** | Duration-dependent | Duration-normalized |
| **Comparison** | Unfair for different durations | Fair across all sessions |
| **Interpretation** | "How far?" | "How active?" |
| **Use Case** | Absolute movement | Relative activity level |

---

## Future Enhancements (Remaining Phase 3)

1. **Temporal Outlier Visualization** - Plot where outliers occur in time
2. **Bone Stability ASCII Tree** - Hierarchical skeleton with CV% annotations
3. **Movement Intensity Heat Maps** - Spatial distribution visualization

---

## Files Modified

1. **`notebooks/06_ultimate_kinematics.ipynb`**
   - Added intensity computation in Cell 13
   - Added to validation_report.json export

2. **`src/utils_nb07.py`**
   - Updated `extract_phase2_metrics()` (now handles Phase 3 too)
   - Added 19 new columns to `build_engineering_profile_row()`

3. **`notebooks/08_engineering_physical_audit.ipynb`**
   - Added Section 11.6 (Intensity Index)
   - Added cells 13-14

---

## Documentation

- **Full guide:** This document (`docs/PHASE_3_INTENSITY_INDEX.md`)
- **Phase 2 details:** `docs/PHASE_2_IMPLEMENTATION_SUMMARY.md`
- **Anatomical mapping:** `docs/ANATOMICAL_REGION_MAPPING.md`

---

## Next Steps

**Option A: Test Intensity Index**
- Run notebook 06 → verify JSON → run notebook 08 → check Excel

**Option B: Continue Phase 3**
- Implement remaining Phase 3 features (visualizations, bone tree, etc.)

**Option C: Use What We Have**
- Phase 1-3 (Part 1) gives you a comprehensive engineering audit
- 96 columns covering all major aspects

---

**Status:** Ready to test! Run notebook 06 to generate intensity metrics. 🚀
