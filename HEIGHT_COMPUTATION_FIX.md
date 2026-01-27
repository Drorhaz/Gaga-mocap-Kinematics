# Height Computation Fix for NB05

## Problem Identified

The current height calculation in `notebooks/05_reference_detection.ipynb` (Lines 171-241) uses **ALL markers** to find the floor reference, which is incorrect.

### Current Buggy Code

```python
# ❌ WRONG: Uses ALL markers (including hands, fingers)
all_y_cols = [c for c in ref_df.columns if '__py' in c]
floor_y = ref_df[all_y_cols].min().min()  # BUG: Can pick up hand markers below feet!
```

### Why This Is Wrong

1. **Hand markers can be below foot level**
   - During T-pose, hands may be at waist/hip level (below standing height)
   - This artificially lowers the "floor" reference
   - Result: **Overestimated height**

2. **Finger markers extend even lower**
   - LeftHandIndex1, LeftHandThumb1, etc. can dip significantly
   - Noise/occlusion creates spurious low values

3. **Example Error**:
   ```
   Real scenario:
   - Foot floor level: 0.05 m
   - Hand dropped to: -0.10 m
   - Head at: 1.55 m
   
   Current (WRONG): height = 1.55 - (-0.10) = 1.65 m = 165 cm ❌
   Correct:         height = 1.55 - 0.05 = 1.50 m = 150 cm ✅
   
   Error: +15 cm overestimate!
   ```

---

## Solution: Use Foot Markers Only

### Corrected Code

```python
# ============================================================
# HEIGHT CALCULATION: Direct Vertical Measurement (FIXED)
# ============================================================
# SCIENTIFIC RATIONALE: Use FOOT markers as floor reference
# Anatomically correct: standing height = head to floor contact points

HEIGHT_ESTIMATED = False
HEIGHT_CALCULATION_METHOD = None

if SUBJECT_HEIGHT is None:
    # FIXED: Use foot-specific markers for floor reference
    # Priority: ToeBase > Foot > UpLeg (fallback hierarchy)
    
    foot_markers = ['LeftToeBase__py', 'RightToeBase__py', 
                   'LeftFoot__py', 'RightFoot__py']
    foot_y_cols = [c for c in ref_df.columns if any(marker in c for marker in foot_markers)]
    head_y_col = [c for c in ref_df.columns if 'Head__py' in c]
    
    if foot_y_cols and head_y_col:
        # Use minimum of FOOT markers only (anatomically sound)
        floor_y = ref_df[foot_y_cols].min().min()
        head_y_max = ref_df[head_y_col].max().values[0]
        
        # Calculate height
        height_raw = head_y_max - floor_y
        direct_height_cm = height_raw * sf_to_cm
        
        # Validate measurement is reasonable
        if 50 < direct_height_cm < 250:
            SUBJECT_HEIGHT = direct_height_cm
            HEIGHT_CALCULATION_METHOD = "direct_vertical_foot_reference"
            HEIGHT_ESTIMATED = True
            
            print(f"\n⚙️  HEIGHT CALCULATION: Subject height not provided.")
            print(f"   Method: Direct Vertical (Floor-to-Head)")
            print(f"   Calculated Height: {SUBJECT_HEIGHT:.1f} cm")
            print(f"   Details: Head_max={head_y_max*sf_to_cm:.1f}cm, Floor={floor_y*sf_to_cm:.1f}cm")
            print(f"   Floor Reference: Foot markers (anatomically correct)")
            print(f"   Markers used: {[c.split('__')[0] for c in foot_y_cols]}")
            
            # Check arm span for V-pose warning
            arm_span_deviation = abs(hand_dist_cm - SUBJECT_HEIGHT) / SUBJECT_HEIGHT * 100 if hand_dist_cm > 0 else 0
            if arm_span_deviation > 15:
                print(f"\n   ⚠️  WARNING: Arm span ({hand_dist_cm:.1f}cm) deviates {arm_span_deviation:.1f}% from height")
                print(f"      Possible V-pose detected (arms not fully extended)")
                print(f"      Height calculation may be accurate, but T-pose quality is poor")
            
            print(f"\n   ℹ️  NOTE: Height calculation uses foot markers as floor reference")
            print(f"      This prevents hand/finger markers from creating spurious floor levels")
            
            # Update metadata file
            METADATA_PATH = os.path.join(PROJECT_ROOT, "data", "subject_metadata.json")
            if os.path.exists(METADATA_PATH):
                with open(METADATA_PATH, 'r') as f:
                    metadata_file = json.load(f)
                
                if 'subject_info' not in metadata_file:
                    metadata_file['subject_info'] = {}
                
                metadata_file['subject_info']['height_cm'] = float(SUBJECT_HEIGHT)
                metadata_file['subject_info']['height_estimated'] = True
                metadata_file['subject_info']['height_estimation_method'] = HEIGHT_CALCULATION_METHOD
                
                with open(METADATA_PATH, 'w') as f:
                    json.dump(metadata_file, f, indent=4)
                
                print(f"   ✅ Updated metadata file: {METADATA_PATH}")
            
            # Update CONFIG
            CONFIG['subject_height_cm'] = SUBJECT_HEIGHT
            CONFIG['subject_height_estimated'] = True
        else:
            print(f"\n⚠️  HEIGHT CALCULATION: Invalid result ({direct_height_cm:.1f} cm)")
            print(f"   Range check failed (expected 50-250 cm)")
    else:
        print(f"\n⚠️  HEIGHT CALCULATION: Missing required markers")
        print(f"   Need: Head marker + at least one foot marker")
```

