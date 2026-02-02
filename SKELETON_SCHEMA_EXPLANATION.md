# Skeleton Schema Explanation: Offsets and Quaternion Convention

## 1. Offsets

### What Are Offsets?

**Offsets** are 3D position vectors `[x, y, z]` that define the **rest/T-pose bone lengths** in the skeleton hierarchy. They represent the position of each joint **relative to its parent joint** in the skeleton's default pose.

### Origin: BVH (BioVision Hierarchy) Format

**Offsets are a standard concept from the BVH (BioVision Hierarchy) file format**, which is the industry-standard format for motion capture data.

**Where they come from:**
- Your schema file shows: `"source": "BVH"` and `"bvh_filename": "763_T2_P2_R2_Take_2025-12-25 10.51.23 AM_005_763.bvh"`
- BVH files contain a **HIERARCHY section** that defines the skeleton structure
- Each joint in the BVH hierarchy has an **OFFSET** field that specifies its position relative to its parent
- These offsets are extracted from the BVH file and stored in your `skeleton_schema.json`

**BVH File Structure Example:**
```
HIERARCHY
ROOT Hips
{
    OFFSET 0.0 0.0 0.0
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT Spine
    {
        OFFSET 0.0 7.674516 -0.0
        CHANNELS 3 Zrotation Xrotation Yrotation
        ...
    }
}
```

### Is the Offset Role Generic?

**The CONCEPT is generic, but the VALUES are session-specific:**

#### Generic Concept ✅
- **The field/parameter exists** in all BVH files and skeleton formats
- **Standard practice**: Every motion capture format includes offset/translation data
- **Universal structure**: All skeleton animation systems need to define bone lengths

#### Session-Specific Values ❌
- **Each BVH file has different offset values** based on:
  - The skeleton model used (different subjects = different bone lengths)
  - The motion capture system calibration
  - The specific recording session
- **Your schema file is tied to one specific BVH file**: `"763_T2_P2_R2_Take_2025-12-25 10.51.23 AM_005_763.bvh"`
- **Offsets are extracted per session**, not universal constants

**In Your Pipeline:**
- Offsets come from **one specific BVH file** for **one specific recording session**
- They represent **that subject's skeleton model** at **that recording time**
- If you process a different session/subject, you'd need offsets from **their** BVH file

**Why This Matters:**
- ✅ **Concept is reusable**: The pipeline code works with any BVH file's offsets
- ❌ **Values are not**: Each session needs its own offset values from its BVH file
- 🔄 **Per-session extraction**: Offsets must be extracted from each session's BVH file

### Location in Schema
```json
"offsets": {
  "Hips": [0.0, 0.0, 0.0],
  "Spine": [0.0, 7.674516, -0.0],
  "LeftArm": [11.532102, 1e-06, -1e-06],
  ...
}
```

### Key Properties

1. **Units**: Centimeters (cm) - these are bone lengths in the skeleton model
2. **Coordinate System**: Local to parent joint
3. **Purpose**: 
   - Define bone lengths for quality control
   - Validate tracking consistency (bone lengths should remain constant)
   - Calculate expected bone lengths for comparison with actual motion capture data

### Example Interpretation

```json
"LeftArm": [11.532102, 1e-06, -1e-06]
```

This means:
- **X-axis**: 11.53 cm (forward/backward from parent)
- **Y-axis**: ~0 cm (up/down)
- **Z-axis**: ~0 cm (left/right)

The **bone length** = `√(11.532² + 0.001² + 0.001²) ≈ 11.53 cm`

### How Offsets Are Used

1. **Bone Length QC** (`src/qc.py`):
   ```python
   # Compare actual bone lengths from mocap data vs. expected from offsets
   L_bvh = np.linalg.norm(offset)  # Expected length from schema
   L_actual = np.linalg.norm(child_pos - parent_pos)  # Actual from data
   ratio = L_actual / L_bvh  # Should be ~1.0 if consistent
   ```

2. **Validation**: 
   - If actual bone lengths deviate significantly from offsets, it indicates:
     - Tracking errors
     - Marker occlusion
     - Reconstruction artifacts

3. **Scaling Detection**:
   - Offsets help detect if data is in meters vs. centimeters
   - If bone lengths are ~100x larger, data is likely in meters

### Important Notes

