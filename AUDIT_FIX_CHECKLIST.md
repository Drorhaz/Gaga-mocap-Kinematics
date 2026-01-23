# AUDIT FIX IMPLEMENTATION CHECKLIST

## 🎯 Goal: 100% Parameter Coverage (0% NULL rate)

---

## ✅ Phase 1: Step 04 Filtering Export (PRIORITY 1)

**Time Estimate:** 1-2 hours  
**Files to Modify:** `src/filtering.py` or `notebooks/04_Filtering.ipynb`

### Tasks:

- [ ] **1.1** Compute weighted average `filter_cutoff_hz`
  ```python
  total_markers = sum(region_results[r]['marker_count'] for r in regions)
  weighted_avg = sum(r['cutoff'] * r['markers'] / total_markers for r in region_results.values())
  summary['filter_params']['filter_cutoff_hz'] = round(weighted_avg, 2)
  ```

- [ ] **1.2** Track Winter analysis success/failure
  ```python
  failed = any(r.get('failed', False) for r in region_results.values())
  summary['filter_params']['winter_analysis_failed'] = failed
  ```

- [ ] **1.3** Aggregate failure reasons
  ```python
  reasons = [f"{r}: {data['failure_reason']}" for r, data in region_results.items() if data.get('failed')]
  summary['filter_params']['winter_failure_reason'] = "; ".join(reasons) if reasons else None
  ```

- [ ] **1.4** Generate decision rationale
  ```python
  if not failed:
      reason = "Per-region Winter analysis succeeded - cutoffs range 6.0-10.0 Hz"
  else:
      reason = f"Per-region analysis partially failed - {len(reasons)} region(s) used fallback"
  summary['filter_params']['decision_reason'] = reason
  ```

- [ ] **1.5** Compute average residual RMS
  ```python
  avg_rms = sum(r['residual_rms_mm'] for r in region_results.values()) / len(region_results)
  summary['filter_params']['residual_rms_mm'] = round(avg_rms, 3)
  ```

- [ ] **1.6** Compute average residual slope
  ```python
  avg_slope = sum(r['residual_slope'] for r in region_results.values()) / len(region_results)
  summary['filter_params']['residual_slope'] = round(avg_slope, 6)
  ```

- [ ] **1.7** Add guardrails status
  ```python
  summary['filter_params']['biomechanical_guardrails'] = {
      'enabled': True,  # Or read from config
      'velocity_limit_deg_s': 1500,
      'acceleration_limit_deg_s2': 50000
  }
  ```

- [ ] **1.8** Load subject metadata
  ```python
  import json
  from pathlib import Path
  
  # Load subject config
  subject_id = run_id.split('_')[0]  # e.g., "734"
  subject_file = Path("data/subject_metadata.json")
  
  if subject_file.exists():
      with open(subject_file) as f:
          subjects = json.load(f)
      subject_data = subjects.get(subject_id, {})
      mass_kg = subject_data.get('weight_kg') or subject_data.get('mass_kg')
      height_cm = subject_data.get('height_cm')
  else:
      mass_kg = None
      height_cm = None
  
  summary['subject_metadata'] = {
      'mass_kg': mass_kg,
      'height_cm': height_cm,
      'units_status': 'internal_unscaled'
  }
  ```

### Validation:

- [ ] **1.9** Test on one recording
  ```bash
  # Run Step 04 on test recording
  # Check output JSON has all 8 new fields
  ```

- [ ] **1.10** Verify JSON structure
  ```python
  import json
  data = json.load(open('derivatives/step_04_filtering/734_T1_P1_R1_...__filtering_summary.json'))
  
  assert 'filter_cutoff_hz' in data['filter_params']
  assert 'winter_analysis_failed' in data['filter_params']
  assert 'residual_rms_mm' in data['filter_params']
  assert data['subject_metadata']['mass_kg'] is not None
  print("✅ Step 04 validation passed!")
  ```

---

## ✅ Phase 2: Step 01 Calibration Extraction (PRIORITY 2)

**Time Estimate:** 2-3 hours  
**Files to Modify:** `src/loader.py` or `src/calibration.py`

### Tasks:

- [ ] **2.1** Create `.mcal` parser function
  ```python
  import xml.etree.ElementTree as ET
  from pathlib import Path
  
  def parse_mcal_file(mcal_path: str) -> dict:
      """Parse OptiTrack .mcal file for calibration metrics."""
      
      if not Path(mcal_path).exists():
          return {
              'pointer_tip_rms_error_mm': None,
              'wand_error_mm': None,
              'export_date': None
          }
      
      try:
          tree = ET.parse(mcal_path)
          root = tree.getroot()
          
          # Extract values (adjust XML paths based on actual structure)
          pointer_error = root.find('.//PointerError')
          wand_error = root.find('.//WandError')
          export_date = root.find('.//ExportDate')
          
          return {
              'pointer_tip_rms_error_mm': float(pointer_error.text) if pointer_error is not None else None,
              'wand_error_mm': float(wand_error.text) if wand_error is not None else None,
              'export_date': export_date.text if export_date is not None else None
          }
      except Exception as e:
          print(f"Warning: Failed to parse {mcal_path}: {e}")
          return {
              'pointer_tip_rms_error_mm': None,
              'wand_error_mm': None,
              'export_date': None
          }
  ```

