# AUDIT XLSX FIX - Missing Parameter Root Cause & Solutions
**Date:** 2026-01-23  
**Status:** 🔴 **CRITICAL DATA GENERATION GAPS IDENTIFIED**

---

## ROOT CAUSE CONFIRMED

After inspecting actual JSON files, the problem is **NOT schema mismatch** but **missing data generation** in pipeline steps.

### Verification Results:

✅ **JSON Structure is CORRECT:**
- Step 01: Uses nested `identity.*`, `raw_data_quality.*`, `calibration.*` ✅
- Step 04: Uses nested `filter_params.*`, `subject_metadata.*` ✅  
- Step 05: Uses nested `subject_context.*`, `window_metadata.*` ✅

❌ **Data is MISSING from source JSON files:**
- Step 01: `calibration.*` fields are explicitly `null` in JSON
- Step 04: Many `filter_params.*` fields not being exported
- Step 05: `subject_context.height_status` not being exported

---

## MISSING DATA BY STEP

### STEP 01: Calibration Data (3 fields NULL in JSON)

**File:** `derivatives/step_01_parse/*__step01_loader_report.json`

**JSON Content:**
```json
"calibration": {
  "pointer_tip_rms_error_mm": null,   ❌ Not extracted
  "wand_error_mm": null,              ❌ Not extracted
  "export_date": null                 ❌ Not extracted
}
```

**Root Cause:** The loader (`src/loader.py` or equivalent) is **not parsing .mcal files** to extract calibration metadata.

**Fix Location:** `src/loader.py` or `src/calibration.py`

**Fix Required:**
```python
def parse_mcal_file(mcal_path: str) -> dict:
    """
    Parse OptiTrack .mcal calibration file for quality metrics.
    
    Returns:
        dict with pointer_tip_rms_error_mm, wand_error_mm, export_date
    """
    # Read XML calibration file
    import xml.etree.ElementTree as ET
    
    tree = ET.parse(mcal_path)
    root = tree.getroot()
    
    cal_data = {
        'pointer_tip_rms_error_mm': None,
        'wand_error_mm': None,
        'export_date': None
    }
    
    # Extract calibration quality metrics
    # (XML structure depends on OptiTrack version)
    # Look for: <PointerError>, <WandError>, <ExportDate>
    
    pointer_error = root.find('.//PointerError')
    if pointer_error is not None:
        cal_data['pointer_tip_rms_error_mm'] = float(pointer_error.text)
    
    wand_error = root.find('.//WandError')
    if wand_error is not None:
        cal_data['wand_error_mm'] = float(wand_error.text)
    
    export_date = root.find('.//ExportDate')
    if export_date is not None:
        cal_data['export_date'] = export_date.text
    
    return cal_data
```

**Test Files Available:**
- `data/734/734.mcal`
- `data/763/763.mcal`

---

### STEP 04: Winter Residual Analysis Fields (8 fields missing from JSON)

**File:** `derivatives/step_04_filtering/*__filtering_summary.json`

**Current JSON Content:**
```json
{
  "filter_params": {
    "filter_type": "Winter Residual Analysis + Butterworth Low-pass (Zero-phase)",
    "filter_method": "Per-Region Winter Cutoff Selection",
    "filtering_mode": "per_region",
    "filter_order": 2,
    "region_cutoffs": { "trunk": 6.0, ... },
    "cutoff_range_hz": [6.0, 10.0],
    ...
    // ❌ MISSING FIELDS:
    // "filter_cutoff_hz": <weighted_average>,
    // "winter_analysis_failed": false,
    // "winter_failure_reason": null,
    // "decision_reason": "Per-region analysis succeeded",
    // "residual_rms_mm": <average RMS>,
    // "residual_slope": <average slope>,
    // "biomechanical_guardrails": {"enabled": true}
  },
  "subject_metadata": {
    "mass_kg": null,    ❌ Never populated
    "height_cm": null   ❌ Never populated
  }
}
```

**Root Cause:** The filtering step (`src/filtering.py` or Notebook 04) is:
1. **Not computing/exporting** weighted average cutoff for per-region mode
2. **Not exporting** Winter analysis status fields
3. **Not exporting** residual RMS and slope metrics
4. **Not copying** subject metadata from Step 01/05

**Fix Location:** `src/filtering.py` -> `apply_winter_filter()` or Notebook 04

**Fix Required:**

