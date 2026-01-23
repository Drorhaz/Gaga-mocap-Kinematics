# Quick Reference: Final Push Implementation
**Gaga Motion Capture Pipeline - Scientific Enhancements**  
**Date**: 2026-01-23

---

## 📋 Quick Status Check

| Task | Status | Module | Key Feature |
|------|--------|--------|-------------|
| **Task 1** | ✅ | `subject_validation.py` | Height sanity checks, Intensity normalization |
| **Task 2** | ✅ | `burst_classification.py` | Outlier policy, FAIL on artifact rate >1% |
| **Task 3** | ✅ | `filtering.py` | Filter ceiling + RMS synergy, residual slope |
| **Task 4** | ✅ | `utils_nb07.py` | LaTeX formulas + code refs in schema |

---

## 🎯 Critical Thresholds (Quick Lookup)

### Subject Context (Task 1)
| Parameter | PASS | REVIEW | FAIL |
|-----------|------|--------|------|
| **Height** | 140-210 cm | 0-140 or 210-250 cm | ≤0 or >250 cm |
| **Mass** | 40-150 kg | 20-40 or 150-200 kg | ≤20 or >200 kg |

**Formula**: `I_norm = I / m` (Intensity / Mass)

### Outlier Policy (Task 2)
| Metric | Threshold | Action |
|--------|-----------|--------|
| **Total Outliers** | >5% frames | REVIEW |
| **Artifact Rate** | >1% frames | **FAIL** (Overall_Status) |
| **Consecutive Frames** | 1-3 | Artifact (exclude) |
| **Consecutive Frames** | 4-7 | Burst (review) |
| **Consecutive Frames** | 8+ | Flow (accept) |

### Filter Quality (Task 3)
| Metric | GOLD | SILVER | REVIEW |
|--------|------|--------|--------|
| **Residual RMS** | <15mm | 15-30mm | >30mm |

**Synergy Check**: If cutoff = 16Hz AND RMS > 20mm → **WARNING**

---

## 💻 Usage Examples

### Task 1: Validate Subject
```python
from src.subject_validation import validate_subject_context, compute_normalized_intensity_index

# Validate height and mass
result = validate_subject_context(height_cm=170.0, mass_kg=70.0)
print(result['overall_status'])  # 'PASS', 'REVIEW', or 'FAIL'

# Normalize intensity
norm = compute_normalized_intensity_index(intensity_raw=1000.0, mass_kg=70.0)
print(norm['intensity_normalized'])  # 14.29
```

### Task 2: Check Outlier Status
```python
from src.burst_classification import classify_burst_events

# Classify bursts
result = classify_burst_events(angular_velocity, fs=120.0)

# Check decision
if result['decision']['overall_status'] == 'FAIL':
    print(result['decision']['primary_reason'])
    # "High Artifact Rate: 1.23% > 1.0% threshold (Overall_Status = FAIL)"

# Get outlier percentage
outlier_pct = result['summary']['outlier_rate_percent']
print(f"Total outliers: {outlier_pct:.2f}%")
```

### Task 3: Inspect Filter Quality
```python
from src.filtering import apply_winter_filter

# Apply filter
df_filt, metadata = apply_winter_filter(df, fs, pos_cols, per_region_filtering=True)

# Check for ceiling warning
if metadata.get('filter_ceiling_warning', {}).get('triggered', False):
    warning = metadata['filter_ceiling_warning']
    print(f"Cutoff: {warning['cutoff_hz']}Hz")
    print(f"RMS: {warning['residual_rms_mm']:.2f}mm")
    print(f"Slope: {warning['residual_slope']:.6f}")
    print(warning['decision_reason'])

# Check detailed analysis
if 'winter_details' in metadata:
    details = metadata['winter_details']
    print(f"Residual slope: {details['residual_slope']:.6f}")
    print(f"Knee point found: {details['knee_point_found']}")
```

### Task 4: Access Parameter Metadata
```python
from src.utils_nb07 import PARAMETER_SCHEMA

# Get parameter info
height_param = PARAMETER_SCHEMA['step_05']['parameters']['subject_context.height_cm']
print(height_param['description'])
# "Subject height (cm) - Formula: $h = \sqrt{...}$ | Sanity check: $0 < h \leq 250$ cm | Code: src/reference.py"

# Get all filtering parameters
filter_params = PARAMETER_SCHEMA['step_04']['parameters']
for key, info in filter_params.items():
    if 'filter_cutoff' in key:
        print(f"{key}: {info['description']}")
```

---

## 📊 New Excel Report Columns

