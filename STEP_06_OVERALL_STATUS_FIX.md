# Step 06: Overall Status Fix - Classification-Based Status

## Executive Summary

**Problem**: `overall_status` always fails because the current logic treats ANY velocity over limits as an ERROR.

**Root Cause**: Error-based logic in `06_rotvec_omega.ipynb` (lines 1393, 1664):
```python
overall_status = "PASS" if (max_v < 1500 and ...) else "FAIL"
```

**Solution**: Shift to **Classification-Based Status** using Gate 5 (Burst Classification) results.

---

## New Status Logic (Gaga-Specific)

### Status Determination Rules

```
IF Tier 1 Artifacts > 1.0% of total frames:
    overall_status = "FAIL"
    
ELIF Tier 1 Artifacts > 0.1% of total frames:
    overall_status = "REVIEW" 
    
ELIF Contains Tier 2 (Bursts) OR Tier 3 (Flow):
    overall_status = "PASS (HIGH INTENSITY)"
    
ELSE:
    overall_status = "PASS"
```

### Tier Definitions

- **Tier 1 - ARTIFACT** (1-3 frames, <25ms): Physically impossible spikes → **EXCLUDE from statistics**
- **Tier 2 - BURST** (4-7 frames, 33-58ms): Potential whip/shake → **REVIEW required**
- **Tier 3 - FLOW** (8+ frames, >65ms): Sustained intentional movement → **ACCEPT as valid Gaga**

---

## Residual RMS Policy: "Price of Smoothing"

### Definition
**Residual RMS** = Distance between raw marker position and filtered position (in mm)

### Thresholds

| RMS Value | Classification | Interpretation |
|-----------|---------------|----------------|
| < 15 mm   | GOLD          | Excellent tracking, minimal filtering distortion |
| 15-30 mm  | SILVER        | Acceptable tracking, moderate filtering |
| > 30 mm   | REVIEW        | High filtering distortion - movement is truly explosive |

### Meaning
- **High RMS** → Filter is "fighting" the movement
- If filter cutoff = 16Hz and RMS is still high → Movement is authentically explosive (not sensor noise)

---

## Implementation Plan

### 1. Update Notebook 06 - Overall Status Logic

**File**: `notebooks/06_rotvec_omega.ipynb`

**Cells to Modify**:
- Cell 9 (line ~1393): `export_final_results()` function
- Cell 11 (line ~1664): Standalone summary build
- Cell 13 (line ~2469): Gate integration summary update

**Old Logic**:
```python
overall_status = "PASS" if (max_ang_vel < 1500 and ...) else "FAIL"
```

**New Logic**:
```python
# Step 1: Get Gate 5 burst classification results
artifact_rate = gate_5_fields.get('step_06_burst_analysis', {}).get('frame_statistics', {}).get('artifact_rate_percent', 0.0)
burst_decision = gate_5_fields.get('step_06_burst_decision', {}).get('overall_status', 'PASS')

# Step 2: Determine overall_status based on Tier 1 artifact rate
if artifact_rate > 1.0:
    overall_status = "FAIL"
    status_reason = f"Tier 1 artifacts exceed 1.0% threshold ({artifact_rate:.2f}%)"
elif artifact_rate > 0.1:
    overall_status = "REVIEW"
    status_reason = f"Tier 1 artifacts exceed 0.1% threshold ({artifact_rate:.2f}%)"
elif burst_decision == "ACCEPT_HIGH_INTENSITY":
    overall_status = "PASS (HIGH INTENSITY)"
    status_reason = "High-intensity Gaga movement confirmed (Tier 2/3 flows present)"
elif burst_decision == "REVIEW":
    overall_status = "REVIEW"
    status_reason = "Manual review required for burst events"
else:
    overall_status = "PASS"
    status_reason = "Standard gait within physiological limits"
```

### 2. Add Residual RMS Classification

**File**: `notebooks/06_rotvec_omega.ipynb`

**Add to Signal Quality Section**:
```python
# Residual RMS Classification (Price of Smoothing)
avg_res_rms = 0.0
res_vals = [v for k, v in ang_audit_metrics.items() if k.endswith("_vel_residual_rms")]
if res_vals:
    avg_res_rms = float(np.mean(res_vals))

# Classify RMS quality
if avg_res_rms < 15.0:
    rms_quality = "GOLD"
    rms_interpretation = "Excellent tracking, minimal filtering distortion"
elif avg_res_rms < 30.0:
    rms_quality = "SILVER"
    rms_interpretation = "Acceptable tracking, moderate filtering"
else:
    rms_quality = "REVIEW"
    rms_interpretation = "High filtering distortion - movement is truly explosive"

# Add to summary
summary["signal_quality"]["avg_residual_rms_mm"] = round(avg_res_rms, 2)
summary["signal_quality"]["rms_quality_grade"] = rms_quality
summary["signal_quality"]["rms_interpretation"] = rms_interpretation
```

