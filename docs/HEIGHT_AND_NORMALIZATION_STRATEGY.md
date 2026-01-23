# Height Computation & Normalization Strategy in NB05

## Executive Summary

This document discusses the **height computation methodology** in Notebook 05 (Reference Detection) and proposes a **normalization strategy** for biomechanical metrics to ensure fair cross-subject comparisons.

**🚨 CRITICAL BUG IDENTIFIED**: The current height calculation uses ALL markers (including hands/fingers) to find the floor reference, which causes **height overestimation**. The fix is detailed in `HEIGHT_COMPUTATION_FIX.md` and must be applied before implementing normalization strategies.

---

## 1. Current Height Computation (NB05)

### 1.1 Implementation Overview

**Location**: `notebooks/05_reference_detection.ipynb`, Cell 02 (Lines 171-241)

**Method**: Direct Vertical Measurement from Motion Capture Data

### 1.2 Scientific Rationale

The pipeline estimates subject height using the **Direct Vertical (Floor-to-Head) Method**:

```python
# Get all Y-position columns to find absolute floor
all_y_cols = [c for c in ref_df.columns if '__py' in c]
head_y_col = [c for c in ref_df.columns if 'Head__py' in c]

# ❌ PROBLEM: Use GLOBAL minimum across ALL markers as floor reference
floor_y = ref_df[all_y_cols].min().min()
head_y_max = ref_df[head_y_col].max().values[0]

# Calculate height
height_raw = head_y_max - floor_y
direct_height_cm = height_raw * sf_to_cm
```

### 1.3 **CRITICAL BUG IDENTIFIED** 🚨

**Problem**: Using `ref_df[all_y_cols].min().min()` is **incorrect** because:

1. **Hand/finger markers can dip below foot level**
   - During T-pose, if hands are slightly lowered, they may be below the floor
   - Finger markers (LeftHandIndex1, etc.) extend even lower
   
2. **Spurious low values from noise/occlusion**
   - Marker reconstruction errors can create artificially low Y-values
   - This inflates the computed height

3. **Example of the error**:
   ```
   Actual foot floor level: 0.05 m
   Hand marker minimum: -0.10 m (hand dropped below waist)
   Head maximum: 1.55 m
   
   WRONG: height = 1.55 - (-0.10) = 1.65 m (165 cm) ❌
   RIGHT: height = 1.55 - 0.05 = 1.50 m (150 cm) ✅
   ```

### 1.4 Correct Implementation

**Use specific foot markers as floor reference**:

```python
# CORRECT: Use foot-specific markers for floor reference
foot_y_cols = [c for c in ref_df.columns if any(marker in c for marker in 
              ['LeftToeBase__py', 'RightToeBase__py', 'LeftFoot__py', 'RightFoot__py'])]
head_y_col = [c for c in ref_df.columns if 'Head__py' in c]

if foot_y_cols and head_y_col:
    # Use minimum of FOOT markers only (not all markers)
    floor_y = ref_df[foot_y_cols].min().min()
    head_y_max = ref_df[head_y_col].max().values[0]
    
    # Calculate height
    height_raw = head_y_max - floor_y
    direct_height_cm = height_raw * sf_to_cm
```

**Why this is correct**:
- ✅ **Anatomically sound**: Feet define the floor during standing T-pose
- ✅ **Robust to hand position**: Ignores hand/finger markers that may dip low
- ✅ **Noise resistant**: Foot markers are typically well-tracked (weight-bearing)
- ✅ **Matches biomechanics convention**: Height = head - floor contact point

**Fallback hierarchy**:
1. **Primary**: Use LeftToeBase + RightToeBase (most anatomically accurate)
2. **Secondary**: Use LeftFoot + RightFoot (ankle markers)
3. **Tertiary**: Use LeftUpLeg + RightUpLeg minimum (if feet missing)
4. **Last resort**: Use all markers (current buggy behavior)

### 1.3 Data Flow

```
Notebook 05: Reference Detection
  └─> Detects stable calibration window (T-pose)
  └─> Measures vertical extent: floor_y to head_y_max
  └─> Calculates height_cm = (head_y_max - floor_y) * scale_factor
  └─> Updates data/subject_metadata.json:
      {
        "subject_info": {
          "height_cm": 149.86,
          "height_estimated": true,
          "height_estimation_method": "direct_vertical"
        }
      }

Subsequent Notebooks (02, 04, 06, 07)
  └─> Load height from metadata
  └─> Use in biomechanical calculations
```