```python
def create_filtering_summary(per_region_results: dict, subject_metadata: dict) -> dict:
    """
    Create comprehensive filtering summary with all audit fields.
    
    Args:
        per_region_results: Dict of region -> cutoff analysis
        subject_metadata: Subject mass/height from Step 01 or Step 05
    
    Returns:
        Complete filtering summary dict
    """
    
    # Compute weighted average cutoff
    total_markers = sum(r['marker_count'] for r in per_region_results.values())
    weighted_cutoff = sum(
        r['selected_cutoff'] * r['marker_count'] / total_markers
        for r in per_region_results.values()
    )
    
    # Check if any region failed
    winter_failed = any(r.get('failed', False) for r in per_region_results.values())
    failure_reasons = [
        f"{region}: {r['failure_reason']}"
        for region, r in per_region_results.items()
        if r.get('failed', False)
    ]
    
    # Compute aggregate residual metrics
    avg_residual_rms = sum(r['residual_rms_mm'] for r in per_region_results.values()) / len(per_region_results)
    avg_residual_slope = sum(r['residual_slope'] for r in per_region_results.values()) / len(per_region_results)
    
    summary = {
        "run_id": ...,
        "identity": {...},
        "subject_metadata": {
            "mass_kg": subject_metadata.get('mass_kg'),
            "height_cm": subject_metadata.get('height_cm'),
            "units_status": "internal_unscaled"
        },
        "raw_quality": {...},
        "filter_params": {
            "filter_type": "Winter Residual Analysis + Butterworth Low-pass (Zero-phase)",
            "filter_method": "Per-Region Winter Cutoff Selection",
            "filtering_mode": "per_region",
            "filter_order": 2,
            
            # ✅ ADD THESE FIELDS:
            "filter_cutoff_hz": round(weighted_cutoff, 2),  # Weighted average
            "filter_range_hz": [
                min(r['selected_cutoff'] for r in per_region_results.values()),
                max(r['selected_cutoff'] for r in per_region_results.values())
            ],
            "winter_analysis_failed": winter_failed,
            "winter_failure_reason": "; ".join(failure_reasons) if failure_reasons else None,
            "decision_reason": "Per-region Winter analysis succeeded" if not winter_failed else "Some regions failed Winter analysis",
            "residual_rms_mm": round(avg_residual_rms, 3),
            "residual_slope": round(avg_residual_slope, 6),
            "biomechanical_guardrails": {
                "enabled": True,  # Or read from config
                "velocity_limit_deg_s": 1500,
                "acceleration_limit_deg_s2": 50000
            },
            
            # Existing fields:
            "region_cutoffs": {...},
            "cutoff_range_hz": [...],
            ...
        }
    }
    
    return summary
```

**Subject Metadata Source:**
The `mass_kg` and `height_cm` should be propagated from:
1. **Step 01** (if extracted from CSV metadata or config)
2. **Step 05** (height is computed there)
3. **Subject config file** (`data/subject_metadata.json`)

**Current Issue:** These values are never loaded into Step 04. Need to add metadata loading:

```python
# In Notebook 04 or src/filtering.py:
import json

# Load subject metadata
subject_metadata_file = Path("data/subject_metadata.json")
if subject_metadata_file.exists():
    with open(subject_metadata_file) as f:
        all_subjects = json.load(f)
    
    # Extract subject ID from run_id (e.g., "734_T1_..." -> "734")
    subject_id = run_id.split('_')[0]
    subject_metadata = all_subjects.get(subject_id, {})
else:
    subject_metadata = {}

# Use in summary:
summary['subject_metadata'] = {
    'mass_kg': subject_metadata.get('weight_kg'),  # Or 'mass_kg'
    'height_cm': subject_metadata.get('height_cm'),
    'units_status': 'internal_unscaled'
}
```

---

### STEP 05: Height Status (1 field missing)

**File:** `derivatives/step_05_reference/*__reference_summary.json`

**Current JSON:** (height_status field does not exist)

**Fix Required:** Add height validation status to reference detection output:

```python
# In src/reference.py -> detect_static_reference():

def validate_height(height_cm: float) -> str:
    """
    Validate computed height against physiological ranges.
    
    Returns:
        "PASS", "REVIEW", or "FAIL"
    """
    if height_cm <= 0:
        return "FAIL"  # Invalid height
    elif 140 <= height_cm <= 210:
        return "PASS"  # Normal adult range
    elif 120 < height_cm < 140 or 210 < height_cm < 250:
        return "REVIEW"  # Edge cases (very short/tall, or child)
    else:
        return "FAIL"  # Unphysiological (<120cm or >250cm)

# Then in summary export:
summary['subject_context'] = {
    'height_cm': computed_height,
    'scaling_factor': scaling_factor,
    'height_status': validate_height(computed_height)  # ✅ ADD THIS
}
```

---

## IMPLEMENTATION PLAN

### Phase 1: Step 04 Filtering Fix (HIGH PRIORITY)

**File to Modify:** `src/filtering.py` or Notebook `04_Filtering.ipynb`

