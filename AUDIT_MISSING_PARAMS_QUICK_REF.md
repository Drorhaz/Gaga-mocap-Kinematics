# AUDIT XLSX MISSING PARAMETERS - QUICK SUMMARY
**Date:** 2026-01-23

## THE PROBLEM

Your Master Audit Log XLSX has **14 columns with 100% NULL values** (19.4% data loss).

## ROOT CAUSE ✅ IDENTIFIED

**NOT a schema/extraction bug** - The extraction code works fine.

**Problem:** Pipeline steps are **not generating complete audit data** in JSON files.

---

## WHAT'S MISSING

### 🔴 **Step 04 (Filtering): 8 Fields**
Missing from `__filtering_summary.json`:
1. `filter_cutoff_hz` (weighted average cutoff)
2. `winter_analysis_failed` (success/fail flag)
3. `winter_failure_reason` (why it failed)
4. `decision_reason` (cutoff selection rationale)
5. `residual_rms_mm` (RMS residual - "Price of Smoothing")
6. `residual_slope` (convergence quality)
7. `biomechanical_guardrails.enabled` (guardrails status)
8. `subject_metadata.mass_kg` + `height_cm` (not loaded from config)

**Impact:** Cannot validate Winter analysis, cannot audit filter decisions, biomechanics normalization impossible.

---

### 🟡 **Step 01 (Loader): 3 Fields**
Missing from `__step01_loader_report.json`:
1. `calibration.pointer_tip_rms_error_mm` (anatomical landmark precision)
2. `calibration.wand_error_mm` (volume calibration quality)
3. `calibration.export_date` (data export timestamp)

**Impact:** Rácz calibration layer incomplete, cannot assess OptiTrack quality.

---

### 🟡 **Step 05 (Reference): 1 Field**
Missing from `__reference_summary.json`:
1. `subject_context.height_status` (PASS/REVIEW/FAIL validation)

**Impact:** Height validation status not auditable.

---

## THE FIX

### Fix 1: Step 04 Filtering Export ⚡ **CRITICAL**

**File:** `src/filtering.py` or Notebook `04_Filtering.ipynb`

**Add to filtering summary JSON:**
```python
"filter_params": {
    # ADD THESE:
    "filter_cutoff_hz": 8.2,  # Weighted average from region_cutoffs
    "winter_analysis_failed": False,
    "winter_failure_reason": None,
    "decision_reason": "Per-region Winter analysis succeeded",
    "residual_rms_mm": 9.5,
    "residual_slope": 0.000123,
    "biomechanical_guardrails": {"enabled": True}
}
```

**Load subject metadata from config:**
```python
# Read data/subject_metadata.json
subject_id = run_id.split('_')[0]
subject_data = load_subject_config(subject_id)

"subject_metadata": {
    "mass_kg": subject_data['weight_kg'],
    "height_cm": subject_data['height_cm']
}
```

---

### Fix 2: Step 01 Calibration Extraction ⚡ **MEDIUM**

**File:** `src/loader.py` or `src/calibration.py`

**Parse .mcal file for calibration metrics:**
```python
# Add function to parse data/734/734.mcal
def parse_mcal_file(mcal_path):
    # Extract pointer_tip_rms_error_mm, wand_error_mm, export_date
    # from XML calibration file
    ...

# Use in loader:
cal_data = parse_mcal_file(f"{subject_id}/{subject_id}.mcal")
report['calibration'] = cal_data
```

---

### Fix 3: Step 05 Height Validation ⚡ **LOW**

**File:** `src/reference.py`

**Add height status:**
```python
def validate_height(height_cm):
    if 140 <= height_cm <= 210:
        return "PASS"
    elif 120 < height_cm < 250:
        return "REVIEW"
    else:
        return "FAIL"

summary['subject_context']['height_status'] = validate_height(height_cm)
```

---

## VALIDATION

After fixes, check:
```bash
# Count NULL values in Parameter_Audit sheet
python analyze_audit.py

# Should show: 0 columns with NULL values (currently 14)
```

---

## PRIORITY ORDER

1. **IMMEDIATE:** Fix Step 04 (8 missing fields, affects Winter analysis auditing)
2. **MEDIUM:** Fix Step 01 (3 missing fields, affects calibration QC)
3. **LOW:** Fix Step 05 (1 missing field, minor impact)

---

## FILES TO MODIFY

| Priority | File | Function | What to Add |
|----------|------|----------|-------------|
| 🔴 HIGH | `src/filtering.py` | `create_filtering_summary()` | 8 missing audit fields |
| 🟡 MED | `src/loader.py` | `load_raw_data()` | .mcal calibration parsing |
| 🟢 LOW | `src/reference.py` | `detect_static_reference()` | height_status validation |

---

## ESTIMATED EFFORT

- **Step 04 Fix:** 1-2 hours (compute weighted average, aggregate metrics, load subject config)
- **Step 01 Fix:** 2-3 hours (.mcal XML parsing + testing)
- **Step 05 Fix:** 30 minutes (simple validation function)

**Total:** 4-6 hours to achieve 100% audit completeness

---

## AFTER FIXES

Rerun pipeline → Regenerate JSONs → Rerun Notebook 07 → **0% NULL rate** ✅

---

**See detailed technical specs:** `AUDIT_FIX_ROOT_CAUSE.md`
