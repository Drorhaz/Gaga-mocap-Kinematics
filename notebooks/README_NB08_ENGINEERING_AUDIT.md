# Engineering Physical Audit (Notebook 08)

**Status:** ✅ Phase 2 Complete - Path Length & Bilateral Symmetry Added

---

## Overview

`08_engineering_physical_audit.ipynb` is a brand-new notebook that implements a **"Raw Data Only"** philosophy for motion capture quality reporting. It abandons all synthetic scoring and decision logic from notebook 07, providing pure physical measurements and engineering transparency.

### Key Differences from Notebook 07

| Feature | Notebook 07 (Quality Report) | Notebook 08 (Engineering Audit) |
|---------|------------------------------|----------------------------------|
| **Philosophy** | Scoring & Decision | Raw Data Only |
| **Output** | Quality scores (0-100) | Physical measurements |
| **Decision Labels** | ACCEPT/REVIEW/REJECT | None |
| **Grades** | GOLD/SILVER/BRONZE | None |
| **Purpose** | Automated QC pipeline | Researcher transparency |
| **Target Audience** | Pipeline operators | Biomechanists, data scientists |

---

## What Was Implemented (Phase 1)

### 1. Methodology Passport (NEW)

A comprehensive mathematical documentation system hard-coded into `utils_nb07.py`:

```python
METHODOLOGY_PASSPORT = {
    "interpolation": {
        "rotations": {
            "method": "SLERP",
            "formula": "q(t) = sin((1-t)θ)/sin(θ) · q₀ + sin(tθ)/sin(θ) · q₁",
            "constraint": "Unit quaternion: ||q|| = 1",
            ...
        },
        "positions": { ... }
    },
    "differentiation": {
        "angular_velocity": { ... },
        "angular_acceleration": {
            "method": "Savitzky-Golay",
            "window_sec": 0.175,
            "polynomial_order": 3,
            ...
        }
    },
    "filtering": {
        "stage1_artifact_detection": { ... },
        "stage2_hampel": { ... },
        "stage3_adaptive_winter": { ... }
    }
}
```

**Key Documentation:**
- ✅ Quaternion/SLERP formula
- ✅ CubicSpline method
- ✅ Angular velocity: ω = 2 · (dq/dt) · q*
- ✅ Angular acceleration: Savitzky-Golay (window=0.175s, order=3)
- ✅ 3-stage cleaning pipeline details
- ✅ Per-region adaptive Winter filtering

### 2. Engineering Profile Builder (NEW)

Added `build_engineering_profile_row()` to `utils_nb07.py` (parallel to existing `build_quality_row()`):

**What It Extracts:**
- ✅ Data lineage (Run ID, Subject, Session, Pipeline Version)
- ✅ Capture baseline (raw missing %, native SNR, OptiTrack error)
- ✅ Structural integrity (bone CV%, worst bone, skeleton completeness)
- ✅ Calibration offsets (Left/Right arm, reference quality)
- ✅ Signal quality (TRUE RAW SNR per joint)
- ✅ Processing transparency (interpolation methods, filtering mode)
- ✅ 3-stage cleaning metrics (artifact counts, Hampel outliers, Winter cutoffs)
- ✅ Kinematic extremes (peak velocities, accelerations)
- ✅ Outlier distribution (frame counts, tier 1/2/3 events)
- ✅ Data retention (clean statistics after artifact exclusion)

**What It Does NOT Extract:**
- ❌ Quality scores
- ❌ Component scores
- ❌ Decision labels
- ❌ Grade labels
- ❌ Weighted aggregations

### 3. Per-Joint Analysis Functions (NEW)

Added to `utils_nb07.py`:

```python
def extract_per_joint_noise_profile(steps) -> pd.DataFrame:
    """Per-joint outlier profile with classification."""

def extract_bone_stability_profile(steps) -> Dict:
    """Hierarchical bone stability with physiological context."""

def extract_selected_segments(steps) -> List[str]:
    """19 kinematic segments from rotation_alignment_audit."""

def compute_noise_locality_index(profile) -> float:
    """Locality index: max(outlier_pct) / mean(outlier_pct)"""
```

**Noise Classification:**
- **Sporadic Glitches:** Outlier % 0.1-1%, CRITICAL frames = 0
- **Systemic Noise:** Outlier % > 1%, distributed across joints
- **Artifact Detected:** CRITICAL frames > 0
- **Clean:** Outlier % < 0.1%

**Locality Index:**
- **High (>5):** Localized tracking issue in specific joint
- **Medium (2-5):** Regional problem (e.g., one limb)
- **Low (<2):** Systemic noise across skeleton

---

## Notebook Structure

### Section 1: Setup & Data Loading
- Load JSON files from derivatives folder
- Filter to complete runs (step_01 through step_06)
- Build engineering profile DataFrame

### Section 2: Methodology Passport
- Display all mathematical formulas
- Document interpolation methods (SLERP, CubicSpline)
- Detail differentiation methods (quaternion derivatives, Savitzky-Golay)
- Explain 3-stage cleaning pipeline
- Reference alignment procedure