### 1.4 Current Metadata State

```json
{
    "subject_info": {
        "weight_kg": null,
        "height_cm": 149.85962823320602,
        "body_type": "average",
        "height_estimated": true,
        "height_estimation_method": "direct_vertical"
    }
}
```

**Status**: Height is **computed** (not estimated) from mocap data ✅

---

## 2. Problem Statement: Height Scoring Uniformity

### 2.1 Current Behavior

**Observation from `test_biomechanics_scoring.py` or audit logs**:
> "If the height scores are all the same, the code is likely checking for the **existence** of the value rather than validating its **accuracy**."

### 2.2 Root Cause Analysis

The current scoring system may be using a binary check:

```python
# Current (hypothetical)
height_score = 100.0 if SUBJECT_HEIGHT is not None else 0.0
```

**Problem**: This gives full credit for having **any** height value, regardless of:
- Accuracy of measurement
- Uncertainty in estimation method
- Cross-validation with arm span
- Height reasonableness for demographics

### 2.3 Evidence from Codebase

Looking at `src/utils_nb07.py::score_biomechanics()`:
- Currently scores **physiological plausibility** (velocities/accelerations)
- Currently scores **skeleton stability** (bone length consistency)
- Currently scores **movement continuity** (burst classification)
- **MISSING**: Height validation component

---

## 3. Proposed Solution: Normalized Path Length Metric

### 3.1 Scientific Rationale

**Problem**: Raw path length (mm) is **not comparable across subjects**:
- Taller subjects naturally have longer limbs → larger path lengths
- Mass affects inertial properties and movement dynamics
- Raw metrics confound **subject anthropometry** with **movement quality**

**Solution**: Normalize metrics by subject height and/or mass:

```
Normalized_Path_Length = Path_Length_mm / Subject_Height_cm
```

Or for more sophisticated normalization (Hof, 1996):

```
Dimensionless_Speed = Velocity / sqrt(g * leg_length)
```

### 3.2 Implementation Locations

#### A. Path Length Calculation (NB06)

**Current Implementation**:
```python
# notebooks/06_rotvec_omega.ipynb, Lines 1495-1507
if 'Hips__px' in df_final.columns:
    hips_coords = df_final[['Hips__px', 'Hips__py', 'Hips__pz']].values
    diffs = np.diff(hips_coords, axis=0)
    dist_per_frame = np.linalg.norm(diffs, axis=1)
    path_length = float(np.sum(dist_per_frame))  # Units: mm
```

**Output**: `movement_metrics.path_length_mm`

#### B. Normalization Proposal

**Option 1: Simple Height Normalization**
```python
# Add to kinematics summary (NB06)
path_length_mm = float(np.sum(dist_per_frame))
path_length_normalized = path_length_mm / SUBJECT_HEIGHT_cm if SUBJECT_HEIGHT_cm else np.nan

summary["movement_metrics"]["path_length_mm"] = round(path_length_mm, 1)
summary["movement_metrics"]["path_length_per_cm_height"] = round(path_length_normalized, 3)
```

**Option 2: Height + Mass Normalization (Hof, 1996)**
```python
# Dimensionless metrics for cross-subject comparison
if SUBJECT_HEIGHT_cm and SUBJECT_WEIGHT_kg:
    leg_length_m = SUBJECT_HEIGHT_cm * 0.0053  # Winter 2009 coefficient
    froude_number = avg_velocity**2 / (9.81 * leg_length_m)
    
    summary["movement_metrics"]["froude_number"] = round(froude_number, 3)
    summary["movement_metrics"]["normalization_mode"] = "anthropometric"
else:
    summary["movement_metrics"]["normalization_mode"] = "unit_mass"
```

---

## 4. Implementation Strategy

### 4.1 Phase 1: Add Normalized Metrics (NB06)

**Modifications to `notebooks/06_rotvec_omega.ipynb`**:

