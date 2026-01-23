# Gate 5 Data Disconnect - Complete Resolution Guide

## Executive Summary

**Problem:** The Master Quality Report (Step 07) shows **0 for all burst metrics** despite Step 06 detecting thousands of outlier frames.

**Root Cause:** The Gate 5 burst classification cell in notebook `06_rotvec_omega.ipynb` was not executed for any of the 33 recordings. The data exists in the pipeline logic but hasn't been generated yet.

**Solution:** Execute the "GATE 4 & 5 INTEGRATION" cell for each of the 33 recordings to populate the burst analysis fields in Step 06 JSON files.

**Status:** 0/33 recordings currently have Gate 5 data (verified 2026-01-23)

---

## Quick Start

### 1. Verify Current Status
```bash
python verify_gate5_data.py
```

Expected output: Shows 0/33 recordings with Gate 5 data

### 2. Process Each Recording

For each recording, follow `GATE_05_QUICK_FIX.md`:

1. Open `notebooks/06_rotvec_omega.ipynb`
2. Set `RUN_ID` to the recording identifier
3. Run the "GATE 4 & 5 INTEGRATION" cell (search for it in the notebook)
4. Verify output shows burst classification results

### 3. Verify Completion
```bash
python verify_gate5_data.py
```

Expected output: Should show 33/33 recordings with Gate 5 data

### 4. Update Master Quality Report

1. Open `notebooks/07_master_quality_report.ipynb`
2. Run all cells
3. Check the Excel output: `reports/Master_Audit_Log_*.xlsx`
4. Verify burst metric columns are populated with non-zero values

---

## Understanding the Issue

### The Architecture

```
Step 06 (Processing)                  Step 07 (Reporting)
───────────────────                   ───────────────────
                                      
notebook 06_rotvec_omega.ipynb        notebook 07_master_quality_report.ipynb
  ├─ Compute angular velocity           ├─ Load JSON files
  ├─ Detect outliers (metrics)          ├─ Extract metrics
  └─ Gate 5 Cell (MISSING!)             └─ Generate Excel report
       ├─ classify_burst_events()            ├─ Burst_Artifact_Count → 0 ❌
       ├─ Saves to JSON:                     ├─ Burst_Count → 0 ❌
       │  └─ step_06_burst_analysis          └─ Burst_Flow_Count → 0 ❌
       └─ Saves mask parquet
```

### What's Missing

The Gate 5 cell creates these JSON fields in Step 06:
- `step_06_burst_analysis` - Event counts and statistics
- `step_06_burst_decision` - Quality decision
- `step_06_frames_to_exclude` - Artifact frames
- `step_06_frames_to_review` - Burst/flow frames
- `step_06_data_validity` - Usability assessment

Step 07 expects these fields and shows 0 when they're missing.

### Why It's Missing

The Gate 5 implementation was added to the pipeline after most recordings were processed. The recordings need to be re-processed through just the Gate 5 cell to add this data to their JSON files.

---

## The 3-Tier Classification System

Gate 5 classifies high-velocity events by **duration**:

### Tier 1: ARTIFACT (1-3 frames, <25ms)
- **Physical interpretation:** Sensor glitch, momentary occlusion, tracking error
- **Velocity:** Often exceeds 2000 deg/s
- **Action:** **EXCLUDE** from all statistics
- **Why:** Physically impossible for human joints to sustain

### Tier 2: BURST (4-7 frames, 33-58ms)
- **Physical interpretation:** Rapid directional change, whip movement, sudden shake
- **Velocity:** 2000-5000 deg/s
- **Action:** **INCLUDE** but flag for review
- **Why:** Possible but uncommon, may be intentional Gaga technique

### Tier 3: FLOW (8+ frames, >65ms)
- **Physical interpretation:** Sustained high-intensity movement
- **Velocity:** >2000 deg/s sustained
- **Action:** **ACCEPT** as legitimate movement
- **Why:** Characteristic of Gaga's continuous exploration

---

## Verification Tools

### Tool 1: `verify_gate5_data.py`
**Purpose:** Check which recordings have Gate 5 data

**Usage:**
```bash
python verify_gate5_data.py
```

**Output:**
- List of recordings WITH Gate 5 data (with event counts)
- List of recordings MISSING Gate 5 data
- Summary statistics
- Action items