### Section 3: Data Lineage
- Recording provenance (Run ID, Subject, Session)
- Pipeline version
- CSV source file
- Processing timestamp

### Section 4: Capture Baseline Profile
- Raw missing data %
- Native sampling rate
- OptiTrack system error
- TRUE RAW SNR (mean/min/max)
- SNR per-joint counts

### Section 5: Structural Integrity
- Skeleton completeness (segments found/missing)
- Bone length CV% (rigidity measure)
- Worst bone identification
- Subject anthropometry (height, mass)
- Static pose calibration offsets
- Selected kinematic segments (19 joints)

### Section 6: Signal Quality Profile
- TRUE RAW SNR distribution
- SNR interpretation guide (EXCELLENT/GOOD/ACCEPTABLE/POOR)
- Failed joint list

### Section 7: Processing Transparency
- Interpolation methods (positions/rotations)
- Resampling parameters
- Filtering mode
- 3-stage cleaning metrics:
  - Stage 1: Artifact detection counts
  - Stage 2: Hampel outlier counts
  - Stage 3: Winter cutoff frequencies
- Filter residual RMS (price of smoothing)

### Section 8: Kinematic Extremes
- Max angular velocity/acceleration
- Max linear velocity/acceleration
- Path length (if computed)
- Intensity index (if computed)
- Reference values for interpretation

### Section 9: Per-Joint Noise Profile
- Per-joint outlier percentages
- WARNING/ALERT/CRITICAL frame counts
- Noise classification (Sporadic/Systemic/Artifact/Clean)
- Noise locality index

### Section 10: Outlier Distribution
- Total outlier frames
- Max consecutive runs
- Tier 1/2/3 event classification (Artifact/Burst/Flow)
- Data retention after artifact exclusion
- Clean velocity statistics

### Section 11: Excel Export
- Engineering_Profile sheet (all measurements)
- Methodology_Passport sheet (formulas)

---

## Data Availability Assessment

Based on comprehensive JSON analysis:

| Requirement | Status | Notes |
|-------------|--------|-------|
| Quaternion/SLERP doc | ✅ | Hard-coded in METHODOLOGY_PASSPORT |
| Angular accel formula | ✅ | Savitzky-Golay documented |
| 3-stage cleaning | ✅ | Full detail in filtering_summary.json |
| Skeleton hierarchy | ✅ | From skeleton_schema.json |
| Raw Missing % | ✅ | From preprocess_summary.json |
| True Raw SNR | ✅ | From filtering_summary.json |
| Bone CV% | ✅ | From preprocess_summary.json |
| Static Offsets | ✅ | From reference_summary.json |
| Per-joint outliers | ✅ | From outlier_validation.json |
| Winter cutoffs | ✅ | Per-region from filtering_summary.json |
| Path Length | ⚠️ | Shows 0.0 (upstream fix needed) |
| Bilateral Symmetry | ❌ | Not computed (Phase 2) |

---

## Phase 2 Enhancements (Completed: Jan 29, 2026)

### ✅ Path Length Computation
**Status:** IMPLEMENTED  
**Location:** `06_ultimate_kinematics.ipynb` Cell 15  
**Output:** `validation_report.json["path_length_m"]`

**Features:**
- Cumulative 3D distance traveled per segment (in meters)
- Frame-to-frame Euclidean distance calculation
- Sorted by movement intensity (most active segments first)

**New Engineering Columns:**
- `Path_Length_Max_m` - Maximum path length across segments
- `Path_Length_Mean_m` - Average path length
- `Path_Length_Total_m` - Total distance across all segments
- `Most_Active_Segments` - Top 3 most active segments (comma-separated)

### ✅ Bilateral Symmetry Analysis
**Status:** IMPLEMENTED  
**Location:** `06_ultimate_kinematics.ipynb` Cell 16  
**Output:** `validation_report.json["bilateral_symmetry"]`

**Features:**
- Left/Right comparison for 6 limb pairs
- 18 symmetry metrics: path length, max omega, max linear acceleration
- Symmetry Index = 1 - |L - R| / max(L, R)
  - 1.0 = perfect symmetry
  - 0.0 = complete asymmetry

**Bilateral Pairs:**
- upper_arm, forearm, hand
- thigh, shin, foot

**New Engineering Columns:**
- `Bilateral_Symmetry_Mean` - Average symmetry across all metrics
- `Bilateral_Symmetry_Min` - Worst (most asymmetric) pair
- `Most_Asymmetric_Pair` - Identifier of most asymmetric limb

**Testing:**
```bash
python test_phase2_metrics.py
```

**Documentation:** See `docs/PHASE_2_IMPLEMENTATION_SUMMARY.md`

---

## Remaining Gaps (Phase 3 - Future)

### 1. Intensity Index
**Issue:** Not yet computed  
**Proposed Formula:** `path_length / (duration * segment_size)`  
**Purpose:** Normalize path length for movement intensity  
**Timeline:** Phase 3

