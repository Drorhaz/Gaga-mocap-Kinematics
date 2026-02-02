# Where BVH Offsets Are Used in the Code

## Summary

**BVH offsets** (stored in `skeleton_schema.json`) are used in **one main location** for **bone length quality control**.

---

## Primary Usage: `src/qc.py`

### Function: `bone_length_qc()`

**Location**: `src/qc.py`, lines 4-71

**Purpose**: Compares actual bone lengths from motion capture data against expected bone lengths from BVH offsets.

### How It Works:

```python
def bone_length_qc(pos_m, schema, joints_export_mask, cfg):
    # 1. Extract offsets from schema (line 8)
    offsets = schema.get("offsets", {})
    
    # 2. For each bone (parent->child pair):
    for p_name, c_name in bones:
        # Calculate actual bone length from mocap data
        L = np.linalg.norm(C[valid] - P[valid], axis=1)
        median_L = float(np.median(L))
        
        # 3. Get expected bone length from BVH offset (line 39-40)
        off = offsets.get(c_name, [np.nan, np.nan, np.nan])
        L_bvh = float(np.linalg.norm(off))  # Expected length from BVH
        
        # 4. Compare actual vs expected (line 41)
        ratio = float(median_L / L_bvh)  # Should be ~1.0 if consistent
        
        # 5. Store results (line 53)
        rows.append({
            "bvh_offset_len": L_bvh,        # Expected from BVH
            "ratio_median_to_bvh": ratio,   # Actual/Expected ratio
            ...
        })
```

### Key Lines:

- **Line 8**: `offsets = schema.get("offsets", {})` - Reads offsets from schema
- **Line 39**: `off = offsets.get(c_name, [np.nan, np.nan, np.nan])` - Gets offset for child joint
- **Line 40**: `L_bvh = float(np.linalg.norm(off))` - Calculates expected bone length
- **Line 41**: `ratio = float(median_L / L_bvh)` - Compares actual vs expected
- **Line 53**: `"bvh_offset_len": L_bvh` - Stores BVH offset length in results

---

## Where It's Called

### 1. `src/pipeline.py` (Line 118)

```python
from .qc import bone_length_qc

def run_pipeline(csv_path, schema, seg_map, run_id="run1", cfg=CONFIG, ...):
    # ...
    # schema is loaded from skeleton_schema.json (contains offsets)
    df_bones, bone_sum = bone_length_qc(pos_m, schema, np.ones(len(joint_names), dtype=bool), cfg)
```

**Flow**:
1. Schema (with offsets) is loaded from `skeleton_schema.json`
2. Passed to `bone_length_qc()` function
3. Function extracts offsets and uses them for QC

---

## What It Does

### Quality Control Process:

1. **Reads BVH offsets** from `skeleton_schema.json`
2. **Calculates expected bone lengths** from offsets (using `np.linalg.norm()`)
3. **Measures actual bone lengths** from motion capture position data
4. **Compares** actual vs expected (ratio should be ~1.0)
5. **Flags issues** if:
   - Ratio deviates significantly from 1.0 (scaling issues)
   - Actual bone lengths vary too much (tracking errors)

### Output:

The function returns:
- `df_bones`: DataFrame with bone length analysis including:
  - `bvh_offset_len`: Expected bone length from BVH offset
  - `ratio_median_to_bvh`: Actual/Expected ratio
  - `status`: PASS/WARN/ALERT based on thresholds
- `bone_sum`: Summary statistics

---

## Important Notes

### ⚠️ Note About Notebook 02

The notebook `02_preprocess.ipynb` has its own `run_bone_length_qc()` function (lines 592-652) that:
- **Does NOT use offsets from schema**
- Calculates bone lengths directly from data
- Only checks consistency (CV%), not comparison to BVH offsets

This is a **different implementation** that doesn't use the BVH offsets.

### ✅ Main Pipeline Usage

The **main pipeline** (`src/pipeline.py` → `src/qc.py`) **DOES use BVH offsets** for quality control.

---

## Example Usage Flow

```
1. Load skeleton_schema.json
   └─> Contains "offsets": {"LeftArm": [11.532102, 1e-06, -1e-06], ...}

2. Call bone_length_qc(pos_m, schema, ...)
   └─> Extracts offsets from schema
   └─> For each bone:
       ├─> Get offset: [11.532102, 1e-06, -1e-06]
       ├─> Calculate expected length: ||offset|| = 11.53 cm
       ├─> Measure actual length from mocap: 11.52 cm
       └─> Compare: ratio = 11.52 / 11.53 = 0.999 (✅ good)

3. Return QC results
   └─> Flag bones with ratio far from 1.0 (scaling/tracking issues)
```

---

## Summary Table

| Location | Function | Purpose | Uses BVH Offsets? |
|----------|----------|---------|-------------------|
| `src/qc.py` | `bone_length_qc()` | Bone length QC | ✅ **YES** |
| `src/pipeline.py` | `run_pipeline()` | Main pipeline | ✅ **YES** (calls qc.py) |
| `notebooks/02_preprocess.ipynb` | `run_bone_length_qc()` | Notebook QC | ❌ **NO** (different implementation) |