**Changes:**
1. ✅ Compute weighted average `filter_cutoff_hz` from region cutoffs
2. ✅ Add `winter_analysis_failed` boolean
3. ✅ Add `winter_failure_reason` string (aggregate failures)
4. ✅ Add `decision_reason` explaining cutoff selection
5. ✅ Compute and export `residual_rms_mm` (average across regions)
6. ✅ Compute and export `residual_slope` (average across regions)
7. ✅ Add `biomechanical_guardrails.enabled` flag
8. ✅ Load and populate `subject_metadata.mass_kg` and `height_cm`

**Test:**
```python
# After fix, verify JSON contains:
assert 'filter_cutoff_hz' in data['filter_params']
assert 'winter_analysis_failed' in data['filter_params']
assert data['subject_metadata']['mass_kg'] is not None
```

---

### Phase 2: Step 01 Calibration Fix (MEDIUM PRIORITY)

**File to Modify:** `src/loader.py` or `src/calibration.py`

**Changes:**
1. ✅ Add `parse_mcal_file()` function to extract calibration metrics
2. ✅ Call in Step 01 loader to populate `calibration.*` fields
3. ✅ Handle missing .mcal files gracefully (keep null if not found)

**Test:**
```python
# Check if .mcal exists and is parsed:
mcal_path = "data/734/734.mcal"
cal_data = parse_mcal_file(mcal_path)
assert cal_data['pointer_tip_rms_error_mm'] is not None
```

---

### Phase 3: Step 05 Height Status (LOW PRIORITY)

**File to Modify:** `src/reference.py`

**Changes:**
1. ✅ Add `validate_height()` function
2. ✅ Export `height_status` in reference summary

**Test:**
```python
assert 'height_status' in data['subject_context']
assert data['subject_context']['height_status'] in ['PASS', 'REVIEW', 'FAIL']
```

---

## VALIDATION AFTER FIXES

After implementing all fixes, run validation:

```python
# validation_script.py
import json
from pathlib import Path

def validate_audit_completeness(derivatives_root: Path):
    """Validate all required fields are present in JSON files."""
    
    issues = []
    
    # Check Step 01
    for f in (derivatives_root / "step_01_parse").glob("*__step01_loader_report.json"):
        data = json.load(open(f))
        if data['calibration']['pointer_tip_rms_error_mm'] is None:
            issues.append(f"Step 01: {f.name} - calibration.pointer_tip_rms_error_mm is null")
    
    # Check Step 04
    for f in (derivatives_root / "step_04_filtering").glob("*__filtering_summary.json"):
        data = json.load(open(f))
        if 'filter_cutoff_hz' not in data['filter_params']:
            issues.append(f"Step 04: {f.name} - filter_params.filter_cutoff_hz missing")
        if data['subject_metadata']['mass_kg'] is None:
            issues.append(f"Step 04: {f.name} - subject_metadata.mass_kg is null")
    
    # Check Step 05
    for f in (derivatives_root / "step_05_reference").glob("*__reference_summary.json"):
        data = json.load(open(f))
        if 'height_status' not in data['subject_context']:
            issues.append(f"Step 05: {f.name} - subject_context.height_status missing")
    
    if issues:
        print("❌ VALIDATION FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ ALL VALIDATIONS PASSED")
        return True

# Run validation
validate_audit_completeness(Path("derivatives"))
```

---

## EXPECTED OUTCOME

After all fixes:

| Step | Before | After | Status |
|------|--------|-------|--------|
| Step 01 | 7% complete (1/14) | 100% complete (14/14) | ✅ FIXED |
| Step 02 | 100% complete (9/9) | 100% complete (9/9) | ✅ NO CHANGE |
| Step 04 | 56% complete (10/18) | 100% complete (18/18) | ✅ FIXED |
| Step 05 | 93% complete (13/14) | 100% complete (14/14) | ✅ FIXED |
| Step 06 | 100% complete (15/15) | 100% complete (15/15) | ✅ NO CHANGE |
| **OVERALL** | **74% (48/65)** | **100% (65/65)** | ✅ **COMPLETE** |

---

## CRITICAL INSIGHT

**The XLSX extraction code (`utils_nb07.py`) is working correctly!**

The problem is **upstream data generation**:
- Step 01 loader not parsing .mcal files
- Step 04 filtering not exporting complete Winter analysis results
- Step 04 not loading subject metadata from config
- Step 05 not computing height validation status

Once the JSON files contain complete data, the XLSX will automatically populate all fields.

---

## NEXT ACTIONS

1. **PRIORITY 1:** Fix Step 04 filtering export (add 8 missing fields)
2. **PRIORITY 2:** Fix Step 01 calibration extraction (.mcal parsing)
3. **PRIORITY 3:** Fix Step 05 height status export
4. **Rerun Pipeline:** Process existing recordings to regenerate JSON files
5. **Rerun Notebook 07:** Regenerate Master Audit Log XLSX
6. **Validate:** Confirm 0% NULL rate across all 65 expected parameters

---

**Report Generated:** 2026-01-23  
**Analysis:** Deep JSON inspection revealed data generation gaps, not extraction bugs.
