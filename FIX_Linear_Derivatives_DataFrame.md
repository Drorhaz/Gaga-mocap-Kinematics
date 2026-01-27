# Fix: Linear Derivatives DataFrame Fragmentation

## Location
`notebooks/06_rotvec_omega.ipynb` - Cell containing `compute_linear_derivs_savgol()` function

## Problem
Lines 746-747 and 761-765, 772, 777 cause DataFrame fragmentation:
```python
derivs = pd.DataFrame()
derivs['time_s'] = df_pos['time_s']
# ... in loops:
derivs[f"{col}_vel"] = vel  # ~81 insertions
derivs[f"{col}_acc"] = acc  # ~81 insertions
derivs[f"{joint}_mag_lin_vel"] = ...  # ~27 insertions
derivs[f"{joint}_mag_lin_acc"] = ...  # ~27 insertions
```

## Solution
Replace with dictionary-based approach:

### Step 1: Replace initialization (around line 746-747)
**FROM:**
```python
derivs = pd.DataFrame()
derivs['time_s'] = df_pos['time_s']  # FIXED: Add time_s column
```

**TO:**
```python
# OPTIMIZED: Build all columns at once (eliminates DataFrame fragmentation)
result_dict = {'time_s': df_pos['time_s'].values}
```

### Step 2: Replace loop assignments (around lines 761-765)
**FROM:**
```python
for col in pos_cols:
    data = df_pos[col].values
    vel = savgol_filter(data, window_length=w_len, polyorder=poly, deriv=1, delta=dt)
    derivs[f"{col}_vel"] = vel
    acc = savgol_filter(data, window_length=w_len, polyorder=poly, deriv=2, delta=dt)
    derivs[f"{col}_acc"] = acc
```

**TO:**
```python
for col in pos_cols:
    data = df_pos[col].values
    vel = savgol_filter(data, window_length=w_len, polyorder=poly, deriv=1, delta=dt)
    result_dict[f"{col}_vel"] = vel
    acc = savgol_filter(data, window_length=w_len, polyorder=poly, deriv=2, delta=dt)
    result_dict[f"{col}_acc"] = acc
```

### Step 3: Add temporary DataFrame for magnitude calculations (after pos_cols loop, before joints loop)
**ADD BEFORE:**
```python
# Calculate Magnitude for each joint (useful for Outlier Detection)
```

**ADD:**
```python
# Build temporary DataFrame for magnitude calculations (needed for column access)
derivs_temp = pd.DataFrame(result_dict)
```

### Step 4: Replace magnitude calculations (around lines 772, 777)
**FROM:**
```python
for joint in joints:
    v_cols = [f"{joint}__px_vel", f"{joint}__py_vel", f"{joint}__pz_vel"]
    if all(c in derivs.columns for c in v_cols):
        derivs[f"{joint}_mag_lin_vel"] = np.linalg.norm(derivs[v_cols].values, axis=1)
    a_cols = [f"{joint}__px_acc", f"{joint}__py_acc", f"{joint}__pz_acc"]
    if all(c in derivs.columns for c in a_cols):
        derivs[f"{joint}_mag_lin_acc"] = np.linalg.norm(derivs[a_cols].values, axis=1)
```

**TO:**
```python
for joint in joints:
    v_cols = [f"{joint}__px_vel", f"{joint}__py_vel", f"{joint}__pz_vel"]
    if all(c in derivs_temp.columns for c in v_cols):
        result_dict[f"{joint}_mag_lin_vel"] = np.linalg.norm(derivs_temp[v_cols].values, axis=1)
    a_cols = [f"{joint}__px_acc", f"{joint}__py_acc", f"{joint}__pz_acc"]
    if all(c in derivs_temp.columns for c in a_cols):
        result_dict[f"{joint}_mag_lin_acc"] = np.linalg.norm(derivs_temp[a_cols].values, axis=1)
```

### Step 5: Replace return statement (around line 779)
**FROM:**
```python
    return derivs
```

**TO:**
```python
    # Build final DataFrame once at the end (eliminates fragmentation)
    derivs = pd.DataFrame(result_dict)
    return derivs
```

## Expected Result
- ✅ Zero PerformanceWarning messages
- ✅ 10-50x faster execution
- ✅ Identical output data
- ✅ Same column names and order