- **Hips offset is [0, 0, 0]**: Root joint has no parent, so no offset (standard in BVH format)
- **Symmetry**: Left/Right pairs should have mirrored offsets (e.g., `LeftArm: [11.53, ...]` vs `RightArm: [-11.53, ...]`)
- **Small values (1e-06)**: These are essentially zero, representing perfect alignment in that axis
- **BVH Standard**: Offsets are extracted directly from the BVH file's HIERARCHY section
- **Units**: Typically centimeters in BVH files, but can vary (your schema uses cm)
- **Session-Specific**: These offset values are specific to the BVH file `"763_T2_P2_R2_Take_2025-12-25 10.51.23 AM_005_763.bvh"` - different sessions/subjects will have different offset values

---

## 2. Quaternion Convention (quat_convention)

### What Is Quaternion Convention?

**Quaternion convention** specifies the **order and format** of quaternion components. Quaternions represent rotations using 4 numbers, but different systems use different orderings.

### Location in Schema
```json
"notes": {
  "quat_convention": "xyzw (SciPy Rotation format)",
  "intended_use": "schema + bone-length QC + joint hierarchy for q_local"
}
```

### Convention: `xyzw` (SciPy Format)

This means quaternions are stored as: **[x, y, z, w]**

- **x, y, z**: Vector part (rotation axis × sin(θ/2))
- **w**: Scalar part (cos(θ/2))

### Alternative Conventions

| Convention | Order | Used By |
|------------|-------|---------|
| **xyzw** | [x, y, z, w] | **SciPy, this pipeline** |
| **wxyz** | [w, x, y, z] | Unity, some game engines |
| **ijkl** | [i, j, k, l] | Mathematical notation |

### Why This Matters

**Critical for correct rotation calculations!** Using the wrong convention will produce incorrect rotations.

### Example

If your data has quaternions as `[qx, qy, qz, qw]`:
- ✅ **Correct**: `Rotation.from_quat([qx, qy, qz, qw])` (SciPy expects xyzw)
- ❌ **Wrong**: `Rotation.from_quat([qw, qx, qy, qz])` (would be wxyz format)

### How It's Used in the Pipeline

1. **Quaternion Loading** (`src/calibration.py`):
   ```python
   # Stack into (N, 4) array in xyzw order
   quats = np.stack([qx, qy, qz, qw], axis=1)  # Shape: (N, 4)
   R = Rotation.from_quat(quats)  # SciPy expects xyzw
   ```

2. **Data Columns**: The pipeline expects columns named:
   - `JointName__qx`
   - `JointName__qy`
   - `JointName__qz`
   - `JointName__qw`

   These are read in **xyzw order** and passed to SciPy's `Rotation` class.

3. **Quaternion Operations**:
   - All quaternion math (SLERP, multiplication, etc.) assumes xyzw format
   - Converting to Euler angles uses xyzw convention
   - Rotation composition respects this ordering

### Important Notes

- **SciPy Rotation**: The `scipy.spatial.transform.Rotation` class expects `xyzw` format
- **Consistency**: All quaternion operations in the pipeline must use the same convention
- **Data Validation**: When loading data, ensure quaternions match this convention
- **Documentation**: Always document quaternion convention when sharing data

---

## Summary Table

| Concept | Purpose | Format | Units |
|---------|---------|--------|-------|
| **Offsets** | Define bone lengths in rest pose | `[x, y, z]` vector | Centimeters (cm) |
| **Quat Convention** | Specify quaternion component order | `xyzw` format | Unitless (normalized) |

## Practical Usage

### Checking Bone Lengths
```python
import json
import numpy as np

with open('config/skeleton_schema.json') as f:
    schema = json.load(f)

# Get offset for a bone
offset = schema['offsets']['LeftArm']  # [11.532102, 1e-06, -1e-06]
bone_length = np.linalg.norm(offset)  # ~11.53 cm

# Compare with actual data
actual_length = np.linalg.norm(left_arm_pos - left_shoulder_pos)
ratio = actual_length / bone_length  # Should be ~1.0
```

### Working with Quaternions
```python
from scipy.spatial.transform import Rotation

# Load quaternion in xyzw format
q_xyzw = [qx, qy, qz, qw]  # From columns: __qx, __qy, __qz, __qw

# Create Rotation object (expects xyzw)
R = Rotation.from_quat(q_xyzw)

# Convert to Euler angles
euler = R.as_euler('xyz', degrees=True)
```