- [ ] **2.2** Inspect actual `.mcal` file structure
  ```bash
  # Check what the XML structure looks like
  cat data/734/734.mcal | head -100
  # Or open in text editor to see XML tags
  ```

- [ ] **2.3** Update XML paths to match actual structure
  ```python
  # Adjust .find() paths based on inspection
  # Common patterns:
  # - <CalibrationData><PointerTipError>...</PointerTipError></CalibrationData>
  # - <QualityMetrics><WandError units="mm">...</WandError></QualityMetrics>
  ```

- [ ] **2.4** Integrate into Step 01 loader
  ```python
  # In src/loader.py -> load_raw_data() or similar:
  
  # After loading CSV data...
  
  # Try to load calibration data from .mcal file
  subject_id = run_id.split('_')[0]
  mcal_path = Path(f"data/{subject_id}/{subject_id}.mcal")
  cal_data = parse_mcal_file(str(mcal_path))
  
  report['calibration'] = cal_data  # Replaces the null values
  ```

### Validation:

- [ ] **2.5** Test parser on existing .mcal files
  ```python
  cal_data = parse_mcal_file('data/734/734.mcal')
  print(cal_data)
  # Should show actual values, not None
  ```

- [ ] **2.6** Run Step 01 on test recording
  ```bash
  # Re-run Step 01 loader
  # Check output JSON has calibration data populated
  ```

- [ ] **2.7** Verify JSON structure
  ```python
  data = json.load(open('derivatives/step_01_parse/734_T1_P1_R1_...__step01_loader_report.json'))
  
  assert data['calibration']['pointer_tip_rms_error_mm'] is not None
  assert data['calibration']['wand_error_mm'] is not None
  print("✅ Step 01 calibration validation passed!")
  ```

---

## ✅ Phase 3: Step 05 Height Validation (PRIORITY 3)

**Time Estimate:** 30 minutes  
**Files to Modify:** `src/reference.py`

### Tasks:

- [ ] **3.1** Add height validation function
  ```python
  def validate_height(height_cm: float) -> str:
      """
      Validate computed height against physiological ranges.
      
      Returns:
          "PASS" - Normal adult range (140-210 cm)
          "REVIEW" - Edge case (very short/tall, or child)
          "FAIL" - Unphysiological (<120cm or >250cm)
      """
      if height_cm <= 0:
          return "FAIL"  # Invalid height
      elif 140 <= height_cm <= 210:
          return "PASS"  # Normal adult range
      elif 120 < height_cm < 140 or 210 < height_cm < 250:
          return "REVIEW"  # Edge cases
      else:
          return "FAIL"  # Unphysiological
  ```

- [ ] **3.2** Integrate into reference detection
  ```python
  # In src/reference.py -> detect_static_reference() or similar:
  
  # After computing height...
  computed_height = ...  # Height computation logic
  height_status = validate_height(computed_height)
  
  summary['subject_context'] = {
      'height_cm': computed_height,
      'scaling_factor': scaling_factor,
      'height_status': height_status  # ADD THIS LINE
  }
  ```

### Validation:

- [ ] **3.3** Test validation function
  ```python
  assert validate_height(170) == "PASS"
  assert validate_height(130) == "REVIEW"
  assert validate_height(50) == "FAIL"
  assert validate_height(300) == "FAIL"
  print("✅ Height validation logic correct!")
  ```

- [ ] **3.4** Re-run Step 05 on test recording
  ```bash
  # Re-run Step 05 reference detection
  # Check output JSON has height_status
  ```

- [ ] **3.5** Verify JSON structure
  ```python
  data = json.load(open('derivatives/step_05_reference/734_T1_P1_R1_...__reference_summary.json'))
  
  assert 'height_status' in data['subject_context']
  assert data['subject_context']['height_status'] in ['PASS', 'REVIEW', 'FAIL']
  print("✅ Step 05 height status validation passed!")
  ```

---

## ✅ Phase 4: Re-run Pipeline & Validate

**Time Estimate:** 1 hour

### Tasks:

- [ ] **4.1** Re-run full pipeline on test recordings
  ```bash
  python run_pipeline.py --config batch_configs/subject_734_T1_only.json
  ```

