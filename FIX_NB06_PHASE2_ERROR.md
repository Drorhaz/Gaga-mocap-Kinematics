# Fix for Notebook 06 Phase 2 Error

## Problem

```python
NameError: name 'path_lengths_sorted' is not defined
```

**Root Cause:** Cells were in wrong order:
- Cell 13: Tries to export `path_lengths_sorted` and `bilateral_symmetry`
- Cells 15-16: Define these variables
- **Error:** Can't use variables before they're defined!

## Solution Applied

**Merged Phase 2 computation INTO cell 13** (at the beginning, before it's used).

Now cell 13 structure is:
1. **Phase 2 computation** (path length + bilateral symmetry)
2. **Outlier validation export**
3. **Validation report update**

## What to Do

### Option 1: Delete Old Cells 14-16 (Recommended)

Since Phase 2 code is now in cell 13, cells 14-16 are duplicates and should be deleted:

**In Jupyter/VSCode:**
1. Click on cell 14 (markdown header "Phase 2")
2. Press `DD` (delete) or click the trash icon
3. Repeat for cells 15 and 16

### Option 2: Leave Them (Will Cause No Errors)

The duplicate cells won't break anything, but they're redundant. The notebook will:
- Run Phase 2 computation in cell 13 ✅
- Run it again in cells 15-16 (harmless but wasteful)

## Testing

```bash
# 1. Open notebook 06
# 2. Restart kernel
# 3. Run all cells
# Expected: No errors, Phase 2 metrics exported to validation_report.json
```

## Verification

After running, check that `validation_report.json` contains:
```json
{
  "path_length_m": { ... },
  "bilateral_symmetry": { ... }
}
```

## Files Modified

- `notebooks/06_ultimate_kinematics.ipynb` - Cell 13 updated with Phase 2 computation

---

**Status:** Fixed! You can now run notebook 06 without errors.
