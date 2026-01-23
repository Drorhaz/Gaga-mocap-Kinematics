# Height Calculation Feature - Quick Reference

## ✅ What Was Done

Implemented automatic **height calculation** (not estimation) from mocap skeleton data using segment-based or direct vertical measurements.

## 📊 Flow Diagram

```
User starts pipeline
        ↓
   Check metadata
        ↓
   ┌──────────────────────┐
   │ Height provided?     │
   └──────────────────────┘
      ↙              ↘
    YES              NO
     ↓                ↓
Use provided    Notebook 05
   height       detects T-pose
                     ↓
                Measure arm span
                     ↓
                Estimate height
                     ↓
                Save to metadata
                     ↓
              Update CONFIG
                     ↓
              Continue pipeline
```

## 🔧 Modified Files

1. **notebooks/05_reference_detection.ipynb** (3 cells)
   - Cell 02: Arm span calculation + estimation logic
   - Cell 02: Quality report display
   - Cell 08: Diagnostic test display

2. **notebooks/02_preprocess.ipynb** (1 cell)
   - Cell 00: Load estimated height flag

3. **notebooks/04_filtering.ipynb** (1 cell)
   - Cell 00: Display height source

4. **data/subject_metadata.json** (auto-updated)
   - Adds: `height_estimated`, `height_estimation_method`

## 📝 Example Output

### Before Height Provided:
```
ℹ️  Note: Height/Mass missing. Focusing on Kinematic Analysis.
```

### After Calculation:
```
⚙️  HEIGHT CALCULATION: Subject height not provided.
   Method: Segment Based
   Calculated Height: 170.5 cm
   Validation: Segment=170.5cm, Direct=169.8cm (Δ0.4%)
   Rationale: Direct measurement from mocap skeleton (most accurate)
   ✅ Updated metadata file: data/subject_metadata.json

📏 Arm Span: 170.5 cm (Subject Height: 170.5 cm (Segment Based))
✅ Subject Stats loaded: 170.5cm, 70kg
```

## 🎯 Key Features

✅ **Accurate** - Direct measurement from mocap skeleton, not anthropometric estimation
✅ **Robust** - Uses QC-validated bone lengths from rigid body check
✅ **Validated** - Cross-checks segment-based vs direct vertical measurement  
✅ **Transparent** - Clear labeling of calculation method
✅ **Persistent** - Saves to metadata file
✅ **Backward compatible** - Works with existing data

## 📚 Documentation

- `docs/HEIGHT_ESTIMATION_DOCUMENTATION.md` - Full technical docs
- `HEIGHT_ESTIMATION_SUMMARY.md` - Implementation summary
- Inline code comments in notebooks

## 🧪 Calculation Methods

### Primary: Segment-Based
- Sums Y-components of vertical bone segments
- Uses validated bone lengths from QC check
- Most accurate for mocap data

### Validation: Direct Vertical  
- Head Y position - minimum Foot Y position
- Simple geometric measurement
- Validates segment-based result

### Anatomical Check: Arm Span
- Still calculated for consistency validation
- Compares to calculated height (should match ±5%)

## ⚠️ When Calculation Skipped

- Height already provided by user
- Invalid measurements (< 50cm or > 250cm)
- Missing skeleton data

## 🚀 Ready to Use

No configuration needed. Feature is active automatically when height is missing.

To test:
1. Set `height_cm: null` in `data/subject_metadata.json`
2. Run notebook 05
3. Check console for estimation message
4. Verify metadata file updated
