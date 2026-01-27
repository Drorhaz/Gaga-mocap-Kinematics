# Change Log #1: DataFrame Fragmentation Fix

## Date
2026-01-25

## Notebook
`06_rotvec_omega.ipynb` - Cell 4 (`compute_omega_ultimate` function)

## Problem
The original code caused severe DataFrame fragmentation by repeatedly inserting columns one at a time:
```python
derivs = pd.DataFrame(index=df.index)
derivs['time_s'] = df['time_s']
# ... in loop:
derivs[f"{out_name}_X_vel"] = omega_deg[:, 0]  # Repeated 200+ times
derivs[f"{out_name}_Y_vel"] = omega_deg[:, 1]
# etc...
```

This triggered 100+ `PerformanceWarning` messages:
```
PerformanceWarning: DataFrame is highly fragmented. This is usually the result 
of calling `frame.insert` many times, which has poor performance.
```

### Performance Impact
- **Execution time**: 3-5 seconds (fragmented) → Expected: <1 second (optimized)
- **Memory usage**: Excessive memory allocations and copies
- **Warning spam**: 200+ warnings cluttering output

## Solution
Refactored to build all columns in a dictionary first, then create DataFrame once:

```python
# Initialize dictionary instead of DataFrame
result_dict = {'time_s': df['time_s'].values}

# In loop: Add to dictionary (not DataFrame)
result_dict[f"{out_name}_X_vel"] = omega_deg[:, 0]
result_dict[f"{out_name}_Y_vel"] = omega_deg[:, 1]
result_dict[f"{out_name}_Z_vel"] = omega_deg[:, 2]
result_dict[f"{out_name}_mag_vel"] = mag_v
result_dict[f"{out_name}_X_acc"] = alpha_deg[:, 0]
result_dict[f"{out_name}_Y_acc"] = alpha_deg[:, 1]
result_dict[f"{out_name}_Z_acc"] = alpha_deg[:, 2]

# After loop: Build DataFrame once
derivs = pd.DataFrame(result_dict)
return derivs, audit_metrics
```

## Changes Made
1. **Line 503**: Changed from `derivs = pd.DataFrame(index=df.index)` to `result_dict = {'time_s': df['time_s'].values}`
2. **Line 504**: Removed `derivs['time_s'] = df['time_s']` (now in dict initialization)
3. **Lines 605-612**: Changed all `derivs[...]` assignments to `result_dict[...]`
4. **Line 614**: Added `derivs = pd.DataFrame(result_dict)` before return statement

## Expected Benefits
- ✅ **10-50x faster** execution for Cell 4
- ✅ **Zero** PerformanceWarning messages
- ✅ **Lower memory** footprint during computation
- ✅ **Identical output** - no functional changes to results

## Verification Steps
1. Run Cell 4 in the notebook
2. Check execution time (should be <1 second)
3. Verify no PerformanceWarning messages appear
4. Confirm output DataFrame has same shape and columns as before
5. Compare `df_omega` checksums before/after (should be identical)

## Backward Compatibility
✅ **Fully compatible** - No API changes, same inputs/outputs, same column names/order

## References
- Pandas documentation: "Avoid repeated frame.insert() calls"
- Performance best practice: Build dict → DataFrame() instead of incremental inserts
