# Segment to Body Part Mapping

## Overview

The mapping of segments to body parts is determined in **two main locations**:

1. **`src/filtering.py`** - `BODY_REGIONS` dictionary (for filtering cutoffs)
2. **`src/skeleton_defs.py`** - `is_finger_or_toe_segment()` function (for finger/toe exclusion)

---

## 1. Body Regions for Filtering (`src/filtering.py`)

### Location: `src/filtering.py`, lines 58-95

**Purpose**: Categorizes segments into body regions for **per-region filtering cutoffs** (Winter filtering).

### `BODY_REGIONS` Dictionary:

```python
BODY_REGIONS = {
    'trunk': {
        'patterns': ['Pelvis', 'Spine', 'Torso', 'Hips', 'Abdomen', 'Chest', 'Back'],
        'fixed_cutoff': 6,  # 6 Hz for core stability
    },
    'head': {
        'patterns': ['Head', 'Neck'],
        'fixed_cutoff': 8,  # 8 Hz for head dynamics
    },
    'upper_proximal': {
        'patterns': ['Shoulder', 'Clavicle', 'Scapula', 'UpperArm', 'Arm'],
        'fixed_cutoff': 8,  # 8 Hz for shoulder/arm
    },
    'upper_distal': {
        'patterns': ['Elbow', 'Forearm', 'ForeArm', 'Wrist', 'Hand', 
                     'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'],
        'fixed_cutoff': 10,  # 10 Hz for fast hand/finger movements
    },
    'lower_proximal': {
        'patterns': ['Thigh', 'UpLeg', 'UpperLeg', 'Knee'],
        'fixed_cutoff': 8,  # 8 Hz for leg dynamics
    },
    'lower_distal': {
        'patterns': ['Ankle', 'Leg', 'LowerLeg', 'Foot', 'Toe', 'ToeBase', 'Heel'],
        'fixed_cutoff': 10,  # 10 Hz for foot strikes and toe movements
    }
}
```

### How It Works:

**Function: `classify_marker_region()`** (lines 102-124)

```python
def classify_marker_region(marker_name: str) -> str:
    """
    Classify a marker into a body region based on name patterns.
    
    Example:
        'LeftHandIndex1__px' → 'upper_distal' (matches 'Index' pattern)
        'LeftArm__px' → 'upper_proximal' (matches 'Arm' pattern)
        'Hips__px' → 'trunk' (matches 'Hips' pattern)
    """
    base_name = marker_name.replace('__px', '').replace('__py', '').replace('__pz', '')
    
    # Check each region's patterns
    for region, config in BODY_REGIONS.items():
        for pattern in config['patterns']:
            if pattern.lower() in base_name.lower():
                return region
    
    return 'upper_distal'  # Default
```

**Pattern Matching Logic:**
- Checks if any pattern from a region appears in the segment name
- Case-insensitive matching
- **Works for BOTH Left and Right**: Pattern matching is substring-based, so it catches both sides
- Examples:
  - `"LeftHandIndex1"` contains `"Index"` → classified as `'upper_distal'`
  - `"RightHandIndex1"` contains `"Index"` → classified as `'upper_distal'` ✓ **Right hand covered**
  - `"LeftToeBase"` contains `"ToeBase"` → classified as `'lower_distal'`
  - `"RightToeBase"` contains `"ToeBase"` → classified as `'lower_distal'` ✓ **Right foot covered**

---

## 2. Finger/Toe Detection (`src/skeleton_defs.py`)

### Location: `src/skeleton_defs.py`, lines 6-32

**Purpose**: Identifies finger and toe segments for **exclusion** (when `exclude_fingers=True`).

### `is_finger_or_toe_segment()` Function:

```python
def is_finger_or_toe_segment(joint_name):
    """
    Determines if a joint name represents a finger or toe segment.
    
    Hand Fingers: All segments containing Hand(Thumb|Index|Middle|Ring|Pinky)
    Foot Toes: LeftToeBase, RightToeBase
    """
    # Check for hand fingers
    finger_patterns = ['HandThumb', 'HandIndex', 'HandMiddle', 'HandRing', 'HandPinky']
    if any(pattern in joint_name for pattern in finger_patterns):
        return True
    
    # Check for toe segments
    if joint_name in ['LeftToeBase', 'RightToeBase']:
        return True
    
    return False
```

**Pattern Matching:**
- **Fingers**: Checks if joint name contains `HandThumb`, `HandIndex`, `HandMiddle`, `HandRing`, or `HandPinky`
  - **Works for BOTH Left and Right**: Pattern matching is substring-based, so it catches both sides
  - Example: `"HandIndex"` pattern matches both `"LeftHandIndex1"` and `"RightHandIndex1"`
- **Toes**: Exact match for `LeftToeBase` or `RightToeBase` (both explicitly listed)