**Exit codes:**
- 0: All recordings have Gate 5 data
- 1: Some recordings missing Gate 5 data

### Tool 2: `test_gate5_structure.py`
**Purpose:** Show expected data structure and field mapping

**Usage:**
```bash
python test_gate5_structure.py
```

**Output:**
- Mock JSON structure with all Gate 5 fields
- Field explanations
- Tier classification logic
- Mapping to Step 07 Excel columns
- Verification instructions

---

## Step-by-Step Processing Guide

### Phase 1: Preparation (5 minutes)

1. **Backup existing data** (optional but recommended):
   ```bash
   cp -r derivatives/step_06_kinematics derivatives/step_06_kinematics_backup
   ```

2. **Get the list of recordings to process**:
   ```bash
   python verify_gate5_data.py > gate5_todo.txt
   ```

3. **Review the list** - You should see 33 recordings

### Phase 2: Processing (15-20 minutes)

For **each** of the 33 recordings:

1. **Copy the RUN_ID** from the verification script output
   
2. **Open notebook:** `notebooks/06_rotvec_omega.ipynb`

3. **Update Cell 1** - Set the RUN_ID:
   ```python
   RUN_ID = "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM"
   ```

4. **Find the Gate 5 cell** - Search for: "GATE 4 & 5 INTEGRATION"
   - Or search for: `from burst_classification import`

5. **Run ONLY that cell** (Shift+Enter)

6. **Verify the output** - Should show:
   ```
   GATE 4 & 5 INTEGRATION
   ══════════════════════
   
   🚦 GATE 5 (Burst Classification): ACCEPT_HIGH_INTENSITY
      Total Events: XXX
      - Artifacts (Tier 1): XXX
      - Bursts (Tier 2): XXX  
      - Flows (Tier 3): XXX
   ```

7. **Check files created:**
   - JSON updated: `derivatives/step_06_kinematics/{RUN_ID}__kinematics_summary.json`
   - Mask created: `derivatives/step_06_kinematics/{RUN_ID}__joint_status_mask.parquet`

8. **Move to next recording** - Repeat steps 1-7

### Phase 3: Verification (2 minutes)

1. **Run verification script:**
   ```bash
   python verify_gate5_data.py
   ```

2. **Expected output:**
   ```
   [OK] With Gate 5 Data: 33 (100.0%)
   [MISSING] Missing Gate 5: 0 (0.0%)
   
   [OK] All recordings have Gate 5 data!
   ```

3. **Review summary statistics:**
   - Total Artifacts (Tier 1): Should be in hundreds/thousands
   - Total Bursts (Tier 2): Should be tens to hundreds
   - Total Flows (Tier 3): Should be tens
   - Decision Distribution: Should show ACCEPT_HIGH_INTENSITY, REVIEW, etc.

### Phase 4: Update Master Quality Report (2 minutes)

1. **Open notebook:** `notebooks/07_master_quality_report.ipynb`

2. **Run all cells** (Cell → Run All)

3. **Check console output** - Section 6 should now show:
   ```
   SECTION 6: BIOMECHANICS & OUTLIER ANALYSIS
   ══════════════════════════════════════════
   
   Biomechanics Summary:
     Pipeline PASS: 33/33
     Mean Burst Artifact Count: XXX
     Mean Burst Count: XXX
     Mean Flow Count: XXX
   ```

4. **Open the Excel file:** `reports/Master_Audit_Log_*.xlsx`

5. **Verify columns populated:**
   - Navigate to "Quality_Report" sheet
   - Check columns: `Burst_Artifact_Count`, `Burst_Count`, `Burst_Flow_Count`
   - Values should be non-zero for all recordings

---

## Expected Results

### Before Gate 5 Processing

**Step 06 JSON:**
```json
{
  "run_id": "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM",
  "overall_status": "PASS",
  "metrics": { ... },
  "outlier_analysis": {
    "counts": {
      "total_outliers": 2013  ← Outliers detected but not classified!
    }
  }
}
```

**Step 07 Excel (Quality_Report sheet):**
| Run_ID | Burst_Artifact_Count | Burst_Count | Burst_Flow_Count |
|--------|---------------------|-------------|------------------|
| 734_T1_P1 | 0 | 0 | 0 |

### After Gate 5 Processing