### 2. Temporal Outlier Visualization  
**Data Available:** Left/Right values exist in static_offset_audit  
**Fix Required:** New computation in `06_rotvec_omega.ipynb`  
**Timeline:** v3.1 enhancement

### 3. Per-Bone CV% Time Series
**Issue:** Only mean CV% reported, not per-bone breakdown  
**Data Available:** `worst_bone` identified, but not individual CV values  
**Fix Required:** Expand `preprocess_summary.json` to include per-bone stats  
**Timeline:** v3.2 enhancement

---

## Usage

### Running the Notebook

```bash
cd notebooks
jupyter notebook 08_engineering_physical_audit.ipynb
```

**Or via VSCode/Cursor:**
1. Open `08_engineering_physical_audit.ipynb`
2. Run All Cells
3. Check `reports/Engineering_Audit_YYYYMMDD_HHMMSS.xlsx`

### Expected Output

```
Engineering DataFrame: 5 runs × 62 measurements

Excel Output:
  Sheet 1: Engineering_Profile (62 columns)
  Sheet 2: Methodology_Passport
```

### Verifying Success

✅ **No errors during cell execution**  
✅ **Excel file created in `reports/` folder**  
✅ **No quality scores in output**  
✅ **No ACCEPT/REVIEW/REJECT labels**  
✅ **Methodology Passport displays formulas**  
✅ **Per-joint noise profile shows classifications**

---

## Design Principles

### 1. Non-Breaking Architecture
- **Parallel Functions:** `build_engineering_profile_row()` exists alongside `build_quality_row()`
- **No Existing Code Changed:** Notebook 07 and scoring functions untouched
- **Opt-In Usage:** New notebook uses new functions, old notebook works unchanged

### 2. Raw Data Only
- **Zero Scoring:** No quality scores, component scores, or weighted aggregations
- **Zero Decisions:** No ACCEPT/REVIEW/REJECT labels
- **Zero Grades:** No GOLD/SILVER/BRONZE classifications
- **Pure Measurements:** Only physical values, thresholds, and formulas

### 3. Transparency First
- **Methodology Passport:** All formulas hard-coded and version-controlled
- **Processing Transparency:** What was done, how it was done, why it was done
- **Root Cause Analysis:** Per-joint profiles, noise locality, classification logic

### 4. Researcher-Friendly
- **Interpretation Guides:** Reference values for velocity, acceleration, SNR
- **Context Annotations:** Physiological notes for bone stability
- **ASCII Visualizations:** Skeleton tree, region groupings
- **Excel Export:** Easy cross-software analysis

---

## Testing Checklist

Before deploying to production:

- [ ] Run notebook on all 5 available recordings
- [ ] Verify Excel export creates both sheets
- [ ] Confirm no quality scores in output
- [ ] Check Methodology Passport displays correctly
- [ ] Validate per-joint noise profile extracts data
- [ ] Verify bone stability profile identifies worst bone
- [ ] Confirm kinematic extremes match validation_report.json
- [ ] Check that 3-stage cleaning metrics sum correctly
- [ ] Validate SNR interpretation matches filtering_summary.json
- [ ] Confirm no errors for runs with missing steps

---

## Future Enhancements (Phase 2+)

### Phase 2: Upstream Fixes
1. **Path Length Computation:** Fix in `06_rotvec_omega.ipynb`
2. **Bilateral Symmetry:** Add to `validation_report.json`
3. **Per-Bone CV%:** Expand `preprocess_summary.json`

### Phase 3: Advanced Analysis
1. **Movement Intensity Heat Maps:** Per-segment intensity visualization
2. **Temporal Outlier Plots:** Frame-by-frame outlier timeline
3. **Bone Stability Tree:** ASCII tree with CV% annotations
4. **Bilateral Symmetry Tables:** Left vs Right comparison

### Phase 4: Cross-Session Analysis
1. **Subject Profiles:** Aggregate metrics across sessions
2. **Session Comparisons:** T1 vs T2 vs T3 evolution
3. **Movement Pattern Detection:** Identify recurring patterns
4. **Anomaly Detection:** Flag sessions with unusual characteristics

---

## References

### Mathematical Methods
- **Shoemake (1985):** Quaternion SLERP interpolation
- **Savitzky & Golay (1964):** Smoothing differentiation
- **Winter (1990):** Residual analysis for optimal cutoff

### Calibration & Quality
- **Cereatti et al. (2024):** Data lineage and provenance
- **Rácz et al. (2025):** ISB/CAST calibration layer
- **Robertson et al. (2013):** Gap-filling guidelines

---

## Contact

For questions or issues with this notebook:
- Check `utils_nb07.py` for implementation details
- Review `METHODOLOGY_PASSPORT` constant for formula documentation
- Consult `derivatives/` JSON files for data structure

**Phase 1 Status:** ✅ Complete and ready for testing  
**Next Steps:** Run on full dataset and validate outputs