```python
# After path_length calculation
SUBJECT_HEIGHT = CONFIG.get('subject_height_cm', None)
SUBJECT_WEIGHT = CONFIG.get('subject_weight_kg', None)

# Compute normalized metrics
normalized_metrics = {}

if SUBJECT_HEIGHT:
    normalized_metrics['path_length_per_cm_height'] = round(path_length / SUBJECT_HEIGHT, 3)
    normalized_metrics['normalization_available'] = True
else:
    normalized_metrics['path_length_per_cm_height'] = None
    normalized_metrics['normalization_available'] = False

# Add to summary
summary["movement_metrics"].update(normalized_metrics)
```

### 4.2 Phase 2: Update Master Audit Export (NB07)

**Modifications to `src/utils_nb07.py::build_master_audit_row()`**:

```python
# Add normalized columns (around line 991)
row = {
    # ... existing fields ...
    "Path_Length_mm": round(safe_float(safe_get_path(s06, "movement_metrics.path_length_mm")), 1),
    "Path_Length_Normalized": round(safe_float(safe_get_path(s06, "movement_metrics.path_length_per_cm_height")), 3),
    "Intensity_Index": round(safe_float(safe_get_path(s06, "movement_metrics.intensity_index")), 3),
    
    # Subject anthropometrics
    "Subject_Height_cm": round(safe_float(safe_get_path(s05, "subject_info.height_cm")), 1),
    "Height_Estimated": safe_get_path(s05, "subject_info.height_estimated"),
    "Height_Method": safe_get_path(s05, "subject_info.height_estimation_method"),
}
```

### 4.3 Phase 3: Enhance Height Validation Scoring

**Modifications to `src/utils_nb07.py::score_biomechanics()`**:

```python
def score_height_quality(s05: dict) -> Tuple[float, dict]:
    """
    Score height measurement quality (0-100).
    
    Components:
    - Measurement method (direct_vertical vs arm_span vs user_provided)
    - Cross-validation with arm span
    - Reasonableness check (population norms)
    """
    height_cm = safe_float(safe_get_path(s05, "subject_info.height_cm"))
    height_estimated = safe_get_path(s05, "subject_info.height_estimated")
    height_method = safe_get_path(s05, "subject_info.height_estimation_method")
    arm_span_cm = safe_float(safe_get_path(s05, "reference_quality.hand_dist_cm"))
    
    score = 100.0
    details = {
        'height_cm': height_cm,
        'method': height_method,
        'estimated': height_estimated
    }
    
    # 1. Existence check
    if not height_cm or height_cm <= 0:
        return 0.0, {'error': 'No height available'}
    
    # 2. Reasonableness check (adult human range)
    if height_cm < 140 or height_cm > 220:
        score -= 30
        details['warning'] = f'Height {height_cm:.1f}cm outside typical range'
    
    # 3. Method quality
    if height_method == "direct_vertical":
        score -= 0  # Best method
        details['method_quality'] = 'excellent'
    elif height_method == "arm_span_tpose":
        score -= 10  # Good approximation
        details['method_quality'] = 'good'
    elif not height_estimated:
        score -= 5  # User-provided
        details['method_quality'] = 'user_provided'
    else:
        score -= 15  # Unknown method
        details['method_quality'] = 'unknown'
    
    # 4. Cross-validation with arm span
    if arm_span_cm > 0:
        deviation_pct = abs(arm_span_cm - height_cm) / height_cm * 100
        details['arm_span_deviation_pct'] = round(deviation_pct, 2)
        
        if deviation_pct > 20:
            score -= 20
            details['cross_validation'] = 'poor'
        elif deviation_pct > 10:
            score -= 10
            details['cross_validation'] = 'fair'
        else:
            details['cross_validation'] = 'excellent'
    
    return max(score, 0.0), details
```

**Integration into main scoring**:
```python
def score_biomechanics(steps: Dict[str, dict]) -> Tuple[float, Dict[str, Any]]:
    # Existing components (90% total)
    physiological_score, phys_details = score_physiological_plausibility(steps)
    skeleton_score, skel_details = score_skeleton_stability(steps)
    movement_score, move_details = score_movement_continuity(steps)
    
    # NEW: Height quality (10% weight)
    height_score, height_details = score_height_quality(steps.get("step_05", {}))
    
    # Weighted combination
    overall_score = (
        0.35 * physiological_score +  # Reduced from 40%
        0.30 * skeleton_score +
        0.25 * movement_score +        # Reduced from 30%
        0.10 * height_score            # NEW component
    )
    
    scorecard = {
        'overall_score': round(overall_score, 2),
        'components': {
            'physiological': {'score': phys_details, 'weight': 0.35},
            'skeleton': {'score': skel_details, 'weight': 0.30},
            'movement': {'score': move_details, 'weight': 0.25},
            'height': {'score': height_details, 'weight': 0.10}  # NEW
        }
    }
    
    return overall_score, scorecard
```

