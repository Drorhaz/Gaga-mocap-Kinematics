# Finger and Toe Segments Mapping

This document lists all finger and toe segments that can be excluded from processing when `exclude_fingers: true` is set in the config.

## Hand Fingers (30 segments total)

### Left Hand Fingers (15 segments)
- **Thumb**: `LeftHandThumb1`, `LeftHandThumb2`, `LeftHandThumb3`
- **Index**: `LeftHandIndex1`, `LeftHandIndex2`, `LeftHandIndex3`
- **Middle**: `LeftHandMiddle1`, `LeftHandMiddle2`, `LeftHandMiddle3`
- **Ring**: `LeftHandRing1`, `LeftHandRing2`, `LeftHandRing3`
- **Pinky**: `LeftHandPinky1`, `LeftHandPinky2`, `LeftHandPinky3`

### Right Hand Fingers (15 segments)
- **Thumb**: `RightHandThumb1`, `RightHandThumb2`, `RightHandThumb3`
- **Index**: `RightHandIndex1`, `RightHandIndex2`, `RightHandIndex3`
- **Middle**: `RightHandMiddle1`, `RightHandMiddle2`, `RightHandMiddle3`
- **Ring**: `RightHandRing1`, `RightHandRing2`, `RightHandRing3`
- **Pinky**: `RightHandPinky1`, `RightHandPinky2`, `RightHandPinky3`

## Foot Toes (2 segments)
- `LeftToeBase`
- `RightToeBase`

## Total Excludable Segments: 32

**Note**: Currently, only `LeftHandThumb1-3` and `LeftHandIndex1-3` are defined in `SKELETON_HIERARCHY`, but the raw data contains all finger segments listed above. The exclusion will work for any finger/toe segments that exist in the data, regardless of whether they're in the hierarchy definition.