### 3. Update Scoring System

**File**: `src/utils_nb07.py`

**Update `score_signal_quality()` function** (lines 833-840):

**Old**:
```python
# Residual RMS (lower is better)
rms = safe_float(safe_get_path(s06, "signal_quality.avg_residual_rms"))
if rms > 20:
    score -= 30
elif rms > 15:
    score -= 20
elif rms > 10:
    score -= 10
```

**New**:
```python
# Residual RMS - "Price of Smoothing" Policy
rms = safe_float(safe_get_path(s06, "signal_quality.avg_residual_rms_mm"))
if rms > 30:
    score -= 30  # REVIEW: High filtering distortion
elif rms > 15:
    score -= 10  # SILVER: Acceptable
# else: < 15mm = GOLD, no penalty
```

### 4. Update Movement Continuity Scoring

**File**: `src/utils_nb07.py`

**Update `score_biomechanics()` function** (lines 729-776):

**Change**:
```python
# Line 730: burst_decision already uses Gate 5 status
burst_decision = safe_get_path(s06, "step_06_burst_decision.overall_status")

# Line 772: Update to use new status
status = safe_get_path(s06, "overall_status")
continuity_details['pipeline_status'] = status
if status in ["FAIL", "REVIEW"]:
    continuity_score -= 30
elif status == "PASS (HIGH INTENSITY)":
    continuity_score += 0  # No penalty for legitimate high-intensity movement
```

---

## Expected Behavior After Fix

### Scenario 1: Standard Gait
- Max velocity: 800 deg/s
- Artifact rate: 0.05%
- **Result**: `overall_status = "PASS"`

### Scenario 2: High-Intensity Gaga (Legitimate)
- Max velocity: 2500 deg/s
- Artifact rate: 0.3%
- Tier 3 flows: 12 events
- **Result**: `overall_status = "PASS (HIGH INTENSITY)"`

### Scenario 3: Data Quality Issue
- Max velocity: 3000 deg/s
- Artifact rate: 1.5%
- Tier 1 artifacts: 450 frames (1.5% of 30,000)
- **Result**: `overall_status = "FAIL"`

### Scenario 4: Needs Review
- Max velocity: 1800 deg/s
- Artifact rate: 0.2%
- Tier 2 bursts: 8 events
- **Result**: `overall_status = "REVIEW"`

---

## Validation Steps

1. **Test with known high-intensity file**:
   ```python
   # Subject 734, T1, P1, R1 (known explosive movement)
   # Expected: "PASS (HIGH INTENSITY)"
   ```

2. **Check artifact threshold logic**:
   ```python
   # Verify 1.0% threshold triggers FAIL
   # Verify 0.1% threshold triggers REVIEW
   ```

3. **Verify RMS classification**:
   ```python
   # Check < 15mm → GOLD
   # Check 15-30mm → SILVER
   # Check > 30mm → REVIEW
   ```

---

## Files to Modify

1. ✅ `notebooks/06_rotvec_omega.ipynb` (Cells 9, 11, 13)
2. ✅ `src/utils_nb07.py` (lines 730-776, 833-840)
3. 📝 Update schema: `config/report_schema.json` (add `overall_status` enum values)

---

## Breaking Changes

⚠️ **IMPORTANT**: This changes the meaning of `overall_status`:

**Before**: ERROR-based (any violation = FAIL)
**After**: CLASSIFICATION-based (only Tier 1 artifacts > 1% = FAIL)

This means files that previously FAILED may now PASS (HIGH INTENSITY) if they contain legitimate Gaga movement.

---

## References

- **Gate 5 Implementation**: `src/burst_classification.py`
- **Tier Definitions**: `test_gate5_structure.py` lines 31-33
- **Thresholds**: `burst_classification.py` lines 57-63
- **Current Scoring**: `src/utils_nb07.py` lines 700-862

---

**Status**: Ready for Implementation
**Date**: 2026-01-23
**Author**: Cursor AI Assistant
