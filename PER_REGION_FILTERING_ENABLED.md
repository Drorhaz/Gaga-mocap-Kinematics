# Per-Region Filtering Now Enabled

## Summary
Per-region filtering has been **enabled as the default** in the pipeline (Notebook 04).

## Changes Made

### 1. Main Filtering Call Updated
**File**: `notebooks/04_filtering.ipynb` (Cell ~17)

**Before**: Single global cutoff with no guardrails
```python
df_filtered, winter_metadata = apply_winter_filter(
    df, fs=FS, pos_cols=pos_cols_to_filter,
    fmax=12, allow_fmax=True,
    min_cutoff_trunk=None,    # Disabled
    min_cutoff_distal=None,   # Disabled
    use_trunk_global=False
)
```

**After**: Per-region filtering enabled
```python
df_filtered, winter_metadata = apply_winter_filter(
    df, fs=FS, pos_cols=pos_cols_to_filter,
    fmax=12, allow_fmax=True,
    per_region_filtering=True  # ← ENABLED
)
```

### 2. Updated Output Display
Now shows region-specific cutoffs when per-region mode is active:
```
✅ Per-Region Filtering Applied
   Region-specific cutoffs:
     trunk               :  6.0 Hz (9 markers)
     head                :  7.0 Hz (6 markers)
     upper_proximal      :  8.0 Hz (6 markers)
     upper_distal        : 10.0 Hz (48 markers)
     lower_proximal      :  8.0 Hz (12 markers)
     lower_distal        :  9.0 Hz (12 markers)
   Cutoff range: 6.0 - 10.0 Hz
```

### 3. Updated Filtering Summary JSON
**File**: `derivatives/step_04_filtering/*__filtering_summary.json`

**New fields for per-region mode**:
```json
{
  "filter_params": {
    "filtering_mode": "per_region",
    "filter_method": "Per-Region Winter Cutoff Selection",
    "region_cutoffs": {
      "trunk": 6.0,
      "head": 7.0,
      "upper_proximal": 8.0,
      "upper_distal": 10.0,
      "lower_proximal": 8.0,
      "lower_distal": 9.0
    },
    "cutoff_range_hz": [6.0, 10.0],
    "n_regions": 6,
    "region_marker_counts": {
      "trunk": 9,
      "head": 6,
      "upper_proximal": 6,
      "upper_distal": 48,
      "lower_proximal": 12,
      "lower_distal": 12
    }
  }
}
```

### 4. Pipeline Version Updated
- **Old**: `v2.7_winter_failure_tracking`
- **New**: `v2.8_per_region_filtering`

## Region Definitions (from `src/filtering.py`)

| Region | Cutoff Range | Markers | Rationale |
|--------|-------------|---------|-----------|
| **Trunk** | 6-8 Hz | Pelvis, Spine, Torso, Hips, Abdomen, Chest, Back | Slow, constrained core movements |
| **Head** | 7-9 Hz | Head, Neck | Moderate dynamics, somewhat constrained |
| **Upper Proximal** | 8-10 Hz | Shoulder, Clavicle, Scapula, UpperArm | Moderate-fast, semi-constrained |
| **Upper Distal** | 10-12 Hz | Elbow, Forearm, Wrist, Hand, Finger | Very fast gestures, unconstrained |
| **Lower Proximal** | 8-10 Hz | Thigh, Knee, UpperLeg | Moderate-fast locomotion |
| **Lower Distal** | 9-11 Hz | Ankle, Foot, Toe, Heel, LowerLeg | Fast, ground contact impacts |

## How It Works

1. **Marker Classification**: Each marker is automatically classified into a body region based on name patterns
2. **Per-Region Winter Analysis**: Winter residual analysis is run separately for each region
3. **Region-Specific Cutoffs**: Each region gets a cutoff within its biomechanically-appropriate range
4. **Individual Filtering**: Each marker is filtered with its region's specific cutoff frequency

## Benefits for Dance Motion Capture

- **Preserves Hand Dynamics**: Rapid hand gestures are filtered at 10-12 Hz instead of being over-smoothed
- **Appropriate Trunk Filtering**: Core movements filtered conservatively at 6-8 Hz
- **Biomechanically Principled**: Different body parts have different movement frequencies
- **Better Dance Representation**: Fast distal movements preserved while core stability maintained

## Testing Recommendation

Run a single file through the updated pipeline to verify:
```bash
python run_pipeline.py --config batch_configs/subject_734_all.json --max-files 1
```

Expected output in filtering summary:
- `"filtering_mode": "per_region"`
- Region-specific cutoffs for all 6 body regions
- Cutoff range approximately 6-10 Hz (dance-appropriate)

## Validation

The per-region filtering was already implemented and tested in the **"VALIDATION SECTION 2"** of notebook 04, where it showed:
- Preservation of high-frequency content in distal markers
- Appropriate smoothing of trunk movements
- Clear visual differences in PSD between regions

Now this validated approach is the **default production method**.
