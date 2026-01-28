# Exclude Fingers Feature

## Overview
This feature allows you to exclude finger and toe segments from preprocessing by setting a configuration option.

## Configuration

### YAML Config (`config/config_v1.yaml`)
```yaml
exclude_fingers: false  # Set to true to exclude finger and toe segments
```

### Default Value
- Default: `false` (fingers are included)
- Defined in `src/pipeline_config.py` as `"exclude_fingers": False`

## What Gets Excluded

When `exclude_fingers: true` is set, the following segments are excluded from processing:

### Hand Fingers (30 segments)
- **Left Hand**: All `LeftHandThumb1-3`, `LeftHandIndex1-3`, `LeftHandMiddle1-3`, `LeftHandRing1-3`, `LeftHandPinky1-3`
- **Right Hand**: All `RightHandThumb1-3`, `RightHandIndex1-3`, `RightHandMiddle1-3`, `RightHandRing1-3`, `RightHandPinky1-3`

### Foot Toes (2 segments)
- `LeftToeBase`
- `RightToeBase`

**Total**: 32 segments can be excluded

See `FINGER_TOE_SEGMENTS_MAPPING.md` for the complete list.

## Implementation Details

### Function: `is_finger_or_toe_segment()`
Location: `src/skeleton_defs.py`

This helper function identifies finger and toe segments by:
- Checking for hand finger patterns: `HandThumb`, `HandIndex`, `HandMiddle`, `HandRing`, `HandPinky`
- Checking for toe segments: `LeftToeBase`, `RightToeBase`

### Modified Function: `standardize_to_hierarchy()`
Location: `notebooks/02_preprocess.ipynb` (Cell 2)

The function now:
1. Checks the `exclude_fingers` config option
2. Filters out finger/toe segments from the essential joints list if exclusion is enabled
3. Reports which segments were excluded
4. Processes only the remaining joints

### Automatic Propagation
- The kinematics map (`build_map_from_available_joints`) automatically excludes finger/toe segments because it only includes joints present in the filtered DataFrame
- All downstream notebooks (03-09) will automatically work with the filtered data

## Usage Example

### To Exclude Fingers:
1. Open `config/config_v1.yaml`
2. Set `exclude_fingers: true`
3. Run notebook `02_preprocess.ipynb`

### Output Example:
```
==================== DATA STANDARDIZATION ====================
🔒 Finger/Toe Exclusion: 6 segments excluded
   Excluded: LeftHandIndex1, LeftHandIndex2, LeftHandIndex3, LeftHandThumb1, LeftHandThumb2, LeftHandThumb3
Original joints: 51
Hierarchy essential: 21
Excluded finger/toe segments: 6
Kept for processing: 21
✅ Data standardized to Hierarchy Report. Shape: (17263, 155)
```

## Notes

- The exclusion works for **any** finger/toe segments that exist in the data, even if they're not currently defined in `SKELETON_HIERARCHY`
- The `LeftHand` and `RightHand` segments themselves are **NOT** excluded (only their finger children)
- The `LeftFoot` and `RightFoot` segments are **NOT** excluded (only `ToeBase` children)