**Examples (showing BOTH left and right are covered):**
- `"LeftHandIndex1"` → `True` (contains `"HandIndex"`)
- `"RightHandIndex1"` → `True` (contains `"HandIndex"`) ✓ **Right hand covered**
- `"LeftHandThumb2"` → `True` (contains `"HandThumb"`)
- `"RightHandThumb2"` → `True` (contains `"HandThumb"`) ✓ **Right hand covered**
- `"LeftHandMiddle3"` → `True` (contains `"HandMiddle"`)
- `"RightHandMiddle3"` → `True` (contains `"HandMiddle"`) ✓ **Right hand covered**
- `"LeftHandRing1"` → `True` (contains `"HandRing"`)
- `"RightHandRing1"` → `True` (contains `"HandRing"`) ✓ **Right hand covered**
- `"LeftHandPinky2"` → `True` (contains `"HandPinky"`)
- `"RightHandPinky2"` → `True` (contains `"HandPinky"`) ✓ **Right hand covered**
- `"LeftToeBase"` → `True` (exact match) ✓ **Left foot covered**
- `"RightToeBase"` → `True` (exact match) ✓ **Right foot covered**
- `"LeftArm"` → `False` (not a finger/toe)

---

## 3. Hierarchy Comments (`src/skeleton_defs.py`)

### Location: `src/skeleton_defs.py`, lines 34-79

**Purpose**: Documents body part organization in the hierarchy (informational only).

```python
SKELETON_HIERARCHY = {
    # --- Root (Global) ---
    "Hips": {...},
    
    # --- Spine ---
    "Spine": {...},
    "Spine1": {...},
    "Neck": {...},
    "Head": {...},
    
    # --- Left Leg ---
    "LeftUpLeg": {...},
    "LeftLeg": {...},
    "LeftFoot": {...},
    "LeftToeBase": {...},
    
    # --- Right Leg ---
    "RightUpLeg": {...},
    ...
    
    # --- Left Arm ---
    "LeftShoulder": {...},
    "LeftArm": {...},
    "LeftForeArm": {...},
    "LeftHand": {...},
    
    # --- Fingers (Left) ---
    "LeftHandThumb1": {...},
    "LeftHandIndex1": {...},
    "LeftHandMiddle1": {...},
    "LeftHandRing1": {...},
    "LeftHandPinky1": {...},
    # ... (and their child segments: Thumb2/3, Index2/3, etc.)
    
    # --- Fingers (Right) ---
    "RightHandThumb1": {...},
    "RightHandIndex1": {...},
    "RightHandMiddle1": {...},
    "RightHandRing1": {...},
    "RightHandPinky1": {...},
    # ... (and their child segments: Thumb2/3, Index2/3, etc.)
}
```

**Note**: These are just comments for organization - not used for automatic categorization.

---

## Summary Table

| Location | Purpose | How It Works | Used For |
|----------|---------|--------------|----------|
| **`src/filtering.py`**<br>`BODY_REGIONS` | Body region categorization | Pattern matching in segment names | **Filtering cutoffs** (Winter analysis) |
| **`src/skeleton_defs.py`**<br>`is_finger_or_toe_segment()` | Finger/toe detection | Pattern matching for `Hand*` and `ToeBase` | **Exclusion** (when `exclude_fingers=True`) |
| **`src/skeleton_defs.py`**<br>Comments | Documentation | Manual comments | **Reference only** |

---

## How to Modify

### To Add New Body Region Patterns:

**Edit `src/filtering.py`**, `BODY_REGIONS` dictionary:

```python
'upper_distal': {
    'patterns': ['Elbow', 'Forearm', 'ForeArm', 'Wrist', 'Hand', 
                 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky',
                 'YourNewPattern'],  # Add here
    'fixed_cutoff': 10,
}
```

### To Add New Finger/Toe Patterns:

**Edit `src/skeleton_defs.py`**, `is_finger_or_toe_segment()` function:

```python
finger_patterns = ['HandThumb', 'HandIndex', 'HandMiddle', 'HandRing', 'HandPinky',
                   'YourNewFingerPattern']  # Add here
```

---

## Current Mappings

### Fingers (from `is_finger_or_toe_segment()`):
**Pattern-based matching - covers BOTH Left and Right hands:**
- `HandThumb` pattern → Matches: `LeftHandThumb1/2/3`, `RightHandThumb1/2/3`
- `HandIndex` pattern → Matches: `LeftHandIndex1/2/3`, `RightHandIndex1/2/3`
- `HandMiddle` pattern → Matches: `LeftHandMiddle1/2/3`, `RightHandMiddle1/2/3`
- `HandRing` pattern → Matches: `LeftHandRing1/2/3`, `RightHandRing1/2/3`
- `HandPinky` pattern → Matches: `LeftHandPinky1/2/3`, `RightHandPinky1/2/3`

**Total: 30 finger segments (15 left + 15 right)**

### Toes:
**Explicitly listed - covers BOTH Left and Right feet:**
- `LeftToeBase` → Left foot toe
- `RightToeBase` → Right foot toe

**Total: 2 toe segments (1 left + 1 right)**

### Body Regions (from `BODY_REGIONS`):
- **Trunk**: Pelvis, Spine, Torso, Hips, Abdomen, Chest, Back
- **Head**: Head, Neck
- **Upper Proximal**: Shoulder, Clavicle, Scapula, UpperArm, Arm
- **Upper Distal**: Elbow, Forearm, ForeArm, Wrist, Hand, Finger, Thumb, Index, Middle, Ring, Pinky
- **Lower Proximal**: Thigh, UpLeg, UpperLeg, Knee
- **Lower Distal**: Ankle, Leg, LowerLeg, Foot, Toe, ToeBase, Heel