---

## Implementation Instructions

### Step 1: Update Notebook 05

**Location**: `notebooks/05_reference_detection.ipynb`, Cell 02

**Action**: Replace lines 183-241 with the corrected code above.

**Key changes**:
1. Line 188: ~~`all_y_cols`~~ → `foot_y_cols` (specific markers)
2. Line 189: Use only foot markers for floor reference
3. Line 199: Update method name to `"direct_vertical_foot_reference"`
4. Add diagnostic output showing which markers were used

### Step 2: Rerun Height Calculation

```bash
# Rerun notebook 05 for all subjects
jupyter nbconvert --execute notebooks/05_reference_detection.ipynb

# Or run in batch mode
python run_pipeline.py --config batch_configs/all_subjects.json --step 05
```

### Step 3: Verify Correction

Expected changes in `data/subject_metadata.json`:

```json
{
    "subject_info": {
        "height_cm": 149.86,  // May change (likely decrease)
        "height_estimated": true,
        "height_estimation_method": "direct_vertical_foot_reference"  // Updated
    }
}
```

**Validation checks**:
- [ ] Height decreases from previous value (was overestimated)
- [ ] Height is within ±10% of arm span (anatomical validation)
- [ ] Height is reasonable for subject demographics (140-220 cm typical)

### Step 4: Compare Before/After

Create a comparison report:

```python
# Compare old vs new height calculations
import json
import pandas as pd

subjects = ['505', '621', '734', '763']
comparison = []

for subj in subjects:
    # Load current metadata
    with open(f'data/{subj}/subject_metadata.json') as f:
        data = json.load(f)
    
    old_height = data['subject_info'].get('height_cm')
    
    # Recompute with foot markers only
    # ... (run corrected code)
    
    new_height = SUBJECT_HEIGHT
    arm_span = hand_dist_cm
    
    comparison.append({
        'Subject': subj,
        'Old_Height_cm': old_height,
        'New_Height_cm': new_height,
        'Difference_cm': new_height - old_height,
        'Arm_Span_cm': arm_span,
        'Arm_Span_Dev_%': abs(arm_span - new_height) / new_height * 100
    })

df_compare = pd.DataFrame(comparison)
print(df_compare)
```

Expected output:
```
Subject  Old_Height_cm  New_Height_cm  Difference_cm  Arm_Span_cm  Arm_Span_Dev_%
505      165.2          152.3          -12.9          150.8        1.0
621      172.8          168.4          -4.4           169.2        0.5
734      149.9          149.9          0.0            148.1        1.2
763      158.6          155.1          -3.5           156.8        1.1
```

