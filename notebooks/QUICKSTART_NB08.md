# Quick Start: Engineering Physical Audit (NB08)

**Ready to run in 3 steps!**

---

## Step 1: Open the Notebook

### Option A: Jupyter Notebook
```bash
cd c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\notebooks
jupyter notebook 08_engineering_physical_audit.ipynb
```

### Option B: VSCode/Cursor
1. Open file: `notebooks/08_engineering_physical_audit.ipynb`
2. Select Python kernel
3. Click "Run All"

---

## Step 2: What You'll See

**Section-by-Section Output:**

### ✅ Methodology Passport
```
📐 Rotation Interpolation: SLERP
   Formula: q(t) = sin((1-t)θ)/sin(θ) · q₀ + sin(tθ)/sin(θ) · q₁
   Constraint: Unit quaternion: ||q|| = 1

🔄 Angular Velocity: Quaternion Derivative
   Formula: ω = 2 · (dq/dt) · q*

🔄 Angular Acceleration: Savitzky-Golay Filter
   Window: 0.175s (21 frames @ 120Hz)
   Polynomial Order: 3
```

### ✅ Capture Baseline
```
Recording Duration:
  Total: 1308.6 seconds (21.8 minutes)
  Mean: 261.7 seconds

Raw Data Completeness:
  Pristine (0% missing): 5/5 recordings
  Mean Missing: 0.000%

Inherent Signal Quality (Pre-Processing SNR):
  Mean SNR: 47.9 dB
  Interpretation: EXCELLENT - Publication-quality capture
```

### ✅ Structural Integrity
```
Bone Length Coefficient of Variation:
  Mean CV: 0.398%

Worst Bone Segments:
  Hips->Spine: 5 recordings, Mean CV = 0.404%
  
Static Pose Calibration Offsets:
  Left Arm Mean: 6.67°
  Right Arm Mean: 7.12°
```

### ✅ Per-Joint Noise Profile
```
Noise Locality Index: 2.3
Interpretation: MEDIUM - Regional problem (e.g., one limb)

Classification Summary:
  Clean: 16 joints
  Sporadic_Glitches: 2 joints
  Artifact_Detected: 1 joint
```

---

## Step 3: Check Your Output

### Excel File Created
```
reports/Engineering_Audit_20260129_HHMMSS.xlsx
```

**Sheet 1: Engineering_Profile**
- 5 rows (one per recording)
- 62 columns (pure measurements)
- NO quality scores
- NO decision labels

**Sheet 2: Methodology_Passport**
- Mathematical formulas
- Processing parameters
- Reference documentation

---

## Expected Results (5 Recordings)

| Metric | Expected Value |
|--------|---------------|
| Total Recordings | 5 |
| Mean Duration | ~260 seconds |
| Raw Missing % | 0.0% (all pristine) |
| Mean SNR | ~48 dB (EXCELLENT) |
| Mean Bone CV | ~0.4% (research-grade) |
| Worst Bone | Hips→Spine (physiological) |
| Mean Artifact Rate | <0.1% |
| Data Retained | >99.9% |

---

## Troubleshooting

### Problem: Import Error
```python
ModuleNotFoundError: No module named 'utils_nb07'
```

**Fix:**
```python
import sys
sys.path.insert(0, "c:/Users/drorh/OneDrive - Mobileye/Desktop/gaga/src")
```

### Problem: No Runs Found
```
Complete runs: 0
```

**Fix:** Check derivatives folder has step_01 through step_06 for each run:
```bash
ls derivatives/step_01_parse/*.json
ls derivatives/step_06_kinematics/ultimate/*.json
```

### Problem: Path Length Shows 0.0
```
Path_Length_Hips_mm: 0.0
```

**Expected:** This is a known gap (Phase 2). Notebook displays warning:
```
⚠️ Path Length: Not computed in current pipeline version
```

---

## What's Different from Notebook 07?

| Feature | NB07 | NB08 |
|---------|------|------|
| Quality Score | ✅ 93.2/100 | ❌ Not computed |
| Research Decision | ✅ ACCEPT | ❌ Not computed |
| Bone CV% | ✅ 0.398% (GOLD) | ✅ 0.398% (no label) |
| Max Velocity | ✅ 1992 deg/s (HIGH) | ✅ 1992 deg/s (no label) |
| Methodology | ❌ Not shown | ✅ Full formulas |
| Per-Joint Profile | ❌ Not shown | ✅ Detailed table |

**Philosophy:** NB08 gives you the raw numbers, YOU decide what they mean.

---

## Next Steps

After successful run:

1. ✅ Open Excel file and review Engineering_Profile sheet
2. ✅ Check Methodology_Passport sheet has formulas
3. ✅ Compare with NB07 output (if available)
4. ✅ Identify any sessions with unusual patterns

**Phase 2 (Future):**
- Fix Path Length computation
- Add Bilateral Symmetry
- Enhance per-bone CV% reporting

---

## Support

**Documentation:**
- Full guide: `notebooks/README_NB08_ENGINEERING_AUDIT.md`
- Implementation: `docs/PHASE_1_IMPLEMENTATION_SUMMARY.md`
- Code reference: `src/utils_nb07.py` (see `METHODOLOGY_PASSPORT`)

**Questions?**
- Check console output for error messages
- Review JSON files in `derivatives/` folder
- Verify all 6 pipeline steps completed for each run

---

**Ready to run!** 🚀
