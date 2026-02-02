# Notebook 06 Output Directory Configuration - Validation Report

## Current Configuration

### Code (Cell 1):
```python
OUT_DIR = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_06_kinematics", "ultimate")
```

### Actual Path:
```
derivatives/step_06_kinematics/ultimate/
```

### Files that WILL be saved:
1. `{RUN_ID}__kinematics_master.parquet` - Main output file with all features
2. `{RUN_ID}__validation_report.json` - Validation metrics and quality report
3. `{RUN_ID}__outlier_validation.json` - 3-tier outlier frame counts

---

## Current Status

### Directory Structure:
```
derivatives/
└── step_06_kinematics/
    ├── ultimate/                                    ← CURRENT: Subdirectory (doesn't exist yet)
    │   ├── {RUN_ID}__kinematics_master.parquet    ← Will be saved here
    │   ├── {RUN_ID}__validation_report.json       ← Will be saved here
    │   └── {RUN_ID}__outlier_validation.json      ← Will be saved here
    │
    ├── {RUN_ID}__validation_report.json           ← EXISTING (old files?)
    └── {RUN_ID}__outlier_validation.json          ← EXISTING (old files?)
```

**Note:** The two JSON files in `step_06_kinematics/` (not in `ultimate/`) appear to be from a previous run or different workflow.

---

## Option Analysis

### **OPTION 1: Keep Current Structure (with "ultimate" subdirectory)**

**Path:** `derivatives/step_06_kinematics/ultimate/`

**Advantages:**
- ✅ Separates this "ultimate" gold-standard pipeline from other potential step_06 outputs
- ✅ If you have multiple step_06 variants (e.g., "basic", "ultimate", "minimal"), they won't conflict
- ✅ Clear semantic meaning: "ultimate" = production-grade gold standard
- ✅ Easier to version different approaches (step_06_kinematics/v1/, v2/, ultimate/)

**Disadvantages:**
- ❌ Extra directory level (slightly deeper path)
- ❌ Not consistent with other steps if they save directly to step_XX directories

**Example full path:**
```
derivatives/step_06_kinematics/ultimate/734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002__kinematics_master.parquet
```

---

### **OPTION 2: Save Directly to step_06_kinematics/**

**Path:** `derivatives/step_06_kinematics/`

**Advantages:**
- ✅ Flatter structure (one less directory level)
- ✅ Consistent with other pipeline steps if they save directly to step_XX/
- ✅ Simpler paths
- ✅ Files are immediately visible when browsing step_06_kinematics/

**Disadvantages:**
- ❌ If you ever add other step_06 variants, files will mix together
- ❌ Loses semantic separation of "ultimate" vs other approaches
- ❌ All step_06 files in one directory (could get cluttered)

**Example full path:**
```
derivatives/step_06_kinematics/734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002__kinematics_master.parquet
```

---

## Recommendation

Based on your file naming and the fact that existing JSON files are in the root `step_06_kinematics/`, I see two patterns:

**Pattern in your codebase:**
- You already have files in `derivatives/step_06_kinematics/` (the 2 JSON files)
- This suggests you may have been saving directly without subdirectories

**My recommendation: OPTION 2 - Save directly to `step_06_kinematics/`**

**Reasoning:**
1. **Consistency:** Your existing files are already there
2. **Simplicity:** One less directory to navigate
3. **Standard pattern:** Most pipeline steps likely save to `derivatives/step_XX/` directly
4. **File naming handles versioning:** Your filename already has `RUN_ID` which uniquely identifies the run

---

## Required Change

If you want to save directly to `step_06_kinematics/` (OPTION 2):

**Change this line in Cell 1:**

**FROM:**
```python
OUT_DIR = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_06_kinematics", "ultimate")
```

**TO:**
```python
OUT_DIR = os.path.join(PROJECT_ROOT, CONFIG['derivatives_dir'], "step_06_kinematics")
```

**Also update the markdown description in Cell 0:**

**FROM:**
```markdown
**Outputs:** `derivatives/step_06_kinematics/ultimate/{RUN_ID}__kinematics_master.parquet`
```

**TO:**
```markdown
**Outputs:** `derivatives/step_06_kinematics/{RUN_ID}__kinematics_master.parquet`
```

---

## What to Tell Me

Please confirm your preference:

**A)** Keep current structure with `/ultimate/` subdirectory
**B)** Change to save directly to `step_06_kinematics/` (RECOMMENDED based on existing files)

Once you decide, I can make the change if needed.