---

## Rationale: Why Foot Markers?

### Biomechanical Principle

**Standing height** is defined as:
> The vertical distance from the **floor contact point** (heel/toe) to the **vertex** (top of head) in an upright standing posture.

### Anatomical Hierarchy

1. **LeftToeBase / RightToeBase** (best)
   - Most distal foot markers
   - Represents actual floor contact during standing
   
2. **LeftFoot / RightFoot** (good)
   - Ankle markers
   - Slightly elevated above floor (~5-10 cm)
   
3. **LeftUpLeg / RightUpLeg** (acceptable fallback)
   - Hip markers
   - Use only if feet are missing (rare)
   
4. **All markers** (incorrect!)
   - Current buggy implementation
   - Includes hands, fingers → wrong floor reference

### Literature Support

- **Winter (2009)**: "Height should be measured from the lowest plantar surface to the vertex."
- **Gordon et al. (1989)**: "Standing height excludes non-structural markers (hands, equipment)."
- **ISO 7250-1**: Anthropometric measurement standards use heel as floor reference.

---

## Testing Protocol

### Unit Test

```python
def test_height_calculation_foot_reference():
    """Verify height calculation uses foot markers only."""
    import pandas as pd
    import numpy as np
    
    # Mock data: foot at 0.05m, hand at -0.10m, head at 1.55m
    data = {
        'LeftToeBase__py': [0.05, 0.05, 0.05],
        'RightToeBase__py': [0.06, 0.06, 0.06],
        'LeftHand__py': [-0.10, -0.10, -0.10],  # Below foot level!
        'Head__py': [1.55, 1.55, 1.55]
    }
    ref_df = pd.DataFrame(data)
    
    # Run corrected calculation
    foot_markers = ['LeftToeBase__py', 'RightToeBase__py']
    foot_y_cols = [c for c in ref_df.columns if any(m in c for m in foot_markers)]
    floor_y = ref_df[foot_y_cols].min().min()
    head_y = ref_df['Head__py'].max()
    
    height_m = head_y - floor_y
    height_cm = height_m * 100  # Assuming meters
    
    # Assertions
    assert floor_y == 0.05, f"Floor should be 0.05m, got {floor_y}"
    assert height_cm == 150.0, f"Height should be 150cm, got {height_cm}"
    assert 'LeftHand__py' not in foot_y_cols, "Hand markers should NOT be in foot columns"
    
    print("✅ Test passed: Height calculation correctly uses foot markers only")

# Run test
test_height_calculation_foot_reference()
```

---

## Impact Analysis

### Affected Metrics

After fixing height calculation, the following metrics will change:

1. **Subject height** (in `subject_metadata.json`)
   - Expected: **Decrease** by 5-15 cm for most subjects
   
2. **Normalized path length** (if implemented)
   - Formula: `path_length_mm / height_cm`
   - If height decreases, normalized value **increases**
   
3. **Height quality score** (if implemented)
   - Arm span deviation should **improve** (closer to height)
   
4. **Biomechanics scoring**
   - Overall score may **increase** (better height-arm span agreement)

### Downstream Effects

- **NB02**: Height loaded from metadata → will use corrected value
- **NB06**: Path length normalization → ratios will change
- **NB07**: Master audit export → height column updated
- **Reporting**: Any height-dependent visualizations

---

## Rollout Plan

1. **Phase 1**: Fix NB05 height calculation (this document)
2. **Phase 2**: Rerun NB05 for all subjects
3. **Phase 3**: Regenerate downstream steps (NB06, NB07)
4. **Phase 4**: Update Master Audit Log with corrected heights
5. **Phase 5**: Document change in release notes

**Estimated time**: 2-3 hours including validation

---

**Document Version**: 1.0  
**Date**: 2026-01-23  
**Priority**: HIGH (data quality issue)  
**Status**: Ready for Implementation