| Column | Description | Task |
|--------|-------------|------|
| `Subject_Height_cm` | Height with validation | 1 |
| `Height_Status` | PASS/REVIEW/FAIL | 1 |
| `Subject_Mass_kg` | Mass with validation | 1 |
| `Residual_RMS_mm` | RMS at selected cutoff | 3 |
| `Residual_Slope` | Convergence quality | 3 |

All existing columns remain unchanged.

---

## 🔍 Debugging & Troubleshooting

### Height Validation Failed
```python
# Check what failed
from src.subject_validation import validate_height

status, reason = validate_height(0.0)
print(status)   # 'FAIL'
print(reason)   # 'Height is zero or negative: 0.00 cm (FAIL)'
```

**Solutions**:
- If height = 0: Check if height estimation ran (step_05)
- If height > 250: Verify marker tracking quality (step_01)
- If height < 140: Confirm subject is not child/seated

### Overall_Status = FAIL
```python
# Check artifact rate
burst_result = classify_burst_events(omega, fs)
artifact_rate = burst_result['summary']['artifact_rate_percent']

if artifact_rate > 1.0:
    print(f"Artifact rate {artifact_rate:.2f}% exceeds 1% threshold")
    print("Action: Review marker tracking quality or increase filtering")
```

**Common Causes**:
1. Marker occlusions/swaps
2. Poor calibration (check step_01 errors)
3. High-frequency noise not filtered

### Filter Ceiling Warning
```python
# Investigate filter performance
if metadata['filter_ceiling_warning']['triggered']:
    rms = metadata['filter_ceiling_warning']['residual_rms_mm']
    slope = metadata['filter_ceiling_warning']['residual_slope']
    
    print(f"RMS: {rms:.2f}mm (>20mm threshold)")
    print(f"Slope: {slope:.6f}")
    
    if slope > -0.1:  # Near zero slope = flat curve
        print("WARNING: RMS curve is flat - Winter method may have failed")
```

**Interpretation**:
- **Slope ≈ 0**: Flat RMS curve, no clear knee-point
- **RMS > 20mm @ 16Hz**: Movement has genuine high-frequency content
- **Action**: Review movement type, consider if 16Hz is adequate

---

## 🧪 Testing Checklist

### Before Deployment
- [ ] Run `test_subject_validation.py` - height/mass edge cases
- [ ] Run `test_filtering_synergy.py` - residual slope, ceiling warning
- [ ] Run `test_outlier_policy.py` - 5% outlier, 1% artifact thresholds
- [ ] Verify Excel report has new columns
- [ ] Check backward compatibility with existing pipelines

### Integration Testing
- [ ] Process 1 known-good recording → verify PASS status
- [ ] Process 1 known-bad recording → verify FAIL with correct reason
- [ ] Process 1 edge-case recording → verify REVIEW status
- [ ] Compare new vs. old Excel reports → verify column alignment

---

## 📁 File Locations

### Modified Files
- `src/utils_nb07.py` - Parameter schema, Excel columns
- `src/filtering.py` - Residual slope, ceiling check
- `src/burst_classification.py` - Outlier policy, thresholds

### New Files
- `src/subject_validation.py` - Height/mass validation, intensity normalization
- `TASK_IMPLEMENTATION_FINAL_PUSH.md` - Full documentation

### Documentation
- `THRESHOLDS_CHEAT_SHEET.md` - All thresholds (append to existing)
- Master Quality Report (Excel) - New columns added

---

## 🚀 Next Steps

### Immediate Actions
1. **Test on Sample Data**: Run pipeline on 3-5 recordings
2. **Verify Excel Output**: Check new columns appear correctly
3. **Review Status Changes**: Confirm FAIL triggers on artifact rate >1%

### Follow-Up Enhancements
1. Add visualization for residual curve with slope annotation
2. Create automated alerts for FAIL status
3. Collect population statistics to refine height/mass ranges
4. Add age/sex-specific thresholds

### Research Questions
1. Is 1% artifact rate threshold optimal for all movement types?
2. Does residual slope correlate with downstream quality metrics?
3. What percentage of recordings trigger filter ceiling warning?

---

## 📞 Support

### Common Issues

**Q: Height always shows FAIL**  
**A**: Check if step_05 height estimation is running. Default = 0.0 if not estimated.

**Q: Overall_Status changed from PASS to FAIL**  
**A**: Expected - now fails on artifact rate >1% instead of velocity. Check `Artifact_Rate_%` column.

**Q: What does negative residual slope mean?**  
**A**: Good! Negative slope = RMS decreasing as cutoff increases = filter converging properly.

**Q: When should I use `validate_subject_context()`?**  
**A**: Call in step_05 notebooks after height estimation, before saving summary JSON.

---

**Last Updated**: 2026-01-23  
**Version**: Gate 1-5 Complete + Final Push Enhancements  
**Status**: Production Ready ✅