- [ ] **4.2** Check all JSON files have new fields
  ```python
  # Quick validation script
  from pathlib import Path
  import json
  
  # Check Step 04
  for f in Path('derivatives/step_04_filtering').glob('*__filtering_summary.json'):
      data = json.load(open(f))
      assert 'filter_cutoff_hz' in data['filter_params'], f"Missing filter_cutoff_hz in {f.name}"
      assert data['subject_metadata']['mass_kg'] is not None, f"Missing mass_kg in {f.name}"
  
  # Check Step 01
  for f in Path('derivatives/step_01_parse').glob('*__step01_loader_report.json'):
      data = json.load(open(f))
      # Note: calibration may still be None if .mcal doesn't exist - that's OK
  
  # Check Step 05
  for f in Path('derivatives/step_05_reference').glob('*__reference_summary.json'):
      data = json.load(open(f))
      assert 'height_status' in data['subject_context'], f"Missing height_status in {f.name}"
  
  print("✅ All JSON validations passed!")
  ```

- [ ] **4.3** Re-run Notebook 07 (Master Quality Report)
  ```bash
  jupyter nbconvert --to notebook --execute notebooks/07_master_quality_report.ipynb
  ```

- [ ] **4.4** Run audit analysis script
  ```bash
  python analyze_audit.py > audit_analysis_AFTER_FIX.txt
  ```

- [ ] **4.5** Verify 0% NULL rate
  ```python
  import pandas as pd
  
  xl = pd.ExcelFile('reports/Master_Audit_Log_<TIMESTAMP>.xlsx')
  df = pd.read_excel(xl, sheet_name='Parameter_Audit')
  
  null_counts = df.isnull().sum()
  null_cols = null_counts[null_counts > 0]
  
  if len(null_cols) == 0:
      print("✅ SUCCESS: 0% NULL rate - all parameters populated!")
  else:
      print(f"❌ STILL MISSING: {len(null_cols)} columns have NULL values:")
      print(null_cols)
  ```

- [ ] **4.6** Compare before/after statistics
  ```bash
  # Before: 14 columns with NULL (19.4%)
  # After: 0 columns with NULL (0%)
  # Improvement: 100% parameter coverage achieved! ✅
  ```

---

## ✅ Phase 5: Documentation & Version Control

**Time Estimate:** 30 minutes

### Tasks:

- [ ] **5.1** Update pipeline version string
  ```python
  # In src/__init__.py or config:
  PIPELINE_VERSION = "v2.9_complete_audit_export"
  ```

- [ ] **5.2** Document changes in CHANGELOG
  ```markdown
  ## v2.9 - Complete Audit Export (2026-01-23)
  
  ### Fixed
  - Step 04: Export complete Winter analysis metrics (8 new fields)
  - Step 01: Extract calibration data from .mcal files (3 fields)
  - Step 05: Add height validation status (1 field)
  - Master Audit Log: Achieved 100% parameter coverage (was 74%)
  
  ### Changed
  - Step 04 now loads subject metadata from data/subject_metadata.json
  - Filtering summary includes weighted average cutoff for per-region mode
  ```

- [ ] **5.3** Update documentation
  ```bash
  # Update relevant .md files with new fields
  # - AUDIT_REVIEW_EXECUTIVE_SUMMARY.md (mark as RESOLVED)
  # - pipeline documentation with new audit fields
  ```

- [ ] **5.4** Commit changes
  ```bash
  git add src/filtering.py src/loader.py src/reference.py
  git commit -m "Fix audit export: achieve 100% parameter coverage
  
  - Step 04: Add 8 missing Winter analysis fields + subject metadata
  - Step 01: Add .mcal calibration extraction
  - Step 05: Add height validation status
  - Resolves 14 NULL parameters in Master Audit Log
  "
  ```

---

## 🎯 SUCCESS CRITERIA

- [ ] **Parameter Coverage:** 65/65 fields (100%) ✅
- [ ] **NULL Values:** 0 columns (0%) ✅
- [ ] **Step 04 Completeness:** 18/18 fields (100%) ✅
- [ ] **Step 01 Completeness:** 14/14 fields (100%) ✅
- [ ] **Step 05 Completeness:** 14/14 fields (100%) ✅
- [ ] **Master Audit Log:** Regenerated with complete data ✅
- [ ] **Documentation:** Updated with new fields ✅
- [ ] **Version Control:** Changes committed ✅

---

## 📊 PROGRESS TRACKER

| Phase | Status | Time | Notes |
|-------|--------|------|-------|
| Phase 1 (Step 04) | ⬜ Not Started | 0/2h | 8 fields to add |
| Phase 2 (Step 01) | ⬜ Not Started | 0/3h | .mcal parsing |
| Phase 3 (Step 05) | ⬜ Not Started | 0/0.5h | Height validation |
| Phase 4 (Validation) | ⬜ Not Started | 0/1h | Re-run pipeline |
| Phase 5 (Docs) | ⬜ Not Started | 0/0.5h | Documentation |
| **TOTAL** | **0%** | **0/6h** | **Target: 100%** |

---

**Instructions:** Work through phases sequentially. Check off tasks as completed. Run validations after each phase. Document any issues encountered.

**Start Here:** Phase 1, Task 1.1 (Compute weighted average filter_cutoff_hz)
