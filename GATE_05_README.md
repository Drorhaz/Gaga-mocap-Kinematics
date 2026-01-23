# Gate 5 Data Disconnect - Resolution Summary

## The Issue
Quality Report shows **0 for all burst metrics** despite detecting thousands of outliers.

## The Cause  
Gate 5 burst classification cell wasn't executed for any recordings.

## The Solution
Run the "GATE 4 & 5 INTEGRATION" cell in notebook 06 for each of 33 recordings.

---

## Quick Fix (3 steps)

### Step 1: Check Status
```bash
python verify_gate5_data.py
```

### Step 2: Process Recordings  
For each recording (list from step 1):
1. Open `notebooks/06_rotvec_omega.ipynb`
2. Set `RUN_ID = "recording_name"`
3. Run the "GATE 4 & 5 INTEGRATION" cell
4. Verify output shows event counts

### Step 3: Update Report
1. Open `notebooks/07_master_quality_report.ipynb`  
2. Run all cells
3. Check Excel: burst columns should have non-zero values

**Time:** ~25 minutes total

---

## Files Created

| File | Purpose |
|------|---------|
| `verify_gate5_data.py` | Check which recordings need processing |
| `test_gate5_structure.py` | Show expected data structure |
| `GATE_05_QUICK_FIX.md` | Quick reference guide |
| `GATE_05_DATA_DISCONNECT_FIX.md` | Technical details |
| `docs/quality_control/GATE_05_COMPLETE_GUIDE.md` | Complete walkthrough |

---

## What Gets Fixed

**Before:**
- Step 07 Excel: `Burst_Artifact_Count = 0`, `Burst_Count = 0`, `Burst_Flow_Count = 0`
- Step 06 JSON: Missing `step_06_burst_analysis` field

**After:**  
- Step 07 Excel: Real counts (e.g., 234 artifacts, 45 bursts, 12 flows)
- Step 06 JSON: Contains complete burst classification data
- New file: `{RUN_ID}__joint_status_mask.parquet` (per-frame status codes)

---

## The 3 Tiers

| Tier | Duration | What | Action |
|------|----------|------|--------|
| 1 - ARTIFACT | <25ms (1-3 frames) | Sensor glitch | **EXCLUDE** |
| 2 - BURST | 33-58ms (4-7 frames) | Rapid movement | **REVIEW** |
| 3 - FLOW | >65ms (8+ frames) | Sustained Gaga | **ACCEPT** |

---

## Documentation Hierarchy

1. **START HERE:** This file (`README.md`)
2. **Quick Fix:** `GATE_05_QUICK_FIX.md` - Concise instructions
3. **Complete Guide:** `docs/quality_control/GATE_05_COMPLETE_GUIDE.md` - Full walkthrough
4. **Technical Details:** `GATE_05_DATA_DISCONNECT_FIX.md` - Architecture & data flow

---

## Verification Checklist

- [ ] Run `python verify_gate5_data.py` → Shows 0/33 recordings
- [ ] Process all 33 recordings (Gate 5 cell)
- [ ] Run `python verify_gate5_data.py` → Shows 33/33 recordings ✅
- [ ] Re-run notebook 07 (Master Quality Report)
- [ ] Check Excel: Burst columns show non-zero values ✅
- [ ] Done! 🎉

---

## Need Help?

**Check status:**
```bash
python verify_gate5_data.py
```

**See expected data structure:**
```bash
python test_gate5_structure.py
```

**Read full guide:**
```bash
# Windows
start docs/quality_control/GATE_05_COMPLETE_GUIDE.md

# Mac/Linux  
open docs/quality_control/GATE_05_COMPLETE_GUIDE.md
```

---

**Created:** 2026-01-23  
**Current Status:** 0/33 recordings processed  
**Estimated Time to Fix:** 25-30 minutes  
**Impact:** All burst metrics will be populated in Quality Report
