# ROM Data - QUALITY CONTROL METRICS ONLY

## ⚠️ CRITICAL WARNING

**THE ROM VALUES IN THIS DIRECTORY ARE FOR QUALITY CONTROL PURPOSES ONLY**

They are **NOT** clinical ROM or anatomical ROM values!

## What is This ROM?

- **Type**: Rotation vector magnitude (mathematical QC metric)
- **Computed from**: Quaternion-derived rotation vectors
- **Purpose**: Detect tracking errors, marker jumps, data quality issues

## What This ROM Is NOT

❌ **NOT** clinical ROM (measured with goniometry)  
❌ **NOT** anatomical ROM (flexion/abduction/rotation separate)  
❌ **NOT** comparable to literature ROM values  
❌ **NOT** suitable for medical/clinical assessment  

## Valid Uses

✅ Quality control and outlier detection  
✅ Detecting tracking errors (ROM > 300° = bad)  
✅ Left/Right symmetry checks  
✅ Relative comparisons within this dataset  
✅ Data rejection criteria  

## Invalid Uses

❌ Comparing to clinical norms ("shoulder flexion is 180°")  
❌ Anatomical analysis ("how much flexion occurred?")  
❌ Cross-study comparisons  
❌ Functional assessments  
❌ Medical diagnosis or documentation  

## Why Is This Different?

### This ROM Method (Rotation Vectors)
- Measures: "How much did the joint move?" (total magnitude)
- Components: rx, ry, rz (arbitrary mathematical axes)
- **Cannot** separate flexion from abduction from rotation

### Clinical ROM (Euler Angles)
- Measures: "How much flexion? Abduction? Rotation?" (per plane)
- Components: Anatomical movements in cardinal planes
- **Can** separate and interpret each movement

## Files in This Directory

| File | Description |
|------|-------------|
| `*__joint_statistics.json` | ROM metrics in JSON format (human-readable) |
| `*__joint_statistics.parquet` | ROM metrics in Parquet format (fast access) |

## Data Structure

```json
{
    "joint_name": "LeftShoulder",
    "rom": 145.3,                    // QC metric (NOT clinical ROM)
    "max_angular_velocity": 678.4,  // deg/s (for detecting marker jumps)
    "mean_angular_velocity": 234.1, // deg/s (movement intensity)
    "p95_angular_velocity": 589.2   // deg/s (95th percentile)
}
```

## Quality Control Thresholds

| ROM Value | Interpretation | Action |
|-----------|----------------|--------|
| 50-180° | Good | Accept data |
| 200-300° | Suspicious | Review manually |
| >300° or 0° | Bad | Reject data |

## Documentation

For complete information:
- **Complete guide**: `docs/ROM_DOCUMENTATION.md` (merged comprehensive documentation)

## Example: Loading ROM Data

```python
import pandas as pd

# Load ROM data
df_rom = pd.read_parquet('*__joint_statistics.parquet')

# Quality control check
bad_joints = df_rom[df_rom['rom'] > 300]
if len(bad_joints) > 0:
    print(f"⚠️ Found {len(bad_joints)} joints with ROM > 300° (tracking errors)")
    print(bad_joints[['joint_name', 'rom']])
else:
    print("✅ All joints have acceptable ROM values")
```

## Questions?

**Q: Can I compare these ROM values to clinical literature?**  
A: **NO** - This ROM uses rotation vectors, not anatomical Euler angles.

**Q: Why not use anatomical ROM?**  
A: Rotation vectors avoid gimbal lock and wrapping artifacts, making them better for QC.

**Q: How do I get anatomical ROM?**  
A: Need to implement Euler angle based ROM (see `docs/ROM_DOCUMENTATION.md` - Literature Analysis section).

**Q: Is this ROM wrong?**  
A: **NO** - It's correct for QC purposes. Just different from clinical ROM.

---

**Remember**: This ROM is a **quality control metric**, not clinical ROM!

**Last Updated**: 2026-01-23  
**Documentation**: `docs/ROM_DOCUMENTATION.md`