---

## 5. Benefits of This Approach

### 5.1 Scientific Benefits

1. **Fair Cross-Subject Comparison**
   - Normalized metrics account for anthropometric differences
   - Movement quality separated from body size effects

2. **Transparent Height Validation**
   - Height quality score reflects measurement uncertainty
   - Method-specific scoring (direct_vertical > arm_span > user_provided)

3. **Enhanced Audit Trail**
   - Master audit log includes both raw and normalized metrics
   - Height method and quality clearly documented

### 5.2 Practical Benefits

1. **Backward Compatibility**
   - Raw metrics still available for absolute comparisons
   - Normalized metrics added as optional columns

2. **Progressive Enhancement**
   - Can be implemented incrementally (Phase 1 → 2 → 3)
   - Existing pipelines continue to work

3. **Research Flexibility**
   - Researchers can choose raw vs normalized based on research question
   - Multiple normalization options available (height-only vs Hof model)

---

## 6. Validation Plan

### 6.1 Test Cases

```python
# test_height_normalization.py

def test_normalized_path_length():
    """Verify path length normalization produces expected ratios."""
    # Subject A: 150cm tall, 15000mm path → ratio = 100
    # Subject B: 180cm tall, 18000mm path → ratio = 100
    # Should be comparable!
    
def test_height_quality_scoring():
    """Verify height scoring differentiates quality levels."""
    # direct_vertical + low arm span deviation → ~95-100
    # arm_span + moderate deviation → ~80-90
    # no height → 0
```

### 6.2 Regression Testing

- Run batch processing on all subjects (505, 621, 734, 763)
- Verify normalized metrics are computed correctly
- Check that height scores vary appropriately across subjects

---

## 7. References

### Scientific Literature

1. **Hof, A. L. (1996)**. "Scaling gait data to body size." *Gait & Posture*, 4(3), 222-223.
   - Seminal work on dimensionless speed and normalization

2. **Winter, D. A. (2009)**. *Biomechanics and Motor Control of Human Movement*.
   - Anthropometric coefficients and segment length ratios

3. **Gordon et al. (1989)**. "Anthropometric Survey of U.S. Army Personnel"
   - Reference data for height/arm span relationships

### Codebase References

- Height calculation: `notebooks/05_reference_detection.ipynb`, Lines 171-241
- Path length calculation: `notebooks/06_rotvec_omega.ipynb`, Lines 1495-1507
- Biomechanics scoring: `src/utils_nb07.py::score_biomechanics()`
- Master audit export: `src/utils_nb07.py::build_master_audit_row()`

---

## 8. Implementation Checklist

- [ ] **Phase 1**: Add normalized path length to NB06 kinematics summary
- [ ] **Phase 2**: Update Master Audit export with normalized columns
- [ ] **Phase 3**: Implement height quality scoring in utils_nb07
- [ ] **Testing**: Create test cases for normalization logic
- [ ] **Validation**: Run batch processing on all subjects
- [ ] **Documentation**: Update user guides and README files

---

## Appendix: Example Output

### Before (Current)
```json
{
  "movement_metrics": {
    "path_length_mm": 25666.2,
    "intensity_index": 0.084
  }
}
```

### After (Proposed)
```json
{
  "movement_metrics": {
    "path_length_mm": 25666.2,
    "path_length_per_cm_height": 171.3,
    "intensity_index": 0.084,
    "normalization_available": true,
    "normalization_method": "height_only"
  },
  "subject_anthropometrics": {
    "height_cm": 149.86,
    "height_estimated": true,
    "height_method": "direct_vertical",
    "height_quality_score": 95.0
  }
}
```

---

**Document Version**: 1.0  
**Date**: 2026-01-23  
**Author**: Gaga Motion Analysis Pipeline  
**Status**: Proposal for Review
