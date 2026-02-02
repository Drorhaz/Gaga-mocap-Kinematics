# Notebook 06 Output Directory - CHANGE COMPLETE

## Changes Made

### 1. Updated Cell 0 (Markdown Header)
**FROM:**
```markdown
**Outputs:** `derivatives/step_06_kinematics/ultimate/{RUN_ID}__kinematics_master.parquet`
```

**TO:**
```markdown
**Outputs:** `derivatives/step_06_kinematics/{RUN_ID}__kinematics_master.parquet`
```

### 2. Updated Cell 1 (Python Code)
**FROM:**
```python
OUT_DIR = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_06_kinematics", "ultimate")
```

**TO:**
```python
OUT_DIR = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_06_kinematics")
```

---

## New Output Structure

All files will now be saved directly to:
```
derivatives/step_06_kinematics/
```

### Files that will be created:
```
derivatives/step_06_kinematics/
├── {RUN_ID}__kinematics_master.parquet        ← Main feature file
├── {RUN_ID}__validation_report.json           ← Quality metrics
└── {RUN_ID}__outlier_validation.json          ← 3-tier outlier counts
```

### Example with your current run:
```
derivatives/step_06_kinematics/
├── 734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002__kinematics_master.parquet
├── 734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002__validation_report.json
└── 734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002__outlier_validation.json
```

---

## Status

✅ **COMPLETE** - Changes applied to notebook

**Next Steps:**
1. Restart kernel in Jupyter
2. Run all cells
3. Files will be saved to `derivatives/step_06_kinematics/` (no subdirectory)

---

## Benefits of This Change

1. ✅ **Consistency** - Matches your existing file pattern (the 2 JSON files already there)
2. ✅ **Simplicity** - Flatter directory structure
3. ✅ **Easier navigation** - Files immediately visible when browsing step_06_kinematics/
4. ✅ **Standard pattern** - Follows typical pipeline conventions (step_XX directories)

---

## Note

If you had previously created the `ultimate/` subdirectory, it will remain empty and can be safely deleted.
