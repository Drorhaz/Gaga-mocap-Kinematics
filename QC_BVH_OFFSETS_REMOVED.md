# QC BVH Offsets Removed - Change Summary

## What Changed

Modified `src/qc.py` to **disable BVH offset comparison by default** and make it optional.

## Changes Made

### 1. Added `use_bvh_offsets` Parameter

**Before:**
```python
def bone_length_qc(pos_m, schema, joints_export_mask, cfg):
```

**After:**
```python
def bone_length_qc(pos_m, schema, joints_export_mask, cfg, use_bvh_offsets=False):
```

- **Default: `False`** - BVH comparison is disabled by default
- **Backward compatible** - existing code continues to work without changes

### 2. Made Offset Extraction Conditional

**Before:**
```python
offsets = schema.get("offsets", {})  # Always extracted
```

**After:**
```python
offsets = schema.get("offsets", {}) if use_bvh_offsets else {}  # Only if enabled
```

### 3. Made BVH Comparison Optional

**Before:**
```python
# Always calculated BVH comparison
off = offsets.get(c_name, [np.nan, np.nan, np.nan])
L_bvh = float(np.linalg.norm(off))
ratio = float(median_L / L_bvh)
row["bvh_offset_len"] = L_bvh
row["ratio_median_to_bvh"] = ratio
```

**After:**
```python
# Only if enabled and offsets available
if use_bvh_offsets and offsets:
    off = offsets.get(c_name, [np.nan, np.nan, np.nan])
    L_bvh = float(np.linalg.norm(off)) if np.all(np.isfinite(off)) else np.nan
    ratio = float(median_L / L_bvh) if (np.isfinite(L_bvh) and L_bvh > 0) else np.nan
    row["bvh_offset_len"] = L_bvh
    row["ratio_median_to_bvh"] = ratio
```

### 4. Added Documentation

Added comprehensive docstring explaining:
- What the function does
- When to use BVH offsets (per-session only)
- Why consistency check is recommended for multi-subject data

## Impact

### ✅ What Still Works

- **Consistency check (CV%)** - Still works perfectly (this is the important part!)
- **All existing code** - No breaking changes, default behavior is safer
- **Multi-subject processing** - No more false warnings from wrong offsets

### ✅ What's Disabled by Default

- **BVH offset comparison** - Disabled to avoid false warnings for different subjects
- **`bvh_offset_len` field** - Only added if `use_bvh_offsets=True`
- **`ratio_median_to_bvh` field** - Only added if `use_bvh_offsets=True`

## Usage

### Default (Recommended for Multi-Subject)
```python
# Consistency check only - works for all subjects
df_bones, bone_sum = bone_length_qc(pos_m, schema, mask, cfg)
```

### With BVH Offsets (Only if per-session offsets available)
```python
# Enable BVH comparison (requires per-session offsets in schema)
df_bones, bone_sum = bone_length_qc(pos_m, schema, mask, cfg, use_bvh_offsets=True)
```

## Rationale

1. **Multi-subject safety**: Shared offsets cause false warnings for different subjects
2. **Consistency is sufficient**: CV% check detects tracking errors without needing "expected" values
3. **Backward compatible**: Existing code works without changes
4. **Flexible**: Can still enable BVH comparison if per-session offsets are available

## Next Steps (Optional)

If you want to completely remove BVH offset support:
1. Remove `offsets` extraction entirely
2. Remove the conditional BVH comparison block
3. Remove `bvh_offset_len` and `ratio_median_to_bvh` from output

But keeping it optional is better - allows future per-session offset support if needed.
