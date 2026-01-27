# Change Log #2: Enhanced Quaternion Continuity Enforcement

## Date
2026-01-25

## Notebook
`06_rotvec_omega.ipynb` - Cell 4 (`compute_omega_ultimate` function)

## Problem
Quaternion double-cover ambiguity can cause velocity spikes:
- Quaternions q and -q represent the **same rotation**
- Without continuity enforcement, quaternions can "flip" between hemispheres
- These sign flips create artificial velocity spikes in derivative calculations
- Previous code only enforced continuity on `q_final` (after all transformations)

### Mathematical Background
```
Quaternion interpolation requires "shortest path" on unit sphere.
If dot(q[i], q[i-1]) < 0, quaternions point to opposite hemispheres.
Flipping sign ensures continuity: q[i] := -q[i]
```

### Why This Matters
Without early continuity enforcement:
1. **Input discontinuities** propagate through transformations
2. **Parent quaternion flips** affect relative rotation calculations
3. **Compounding errors** from multiple transformation stages
4. **Higher velocity spikes** that are purely artifacts

## Solution
Enhanced quaternion continuity enforcement at **three stages**:

### Stage 1: Input Child Quaternions (NEW)
```python
# Before transformations - ensure raw data is continuous
q_c, input_flips_c = enforce_quaternion_continuity(q_c, joint_name)
audit_metrics[f"{out_name}_input_flips_child"] = input_flips_c
```

### Stage 2: Input Parent Quaternions (NEW)
```python
# Parent quaternions also need continuity
q_p, input_flips_p = enforce_quaternion_continuity(q_p, parent_name)
audit_metrics[f"{out_name}_input_flips_parent"] = input_flips_p
```

### Stage 3: Final Transformed Quaternions (ENHANCED)
```python
# After all transformations - final safety check
q_final, final_flips = enforce_quaternion_continuity(q_final, out_name)
audit_metrics[f"{out_name}_final_flips"] = final_flips
audit_metrics[f"{out_name}_total_flips"] = (
    input_flips_child + input_flips_parent + final_flips
)
```

### Helper Function (NEW)
```python
def enforce_quaternion_continuity(quats, segment_name=""):
    """
    Ensures quaternions follow shortest path (no double-cover ambiguity).
    
    Returns: aligned quaternions, flip count
    """
    aligned = quats.copy()
    flip_count = 0
    for i in range(1, len(aligned)):
        if np.dot(aligned[i], aligned[i-1]) < 0:
            aligned[i] *= -1  # Flip to ensure shortest path
            flip_count += 1
    return aligned, flip_count
```

## Changes Made
1. **Lines 296-310**: Added `enforce_quaternion_continuity()` helper function
2. **Line 343**: Apply continuity to child quaternions BEFORE transformations
3. **Line 344**: Track input child flips in audit metrics
4. **Line 356**: Apply continuity to parent quaternions BEFORE transformations
5. **Line 357**: Track input parent flips in audit metrics
6. **Lines 373-378**: Use helper function for final continuity + track total flips

## Expected Benefits
- ✅ **Fewer velocity spikes** from quaternion discontinuities
- ✅ **Smoother derivatives** (especially at high velocities)
- ✅ **Better audit tracking** (know where/when flips occur)
- ✅ **Cleaner code** (reusable function vs inline loop)
- ✅ **Early problem detection** (catch issues before they compound)

## New Audit Metrics
For each joint, the following metrics are now tracked:
- `{joint}_input_flips_child`: Flips in raw child quaternions
- `{joint}_input_flips_parent`: Flips in raw parent quaternions (if exists)
- `{joint}_final_flips`: Flips after transformations
- `{joint}_total_flips`: Sum of all flips (diagnostic for tracking quality)

## Expected Results
### Typical Flip Counts (Good Data):
- Input flips: 0-5 per joint over full session
- Final flips: 0-2 per joint (most transformations preserve continuity)
- Total flips: <10 per joint

### Warning Signs (Poor Tracking):
- Input flips: >20 per joint (sensor re-initializations, tracking loss)
- Final flips: >10 per joint (numerical instability in transformations)
- Investigate frames where flips occur using outlier analysis

## Verification Steps
1. Run Cell 4 in the notebook
2. Check `ang_audit_metrics` dictionary after execution:
   ```python
   # Example inspection:
   for key in sorted(ang_audit_metrics.keys()):
       if 'flips' in key:
           print(f"{key}: {ang_audit_metrics[key]}")
   ```
3. Compare velocity magnitudes before/after (should be smoother)
4. Check outlier counts (should decrease if flips were causing spikes)

## Backward Compatibility
✅ **Fully compatible** - No API changes
- Same inputs/outputs
- Same column names in results
- Only internal processing enhanced
- Additional audit metrics (non-breaking addition)

## Scientific References
- Shoemake, K. (1985): "Animating Rotation with Quaternion Curves"
- Dam, E.B. et al. (1998): "Quaternions, Interpolation and Animation"
- Huynh, D.Q. (2009): "Metrics for 3D Rotations: Comparison and Analysis"
- LaValle, S.M. (2006): "Planning Algorithms" - Section 4.3.2 (Quaternion Interpolation)

## Notes
- This change does NOT alter the mathematical result for continuous data
- It CORRECTS artifacts from quaternion representation ambiguity
- It's a numerical stability enhancement, not a new feature
- The helper function could be extracted to a utilities module in future refactoring
