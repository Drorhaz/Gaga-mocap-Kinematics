# Gate 5 Quick Reference: Fixing the Data Disconnect

## TL;DR - The Problem
Step 06 JSON files are missing burst classification data → Step 07 reports show 0 for all burst metrics

## TL;DR - The Solution
Run the "GATE 4 & 5 INTEGRATION" cell in notebook `06_rotvec_omega.ipynb` for each recording

---

## Verification Status (Run: `python verify_gate5_data.py`)

Current status: **0/33 recordings have Gate 5 data (0%)**

All 33 recordings need processing.

---

## Step-by-Step Fix Instructions

### For EACH of the 33 recordings:

1. **Open notebook:** `notebooks/06_rotvec_omega.ipynb`

2. **Set the RUN_ID** (Cell 1):
   ```python
   RUN_ID = "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM"  # Example
   ```

3. **Run ONLY the Gate 4 & 5 cell** (search for "GATE 4 & 5 INTEGRATION"):
   - This is usually one of the last cells in the notebook
   - Look for: `from burst_classification import classify_burst_events`
   - Runtime: ~10-30 seconds per recording

4. **Verify success** - Cell output should show:
   ```
   🚦 GATE 5 (Burst Classification): ACCEPT_HIGH_INTENSITY (or REVIEW/REJECT)
      Total Events: XXX
      - Artifacts (Tier 1): XXX
      - Bursts (Tier 2): XXX
      - Flows (Tier 3): XXX
   ```

5. **Check the JSON** (optional):
   ```python
   import json
   with open(f"derivatives/step_06_kinematics/{RUN_ID}__kinematics_summary.json") as f:
       data = json.load(f)
   print('step_06_burst_analysis' in data)  # Should print: True
   ```

### After Processing All Recordings:

1. **Re-run verification:**
   ```bash
   python verify_gate5_data.py
   ```
   Expected: `[OK] All recordings have Gate 5 data!`

2. **Re-run Master Quality Report:**
   - Open: `notebooks/07_master_quality_report.ipynb`
   - Run all cells
   - Check output Excel: `reports/Master_Audit_Log_*.xlsx`

3. **Verify burst metrics are populated:**
   - Open the Excel file
   - Look at columns: `Burst_Artifact_Count`, `Burst_Count`, `Burst_Flow_Count`
   - Values should no longer be all zeros

---

## What This Fix Does

### Data Generated (Step 06)
The Gate 5 cell creates:
- **JSON fields** added to kinematics summary:
  - `step_06_burst_analysis`: Event counts and statistics
  - `step_06_burst_decision`: Overall quality decision
  - `step_06_frames_to_exclude`: Artifact frames (Tier 1)
  - `step_06_frames_to_review`: Burst/Flow frames (Tier 2/3)

- **Parquet file**: `{RUN_ID}__joint_status_mask.parquet`
  - Per-frame, per-joint status codes (0=Normal, 1=Artifact, 2=Burst, 3=Flow)

### Data Consumed (Step 07)
The Master Quality Report extracts from Step 06 JSON:
- Event counts (artifacts, bursts, flows)
- Frame statistics (artifact rate %, outlier %)
- Timing metrics (event duration, density)
- Decision status (ACCEPT/REVIEW/REJECT)

These populate the Excel columns:
- `Burst_Artifact_Count`
- `Burst_Count`
- `Burst_Flow_Count`
- `Burst_Total_Events`
- `Artifact_Rate_%`
- `Max_Consecutive_Frames`
- `Mean_Event_Duration_ms`
- `Burst_Decision`
- `Artifact_Frame_Ranges`
- `Burst_Frame_Ranges`

---

## Understanding the Status Mask Codes

| Code | Name | Duration | Meaning | Action |
|------|------|----------|---------|--------|
| 0 | NORMAL | N/A | Clean data | INCLUDE in all statistics |
| 1 | ARTIFACT | 1-3 frames (<25ms) | Physically impossible spike | EXCLUDE from statistics |
| 2 | BURST | 4-7 frames (33-58ms) | Potential whip/shake | REVIEW, but INCLUDE |
| 3 | FLOW | 8+ frames (>65ms) | Sustained Gaga movement | ACCEPT, INCLUDE |

**Key Point:** Only Tier 1 (ARTIFACT) is excluded from statistics. Bursts and Flows are legitimate data that may be high-velocity but are intentional movements.

---

## Batch Processing Tip

If you want to process all recordings in sequence, create a simple script:

```python
import os
import json

# List all recordings
recordings = [
    "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM",
    "734_T1_P2_R1_Take 2025-12-01 02.28.24 PM",
    # ... add all 33 ...
]

# For each, you'll need to manually:
# 1. Set RUN_ID in notebook
# 2. Run Gate 4 & 5 cell
# 3. Verify output

print("Recordings to process:")
for i, rid in enumerate(recordings, 1):
    print(f"{i:2d}. {rid}")
```

**Note:** Jupyter notebooks don't support easy batch execution of individual cells, so this must be done manually for now.

---

## Expected Timeline

- **Per recording:** ~30 seconds (Gate 5 cell execution)
- **Total for 33 recordings:** ~15-20 minutes (manual cell execution)
- **Master Quality Report:** ~30 seconds (re-run notebook 07)

---

## Troubleshooting

### "NameError: name 'burst_classification' is not defined"
- Make sure you're running the correct cell (look for the import statement)
- Ensure `src/burst_classification.py` exists

### "FileNotFoundError: kinematics_summary.json"
- The base Step 06 processing wasn't completed
- Run the full notebook 06 first (all cells before Gate 4 & 5)

### "IndexError: list index out of range"
- Angular velocity data might be missing
- Check that earlier cells (omega computation) ran successfully

### Verification script shows 0/33 after processing
- Check JSON files manually: look for `step_06_burst_analysis` key
- Verify you saved the notebook after running Gate 5 cell
- Ensure the correct RUN_ID was used

---

## Quick Checklist

- [ ] Run `python verify_gate5_data.py` (initial check)
- [ ] Process all 33 recordings (Gate 5 cell)
- [ ] Run `python verify_gate5_data.py` (verification - should show 33/33)
- [ ] Re-run notebook 07 (Master Quality Report)
- [ ] Check Excel output for non-zero burst metrics
- [ ] Celebrate! 🎉

---

**Last Updated:** 2026-01-23  
**Script Location:** `verify_gate5_data.py`  
**Full Documentation:** `GATE_05_DATA_DISCONNECT_FIX.md`