**Step 06 JSON:**
```json
{
  "run_id": "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM",
  "overall_status": "PASS",
  "metrics": { ... },
  "outlier_analysis": {
    "counts": {
      "total_outliers": 2013
    }
  },
  "step_06_burst_analysis": {  ← NEW!
    "classification": {
      "artifact_count": 234,
      "burst_count": 45,
      "flow_count": 12,
      "total_events": 291
    },
    "frame_statistics": {
      "artifact_rate_percent": 1.84
    }
  },
  "step_06_burst_decision": {  ← NEW!
    "overall_status": "ACCEPT_HIGH_INTENSITY"
  }
}
```

**Step 07 Excel (Quality_Report sheet):**
| Run_ID | Burst_Artifact_Count | Burst_Count | Burst_Flow_Count |
|--------|---------------------|-------------|------------------|
| 734_T1_P1 | 234 | 45 | 12 |

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'burst_classification'"

**Cause:** Import path issue

**Solution:**
```python
# In the notebook, ensure this is at the top:
import sys
import os
if os.path.basename(os.getcwd()) == 'notebooks':
    PROJECT_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
else:
    PROJECT_ROOT = os.path.abspath(os.getcwd())
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
```

### Issue: Cell runs but no Gate 5 fields in JSON

**Possible causes:**
1. Cell crashed silently - check for error messages
2. JSON file not saved - check file timestamp
3. Wrong RUN_ID - verify it matches the recording you intended

**Solution:**
```python
# Manually verify the JSON was updated:
import json
json_path = f"derivatives/step_06_kinematics/{RUN_ID}__kinematics_summary.json"
with open(json_path) as f:
    data = json.load(f)
print('step_06_burst_analysis' in data)  # Should be True
```

### Issue: "No angular velocity data available"

**Cause:** Earlier notebook cells weren't run

**Solution:** Run the full notebook 06 from the beginning, not just the Gate 5 cell

### Issue: Verification script still shows missing after processing

**Possible causes:**
1. Wrong RUN_ID was used
2. JSON wasn't saved properly
3. Processing a different recording than intended

**Solution:**
1. Manually check the JSON file
2. Compare RUN_ID in notebook vs. verification script
3. Re-run the Gate 5 cell with correct RUN_ID

---

## File Reference

### Created Files
- `GATE_05_DATA_DISCONNECT_FIX.md` - Detailed technical explanation
- `GATE_05_QUICK_FIX.md` - Quick reference guide (this file)
- `verify_gate5_data.py` - Verification script
- `test_gate5_structure.py` - Data structure reference
- `docs/examples/mock_gate5_kinematics_summary.json` - Example JSON

### Modified Files
- **None** - All fixes involve running existing cells in notebook 06

### Generated Data (per recording)
- `{RUN_ID}__kinematics_summary.json` - Updated with Gate 5 fields
- `{RUN_ID}__joint_status_mask.parquet` - Per-frame status codes

---

## Timeline Estimate

| Phase | Duration | Description |
|-------|----------|-------------|
| Preparation | 5 min | Run verification, review list |
| Processing | 15-20 min | Process all 33 recordings (30 sec each) |
| Verification | 2 min | Re-run verification script |
| Master Report | 2 min | Update Step 07 Excel output |
| **Total** | **25-30 min** | **Complete fix** |

---

## Success Criteria

✅ **Verification script shows:** `[OK] All recordings have Gate 5 data!`

✅ **Step 06 JSON files contain:** `step_06_burst_analysis` field

✅ **Parquet mask files exist:** `{RUN_ID}__joint_status_mask.parquet`

✅ **Step 07 Excel shows:** Non-zero values in burst metric columns

✅ **Quality Report summary:** Mean burst counts > 0

---

## Contact & Support

**Documentation:**
- Full technical details: `GATE_05_DATA_DISCONNECT_FIX.md`
- Quick reference: `GATE_05_QUICK_FIX.md`
- Data structure: Run `python test_gate5_structure.py`

**Verification:**
- Check status: `python verify_gate5_data.py`
- View progress: Compare current count vs. 33 total

**References:**
- Gate 5 module: `src/burst_classification.py`
- Notebook cell: Search for "GATE 4 & 5 INTEGRATION"
- Report builder: `src/utils_nb07.py` lines 864-885

---

**Last Updated:** 2026-01-23  
**Version:** 1.0  
**Status:** Complete - Ready for user execution
